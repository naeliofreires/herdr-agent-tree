"""Atomic, per-socket plugin state storage."""

from __future__ import annotations

import hashlib
import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, TextIO

from .model import LinkState, StateShapeError


class StateStore:
    """Persist links in a user state directory scoped to a Herdr socket."""

    def __init__(self, root: Path, socket_path: str) -> None:
        digest = hashlib.sha256(socket_path.encode("utf-8")).hexdigest()[:24]
        self.path = root / f"{digest}.json"
        self.lock_path = root / f"{digest}.lock"

    @contextmanager
    def locked(self) -> Iterator[None]:
        """Hold the per-socket lock for a state transaction.

        Example: ``with store.locked(): store.save(state)``.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.lock_path.open("a+")
        try:
            self._lock(handle)
            yield
        finally:
            self._unlock(handle)
            handle.close()

    def load(self) -> LinkState:
        """Load state or return the disabled empty default.

        Example: ``state = store.load()``.
        """
        if not self.path.exists():
            return LinkState(enabled=False, links={})
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise StateShapeError(
                f"state file {self.path}: expected valid JSON: {exc}"
            ) from exc
        return LinkState.from_json(payload)

    def save(self, state: LinkState) -> None:
        """Atomically persist a state value.

        Example: ``store.save(LinkState(True, {}))``.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(state.to_json(), sort_keys=True), encoding="utf-8"
        )
        os.replace(temporary, self.path)

    @staticmethod
    def _lock(handle: TextIO) -> None:
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)

    @staticmethod
    def _unlock(handle: TextIO) -> None:
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
