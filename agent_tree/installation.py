"""Print setup steps for the plugin and custom app."""

from __future__ import annotations

from typing import TextIO

INSTALL_GUIDE = """Herdr Agent Tree setup

The Python plugin shows agents in a text tree. A tree links parent and child
agents. Workspace cards need the custom app. This is the Herdr GPUI app with
our code changes.

For the full setup, give one prompt to a coding agent that can use your
terminal. Use this prompt for the latest stable Herdr and custom app:
https://github.com/naeliofreires/herdr-agent-tree/blob/main/README.md#install-with-one-prompt

Install the latest stable Herdr version and the latest stable herdr-gpui
version. Build and use the custom app for workspace cards.

herdr plugin install installs this plugin only. It does not build or change the
Herdr app. For full install and update steps, see:
https://github.com/naeliofreires/herdr-agent-tree/blob/main/INSTALL.md

Set up and turn on the plugin using:
https://github.com/naeliofreires/herdr-agent-tree/blob/main/README.md#install-and-configure
"""


def write_installation_guide(output: TextIO) -> None:
    """Write setup steps for the plugin and custom app.

    Example: write_installation_guide(sys.stdout).
    """
    output.write(INSTALL_GUIDE)
