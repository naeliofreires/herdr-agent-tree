"""Opt-in integration against an explicitly selected, isolated Herdr binary."""

from __future__ import annotations

import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from typing import cast

from agent_tree.api import HerdrApi, SOURCE
from agent_tree.cli import disable, enable, link
from agent_tree.storage import StateStore


def isolated_environment(directory: Path) -> dict[str, str]:
    """Build a private daemon environment; e.g. isolated_environment(Path('/tmp/t'))."""
    isolated = {key: os.environ[key] for key in ("PATH", "LANG") if key in os.environ}
    isolated.update(
        HOME=str(directory),
        SHELL="/bin/sh",
        XDG_CONFIG_HOME=str(directory / "config"),
        XDG_STATE_HOME=str(directory / "state"),
        XDG_RUNTIME_DIR=str(directory / "run"),
        HERDR_SOCKET_PATH=str(directory / "api.sock"),
        HERDR_CONFIG_PATH=str(directory / "config.toml"),
        HERDR_DISABLE_SOUND="1",
    )
    return isolated


def object_field(record: dict[str, object], field: str) -> dict[str, object]:
    """Require an object field in a response; e.g. object_field(response, 'pane')."""
    value = record.get(field)
    if not isinstance(value, dict):
        raise AssertionError(f"{field}={value!r}; expected an object")
    return cast(dict[str, object], value)


@unittest.skipUnless(
    os.environ.get("HERDR_TEST_BINARY"), "set HERDR_TEST_BINARY explicitly"
)
class IsolatedDaemonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sandbox = tempfile.TemporaryDirectory(prefix="hat-", dir="/private/tmp")
        self.addCleanup(self.sandbox.cleanup)
        directory = Path(self.sandbox.name)
        self.environment = isolated_environment(directory)
        (directory / "run").mkdir()
        (directory / "config.toml").write_text("onboarding = false\n", encoding="utf-8")
        self.start_child(directory)
        self.api = HerdrApi(self.environment["HERDR_SOCKET_PATH"])
        self.store = StateStore(
            directory / "plugin-state", self.environment["HERDR_SOCKET_PATH"]
        )
        self.await_ready()

    def start_child(self, directory: Path) -> None:
        self.log = (directory / "daemon.log").open("wb")
        self.addCleanup(self.log.close)
        binary = str(Path(os.environ["HERDR_TEST_BINARY"]).resolve(strict=True))
        self.child = subprocess.Popen(
            [binary, "server"],
            env=self.environment,
            stdin=subprocess.DEVNULL,
            stdout=self.log,
            stderr=self.log,
        )
        self.addCleanup(self.stop_child)

    def stop_child(self) -> None:
        if self.child.poll() is not None:
            return
        self.child.terminate()
        try:
            self.child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.child.kill()
            self.child.wait(timeout=2)

    def await_ready(self) -> None:
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            if self.child.poll() is not None:
                self.fail(
                    f"isolated daemon exited with {self.child.returncode}; expected running"
                )
            if Path(self.environment["HERDR_SOCKET_PATH"]).exists():
                self.api.request("ping", {})
                return
            time.sleep(0.05)
        self.fail(
            "isolated daemon socket missing after 8 seconds; expected ready socket"
        )

    def seed_agents(self) -> list[str]:
        created = self.api.request(
            "workspace.create", {"label": "tree-test", "focus": False}
        )
        root_pane = object_field(created, "root_pane")
        pane_ids = [str(root_pane["pane_id"])]
        for _ in range(2):
            split = self.api.request(
                "pane.split", {"target_pane_id": pane_ids[0], "direction": "right"}
            )
            pane_ids.append(str(object_field(split, "pane")["pane_id"]))
        for pane_id in pane_ids:
            self.report_test_agent(pane_id)
        return pane_ids

    def report_test_agent(self, pane_id: str) -> None:
        report = {
            "pane_id": pane_id,
            "source": "user:tree-test",
            "agent": "codex",
            "state": "working",
        }
        self.api.request("pane.report_agent", report)

    def register_plugin(self) -> None:
        binary = str(Path(os.environ["HERDR_TEST_BINARY"]).resolve(strict=True))
        checkout = str(Path(__file__).resolve().parent.parent)
        command = [binary, "plugin", "link", checkout]
        linked = subprocess.run(
            command, env=self.environment, capture_output=True, timeout=5
        )
        self.assertEqual(linked.returncode, 0, linked.stderr.decode("utf-8"))

    def seed_other_metadata(self, pane_id: str) -> None:
        self.api.report(
            pane_id,
            {
                "naeliofreires_tree_prefix": None,
                "naeliofreires_tree_order": None,
                "naeliofreires_tree_path": None,
            },
        )
        self.api.request(
            "pane.report_metadata",
            {
                "pane_id": pane_id,
                "source": "user:unrelated",
                "tokens": {"unrelated": "keep"},
            },
        )

    def test_three_levels_metadata_and_source_owned_cleanup(self) -> None:
        self.register_plugin()
        pane_ids = self.seed_agents()
        self.seed_other_metadata(pane_ids[0])
        link(self.api, self.store, pane_ids[1], pane_ids[0])
        link(self.api, self.store, pane_ids[2], pane_ids[1])
        self.assertEqual(enable(self.api, self.store), 3)
        self.assert_tree(pane_ids)
        self.api.request(
            "agent.view.set", {"source": "user:unrelated", "label": "other", "sort": []}
        )
        disable(self.api, self.store)
        self.assert_cleanup(pane_ids)

    def assert_tree(self, pane_ids: list[str]) -> None:
        agents = {str(record["pane_id"]): record for record in self.api.agents()}
        expected_prefixes = ["\u200b└─ ", "\u200b   └─ ", "\u200b      └─ "]
        expected_paths = ["v1:0", "v1:00", "v1:000"]
        for rank, pane_id in enumerate(pane_ids):
            tokens = object_field(agents[pane_id], "tokens")
            self.assertEqual(tokens["naeliofreires_tree_order"], f"{rank:08d}")
            self.assertEqual(tokens["naeliofreires_tree_path"], expected_paths[rank])
            # Herdr removes spaces at the end of display values.
            self.assertEqual(
                tokens["naeliofreires_tree_prefix"], expected_prefixes[rank].rstrip()
            )

    def assert_cleanup(self, pane_ids: list[str]) -> None:
        for record in self.api.panes():
            tokens = cast(dict[str, object], record.get("tokens", {}))
            self.assertNotIn("naeliofreires_tree_prefix", tokens)
            self.assertNotIn("naeliofreires_tree_order", tokens)
            self.assertNotIn("naeliofreires_tree_path", tokens)
        root = next(
            record for record in self.api.agents() if record["pane_id"] == pane_ids[0]
        )
        self.assertEqual(object_field(root, "tokens")["unrelated"], "keep")
        view = self.api.request("agent.view.clear", {"source": SOURCE})
        self.assertEqual(view["source"], "user:unrelated")
        self.assertTrue(view["active"])
        self.assertFalse(self.store.load().enabled)


if __name__ == "__main__":
    unittest.main()
