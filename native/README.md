# Custom Herdr GPUI app

For a new install or update, use [INSTALL.md](../INSTALL.md).
It finds the latest stable Herdr and `penso/herdr-gpui` versions. It checks that
they work together. It changes the patches to fit the new code when needed.
It builds, checks, and installs the app for your user. It saves the old app.
That is the main guide for current installs.

This file is a code guide for the old patches. They use one fixed code version.

This directory has three source patches for the
[Herdr GPUI client](https://github.com/penso/herdr-gpui). They use the plugin
token `naeliofreires_tree_path`. They add custom app styling to the nested
Agent Tree view. Build the custom app separately with this guide.
`herdr plugin install` installs the Python plugin only. It does not build the
custom app or install native code from Python.

First install and configure the plugin. Enable its sidebar token and the
nested Agent Tree view. Use the [root README](../README.md#install-and-configure)
for these steps. Native styling starts after the view is on.

The custom app adds:

- Workspace cards with 10px side space and 12px between cards.
- Workspace headers with an 18% shade from the sidebar color.
- Bold workspace labels at 14px.
- Tree lines join the rows. Each level adds 20px of space.
- A colored selected background and a left indicator.
- The tree lines stay in place when you pick a row.
- The app shows the tool icon and hides the tool name. It keeps the task title,
  work state, and text for screen readers.

These changes need the nested Agent Tree view and valid paths with 1–16 bits.
Missing or bad paths use the normal view. There is no button to hide child rows.
Without the patches, the plugin uses text guides and tool names.

```text
Agent Tree metadata
        |
        +-- v1 path ----------------> guides, cards, selection, icons
        |
        +-- text prefix ------------> released client fallback
```

For the old build, install the Rust code tools, `just`, and the packages for
your OS listed in that fixed version. For a current install, read the code
tools and OS guides for the chosen release. [INSTALL.md](../INSTALL.md)
shows how to find them.

On macOS, install Xcode Command Line Tools. For Linux packages, use the original
project's [From source](https://github.com/penso/herdr-gpui/blob/a5b2df2db54061cd2785c3ddf184bce348be3fd1/README.md#from-source)
and [Linux Builds](https://github.com/penso/herdr-gpui/blob/a5b2df2db54061cd2785c3ddf184bce348be3fd1/README.md#linux-builds)
sections.

## Old code version and licenses

The original patches use this code version from the original project:
[`a5b2df2db54061cd2785c3ddf184bce348be3fd1`](https://github.com/penso/herdr-gpui/tree/a5b2df2db54061cd2785c3ddf184bce348be3fd1).
Use [INSTALL.md](../INSTALL.md) for the latest release. Use this fixed code
version only to build the old app again.

Apply all three files in numeric order:

1. `01-native-tree-model.patch`
2. `02-native-sidebar-presentation.patch`
3. `03-compact-agent-icons.patch`

The changed GPUI code keeps its original Apache-2.0 license. See
[`LICENSE`](LICENSE) and [`NOTICE`](NOTICE). The plugin source keeps the MIT
license in the repository root.

## Reproduce the patched client

Run these commands from any directory. Replace each placeholder with an
absolute path. The plugin checkout is the repository that contains this file.

```sh
rtk proxy git clone https://github.com/penso/herdr-gpui.git /path/to/herdr-gpui
rtk proxy git -C /path/to/herdr-gpui checkout a5b2df2db54061cd2785c3ddf184bce348be3fd1
rtk proxy git -C /path/to/herdr-gpui apply /path/to/herdr-agent-tree/native/01-native-tree-model.patch
rtk proxy git -C /path/to/herdr-gpui apply /path/to/herdr-agent-tree/native/02-native-sidebar-presentation.patch
rtk proxy git -C /path/to/herdr-gpui apply /path/to/herdr-agent-tree/native/03-compact-agent-icons.patch
```

Run the checks from `/path/to/herdr-gpui`, not from the plugin checkout:

```sh
rtk proxy just test-agent-tree
rtk proxy env CARGO_BUILD_JOBS=1 CARGO_PROFILE_DEV_DEBUG=0 CARGO_INCREMENTAL=0 cargo check --locked -p herdr-gpui --tests
```

`just test-agent-tree` runs three small production tests for path and guide
geometry. It does not create the full GPUI test binary.

On macOS only, build the debug app bundle from the same native checkout:

```sh
rtk proxy env CARGO_BUILD_JOBS=1 CARGO_PROFILE_DEV_DEBUG=0 CARGO_INCREMENTAL=0 just bundle debug
```

The bundle is at `target/debug/Herdr.app`. These commands do not install or
replace an existing app. For Linux, follow the OS guide for that code version.

For a clear manual check on macOS, first quit every other Herdr GUI client.
The daemon and terminal sessions can stay open. Then open the exact bundle you
built and reload that client's config:

```sh
rtk proxy open /path/to/herdr-gpui/target/debug/Herdr.app
rtk proxy /path/to/herdr-gpui/target/debug/Herdr.app/Contents/MacOS/Herdr config reload
```

The root README command
`/Applications/Herdr.app/Contents/MacOS/Herdr` opens the installed stock app.
For this check, use the executable inside the bundle you built.

The full GPUI test program was not run here. The build needed more memory than
this computer had. We checked the types, ran three path and guide tests, built
the app, and checked it in macOS.

## Relationship to the plugin

The Python plugin sends all three tokens as one report from
`plugin:naeliofreires.agent-tree`:

| Token | Custom app use |
| --- | --- |
| `naeliofreires_tree_prefix` | Text guides in an unpatched client. |
| `naeliofreires_tree_order` | Stable agent-view order. |
| `naeliofreires_tree_path` | `v1:` plus 1–16 binary bits for guides. |

Each bit describes a row in the path. The first bits are for parent rows.
A bit is `1` when there is a later row at the same level. Its line keeps going
down. It is `0` when that row is last at its level. The last bit describes the
current row: `1` means not last, and `0` means last.

The parser checks the path. It rejects missing values, values with characters
other than `0` and `1`, and values that are too long. The custom app ignores bad
paths and keeps normal rows. The plugin and Herdr still keep parent links,
work state, navigation, and server state.
