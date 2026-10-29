import io
import tomllib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_tree import __version__
from agent_tree.api import ApiError
from agent_tree.cli import _run, parser
from agent_tree.installation import write_installation_guide
from agent_tree.storage import StateStore


class SetupOutput(io.StringIO):
    """Named output double for setup guidance tests."""


class EnableApi:
    """Minimal daemon double for the explicit enable command."""

    def __init__(self, failing: bool = False) -> None:
        self.failing = failing

    def agents(self) -> list[dict[str, object]]:
        return []

    def report(self, pane_id: str, tokens: dict[str, str | None]) -> None:
        if self.failing:
            raise ApiError("enable failed", "internal")

    def set_view(self) -> None:
        if self.failing:
            raise ApiError("enable failed", "internal")


class InstallationTests(unittest.TestCase):
    def test_setup_explains_plugin_and_native_boundary(self) -> None:
        output = SetupOutput()
        write_installation_guide(output)
        guide = output.getvalue()
        self.assertIn("Python plugin provides", guide)
        self.assertIn("patched Herdr GPUI native client", guide)
        self.assertIn("does not build or modify", guide)
        self.assertIn("/INSTALL.md", guide)
        self.assertIn("README.md#install-and-configure", guide)

    def test_setup_action_contract_is_workspace_scoped(self) -> None:
        manifest_path = Path(__file__).parents[1] / "herdr-plugin.toml"
        manifest = tomllib.loads(manifest_path.read_text())
        self.assertEqual(manifest["name"], "Agent Tree (cards require native client)")
        self.assertIn(
            "Workspace cards require the native GPUI client", manifest["description"]
        )
        action = next(entry for entry in manifest["actions"] if entry["id"] == "setup")
        self.assertEqual(
            action["title"], "Setup: workspace cards need the native client"
        )
        self.assertEqual(action["contexts"], ["workspace"])
        self.assertEqual(action["command"], ["python3", "-m", "agent_tree", "setup"])

    def test_versions_match_manifest_and_project(self) -> None:
        root = Path(__file__).parents[1]
        manifest = tomllib.loads((root / "herdr-plugin.toml").read_text())
        project = tomllib.loads((root / "pyproject.toml").read_text())
        self.assertEqual(manifest["version"], "0.2.1")
        self.assertEqual(project["project"]["version"], manifest["version"])
        self.assertEqual(__version__, manifest["version"])

    def test_setup_command_does_not_construct_daemon_clients(self) -> None:
        output = SetupOutput()
        arguments = parser().parse_args(["setup"])
        with (
            patch("agent_tree.cli.sys.stdout", output),
            patch("agent_tree.cli.store_from_env", side_effect=AssertionError("store")),
            patch("agent_tree.cli.api_from_env", side_effect=AssertionError("api")),
        ):
            self.assertEqual(_run(arguments), 0)
        self.assertIn("Herdr Agent Tree setup", output.getvalue())

    def test_enable_prints_setup_guide_after_success(self) -> None:
        output = SetupOutput()
        with tempfile.TemporaryDirectory() as directory:
            store = StateStore(Path(directory), "/tmp/setup-test.sock")
            with (
                patch("agent_tree.cli.sys.stdout", output),
                patch("agent_tree.cli.store_from_env", return_value=store),
                patch("agent_tree.cli.api_from_env", return_value=EnableApi()),
            ):
                self.assertEqual(_run(parser().parse_args(["enable"])), 0)
        self.assertIn("enabled; synced 0 agents", output.getvalue())
        self.assertIn("Herdr Agent Tree setup", output.getvalue())

    def test_failed_enable_does_not_print_setup_guide(self) -> None:
        output = SetupOutput()
        with tempfile.TemporaryDirectory() as directory:
            store = StateStore(Path(directory), "/tmp/setup-test.sock")
            with (
                patch("agent_tree.cli.sys.stdout", output),
                patch("agent_tree.cli.store_from_env", return_value=store),
                patch(
                    "agent_tree.cli.api_from_env", return_value=EnableApi(failing=True)
                ),
                self.assertRaises(ApiError),
            ):
                _run(parser().parse_args(["enable"]))
        self.assertNotIn("Herdr Agent Tree setup", output.getvalue())
