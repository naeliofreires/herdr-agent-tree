"""Build deterministic workspace-grouped prefixes for agent rows."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .model import Agent, MAX_AGENTS, MAX_DEPTH


@dataclass(frozen=True)
class TreeRow:
    """Metadata to report for one agent pane."""

    agent: Agent
    prefix: str
    order: str


def parse_agents(records: list[dict[str, object]]) -> list[Agent]:
    """Validate and convert daemon records.

    Example: ``agents = parse_agents(api.agents())``.
    """
    if len(records) > MAX_AGENTS:
        raise ValueError(
            f"agent list has {len(records)} records; expected at most {MAX_AGENTS}"
        )
    agents = [Agent.from_record(record) for record in records]
    terminals = [agent.terminal_id for agent in agents]
    panes = [agent.pane_id for agent in agents]
    if len(set(terminals)) != len(terminals):
        raise ValueError("agent list contains duplicate terminal ids")
    if len(set(panes)) != len(panes):
        raise ValueError("agent list contains duplicate pane ids")
    return agents


def validate_link(
    child: Agent, parent: Agent, links: dict[str, str], agents: dict[str, Agent]
) -> None:
    """Validate one proposed parent link; example: ``validate_link(...)``."""
    if child.terminal_id == parent.terminal_id:
        raise ValueError(f"link {child.terminal_id!r} cannot point to itself")
    if child.workspace_id != parent.workspace_id:
        raise ValueError(
            f"link {child.terminal_id!r} and {parent.terminal_id!r} must share a workspace"
        )
    _validate_proposed_chain(child, parent.terminal_id, links, agents)


def _validate_proposed_chain(
    child: Agent, cursor: str, links: dict[str, str], agents: dict[str, Agent]
) -> None:
    for _ in range(MAX_DEPTH):
        if cursor not in links:
            return
        cursor = links[cursor]
        if cursor == child.terminal_id:
            raise ValueError(f"link {child.terminal_id!r} would create a cycle")
        if cursor not in agents:
            return
    raise ValueError(f"link {child.terminal_id!r} exceeds depth {MAX_DEPTH}")


def validate_graph(agents: list[Agent], links: dict[str, str]) -> None:
    """Validate all known same-workspace links.

    Example: ``validate_graph(agents, state.links)``.
    """
    by_id = {agent.terminal_id: agent for agent in agents}
    for child_id, parent_id in links.items():
        child = by_id.get(child_id)
        parent = by_id.get(parent_id)
        if child is None or parent is None:
            continue
        if child.workspace_id != parent.workspace_id:
            continue
        _validate_chain(child.terminal_id, links, by_id)


def _validate_chain(
    start: str, links: dict[str, str], agents: dict[str, Agent]
) -> None:
    seen: set[str] = set()
    cursor = start
    depth = 1
    while cursor in links:
        parent = _chain_parent(cursor, links, agents, seen, start)
        if parent is None:
            return
        depth += 1
        if depth > MAX_DEPTH:
            raise ValueError(f"link graph at {start!r} exceeds depth {MAX_DEPTH}")
        cursor = parent


def _chain_parent(
    cursor: str,
    links: dict[str, str],
    agents: dict[str, Agent],
    seen: set[str],
    start: str,
) -> str | None:
    if cursor in seen:
        raise ValueError(f"link graph at {start!r} contains a cycle")
    seen.add(cursor)
    parent = links[cursor]
    current = agents.get(cursor)
    parent_agent = agents.get(parent)
    if current is None or parent_agent is None:
        return None
    if current.workspace_id != parent_agent.workspace_id:
        return None
    return parent


def build_rows(agents: list[Agent], links: dict[str, str]) -> list[TreeRow]:
    """Build stable workspace-grouped tree rows.

    Example: ``rows = build_rows(agents, links)``.
    """
    validate_graph(agents, links)
    by_id = {agent.terminal_id: agent for agent in agents}
    children, roots = _group_agents(agents, links, by_id)
    return _walk_roots(agents, roots, children)


def _group_agents(
    agents: list[Agent], links: dict[str, str], by_id: dict[str, Agent]
) -> tuple[dict[str, list[Agent]], dict[str, list[Agent]]]:
    children: dict[str, list[Agent]] = defaultdict(list)
    roots: dict[str, list[Agent]] = defaultdict(list)
    for agent in agents:
        parent_id = links.get(agent.terminal_id)
        parent = by_id.get(parent_id or "")
        if parent is None or parent.workspace_id != agent.workspace_id:
            roots[agent.workspace_id].append(agent)
        else:
            children[parent.terminal_id].append(agent)
    return children, roots


def _walk_roots(
    agents: list[Agent], roots: dict[str, list[Agent]], children: dict[str, list[Agent]]
) -> list[TreeRow]:
    rows: list[TreeRow] = []
    rank = 0
    for workspace in dict.fromkeys(agent.workspace_id for agent in agents):
        for root_index, root in enumerate(roots[workspace]):
            rank = _visit(
                root,
                children,
                rows,
                rank,
                (),
                root_index == len(roots[workspace]) - 1,
            )
    return rows


def _visit(
    agent: Agent,
    children: dict[str, list[Agent]],
    rows: list[TreeRow],
    rank: int,
    guides: tuple[bool, ...],
    last: bool,
) -> int:
    rows.append(TreeRow(agent, _row_prefix(guides, last), f"{rank:08d}"))
    rank += 1
    descendants = children.get(agent.terminal_id, [])
    if len(guides) >= MAX_DEPTH - 1:
        return rank
    return _visit_descendants(descendants, children, rows, rank, guides, last)


def _row_prefix(guides: tuple[bool, ...], last: bool) -> str:
    branch = "└─ " if last else "├─ "
    guides_text = "".join("│  " if more else "   " for more in guides)
    return "\u200b" + guides_text + branch


def _visit_descendants(
    descendants: list[Agent],
    children: dict[str, list[Agent]],
    rows: list[TreeRow],
    rank: int,
    guides: tuple[bool, ...],
    parent_last: bool,
) -> int:
    for index, child in enumerate(descendants):
        rank = _visit(
            child,
            children,
            rows,
            rank,
            guides + (not parent_last,),
            index == len(descendants) - 1,
        )
    return rank
