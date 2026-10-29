"""Small client with retries for Herdr's Unix socket API."""

from __future__ import annotations

import json
import socket
import time
from typing import Callable, Mapping, Protocol

MAX_RESPONSE_BYTES = 4 * 1024 * 1024
SOURCE = "plugin:naeliofreires.agent-tree"
Transport = Callable[[bytes, float], bytes]


class AgentTreeApi(Protocol):
    """Small API used by tree commands and test fakes."""

    def agents(self) -> list[dict[str, object]]: ...

    def panes(self) -> list[dict[str, object]]: ...

    def report(self, pane_id: str, tokens: dict[str, str | None]) -> None: ...

    def set_view(self) -> None: ...

    def clear_view(self) -> None: ...


class ApiError(RuntimeError):
    """Raised when the daemon request fails."""

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code


class HerdrApi:
    """Call Herdr with a time limit. Tests can use their own send function."""

    def __init__(self, socket_path: str, transport: Transport | None = None) -> None:
        self.socket_path = socket_path
        self.transport = transport or self._unix_transport

    def request(self, method: str, params: dict[str, object]) -> dict[str, object]:
        """Send one request with a time limit; example: ``api.request("agent.list", {})``."""
        request_id = f"agent-tree-{time.time_ns()}"
        payload = self._encode(request_id, method, params)
        deadline = time.monotonic() + 2.0
        for attempt in range(2):
            try:
                if time.monotonic() >= deadline:
                    raise TimeoutError("request exceeded 2 seconds")
                raw = self.transport(payload, deadline)
                response = self._decode(raw, request_id)
                return self._result(response, method)
            except (OSError, TimeoutError) as exc:
                if attempt == 1:
                    raise ApiError(f"{method}: transport failed: {exc}") from exc
                _sleep_for_retry(deadline, attempt, method, exc)
        raise ApiError(f"{method}: request exhausted")

    @staticmethod
    def _encode(request_id: str, method: str, params: dict[str, object]) -> bytes:
        request = {"id": request_id, "method": method, "params": params}
        return json.dumps(request, separators=(",", ":")).encode("utf-8") + b"\n"

    def agents(self) -> list[dict[str, object]]:
        """Return current agent records.

        Example: ``agents = api.agents()``.
        """
        payload = self.request("agent.list", {})
        agents = payload.get("agents")
        if not isinstance(agents, list):
            raise ApiError(f"agent.list response {agents!r} expected agents list")
        return [self._agent_record(agent) for agent in agents]

    def panes(self) -> list[dict[str, object]]:
        """Return current pane records.

        Example: ``panes = api.panes()``.
        """
        payload = self.request("pane.list", {})
        panes = payload.get("panes")
        if not isinstance(panes, list):
            raise ApiError(f"pane.list response {panes!r} expected panes list")
        return [self._agent_record(pane) for pane in panes]

    @staticmethod
    def _agent_record(agent: object) -> dict[str, object]:
        if not isinstance(agent, dict):
            raise ApiError(f"agent.list record {agent!r} expected object")
        return agent

    def report(self, pane_id: str, tokens: dict[str, str | None]) -> None:
        """Send this plugin's metadata for one pane.

        Example: ``api.report("w1:p1", {"key": "value"})``.
        """
        params = {"pane_id": pane_id, "source": SOURCE, "tokens": tokens}
        self.request("pane.report_metadata", params)

    def set_view(self) -> None:
        """Set the Agent Tree view.

        Example: ``api.set_view()``.
        """
        sort = [
            {"field": "workspace_order", "order": "asc"},
            {"field": {"token": "naeliofreires_tree_order"}, "order": "asc"},
        ]
        params = {"source": SOURCE, "label": "Agent Tree", "sort": sort}
        self.request("agent.view.set", params)

    def clear_view(self) -> None:
        """Clear this plugin's Agent Tree view.

        Example: ``api.clear_view()``.
        """
        self.request("agent.view.clear", {"source": SOURCE})

    def _unix_transport(self, payload: bytes, deadline: float) -> bytes:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as channel:
            channel.settimeout(_remaining(deadline))
            channel.connect(self.socket_path)
            channel.settimeout(_remaining(deadline))
            channel.sendall(payload)
            return self._read(channel, deadline)

    @staticmethod
    def _read(channel: socket.socket, deadline: float) -> bytes:
        chunks: list[bytes] = []
        total = 0
        while total < MAX_RESPONSE_BYTES:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("socket response exceeded 2 seconds")
            channel.settimeout(remaining)
            chunk = channel.recv(min(65536, MAX_RESPONSE_BYTES - total))
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)
            total += len(chunk)
            if b"\n" in chunk:
                return b"".join(chunks)
        raise ApiError(f"response exceeded {MAX_RESPONSE_BYTES} bytes")

    @staticmethod
    def _decode(raw: bytes, request_id: str) -> dict[str, object]:
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ApiError(f"response exceeded {MAX_RESPONSE_BYTES} bytes")
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ApiError(
                f"protocol response {raw[:120]!r} expected JSON object"
            ) from exc
        if not isinstance(value, dict):
            raise ApiError(f"protocol response {value!r} expected object")
        if value.get("id") != request_id:
            raise ApiError(
                f"protocol response id {value.get('id')!r} expected {request_id!r}"
            )
        return value

    @staticmethod
    def _result(response: Mapping[str, object], method: str) -> dict[str, object]:
        error = response.get("error")
        if error is not None:
            code = error.get("code") if isinstance(error, Mapping) else None
            raise ApiError(
                f"{method}: daemon error {error!r}",
                code if isinstance(code, str) else None,
            )
        result = response.get("result")
        if not isinstance(result, dict):
            raise ApiError(f"{method} response {result!r} expected result object")
        return result


def _remaining(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("request exceeded 2 seconds")
    return remaining


def _sleep_for_retry(
    deadline: float, attempt: int, method: str, error: Exception
) -> None:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise ApiError(f"{method}: transport failed: {error}") from error
    time.sleep(min(0.05 * (attempt + 1), remaining))
