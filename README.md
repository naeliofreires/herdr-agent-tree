# Herdr Agent Tree

Herdr Agent Tree is an MIT-licensed plugin for Herdr 0.9.0+. It shows linked
parent and child agents in the sidebar. It runs on macOS and Linux. It needs
Python 3.11+ and has no other Python packages.

## Install with one prompt

Copy this prompt to a coding agent that can use your terminal.
The agent must follow [INSTALL.md](INSTALL.md) for the full setup.

```text
Install Herdr Agent Tree on this computer.
Use this guide:
https://raw.githubusercontent.com/naeliofreires/herdr-agent-tree/main/INSTALL.md

Find the latest stable versions of Herdr and Herdr GPUI.
Get the tools this computer needs. Install and turn on the plugin.
Add all code changes for our app style. Build, install, and open the custom app.
Check the workspace cards, dark headers, tree lines, row marks, and icons.
Keep my settings, saved links, and running sessions.
Tell me the versions, code IDs, app path, and checks that passed.
Also tell me how to use the old app again and what still needs work.
```

> Workspace cards need the custom app. `herdr plugin install` installs the
> Python plugin and text guides only.

The plugin does not guess which agent is a parent or child. You set each link.
It saves the link with a terminal ID. The [custom app](native/README.md) adds
tree lines and card styles. The text tree also works in the normal Herdr app.

```text
workspace
  ├─ main task
  │  ├─ code task
  │  │  └─ tests
  │  └─ review
  └─ independent task
```

## Custom app styles

The custom app uses code changes for Herdr GPUI. The plugin command does not
build this app.

| Feature | Standard GPUI | Patched GPUI |
| --- | --- | --- |
| Workspace view | Standard rows and gaps. | Cards with 10px side space and 12px gaps. |
| Workspace header | Standard theme. | Darker header from the sidebar color and bold labels. |
| Tree guides | Text marks. | Lines join the tree rows. Each level adds 20px. |
| Selection | Normal row color. | A row color and left mark keep the tree lines in place. |
| Agent name | Tool name in the row. | Tool icon and task title. The app keeps work state and screen reader text. |

The custom view needs the Agent Tree view, nested rows, and valid tree paths.
Empty workspaces keep the normal view. There is no button to hide child rows.
Missing or bad paths use the normal text tree.

## Words used in this guide

- Plugin: a small tool that adds a feature to Herdr.
- Custom app: Herdr GPUI with our card and tree styles.
- Server, or daemon: the Herdr program that keeps terminals running.
- Pane: one terminal area. A workspace is a group of tabs and panes.
- Stable version: a version for normal use.
- Patch: a file with code changes.
- SHA: an ID for a code version. A hash is an ID for a file.
- Protocol: rules the app and server use to talk.

## What you need

**Text mode only.** You need Herdr 0.9.0+, Python 3.11+, and macOS or Linux.
The plugin command adds the text tree. Use the prompt above for the custom app.

**Full setup.** Use a coding agent that can run commands on your computer and
use the internet. It finds and installs the tools for the latest stable Herdr
and GPUI versions.

- Each agent needs its own Herdr pane. Nested agents in one terminal are not
  visible through the pane API.
- Links use pane IDs or stable terminal IDs. Links stay in one workspace.
- Parent links cannot make a loop. Tree depth has a limit. At most 2,048 agents
  can be in the list.
- A missing parent moves its child to the root for now. The saved link remains.
- The plugin sets one `agent.view` list. Use only one tree view plugin at a time.
- The Python plugin keeps your settings and other plugins' values in place.

The examples use `rtk proxy`, an optional command wrapper. RTK is not a plugin
package. Remove the `rtk proxy` prefix when RTK is not installed.

<a id="install-and-configure"></a>

## Install and set up

Herdr shows the package as **Agent Tree (cards need the custom app)**. The
plugin ID is `naeliofreires.agent-tree`.

Use this section for text mode or to set up a custom app you have built.
Use the prompt above for a full install.

Choose one path. A local checkout is best when you will make links by hand.

**Local checkout:**

```sh
rtk proxy git clone https://github.com/naeliofreires/herdr-agent-tree.git /path/to/herdr-agent-tree
rtk proxy herdr plugin link /path/to/herdr-agent-tree
```

**GitHub-managed install:**

```sh
rtk proxy herdr plugin install naeliofreires/herdr-agent-tree
```

The managed form is `OWNER/REPO[/SUBDIR] [--ref REF]`. Do not use both paths
for the same plugin ID.

From the plugin checkout, print the setup guide without a daemon:

```sh
rtk proxy python3 -m agent_tree setup
```

The setup action also writes the guide to the Herdr plugin log:

```sh
rtk proxy herdr plugin action invoke naeliofreires.agent-tree.setup
rtk proxy herdr plugin log list --plugin naeliofreires.agent-tree --limit 3
```

Add the text token to `~/.config/herdr/config.toml`. Keep `state_icon` first:

```toml
[ui.sidebar.agents]
rows = [["state_icon", { token = "$naeliofreires_tree_prefix", dim = true }, "agent", "tab"]]
```

If you have custom rows, add the token to the current agent row. Do not replace
the row.

For the custom app, edit `~/.config/herdr/config-gpui.local.toml`:

```toml
agents_placement = "nested"
layout = "compact"
edge_rail = false

[usage]
inline = true
```

Reload the daemon and client, then enable the view:

```sh
rtk proxy herdr server reload-config
rtk proxy /Applications/Herdr.app/Contents/MacOS/Herdr config reload
rtk proxy herdr plugin action invoke naeliofreires.agent-tree.enable
```

Use the program inside the custom app when testing its changes.
On Linux, reload the running client with `herdr-gpui config reload`.

## Link agents

Run these commands from the plugin checkout. Use `list` to find pane and
terminal IDs:

```sh
rtk proxy python3 -m agent_tree list
rtk proxy python3 -m agent_tree link CHILD --parent PARENT
rtk proxy python3 -m agent_tree unlink CHILD
```

Links are saved by terminal ID, not by pane label. Herdr panes provide
`HERDR_SOCKET_PATH`. Outside Herdr, set it for the daemon session you want.

## When it runs and how to remove it

When enabled, startup and these events refresh the tree:
`pane.agent_detected`, `pane.closed`, `pane.moved`, `tab.moved`, and
`workspace.reordered`. There is no watcher. Events do not enable the tree.

From any directory, use these action IDs:

```sh
rtk proxy herdr plugin action invoke naeliofreires.agent-tree.sync
rtk proxy herdr plugin action invoke naeliofreires.agent-tree.list
rtk proxy herdr plugin action invoke naeliofreires.agent-tree.disable
```

Turn off the tree in each server session before you remove the plugin. This
clears its three values from each pane it can list. It also clears this plugin's
view. Your other values, views, links, settings, patch files, and apps stay.
Remove the text token from your config only when you no longer want text mode.

For a local checkout:

```sh
rtk proxy herdr plugin unlink naeliofreires.agent-tree
```

For a managed install:

```sh
rtk proxy herdr plugin uninstall naeliofreires.agent-tree
```

Managed uninstall keeps Herdr config and saved state. Local unlink keeps your
copy of the code and saved state. File cleanup may wait for plugin work to end.

A socket is the path used to talk to one server. Each socket has its own saved
state. The plugin finds the socket with
`HERDR_SOCKET_PATH`, then `XDG_CONFIG_HOME` or `~/.config`, plus
`herdr/herdr.sock`. Plugin state uses `HERDR_PLUGIN_STATE_DIR`, then
`XDG_STATE_HOME` or `~/.local/state`, plus
`herdr/plugins/naeliofreires.agent-tree`.

## How it works and how to test it

```text
Herdr hooks / CLI
        |
        v
server state + checked links
        |
        v
tree rows -> prefix/order/path -> agent.view.set
                              |              |
                         text tree       custom app
```

From the plugin checkout:

```sh
rtk proxy python3 -m unittest discover -s tests
```

The optional live suite needs an absolute Herdr binary. It uses a private HOME,
state path, config path, and socket:

```sh
rtk proxy env HERDR_TEST_BINARY=/absolute/path/to/herdr python3 -m unittest discover -s tests_live -v
```

## Values sent by the plugin

The plugin sends three values for each agent in one update. These values are
called metadata. The source name is `plugin:naeliofreires.agent-tree`:

| Token | Use |
| --- | --- |
| `naeliofreires_tree_prefix` | Text guides in the released client. |
| `naeliofreires_tree_order` | Stable agent-view order. |
| `naeliofreires_tree_path` | `v1:` plus 1–16 binary bits for native guides. |

See [native/README.md](native/README.md) for path rules and bad-value fallback.

See the [Herdr plugin contract](https://herdr.dev/docs/plugins/),
[Herdr daemon source](https://github.com/herdrdev/herdr), and
[Herdr GPUI source](https://github.com/penso/herdr-gpui).

The plugin is [MIT licensed](LICENSE). App patches keep the original
[Apache-2.0 license](native/LICENSE) and attribution ([native/NOTICE](native/NOTICE)).
