# Native GPUI companion

These patches implement Option A in [Herdr GPUI](https://github.com/penso/herdr-gpui):
workspace cards, continuous tree guides, and an accent selection drawn without
changing the row's measured geometry. Workspace cards have 12px external spacing.

The plugin still works with the released client through its textual prefix.
The native companion consumes the optional `naeliofreires_tree_path` token.

```text
Agent Tree plugin -> v1 binary branch paths -> GPUI guides and workspace cards
                  -> textual prefix        -> released-client fallback
```

## Reproduce

The patches are based on upstream commit
`a5b2df2db54061cd2785c3ddf184bce348be3fd1`. Use a checkout at that revision and
apply both patches in numeric order. Paths below are relative to this plugin:

```sh
rtk git apply /path/to/herdr-agent-tree/native/01-native-tree-model.patch
rtk git apply /path/to/herdr-agent-tree/native/02-native-sidebar-presentation.patch
rtk proxy just test-agent-tree
rtk proxy env CARGO_BUILD_JOBS=1 CARGO_PROFILE_DEV_DEBUG=0 CARGO_INCREMENTAL=0 cargo check --locked -p herdr-gpui --tests
rtk proxy env CARGO_BUILD_JOBS=1 CARGO_PROFILE_DEV_DEBUG=0 CARGO_INCREMENTAL=0 just bundle debug
```

Rust 1.96.1 and the upstream macOS prerequisites are required. Follow the upstream
README for other platforms. `just test-agent-tree` executes the actual parser and
guide geometry without generating the entire GPUI test binary.

The complete GPUI test binary was not executed locally because its compilation
exceeded the available memory. Type checking, the lightweight geometry tests,
the application build, and direct native UI inspection were used instead.

## Compatibility

Enhanced rendering is scoped to the nested Agent Tree view with a valid bounded
path. Missing or malformed paths retain the previous rendering. Agent names,
lifecycle states, navigation, and the daemon protocol are unchanged.

The native patches retain the upstream Apache-2.0 license; see `LICENSE` and
`NOTICE` in this directory. The Python plugin remains MIT-licensed.
