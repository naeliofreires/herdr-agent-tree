# Herdr Agent Tree

Herdr Agent Tree is an MIT-licensed plugin for Herdr 0.9.0+ that keeps
explicitly linked parent and child agents adjacent in the sidebar. It runs on
macOS and Linux with Python 3.11+ and has no Python runtime dependencies.

## Install with one prompt

Use this single request with a coding agent that has local terminal access. It
is the primary path to the complete experience; detailed guardrails and steps
live in [INSTALL.md](INSTALL.md):

```text
Instale o Herdr Agent Tree seguindo integralmente:
https://raw.githubusercontent.com/naeliofreires/herdr-agent-tree/main/INSTALL.md

Descubra as últimas versões estáveis do Herdr e do Herdr GPUI, instale os pré-requisitos e o plugin, aplique todos os patches nativos, compile, instale e abra o cliente com os estilos do repositório.

Preserve minhas configurações e sessões. Valide os cards, cabeçalhos, árvore, seleção e ícones antes de concluir. Informe versões, caminho instalado, testes, rollback e qualquer bloqueio.
```

> **Workspace cards require the native client.**
> `herdr plugin install naeliofreires/herdr-agent-tree` installs the Python
> plugin and text guides. For cards, darker headers, continuous guides, and
> compact agent icons, follow the [complete installation guide](INSTALL.md)
> and launch the resulting native client.

The plugin does not infer relationships from titles, process names, or timing.
Each link is authored explicitly and stored by stable terminal ID. The optional
[native GPUI companion](native/README.md) adds native guides and hierarchy
styling; the released client continues to work through the textual fallback.

```text
workspace
  ├─ coordinator
  │  ├─ implementation
  │  │  └─ tests
  │  └─ review
  └─ independent task
```

## Native companion at a glance

The optional companion is a source patch set for Herdr GPUI. It is not part of
the plugin installer; the standard client remains useful through the textual
prefix fallback.

| Feature | Standard GPUI | Patched GPUI |
| --- | --- | --- |
| Workspace presentation | Standard rows and spacing. | Cards with 10px side spacing and 12px card gaps. |
| Workspace heading | Standard theme styling. | Darker background based on the sidebar color and bold workspace labels. |
| Tree guides | Textual prefix token. | Continuous ancestor and elbow guides at 20px levels. |
| Selection | Standard row selection. | Accent background and a left marker that keep tree guides aligned. |
| Agent identity | Engine name remains in the row. | Tool icon and task/tab title, with lifecycle indicators and accessibility labels. |

The native treatment is scoped to nested Agent Tree rows with valid paths.
Cards appear in workspaces containing detected agents; empty workspaces retain
the standard layout. There are no collapsible branch controls. See
[native/README.md](native/README.md)
for the patch reference; use [INSTALL.md](INSTALL.md) for current builds.

## Requirements and boundaries

**Python-only fallback (advanced).** An existing Herdr **0.9.0+** installation,
Python **3.11+**, and macOS or Linux are enough for the textual plugin. This is
not the default end goal when the native workspace cards are requested:
`herdr plugin install` does not build or modify the GUI.

**Complete experience.** The one-prompt workflow additionally needs a coding
agent with local terminal access, network/Git access, and the official
prerequisites for the latest compatible Herdr daemon and GPUI revision. The
workflow discovers those requirements at execution time instead of pinning an
old toolchain here.

- Each represented agent must occupy a distinct Herdr pane. Agents nested
  inside one terminal are not visible through Herdr's pane API.
- Links must stay within one workspace. Cycles are rejected, parent depth is
  bounded, and the maximum agent list is 2048.
- A missing parent temporarily promotes its child to a root; the stored link is
  retained so the hierarchy can recover when the parent returns.
- The plugin owns one `agent.view` projection while enabled. Do not enable a
  second plugin that controls the same projection.
- The plugin never changes Herdr runtime preferences or other metadata sources.

The examples use `rtk proxy`, an optional local command wrapper that reduces
terminal output. RTK is not a plugin dependency; omit the `rtk proxy` prefix if
RTK is not installed.

## Install and configure

Herdr shows the package as **Agent Tree (cards require native client)** in its
installation preview. The plugin ID remains `naeliofreires.agent-tree`.

Use this section only for the Python-only fallback or when the complete
one-prompt workflow is configuring the already-built native client. It does not
replace the complete installation path above.

Choose one installation path. A local checkout is recommended when you will
author relationships; the GitHub-managed path is convenient for a fixed copy.

**Local checkout, recommended for relationship authoring.** From any directory,
replace `/path/to/herdr-agent-tree` with the absolute clone path you choose:

```sh
rtk proxy git clone https://github.com/naeliofreires/herdr-agent-tree.git /path/to/herdr-agent-tree
rtk proxy herdr plugin link /path/to/herdr-agent-tree
```

**GitHub-managed alternative.** From any directory:

```sh
rtk proxy herdr plugin install naeliofreires/herdr-agent-tree
```

The managed installer accepts the standard `OWNER/REPO[/SUBDIR] [--ref REF]`
form. Do not run both paths for the same plugin ID.

From the plugin checkout, print setup instructions without a running daemon:

```sh
rtk proxy python3 -m agent_tree setup
```

Both installation paths also register a `setup` action. Herdr runs actions
asynchronously and saves their output in plugin logs:

```sh
rtk proxy herdr plugin action invoke naeliofreires.agent-tree.setup
rtk proxy herdr plugin log list --plugin naeliofreires.agent-tree --limit 3
```

Once the action finishes, its log contains the guide. The setup command and
action explain the two installation layers; they do not build the native client.

Add the plugin's text fallback token to `~/.config/herdr/config.toml`. Keep
`state_icon` first so the native lifecycle indicator remains visible:

```toml
[ui.sidebar.agents]
rows = [["state_icon", { token = "$naeliofreires_tree_prefix", dim = true }, "agent", "tab"]]
```

If you already have custom rows, add `$naeliofreires_tree_prefix` to the
existing agent row instead of replacing that row.

For the nested layout, edit `~/.config/herdr/config-gpui.local.toml`:

```toml
agents_placement = "nested"
layout = "compact"
edge_rail = false

[usage]
inline = true
```

Reload the daemon and the running client, then enable the view:

```sh
rtk proxy herdr server reload-config
rtk proxy /Applications/Herdr.app/Contents/MacOS/Herdr config reload
rtk proxy herdr plugin action invoke naeliofreires.agent-tree.enable
```

A successful explicit `enable` also writes the setup guide to its command
output. When invoked through Herdr, read that output in the plugin logs above.
Background event hooks stay quiet.

The macOS example uses the installed app. For the native companion, use the
executable inside your [built bundle](native/README.md#reproduce-the-patched-client).
On Linux, reload the running client with `herdr-gpui config reload`.

## Link agents

The following commands require the plugin checkout as their working directory.
They accept pane IDs or stable terminal IDs; use `list` to discover both:

```sh
rtk proxy python3 -m agent_tree list
rtk proxy python3 -m agent_tree link CHILD --parent PARENT
rtk proxy python3 -m agent_tree unlink CHILD
```

For example:

```sh
rtk proxy python3 -m agent_tree link w1:p2 --parent w1:p1
rtk proxy python3 -m agent_tree link w1:p3 --parent w1:p2
```

Relationships are persisted by terminal ID, not reusable pane labels. The
commands inherit `HERDR_SOCKET_PATH` from a Herdr pane. Outside Herdr, set it
explicitly when targeting a named daemon session.

## Lifecycle and cleanup

When enabled, startup and these pane/workspace events refresh the tree:
`pane.agent_detected`, `pane.closed`, `pane.moved`, `tab.moved`, and
`workspace.reordered`. The plugin does not run a watcher and events do not
enable a previously disabled tree.

From any directory, use the fully qualified plugin action IDs:

```sh
rtk proxy herdr plugin action invoke naeliofreires.agent-tree.sync
rtk proxy herdr plugin action invoke naeliofreires.agent-tree.list
rtk proxy herdr plugin action invoke naeliofreires.agent-tree.disable
```

Disable the plugin in each relevant daemon session before removing it. Disable
clears all three plugin tokens from every pane it can enumerate in that session,
clears the plugin's source-owned agent view, and leaves unrelated metadata and
views intact. It does not remove stored links, runtime preferences, or native
source patches/bundles. After removing the plugin, you can remove the optional
prefix token from your sidebar configuration manually. Keep that token when
using the plugin's textual fallback in an unpatched client.

For a local checkout, unlink it from any directory:

```sh
rtk proxy herdr plugin unlink naeliofreires.agent-tree
```

For a GitHub-managed install, use the managed uninstall command instead:

```sh
rtk proxy herdr plugin uninstall naeliofreires.agent-tree
```

Managed uninstall preserves Herdr configuration and state. Local unlink leaves
the checkout and plugin-state files in place; cleanup of managed installed files
may be deferred until any running plugin use finishes.

State is isolated per daemon socket. The socket is resolved from
`HERDR_SOCKET_PATH`, then `XDG_CONFIG_HOME` or `~/.config` plus
`herdr/herdr.sock`. Plugin state is resolved from `HERDR_PLUGIN_STATE_DIR`,
then `XDG_STATE_HOME` or `~/.local/state` plus
`herdr/plugins/naeliofreires.agent-tree`.

## Architecture and verification

```text
Herdr hooks / CLI
        |
        v
socket-scoped state + validated terminal-ID links
        |
        v
stable depth-first rows -> prefix/order/path -> agent.view.set
                                      |             |
                              released text     native GPUI companion
```

From the plugin checkout, run the unit suite:

```sh
rtk proxy python3 -m unittest discover -s tests
```

The opt-in live suite requires an explicit absolute Herdr binary and starts an
isolated daemon with private HOME, state, configuration, and socket paths:

```sh
rtk proxy env HERDR_TEST_BINARY=/absolute/path/to/herdr python3 -m unittest discover -s tests_live -v
```

## Metadata reference

Every synchronized row reports all three tokens from source
`plugin:naeliofreires.agent-tree` in one metadata update:

| Token | Purpose |
| --- | --- |
| `naeliofreires_tree_prefix` | Zero-width-prefixed textual guides for the released client. |
| `naeliofreires_tree_order` | Stable depth-first order used by the agent view. |
| `naeliofreires_tree_path` | Bounded `v1:` path consumed by the optional native companion. |

The path bit format and malformed-value fallback are documented in
[native/README.md](native/README.md).

See the [Herdr plugin contract](https://herdr.dev/docs/plugins/),
[Herdr daemon source](https://github.com/herdrdev/herdr), and
[Herdr GPUI source](https://github.com/penso/herdr-gpui) for upstream APIs.

The plugin is [MIT licensed](LICENSE). Native patches retain upstream
[Apache-2.0 licensing](native/LICENSE) and attribution ([native/NOTICE](native/NOTICE)).
