# Herdr Agent Tree

The optional [native GPUI companion](native/README.md) adds workspace cards,
continuous tree guides, and accent selection to the sidebar.

A Herdr plugin that keeps parent agents and their children adjacent in the
sidebar, with textual tree guides and an explicit relationship registry.

```text
workspace
  ├─ codex       coordinator
  │  ├─ claude   implementation
  │  │  └─ codex tests
  │  └─ codex    review
  └─ opencode    independent task
```

This extends the existing sidebar through supported metadata tokens and
`agent.view.set`. It does not patch Herdr or replace its status indicators.
Names, terminal titles, agent lifecycle reports, and other plugins' metadata
remain owned by their original sources.

## Requirements and limitations

- Herdr **0.9.0+**, Python **3.11+**, macOS or Linux. No Python runtime packages.
- Herdr GPUI must support custom sidebar tokens and have `[usage] inline = true`.
- Each represented agent must occupy a distinct Herdr pane. Subagents running
  inside one Codex/Claude terminal are not exposed by Herdr's pane API.
- Parent links are explicit. Herdr does not provide parent-agent IDs, and this
  plugin never guesses relationships from titles or process names.
- Links must stay within one workspace. Cycles and excessive depth are refused.
- Guides are text inside native rows. Continuous native connectors, separate
  ancestor styling, and clickable branch expansion need changes to Herdr GPUI.
- Each row also receives `naeliofreires_tree_path`, a compact `v1:` binary
  branch path for an optional native GPUI companion. The released GPUI client
  currently falls back to `naeliofreires_tree_prefix`; this repository does not
  ship or install native GPUI changes, and its companion renderer is still
  development work.
- The plugin controls the session's one agent-view projection while enabled;
  do not enable another agent-view plugin at the same time.

## Install

The examples use the optional `rtk proxy` command wrapper. Herdr and Python are
the only runtime requirements; the plugin itself does not invoke RTK.

```sh
rtk proxy herdr plugin install naeliofreires/herdr-agent-tree
```

Add the tree token to `~/.config/herdr/config.toml`. If you already have custom
rows, insert `$naeliofreires_tree_prefix` into those rows instead of replacing them.

```toml
[ui.sidebar.agents]
rows = [["state_icon", { token = "$naeliofreires_tree_prefix", dim = true }, "agent", "tab"]]
```

For GPUI, keep agents under their workspaces and avoid repeating rounded frames
at every level. These settings belong in `config-gpui.local.toml`:

```toml
agents_placement = "nested"
layout = "compact"
edge_rail = false

[usage]
inline = true
```

Reload the daemon and GPUI configuration, then enable the plugin's tree view:

```sh
rtk proxy herdr server reload-config
rtk proxy /Applications/Herdr.app/Contents/MacOS/Herdr config reload
rtk proxy herdr plugin action invoke naeliofreires.agent-tree.enable
```

The GUI command above is macOS-specific. On Linux, use the installed
`herdr-gpui config reload` command. Keep `state_icon` first in the configured
row so GPUI retains native lifecycle indicators.

## Link agents

For authoring and managing relationships, keep a local checkout:

```sh
rtk proxy git clone https://github.com/naeliofreires/herdr-agent-tree.git
rtk proxy python3 -m agent_tree list
rtk proxy python3 -m agent_tree link w1:p2 --parent w1:p1
rtk proxy python3 -m agent_tree link w1:p3 --parent w1:p2
rtk proxy python3 -m agent_tree unlink w1:p2
```

Run the Python commands from inside that checkout. Replace example pane IDs
with IDs from `list`; stable terminal IDs are accepted as well. The commands
inherit `HERDR_SOCKET_PATH` inside a Herdr pane. Outside Herdr they use the
default local socket; set `HERDR_SOCKET_PATH` explicitly for a named session.

Relationships are saved using terminal IDs, not reusable pane labels. A new
terminal in an old pane will not inherit that pane's previous parent. Missing
parents temporarily promote their children to roots; existing links are retained
so a returning parent can be restored. Agents in separate workspaces remain
separate roots until you explicitly link agents within a workspace.

## Lifecycle and removal

```sh
rtk proxy herdr plugin action invoke naeliofreires.agent-tree.sync
rtk proxy herdr plugin action invoke naeliofreires.agent-tree.list
rtk proxy herdr plugin action invoke naeliofreires.agent-tree.disable
rtk proxy herdr plugin unlink naeliofreires.agent-tree
```

Use the **disable action before unlinking**. Disabling clears only this plugin's
metadata tokens and its source-owned agent view. Unlinking alone does not invoke
the cleanup action. The optional sidebar token is harmless when no value is
reported; remove it from your rows if you stop using the plugin. GPUI layout
settings are preferences and are not changed by the plugin runtime.

Startup and pane lifecycle hooks refresh an enabled tree. They do not enable a
previously disabled tree, run a background watcher, or subscribe to their own
metadata updates. State is isolated per daemon socket below
`HERDR_PLUGIN_STATE_DIR`, or Herdr's standard user plugin-state directory when
invoked directly. Link changes and synchronization share an exclusive file lock.

## Architecture and verification

```text
CLI / plugin hooks
        |
        v
session-scoped state + validated parent links
        |
        v
stable depth-first tree -> pane metadata -> agent.view.set
        |                                    |
        +--------- Herdr native sidebar -----+
```

Tests use named fakes and isolated temporary directories; they do not connect
to your real daemon. From the repository root:

```sh
rtk proxy python3 -m unittest discover -s tests
```

To additionally test three levels and cleanup against a real daemon, explicitly
select the binary. This starts a separate server with private HOME, state,
configuration, and socket directories; it never attaches to your regular daemon.

```sh
rtk proxy env HERDR_TEST_BINARY=/absolute/path/to/herdr python3 -m unittest discover -s tests_live -v
```

API references: [Herdr plugin contract](https://herdr.dev/docs/plugins/),
[Herdr daemon source](https://github.com/herdrdev/herdr), and
[Herdr GPUI sidebar token support](https://github.com/penso/herdr-gpui/blob/main/crates/herdr-gpui/README.md).

License: MIT.
