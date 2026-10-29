import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch
from pathlib import Path

from agent_tree.api import ApiError, SOURCE
from agent_tree.cli import (
    disable,
    enable,
    link,
    list_links,
    socket_path_from_env,
    sync,
    unlink,
)
from agent_tree.model import LinkState
from agent_tree.storage import StateStore


class FakeApi:
    def __init__(self, records: list[dict[str, object]]) -> None:
        self.records = records
        self.reports: list[tuple[str, dict[str, str | None]]] = []
        self.view_sets = 0
        self.view_clears = 0

    def agents(self) -> list[dict[str, object]]:
        return self.records

    def panes(self) -> list[dict[str, object]]:
        return [{"pane_id": record["pane_id"]} for record in self.records]

    def report(self, pane_id: str, tokens: dict[str, str | None]) -> None:
        self.reports.append((pane_id, tokens))

    def set_view(self) -> None:
        self.view_sets += 1

    def clear_view(self) -> None:
        self.view_clears += 1


class FailingApi(FakeApi):
    def report(self, pane_id: str, tokens: dict[str, str | None]) -> None:
        raise ApiError("missing pane", "pane_not_found")


class BrokenApi(FakeApi):
    def report(self, pane_id: str, tokens: dict[str, str | None]) -> None:
        raise ApiError("daemon unavailable", "internal")


class PartialFailApi(FakeApi):
    def __init__(self, records: list[dict[str, object]]) -> None:
        super().__init__(records)
        self.calls = 0

    def report(self, pane_id: str, tokens: dict[str, str | None]) -> None:
        self.calls += 1
        if tokens["naeliofreires_tree_prefix"] is not None and self.calls == 2:
            raise ApiError("daemon unavailable", "internal")
        self.reports.append((pane_id, tokens))


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.store = StateStore(Path(self.temp.name), "/tmp/socket")
        self.api = FakeApi(
            [
                {
                    "terminal_id": "root",
                    "pane_id": "p1",
                    "workspace_id": "w1",
                    "tab_id": "t1",
                },
                {
                    "terminal_id": "child",
                    "pane_id": "p2",
                    "workspace_id": "w1",
                    "tab_id": "t1",
                },
            ]
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_enable_link_sync_and_unlink(self) -> None:
        self.store.save(LinkState(False, {}))
        enable(self.api, self.store)
        link(self.api, self.store, "p2", "p1")
        self.api.reports.clear()
        self.assertEqual(sync(self.api, self.store), 2)
        self.assertEqual(self.api.view_sets, 3)
        self.assertEqual(
            self.api.reports[1][1]["naeliofreires_tree_prefix"], "\u200b   └─ "
        )
        self.assertEqual(self.api.reports[1][1]["naeliofreires_tree_path"], "v1:00")
        unlink(self.api, self.store, "child")
        self.assertEqual(self.store.load().links, {})

    def test_all_missing_pane_codes_are_tolerated_in_sync_and_disable(self) -> None:
        for code in ("pane_not_found", "agent_pane_not_found", "agent_not_found"):
            with self.subTest(code=code):
                self.store.save(LinkState(True, {}))
                api = FakeApi(self.api.records)
                with patch.object(
                    api, "report", side_effect=ApiError("missing", code)
                ) as report:
                    self.assertEqual(sync(api, self.store), 2)
                    self.assertEqual(disable(api, self.store), 2)
                self.assertEqual(report.call_count, 4)
                self.assertEqual(api.view_sets, 1)
                self.assertEqual(api.view_clears, 1)
                self.assertFalse(self.store.load().enabled)

    def test_unexpected_report_error_propagates_in_sync_and_disable(self) -> None:
        for command in (sync, disable):
            with self.subTest(command=command.__name__):
                self.store.save(LinkState(True, {}))
                api = FakeApi(self.api.records)
                error = ApiError("daemon unavailable", "internal")
                with patch.object(api, "report", side_effect=error) as report:
                    with self.assertRaises(ApiError) as raised:
                        command(api, self.store)
                self.assertIs(raised.exception, error)
                self.assertEqual(report.call_count, 1)
                self.assertEqual(api.view_sets, 0)
                self.assertEqual(api.view_clears, 0)
                self.assertEqual(self.store.load().enabled, command is sync)

    def test_set_view_failure_rolls_back_and_clears_exact_report_tokens(self) -> None:
        previous = LinkState(False, {"child": "root"})
        self.store.save(previous)
        error = ApiError("view unavailable", "internal")
        with patch.object(self.api, "set_view", side_effect=error):
            with self.assertRaises(ApiError) as raised:
                enable(self.api, self.store)
        self.assertIs(raised.exception, error)
        self.assertEqual(self.store.load(), previous)
        self.assertEqual(self.api.reports, [
            ("p1", {
                "naeliofreires_tree_prefix": "\u200b└─ ",
                "naeliofreires_tree_order": "00000000",
                "naeliofreires_tree_path": "v1:0",
            }),
            ("p2", {
                "naeliofreires_tree_prefix": "\u200b   └─ ",
                "naeliofreires_tree_order": "00000001",
                "naeliofreires_tree_path": "v1:00",
            }),
            ("p1", {
                "naeliofreires_tree_prefix": None,
                "naeliofreires_tree_order": None,
                "naeliofreires_tree_path": None,
            }),
            ("p2", {
                "naeliofreires_tree_prefix": None,
                "naeliofreires_tree_order": None,
                "naeliofreires_tree_path": None,
            }),
        ])
        self.assertEqual(self.api.view_clears, 1)

    def test_disable_clears_plugin_tokens_and_view(self) -> None:
        self.store.save(LinkState(True, {}))
        self.assertEqual(disable(self.api, self.store), 2)
        self.assertEqual(self.api.view_clears, 1)
        self.assertTrue(
            all(
                report[1]["naeliofreires_tree_prefix"] is None
                for report in self.api.reports
            )
        )
        self.assertTrue(
            all(
                report[1]["naeliofreires_tree_path"] is None
                for report in self.api.reports
            )
        )
        self.assertFalse(self.store.load().enabled)
        self.assertEqual(SOURCE, "plugin:naeliofreires.agent-tree")

    def test_disable_marker_survives_cleanup_failure_and_enable_rolls_back(
        self,
    ) -> None:
        self.store.save(LinkState(True, {}))
        with self.assertRaises(ApiError):
            disable(BrokenApi(self.api.records), self.store)
        self.assertFalse(self.store.load().enabled)
        self.store.save(LinkState(False, {}))
        with self.assertRaises(ApiError):
            enable(BrokenApi(self.api.records), self.store)
        self.assertFalse(self.store.load().enabled)

    def test_enable_cleans_successful_partial_reports(self) -> None:
        self.store.save(LinkState(False, {}))
        api = PartialFailApi(self.api.records)
        with self.assertRaises(ApiError):
            enable(api, self.store)
        self.assertFalse(self.store.load().enabled)
        self.assertTrue(
            any(
                tokens["naeliofreires_tree_prefix"] is None for _, tokens in api.reports
            )
        )
        self.assertEqual(api.view_clears, 1)

    def test_enable_failure_keeps_existing_enabled_projection(self) -> None:
        self.store.save(LinkState(True, {}))
        api = PartialFailApi(self.api.records)
        with self.assertRaises(ApiError):
            enable(api, self.store)
        self.assertTrue(self.store.load().enabled)
        self.assertFalse(
            any(
                tokens["naeliofreires_tree_prefix"] is None for _, tokens in api.reports
            )
        )
        self.assertEqual(api.view_clears, 0)

    def test_missing_pane_cleanup_is_tolerated_and_link_syncs(self) -> None:
        self.store.save(LinkState(True, {}))
        api = FailingApi(self.api.records)
        self.assertEqual(disable(api, self.store), 2)
        self.store.save(LinkState(True, {}))
        link(self.api, self.store, "child", "root")
        self.assertGreater(self.api.view_sets, 0)

    def test_disable_clears_panes_without_detected_agents(self) -> None:
        class ExtraPaneApi(FakeApi):
            def panes(self) -> list[dict[str, object]]:
                return super().panes() + [{"pane_id": "p-undetected"}]

        self.store.save(LinkState(True, {}))
        api = ExtraPaneApi(self.api.records)
        self.assertEqual(disable(api, self.store), 3)
        self.assertEqual(
            [pane_id for pane_id, _ in api.reports], ["p1", "p2", "p-undetected"]
        )
        self.assertTrue(
            all(tokens["naeliofreires_tree_path"] is None for _, tokens in api.reports)
        )

    def test_list_prints_live_agents_even_without_links(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            list_links(self.api, self.store)
        self.assertIn("root pane=p1 workspace=w1 parent=-", output.getvalue())
        self.assertIn("child pane=p2 workspace=w1 parent=-", output.getvalue())

    def test_default_socket_namespace_is_shared(self) -> None:
        with patch.dict(
            "os.environ",
            {"HERDR_SOCKET_PATH": "", "XDG_CONFIG_HOME": "/tmp/herdr-test-config"},
            clear=False,
        ):
            self.assertEqual(
                socket_path_from_env(), "/tmp/herdr-test-config/herdr/herdr.sock"
            )

    def test_disabled_event_does_not_construct_api(self) -> None:
        self.store.save(LinkState(False, {}))
        with (
            patch("agent_tree.cli.store_from_env", return_value=self.store),
            patch("agent_tree.cli.api_from_env", side_effect=AssertionError("I/O")),
        ):
            from agent_tree.cli import _run, parser

            self.assertEqual(_run(parser().parse_args(["event"])), 0)
