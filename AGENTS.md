# Herdr Agent Tree

This repository contains two related deliverables:

- the Python Agent Tree plugin, installed with Herdr's plugin commands;
- an optional native GPUI companion, which adds workspace cards and hierarchy styling.

When a user asks to install, update, rebuild, or "put the cards in Herdr", read
[INSTALL.md](INSTALL.md) and follow it as the source of truth. The workflow must
select the latest stable `penso/herdr-gpui` release at execution time, apply and
port the patches in `native/`, verify the build, and install a user-local bundle
with a recorded rollback path.

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
