"""Command handlers for the Herdr Agent Tree plugin."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .api import AgentTreeApi, ApiError, HerdrApi
from .installation import write_installation_guide
from .model import Agent, LinkState
from .storage import StateStore
from .tree import build_rows, parse_agents, validate_graph, validate_link

NOT_FOUND_CODES = {"pane_not_found", "agent_pane_not_found", "agent_not_found"}


def socket_path_from_env() -> str:
    """Resolve the daemon socket from plugin context or XDG config."""
    configured = os.environ.get("HERDR_SOCKET_PATH")
    return configured or _default_socket_path()


def store_from_env() -> StateStore:
    """Build state storage using the same socket namespace as the API."""
    state_root = os.environ.get("HERDR_PLUGIN_STATE_DIR")
    root = Path(state_root) if state_root else _default_state_root()
    return StateStore(root, socket_path_from_env())


def api_from_env() -> HerdrApi:
    """Build an API client from Herdr's injected runtime environment."""
    return HerdrApi(socket_path_from_env())


def _default_state_root() -> Path:
    state_home = os.environ.get("XDG_STATE_HOME")
    base = Path(state_home) if state_home else Path.home() / ".local/state"
    return base / "herdr/plugins/naeliofreires.agent-tree"


def _default_socket_path() -> str:
    config_home = os.environ.get("XDG_CONFIG_HOME")
    base = Path(config_home) if config_home else Path.home() / ".config"
    return str(base / "herdr/herdr.sock")


def sync(api: AgentTreeApi, store: StateStore) -> int:
    """Synchronize enabled metadata while holding the state lock."""
    with store.locked():
        return _sync_locked(api, store)


def _sync_locked(
    api: AgentTreeApi, store: StateStore, *, cleanup_on_error: bool = False
) -> int:
    state = store.load()
    if not state.enabled:
        return 0
    agents = parse_agents(api.agents())
    rows = build_rows(agents, state.links)
    reported: list[str] = []
    try:
        for row in rows:
            _report_if_present(
                api, row.agent.pane_id, row.prefix, row.order, row.branch_path
            )
            reported.append(row.agent.pane_id)
        api.set_view()
        return len(rows)
    except Exception:
        if cleanup_on_error:
            _cleanup_partial(api, reported)
        raise


def _cleanup_partial(api: AgentTreeApi, pane_ids: list[str]) -> None:
    for pane_id in pane_ids:
        try:
            _clear_if_present(api, pane_id)
        except Exception:
            continue
    try:
        api.clear_view()
    except Exception:
        pass


def _report_if_present(
    api: AgentTreeApi,
    pane_id: str,
    prefix: str | None,
    order: str | None,
    branch_path: str | None,
) -> None:
    try:
        api.report(
            pane_id,
            {
                "naeliofreires_tree_prefix": prefix,
                "naeliofreires_tree_order": order,
                "naeliofreires_tree_path": branch_path,
            },
        )
    except ApiError as exc:
        if exc.code not in NOT_FOUND_CODES:
            raise


def enable(api: AgentTreeApi, store: StateStore) -> int:
    """Enable the projection and roll back the marker if synchronization fails."""
    with store.locked():
        previous = store.load()
        store.save(LinkState(enabled=True, links=previous.links))
        try:
            return _sync_locked(api, store, cleanup_on_error=not previous.enabled)
        except Exception:
            store.save(previous)
            raise


def disable(api: AgentTreeApi, store: StateStore) -> int:
    """Disable first, then clear only metadata owned by this plugin."""
    with store.locked():
        previous = store.load()
        store.save(LinkState(enabled=False, links=previous.links))
        panes = api.panes()
        for pane in panes:
            pane_id = pane.get("pane_id")
            if isinstance(pane_id, str) and pane_id:
                _clear_if_present(api, pane_id)
        api.clear_view()
        return len(panes)


def _clear_if_present(api: AgentTreeApi, pane_id: str) -> None:
    _report_if_present(api, pane_id, None, None, None)


def _agent_refs(agents: list[Agent]) -> dict[str, Agent]:
    refs = {agent.terminal_id: agent for agent in agents}
    refs.update({agent.pane_id: agent for agent in agents})
    return refs


def link(api: AgentTreeApi, store: StateStore, child_ref: str, parent_ref: str) -> None:
    """Persist a parent relationship and synchronize enabled views."""
    agents = parse_agents(api.agents())
    refs = _agent_refs(agents)
    child, parent = refs.get(child_ref), refs.get(parent_ref)
    if child is None or parent is None:
        raise ValueError(f"unknown agent reference {child_ref!r} or {parent_ref!r}")
    with store.locked():
        state = store.load()
        links = dict(state.links)
        validate_link(
            child, parent, links, {agent.terminal_id: agent for agent in agents}
        )
        links[child.terminal_id] = parent.terminal_id
        validate_graph(agents, links)
        store.save(LinkState(enabled=state.enabled, links=links))
        if state.enabled:
            _sync_locked(api, store)


def unlink(api: AgentTreeApi, store: StateStore, child_ref: str) -> None:
    """Remove a parent relationship and synchronize enabled views."""
    agents = parse_agents(api.agents())
    child = _agent_refs(agents).get(child_ref)
    if child is None:
        raise ValueError(f"unknown agent reference {child_ref!r}")
    with store.locked():
        state = store.load()
        links = dict(state.links)
        links.pop(child.terminal_id, None)
        store.save(LinkState(enabled=state.enabled, links=links))
        if state.enabled:
            _sync_locked(api, store)


def list_links(api: AgentTreeApi, store: StateStore) -> None:
    """Print all live agents and their stored parent references."""
    state = store.load()
    rows = build_rows(parse_agents(api.agents()), state.links)
    for row in rows:
        parent = state.links.get(row.agent.terminal_id, "-")
        print(
            f"{row.prefix}{row.agent.terminal_id} pane={row.agent.pane_id} workspace={row.agent.workspace_id} parent={parent}"
        )


def parser() -> argparse.ArgumentParser:
    """Build the plugin's command parser."""
    command_parser = argparse.ArgumentParser(prog="agent-tree")
    commands = command_parser.add_subparsers(dest="command", required=True)
    for name in ("sync", "event", "enable", "disable", "list", "setup"):
        commands.add_parser(name)
    link_parser = commands.add_parser("link")
    link_parser.add_argument("child")
    link_parser.add_argument("--parent", required=True)
    unlink_parser = commands.add_parser("unlink")
    unlink_parser.add_argument("child")
    return command_parser


def main(argv: list[str] | None = None) -> int:
    """Run one plugin command and convert expected errors to CLI status 1."""
    try:
        return _run(parser().parse_args(argv))
    except (ApiError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _run(arguments: argparse.Namespace) -> int:
    if arguments.command == "setup":
        write_installation_guide(sys.stdout)
        return 0
    store = store_from_env()
    if arguments.command == "event" and not store.load().enabled:
        return 0
    api = api_from_env()
    return _dispatch_tree_command(arguments, api, store)


def _dispatch_tree_command(
    arguments: argparse.Namespace, api: AgentTreeApi, store: StateStore
) -> int:
    """Dispatch commands after the setup and disabled-event guards."""
    if arguments.command == "list":
        list_links(api, store)
    elif arguments.command == "sync":
        print(f"synced {sync(api, store)} agents")
    elif arguments.command == "event":
        sync(api, store)
    elif arguments.command == "enable":
        print(f"enabled; synced {enable(api, store)} agents")
        write_installation_guide(sys.stdout)
    elif arguments.command == "disable":
        print(f"disabled {disable(api, store)} agents")
    elif arguments.command == "link":
        link(api, store, arguments.child, arguments.parent)
    elif arguments.command == "unlink":
        unlink(api, store, arguments.child)
    return 0
