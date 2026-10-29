# Install the native Agent Tree client

This runbook is for an agent working in this repository after a user asks for a
complete Agent Tree installation. It builds a patched Herdr GPUI client from the
latest stable upstream release available at execution time. It does not mutate
the upstream repository or the managed plugin installation directory.

The Python plugin and the native client are separate layers:

```text
Herdr plugin install -> metadata, links, textual fallback
native build         -> workspace cards, native guides, selection and icons
```

The plugin is listed as **Agent Tree (cards require native client)** so the
dependency is visible in Herdr's installation preview. For a reminder of the
setup steps, run this from the plugin checkout; it does not require a daemon:

```sh
rtk proxy python3 -m agent_tree setup
```

The equivalent `naeliofreires.agent-tree.setup` action records its guide in
Herdr's plugin command log. Successful explicit `enable` commands also record
the guide; ordinary startup and pane-event hooks do not repeat it. Neither
command builds or installs the native client. Follow the remaining steps here
for a complete installation.

Shell examples use the optional RTK wrapper, matching this repository's README.
If RTK is unavailable on the user's machine, omit `rtk proxy`.

## 1. Inspect before changing anything

Record the operating system, architecture, current user, Herdr version, exact
GUI executable and whether a daemon is running. Read any `AGENTS.md`, toolchain
file, README, and `justfile` in the upstream checkout selected below. Check for:

- an existing managed or locally linked `naeliofreires.agent-tree` plugin;
- disabled plugin state and recent plugin logs;
- custom Herdr sidebar rows and Agent Tree settings;
- an existing user-local Agent Tree bundle and its recorded source commit;
- a dirty native source checkout that must not be reused.

Preserve existing configuration, agent sessions, links, and user edits. Use a
named socket when the user has more than one daemon; never guess the target from
the current directory. Do not stop the daemon or kill agent processes. If the
agent itself is running inside the Herdr GUI that must be replaced, checkpoint
or coordinate that session before asking the GUI to quit.

## 2. Select and prepare upstream

Use the latest stable release from `https://github.com/penso/herdr-gpui` at the
time of installation. Prefer the official release API, for example:

```sh
rtk proxy gh api repos/penso/herdr-gpui/releases/latest
```

If `gh` is unavailable, use the official releases page or API with an equivalent
read-only request. Record the release tag and full commit SHA. Do not silently
use `main`, a preview build, or an older pinned commit. If the installed client
is newer than the latest stable release, stop and ask whether to use preview or
build from `main`.

Create a persistent user-local build directory outside this plugin checkout and
outside Herdr's managed plugin roots. Clone the selected tag there, verify the
full SHA, and create a disposable branch or worktree for the port. Read the
upstream toolchain and build instructions before installing missing tools. Use
the toolchain required by that exact revision; do not assume the version in the
historical patch notes is still current.

Check the selected client's daemon version and protocol requirements against
the running daemon. If an upgrade is required, follow the official supported
upgrade/handoff procedure while preserving sessions. Report a compatibility
blocker if that cannot be done; compiling the GUI alone is insufficient.

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
rtk proxy env CARGO_BUILD_JOBS=1 CARGO_PROFILE_DEV_DEBUG=0 CARGO_INCREMENTAL=0 \
  cargo check --locked -p herdr-gpui --tests
```

Run the upstream sidebar, build, lint, or GUI checks that exist at the selected
revision. Do not claim a visual check when no desktop session is available.
Build a complete macOS bundle with the current upstream recipe (normally
`just bundle` for `target/release/Herdr.app`), then verify its executable
identity and the recorded upstream SHA. On Linux, follow the selected revision's
documented package or user-local installation method; do not run macOS commands.

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
Do not use `sudo`, bypass Gatekeeper, remove quarantine flags, or claim that an
unsigned local build is equivalent to the signed upstream application.

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
Confirm the plugin log reports a successful enable/sync and that the three
metadata tokens are present. In a desktop session, inspect a workspace with
distinct linked panes: workspace cards, headers, ancestor/elbow guides, selected
row marker, agent identity, lifecycle state, and accessibility labels must all
remain visible. Use temporary links only when safe and remove them afterward.

If desktop inspection is unavailable, report the build and metadata checks as
verified and visual behavior as pending. The final report must include the exact
release tag/SHA, patch or port conflicts, tests, installed path, backup/rollback
path, and any pending visual check. A build alone is not a completed install.

Later updates repeat this workflow: select the new stable release, port and test
the patches, stage a new bundle, preserve the previous version, and record the
new provenance. Official Herdr updates may replace a system app only when the
user explicitly opted into that target; rerun this workflow afterward.
Update the custom client through this runbook so the native patches are carried
forward to the selected stable release.
