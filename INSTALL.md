# Install the custom Agent Tree app

This guide installs the plugin and custom app. Start with the prompt in
[README.md](README.md). Find the latest stable versions at install time.
Work in a new build folder. Keep the files of other installed apps.

Words used here: a daemon is a server; a SHA is a code ID; a hash is a file ID.
A tag is a version name. A patch is a file with code changes.
Metadata means extra details about an agent or app. A text fallback is the
text tree used when the custom view is not available. Lifecycle means the
agent's current state. Screen reader labels help people use assistive tools.
Code signing adds a signature to an app. It helps check that its code did not
change. A fixture is test data. Rollback means use the old app again. A protocol
is how app and server talk. On macOS, an app bundle is a folder ending in `.app`.

The Python plugin and the custom app are two parts:

```text
Herdr plugin install -> saved tree data, links, text fallback
custom app build     -> workspace cards, guides, selection and icons
```

The plugin is shown as **Agent Tree (cards need the custom app)**. The Python
installer does not build the custom app.

If Git or Python is missing, install it from its official guide and check it
before use. This guide assumes neither tool is present.

If there is no local copy, clone this public repository outside Herdr's managed
plugin roots. Then read both instruction files before making changes:

```sh
rtk proxy git clone https://github.com/naeliofreires/herdr-agent-tree.git /path/to/herdr-agent-tree
rtk proxy sed -n '1,220p' /path/to/herdr-agent-tree/AGENTS.md
rtk proxy sed -n '1,320p' /path/to/herdr-agent-tree/INSTALL.md
```

The raw guide is also at
https://raw.githubusercontent.com/naeliofreires/herdr-agent-tree/main/INSTALL.md.
The Python installer does not build the custom app. RTK is an optional command
wrapper, not a project dependency; remove `rtk proxy` if it is unavailable.

## 1. Check before changing anything

Record the OS, CPU, user, Herdr and GUI versions, GUI path, and daemon status.
Read `AGENTS.md`, Rust build files, READMEs, and `justfile` files. Check:

- an existing managed or locally linked `naeliofreires.agent-tree` plugin;
- disabled plugin state and recent plugin logs;
- custom Herdr sidebar rows and Agent Tree settings;
- an existing user-local Agent Tree bundle and its recorded source commit;
- a dirty native source folder that must not be reused.

Keep config, sessions, links, and user edits. Use a named socket for more than
one daemon. Do not stop a daemon or kill agents. Save install work before
asking its GUI to quit.

## 2. Choose versions that work together

Find the latest stable release in both official repositories: Herdr at
`https://github.com/herdrdev/herdr` and GPUI at
`https://github.com/penso/herdr-gpui`. Use each release API first:

```sh
rtk proxy gh api repos/herdrdev/herdr/releases/latest
rtk proxy gh api repos/penso/herdr-gpui/releases/latest
```

Use official release pages or APIs if `gh` is unavailable. Record each tag and
resolve it to a full commit SHA. A `target_commitish` can move, so do not use it
as the SHA. Check GUI and daemon protocol versions. If the latest pair cannot
work together, report a blocker. Do not silently use `main`, a preview, or an
old base, or downgrade a newer preview without approval.

If the daemon is missing, install the selected stable release with the current
official guide and start it normally. Check version and protocol before opening
the GUI. Use the same official channel for updates. Replacing a CLI file does
not replace a running server. Record installed CLI and running server versions
and protocol. An older server with active panes may stay if it works, but report
the pending upgrade.

Read [Herdr update docs](https://herdr.dev/docs/install/#update),
[live handoff](https://herdr.dev/docs/session-state/#live-handoff), and the
[old session note](https://herdr.dev/docs/troubleshooting/#herdr-updated-but-the-running-session-is-still-old).
The experimental `herdr update --handoff` is for direct Herdr-managed installs
only and needs approval. Keep panes alive. Report unsafe upgrades as blockers.

Create a user-local build folder outside this source folder and Herdr's managed
roots. Copy the GPUI tag there, check its SHA, and use a short-lived separate
code copy.
Use the official daemon binary channel unless its guide requires source. Read
the selected Rust and platform guides before installing code tools.

## 3. Add the custom app changes

Apply these files in order:

1. `native/01-native-tree-model.patch`
2. `native/02-native-sidebar-presentation.patch`
3. `native/03-compact-agent-icons.patch`

Try the normal patch tool first. If one fails, keep the selected release as the
base and copy the change into the current code. Add the `v1:` path model,
cards, guides, selected marker, and small agent icons from
[native/README.md](native/README.md). Keep agent state and labels for assistive
tools. Read every conflict. Do not force or skip a patch without a report. A
report does not make the install complete: all three changes must be applied
and tested. Update the tests when you change code. Keep Apache-2.0 and MIT notices.

## 4. Verify before installation

Run the plugin suite from this source folder:

```sh
rtk proxy python3 -m unittest discover -s tests
```

All tests must pass. Report the test result.

From the changed GPUI source folder, run its native checks. At least run the
Agent Tree path and line tests (`just test-agent-tree` when available). Also
run the package check with fixed dependency versions:

```sh
rtk proxy just test-agent-tree
rtk proxy env CARGO_BUILD_JOBS=1 CARGO_PROFILE_DEV_DEBUG=0 CARGO_INCREMENTAL=0 cargo check --locked -p herdr-gpui --tests
```

Run available sidebar, build, lint, and GUI checks from the original project.
Do not claim a
visual check without a desktop session. Build a full bundle with the selected
recipe and check its executable and source SHA. On macOS this is often
`just bundle` for `target/release/Herdr.app`; on Linux use that release's guide.
Do not run macOS commands on Linux.

## 5. Set up the plugin and custom app

Install or link the Python plugin once. Keep its source kind. Use the managed
update command, or reinstall the same GitHub source when no update command
exists. Use `plugin link` only for a local source folder. Do not replace a
managed source with a local one.

If the plugin is off, turn it on and read its action log. Herdr can accept a
command while it is still running. Wait for a result that says it passed.

Herdr's plugin list has one on/off setting. The saved tree has another one.
Both must be on:

```sh
rtk proxy herdr plugin action invoke naeliofreires.agent-tree.enable
rtk proxy herdr plugin log list --plugin naeliofreires.agent-tree --limit 3
```

Keep `state_icon` first when adding the textual fallback token:

```toml
[ui.sidebar.agents]
rows = [["state_icon", { token = "$naeliofreires_tree_prefix", dim = true }, "agent", "tab"]]
```

The custom app needs nested placement and inline metadata. Apply these values
while preserving other settings:

```toml
agents_placement = "nested"
layout = "compact"
edge_rail = false

[usage]
inline = true
```

Back up each config before editing. Reload the daemon and exact client in use.
Do not reload `/Applications/Herdr.app` when testing the custom bundle.

## 6. Install with rollback

Prepare the complete, tested app bundle before changing the target. On macOS,
use `~/Applications/Herdr Agent Tree.app`; leave `/Applications/Herdr.app`
untouched unless asked. Move an old custom bundle to a versioned backup first.
Record the release tag, full SHA, patch hashes, built file path, and config paths.

Give it the display name **Herdr Agent Tree** and bundle ID
`dev.naeliofreires.herdr-agent-tree`. Finalize metadata and local code
signature before recording the hash. Keep daemon and config paths when updating.

Quit only the GUI client with its documented app command, after checking it
will not terminate the install agent. Keep the daemon and sessions running.
Move the bundle in one safe move. On failure, restore the old bundle and config.
Use elevated OS permissions only when the official path needs them and approval
exists. Do not bypass Gatekeeper, remove quarantine flags, or call an unsigned
build an upstream app.

## 7. Verify the installed result

Record build information and the verified source SHA. Hash the final prepared
and installed executables and require an exact match. Finish signing first.
Store the executable hash with the release SHA and patch hashes. Build
information alone does not prove our code is running.

Launch the bundle by absolute path, not app name. Check the running PID and
executable path inside that bundle. Validate config and reload the same client.
Check the plugin list and saved view. Check for a passed plugin log and all
three tokens on the real panes. In a desktop session, check linked panes. Completion
needs cards with 10px side spacing, 12px gaps, darker headers, continuous
tree lines, a selected row mark that stays in place, and agent icons that keep
task/tab titles, work state, and screen reader labels. Remove test links.

On a fresh install with no agents, use a labelled temporary workspace with real
panes and test agent data. The pattern in
[tests_live/test_daemon.py](tests_live/test_daemon.py)
avoids provider agents and existing parent links. Check cards and tree. Remove
test links before their panes and workspace. Empty workspaces do not receive
cards without agent metadata.

If desktop inspection is unavailable, report build and metadata checks as done
and visual checks as pending. If a stable pair cannot be selected, a patch
cannot be copied into the current code, or the GUI cannot launch, report the
blocker and safe work only. Do not claim completion. The final report must
include daemon, GUI, and plugin versions; release tags and SHAs; patch
conflicts; executable hash/path; tests; install path; backup/rollback path;
and all pending visual checks. A
build, setup guide, or accepted command is not enough.

Use this guide again for updates. Find the new stable versions. Add and test
all our code changes. Keep the old app before you add the new one.
Save the new code and file IDs. Change a system app only when the user asks.
