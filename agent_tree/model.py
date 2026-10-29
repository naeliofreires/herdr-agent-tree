"""Typed models and validation for the Herdr agent tree."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

MAX_AGENTS = 2048
MAX_DEPTH = 16


class StateShapeError(ValueError):
    """Raised when persisted plugin state has an invalid shape."""


@dataclass(frozen=True)
class Agent:
    """A bounded projection of one daemon agent record.

    Example: ``Agent.from_record(record)``.
    """

    terminal_id: str
    pane_id: str
    workspace_id: str
    tab_id: str

    @classmethod
    def from_record(cls, record: object) -> "Agent":
        if not isinstance(record, Mapping):
            raise StateShapeError(f"agent {record!r} expected an object")
        terminal_id = record.get("terminal_id")
        pane_id = record.get("pane_id")
        workspace_id = record.get("workspace_id")
        tab_id = record.get("tab_id")
        fields = (terminal_id, pane_id, workspace_id, tab_id)
        if any(not isinstance(value, str) or not value for value in fields):
            raise StateShapeError(f"agent {record!r} expected non-empty string ids")
        return cls(
            terminal_id=terminal_id,
            pane_id=pane_id,
            workspace_id=workspace_id,
            tab_id=tab_id,
        )


@dataclass(frozen=True)
class LinkState:
    """Plugin-owned enabled flag and terminal-id parent links.

    Example: ``LinkState.from_json({})`` creates a disabled empty state.
    """

    enabled: bool
    links: dict[str, str]

    @classmethod
    def from_json(cls, payload: object) -> "LinkState":
        if not isinstance(payload, Mapping):
            raise StateShapeError(f"state {payload!r} expected an object")
        enabled = payload.get("enabled", False)
        links = payload.get("links", {})
        if not isinstance(enabled, bool) or not isinstance(links, Mapping):
            raise StateShapeError(
                f"state {payload!r} expected enabled boolean and links object"
            )
        normalized = _normalize_links(links)
        return cls(enabled=enabled, links=normalized)

    def to_json(self) -> dict[str, object]:
        """Return a JSON-compatible state mapping.

        Example: ``state.to_json()["links"]``.
        """
        return {"enabled": self.enabled, "links": dict(self.links)}


def _normalize_links(links: Mapping[object, object]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for child, parent in links.items():
        if (
            not isinstance(child, str)
            or not isinstance(parent, str)
            or not child
            or not parent
        ):
            raise StateShapeError(
                f"link {child!r}: {parent!r} expected non-empty strings"
            )
        normalized[child] = parent
    return normalized
