import json
import time
import unittest

from agent_tree.api import ApiError, HerdrApi


class FakeTransport:
    def __init__(self, responses: list[bytes | Exception]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []
        self.deadlines: list[float] = []

    def __call__(self, payload: bytes, deadline: float) -> bytes:
        self.deadlines.append(deadline)
        request = json.loads(payload)
        self.calls.append(request)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        if response.startswith(b'{"result"'):
            response = response.replace(
                b'{"result"', b'{"id":"' + request["id"].encode() + b'","result"', 1
            )
        return response


class SlowSocket:
    def __init__(self, behavior: str) -> None:
        self.behavior = behavior
        self.timeout = 0.0

    def settimeout(self, timeout: float) -> None:
        self.timeout = timeout

    def recv(self, size: int) -> bytes:
        if self.behavior == "timeout":
            raise TimeoutError("slow fake")
        return b"x" * size


class ApiTests(unittest.TestCase):
    def test_agents_and_metadata_calls(self) -> None:
        transport = FakeTransport([b'{"result":{"agents":[]}}\n'] * 4)
        api = HerdrApi("/tmp/socket", transport)
        self.assertEqual(api.agents(), [])
        api.report(
            "p1",
            {
                "naeliofreires_tree_prefix": "\u200b",
                "naeliofreires_tree_order": "00000000",
            },
        )
        api.set_view()
        api.clear_view()
        self._assert_methods(transport)

    def _assert_methods(self, transport: FakeTransport) -> None:
        methods = [call["method"] for call in transport.calls]
        expected = [
            "agent.list",
            "pane.report_metadata",
            "agent.view.set",
            "agent.view.clear",
        ]
        self.assertEqual(methods, expected)

    def test_transport_retries_once(self) -> None:
        transport = FakeTransport([OSError("closed"), b'{"result":{"agents":[]}}\n'])
        self.assertEqual(HerdrApi("/tmp/socket", transport).agents(), [])
        self.assertEqual(len(transport.calls), 2)
        self.assertEqual(transport.deadlines[0], transport.deadlines[1])

    def test_protocol_and_daemon_errors_are_clear(self) -> None:
        for response in (b"bad\n", b'{"error":{"code":"bad"}}\n', b'{"result":[]}\n'):
            with self.subTest(response=response), self.assertRaises(ApiError):
                HerdrApi("/tmp/socket", FakeTransport([response])).agents()

    def test_correlation_and_injected_response_bound(self) -> None:
        with self.assertRaises(ApiError):
            HerdrApi._decode(b'{"id":"wrong","result":{}}', "expected")
        oversized = b"x" * (4 * 1024 * 1024 + 1)
        with self.assertRaises(ApiError):
            HerdrApi._decode(oversized, "expected")

    def test_socket_reader_enforces_deadline_and_bound(self) -> None:
        with self.assertRaises(TimeoutError):
            HerdrApi._read(SlowSocket("timeout"), time.monotonic() + 2.0)
        with self.assertRaises(ApiError):
            HerdrApi._read(SlowSocket("oversize"), time.monotonic() + 2.0)
