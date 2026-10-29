# Herdr Agent Tree

This repository contains two related deliverables:

- the Python Agent Tree plugin, installed with Herdr's plugin commands;
- an optional native GPUI companion, which adds workspace cards and hierarchy styling.

When a user says "install Herdr Agent Tree", uses the one-prompt workflow, or
asks to install, update, rebuild, or "put the cards in Herdr", complete the full
daemon + GPUI + Python plugin workflow. Read [INSTALL.md](INSTALL.md) and follow
it as the source of truth. Resolve the current latest stable release of both
Herdr and `penso/herdr-gpui`, verify their compatibility, and apply and port the
patches in `native/`. Build and test the client, install and launch a user-local
bundle, then verify the running app. Record provenance and rollback.

Treat Python-only plugin installation as an advanced fallback only when the user
explicitly requests textual mode or declines the native client. Do not stop at a
setup guide or plugin command while safe installation work remains possible.
Completion requires the correctly running user-local bundle, verified executable
hash and release SHA, enabled plugin registry and saved view, and real pane
metadata. Confirm cards, darker headers, continuous guides, stable selected-row
geometry, and icon-only agents that retain task title/lifecycle/accessibility;
report any unavailable desktop or release check as pending.

When a user only asks about plugin development or the textual fallback, read the
root [README.md](README.md) and run the unit suite from this checkout:

```sh
rtk proxy python3 -m unittest discover -s tests
```

Keep the upstream release as the base. If a patch conflicts, inspect the current
upstream code and the patch intent, port the behavior, add or update focused
coverage, and report the conflict and resolution. Do not force a patch, silently
drop a feature, downgrade an installed release, or replace `/Applications/Herdr.app`
without an explicit user request.
