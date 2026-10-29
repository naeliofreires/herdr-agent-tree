# Install the native Agent Tree client

This runbook is the execution path for the complete Agent Tree installation,
including when the user starts with only the one-prompt request in [README.md](README.md)
and no Herdr installation or local checkout. It builds a patched Herdr GPUI
client from the latest stable compatible upstream releases available at
execution time. It does not mutate an upstream repository or managed plugin
installation directory.

The Python plugin and the native client are separate layers:

```text
Herdr plugin install -> metadata, links, textual fallback
native build         -> workspace cards, native guides, selection and icons
```

The plugin is listed as **Agent Tree (cards require native client)** so the
dependency is visible in Herdr's installation preview. The Python installer
does not build the native client. Use this runbook to reach the complete result.

If Git is missing, install it from the official platform instructions and verify
it before cloning. Install Python before invoking any plugin command; the
complete workflow does not assume either prerequisite exists.

If no checkout exists, resolve this public repository outside Herdr's managed
plugin roots, then read both instruction files before changing anything:

```sh
rtk proxy git clone https://github.com/naeliofreires/herdr-agent-tree.git /path/to/herdr-agent-tree
rtk proxy sed -n '1,220p' /path/to/herdr-agent-tree/AGENTS.md
rtk proxy sed -n '1,320p' /path/to/herdr-agent-tree/INSTALL.md
```

The raw runbook is also available at
https://raw.githubusercontent.com/naeliofreires/herdr-agent-tree/main/INSTALL.md.
Continue with the inspection and installation stages below; the Python plugin
installer does not build or install the native client.

Shell examples use the optional RTK wrapper, matching this repository's README.
If RTK is unavailable on the user's machine, omit `rtk proxy`.

## 1. Inspect before changing anything

Record the operating system, architecture, current user, Herdr daemon and GUI
versions, exact GUI executable, and whether a daemon is running. Read any
`AGENTS.md`, toolchain file, README, and `justfile` in every selected checkout.
Check for:

- an existing managed or locally linked `naeliofreires.agent-tree` plugin;
- disabled plugin state and recent plugin logs;
- custom Herdr sidebar rows and Agent Tree settings;
- an existing user-local Agent Tree bundle and its recorded source commit;
- a dirty native source checkout that must not be reused.

Preserve existing configuration, agent sessions, links, and user edits. Use a
named socket when the user has more than one daemon; never guess the target from
the current directory. Do not stop a running daemon or kill agent processes. If
the agent itself is running inside the Herdr GUI that must be replaced,
checkpoint or coordinate that session before asking the GUI to quit.

## 2. Select and prepare the compatible upstream pair

Discover the current latest stable releases at execution time from both official
repositories: the Herdr daemon at `https://github.com/herdrdev/herdr` and the
GPUI client at `https://github.com/penso/herdr-gpui`. Prefer each repository's
official release API, with the release page as a fallback, for example:

```sh
rtk proxy gh api repos/herdrdev/herdr/releases/latest
rtk proxy gh api repos/penso/herdr-gpui/releases/latest
```

If `gh` is unavailable, use the official releases pages or APIs with equivalent
read-only requests. Record each release tag, resolve each tag to its full commit
SHA separately (a `target_commitish` may be a moving branch), then verify the
GUI's documented daemon/protocol compatibility. If the current latest pair
cannot communicate, report that blocker rather than selecting an older pair.
Never silently use `main`, a preview, or an old pinned baseline. Do not
downgrade a newer installed preview without explicit approval.

If the daemon is missing, install the selected stable release using the current
official Herdr documentation and exact commands discovered from that release's
README or CLI help, then start it through the normal supported startup path and
validate its version and protocol before opening the GUI. Use the existing
official install channel for updates; replacing an installed CLI binary does not
replace a compatible server that is already running. Record both installed CLI
and running-daemon versions/protocol. An older compatible server with active
panes may remain running only when safe, but report the pending server upgrade.
For update guidance, consult [Herdr update docs](https://herdr.dev/docs/install/#update),
[live handoff](https://herdr.dev/docs/session-state/#live-handoff), and the
[running-session troubleshooting note](https://herdr.dev/docs/troubleshooting/#herdr-updated-but-the-running-session-is-still-old).
Experimental `herdr update --handoff` is supported only for Herdr-managed direct
installs, not package-manager installs. Use it only with explicit authorization
for experimental handoff; preserve running panes rather than stopping the server
to force the latest claim.
Report a compatibility blocker if safe upgrade or handoff is unavailable;
compiling the GUI alone is insufficient.

Create a persistent user-local build directory outside this plugin checkout and
outside Herdr's managed plugin roots. Clone the selected GPUI tag there, verify
its full SHA, and create a disposable branch or worktree for the port. Use the
official daemon binary/install channel unless its documentation requires a
source checkout. Read the selected revisions' toolchain, platform prerequisites,
and build instructions before installing missing Rust, just, or system tools.
Use the toolchain required by those exact revisions, not historical patch notes.

## 3. Apply or port the native work

Apply these files in order:

1. `native/01-native-tree-model.patch`
2. `native/02-native-sidebar-presentation.patch`
3. `native/03-compact-agent-icons.patch`

Try a normal three-way patch first. On a conflict, keep the selected upstream
code as the base and port the behavior described in [native/README.md](native/README.md):
the `v1:` path model, workspace cards, continuous guides, selected-row marker,
and compact agent identity while preserving lifecycle and accessibility data.
Inspect every hunk; never use a force option or skip a conflicting patch without
reporting it. Add or update focused upstream tests when the port changes code.
Preserve upstream Apache-2.0 attribution and this project's MIT license.

## 4. Verify before installation

Run the plugin suite from this checkout:

```sh
rtk proxy python3 -m unittest discover -s tests
```

From the patched upstream checkout, discover the current equivalent of the
native checks before running them. At minimum, run the patch-provided Agent Tree
path/geometry test (`just test-agent-tree` when the target revision provides it)
and a locked package check with the resource limits appropriate to the machine:

```sh
rtk proxy just test-agent-tree
rtk proxy env CARGO_BUILD_JOBS=1 CARGO_PROFILE_DEV_DEBUG=0 CARGO_INCREMENTAL=0 cargo check --locked -p herdr-gpui --tests
```

Run the upstream sidebar, build, lint, or GUI checks that exist at the selected
revision. Do not claim a visual check when no desktop session is available.
Build a complete bundle with the selected revision's current recipe, then
verify its executable identity and recorded upstream SHA. On macOS, this is
normally `just bundle` for `target/release/Herdr.app`; on Linux, follow the
selected revision's documented package or user-local installation method.
Never run a macOS command on Linux or treat a debug build as a completed
installation without recording that choice.

## 5. Configure the plugin and native view

Install or link the Python plugin exactly once. Preserve the existing source
kind: use the managed update command supported by the installed Herdr CLI, or
reinstall the same GitHub source when that CLI has no `plugin update` command.
Use `plugin link` for a local checkout. If an earlier install left the plugin
disabled, enable it explicitly and inspect its asynchronous log for a
successful sync; an accepted invocation is not proof of completion.

The registry's enabled flag and the tree's saved enabled state are distinct.
Enable the registry entry if necessary, then invoke the view explicitly:

```sh
rtk proxy herdr plugin action invoke naeliofreires.agent-tree.enable
rtk proxy herdr plugin log list --plugin naeliofreires.agent-tree --limit 3
```

Keep `state_icon` first when adding the textual fallback token:

```toml
[ui.sidebar.agents]
rows = [["state_icon", { token = "$naeliofreires_tree_prefix", dim = true }, "agent", "tab"]]
```

The native view requires nested placement and inline metadata. Apply the values
below while preserving unrelated settings. If the user explicitly requires an
incompatible layout, explain the conflict instead of claiming cards are enabled:

```toml
agents_placement = "nested"
layout = "compact"
edge_rail = false

[usage]
inline = true
```

Back up each config before editing. Reload the daemon and the exact client being
used; do not reload the standard `/Applications` client while intending to test
the custom bundle.

## 6. Install reversibly

Stage the complete validated bundle before touching the installed target. The
default macOS target is `~/Applications/Herdr Agent Tree.app`; leave
`/Applications/Herdr.app` untouched unless the user explicitly requests replacement. If a prior custom
bundle exists, move it to a versioned backup before installing the new one and
keep a record containing the release tag, full SHA, patch hashes, artifact path,
and config backup paths.

Give the staged bundle a distinct display name, **Herdr Agent Tree**, and bundle
identifier, such as `dev.naeliofreires.herdr-agent-tree`, so it can be selected
separately from the standard app. Finalize its bundle metadata and local code
signature before recording its executable hash. Preserve an existing custom
installation's daemon connection and configuration paths when updating it.

Quit only the GUI client through its documented app command, after checking that
doing so will not terminate the agent performing the installation. Leave the
Herdr daemon and its agent sessions running. Move the staged bundle into place
atomically; on any failure restore the previous custom bundle and config backups.
Use elevated OS permissions only when the official install path requires them
and the operator approves. Do not bypass Gatekeeper, remove quarantine flags, or
claim that an unsigned local build is equivalent to the signed upstream app.

## 7. Verify the installed result

Record the installed executable's available build-info output. Some revisions
do not include a source SHA there; obtain that identity from the verified Git
checkout and record it with the build. Hash the finalized staged executable
and the installed executable and require an exact match. Signing changes must
be completed before this comparison; build-info alone does not prove our
changes are installed.
Store the executable hash with the release SHA and patch hashes. Launch the
installed bundle by its absolute path, not by app name, and confirm that the
running GUI executable is inside that bundle. Run Herdr config validation and
reload the same client.
Confirm the plugin registry entry and saved Agent Tree view are enabled, the
plugin log reports a successful enable/sync, and all three metadata tokens are
present on the actual pane context. In a desktop session, inspect a workspace
with distinct linked panes. Completion requires workspace cards with 10px side
spacing and 12px gaps, darker headers, continuous ancestor/elbow guides, a
selected marker that does not shift guide geometry, and icon-only agents that
retain task/tab title, lifecycle state, and accessibility labels. Use temporary
links only when safe and remove them afterward.

On a fresh install with no detected agents, use a clearly labelled temporary
verification workspace with real panes and fixture agent reports. The pattern
in [tests_live/test_daemon.py](tests_live/test_daemon.py) avoids starting provider
agents or changing existing parent links. Verify the cards and tree, unlink
fixture children while their panes still exist, then remove only that temporary
workspace. Empty workspaces do not receive cards without agent metadata.

If desktop inspection is unavailable, report the build and metadata checks as
verified and every visual criterion as pending. If a new stable release cannot
be safely selected, a patch cannot be ported, or the GUI cannot be launched,
report the blocker and all safe completed work without claiming completion. The
final report must include daemon/GUI/plugin versions, exact release tags and
SHAs, patch or port conflicts, executable hash and path, tests, installed path,
backup/rollback path, and every pending visual check. A build, setup guide, or
accepted command invocation alone is not a completed install.

Later updates repeat this workflow: select the new stable release, port and test
the patches, stage a new bundle, preserve the previous version, and record the
new provenance. Official Herdr updates may replace a system app only when the
user explicitly opted into that target; rerun this workflow afterward.
Update the custom client through this runbook so the native patches are carried
forward to the selected stable release.
