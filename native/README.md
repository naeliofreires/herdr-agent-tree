# Native GPUI companion

This directory contains three source patches for the native
[Herdr GPUI client](https://github.com/penso/herdr-gpui). They consume the
plugin's `naeliofreires_tree_path` token and add native hierarchy treatment to
the nested Agent Tree view. Build the patched client separately using this
guide; `herdr plugin install` installs the Python plugin only.

Install and configure the plugin, its sidebar token, and the nested Agent Tree
view using the [root README](../README.md#install-and-configure) before testing
the companion. Native styling appears after that view is enabled.

The patched client provides:

- workspace cards with 10px side spacing and 12px between cards;
- headers shaded from the sidebar theme color (18%) and bold 14px workspace
  labels for every workspace;
- continuous ancestor and elbow guides at 20px levels;
- an accented selected background with an absolute left indicator that does not
  change row geometry;
- engine icon-only agent rows while preserving task/tab title, lifecycle state,
  and accessibility text.

These changes apply only to the nested Agent Tree view and valid bounded paths.
Missing or malformed paths retain the released rendering. There are no
collapsible branch controls. Without the patches, the plugin falls back to its
textual prefix and engine labels.

```text
Agent Tree metadata
        |
        +-- v1 path ----------------> native guides, cards, selection, icons
        |
        +-- textual prefix ----------> released/unpatched GPUI fallback
```

Before building, install Rust 1.96.1, `just`, and the platform dependencies
required by the pinned upstream checkout. On macOS, Xcode Command Line Tools
provide the pinned base's platform toolchain. Linux needs the dependencies in
the pinned upstream [From source](https://github.com/penso/herdr-gpui/blob/a5b2df2db54061cd2785c3ddf184bce348be3fd1/README.md#from-source)
and [Linux Builds](https://github.com/penso/herdr-gpui/blob/a5b2df2db54061cd2785c3ddf184bce348be3fd1/README.md#linux-builds)
sections.

## Pinned source and licenses

The patches target upstream commit
[`a5b2df2db54061cd2785c3ddf184bce348be3fd1`](https://github.com/penso/herdr-gpui/tree/a5b2df2db54061cd2785c3ddf184bce348be3fd1),
not the moving default branch. Apply all three files in numeric order:

1. `01-native-tree-model.patch`
2. `02-native-sidebar-presentation.patch`
3. `03-compact-agent-icons.patch`

The patched GPUI source remains under its upstream Apache-2.0 license; see
[`LICENSE`](LICENSE) and [`NOTICE`](NOTICE). The plugin source remains MIT-
licensed under the repository root.

## Reproduce the patched client

The following commands can be run from any directory. Replace the placeholders
with absolute paths; the plugin checkout is the repository containing this
file:

```sh
rtk proxy git clone https://github.com/penso/herdr-gpui.git /path/to/herdr-gpui
rtk proxy git -C /path/to/herdr-gpui checkout a5b2df2db54061cd2785c3ddf184bce348be3fd1
rtk proxy git -C /path/to/herdr-gpui apply /path/to/herdr-agent-tree/native/01-native-tree-model.patch
rtk proxy git -C /path/to/herdr-gpui apply /path/to/herdr-agent-tree/native/02-native-sidebar-presentation.patch
rtk proxy git -C /path/to/herdr-gpui apply /path/to/herdr-agent-tree/native/03-compact-agent-icons.patch
```

Run the verification commands from the native GPUI checkout
`/path/to/herdr-gpui`, not from the plugin checkout:

```sh
rtk proxy just test-agent-tree
rtk proxy env CARGO_BUILD_JOBS=1 CARGO_PROFILE_DEV_DEBUG=0 CARGO_INCREMENTAL=0 cargo check --locked -p herdr-gpui --tests
```

`just test-agent-tree` executes the three lightweight production path and guide
geometry tests without generating the full GPUI test binary.

On macOS only, build the debug app bundle from the same native checkout:

```sh
rtk proxy env CARGO_BUILD_JOBS=1 CARGO_PROFILE_DEV_DEBUG=0 CARGO_INCREMENTAL=0 just bundle debug
```

The bundle is written to `target/debug/Herdr.app`; no command above installs or
replaces an existing app. For Linux native builds, follow the pinned upstream
platform instructions instead of using this macOS bundle command.

For an unambiguous manual check on macOS, quit any other Herdr GUI client first;
the daemon and terminal sessions remain running. Then, from any directory,
open the bundle you just built and reload that client's config:

```sh
rtk proxy open /path/to/herdr-gpui/target/debug/Herdr.app
rtk proxy /path/to/herdr-gpui/target/debug/Herdr.app/Contents/MacOS/Herdr config reload
```

The `/Applications/Herdr.app/Contents/MacOS/Herdr` command in the root README
targets the installed, unpatched client. Native users should use the executable
inside their built bundle for this manual check.

The complete GPUI test binary is intentionally not claimed as a local result:
its code generation exceeded the available memory on the development machine.
The bounded local evidence is type checking, three pure path/geometry tests, a
debug bundle, and native QA on macOS.

## Relationship to the plugin

The Python plugin still reports all three tokens atomically from
`plugin:naeliofreires.agent-tree`:

| Token | Native use |
| --- | --- |
| `naeliofreires_tree_prefix` | Fallback text guides in an unpatched client. |
| `naeliofreires_tree_order` | Stable agent-view ordering. |
| `naeliofreires_tree_path` | `v1:` plus 1–16 binary bits for native guides. |

For the path token, each ancestor bit is `1` when a later sibling continues
that vertical guide and `0` when the ancestor is the last sibling. The final bit
describes the current row (`1` non-last, `0` last). The parser rejects missing,
malformed, non-binary, and overlong values.
The native companion therefore ignores invalid paths without changing ordinary
agent rows. Parent links, lifecycle metadata, navigation, and daemon state
remain owned by the plugin and Herdr.
