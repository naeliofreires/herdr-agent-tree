"""User-facing setup guidance for the Python plugin and native companion."""

from __future__ import annotations

from typing import TextIO

INSTALL_GUIDE = """Herdr Agent Tree setup

For the complete experience, give one prompt to a coding agent with local
terminal access. Copy the prompt for the latest stable Herdr and native styles:
https://github.com/naeliofreires/herdr-agent-tree/blob/main/README.md#install-with-one-prompt

The Python plugin provides the parent/child hierarchy and textual sidebar guides.
Workspace cards, darker headers, continuous native guides, accent selection, and
icon-only agents require the patched Herdr GPUI native client.

herdr plugin install installs this plugin only; it does not build or modify
the Herdr GUI. For complete agent-assisted native install and update steps, see:
https://github.com/naeliofreires/herdr-agent-tree/blob/main/INSTALL.md

Configure and enable the plugin using:
https://github.com/naeliofreires/herdr-agent-tree/blob/main/README.md#install-and-configure

After building the native companion, launch the bundle by its exact path and
verify it is the patched app. Do not assume a generic Herdr.app includes these
native features.
"""


def write_installation_guide(output: TextIO) -> None:
    """Write plugin/native setup guidance.

    Example: write_installation_guide(sys.stdout).
    """
    output.write(INSTALL_GUIDE)
