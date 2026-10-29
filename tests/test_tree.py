import unittest

from agent_tree.model import Agent, LinkState, MAX_DEPTH, StateShapeError
from agent_tree.tree import build_rows, parse_agents, validate_graph, validate_link


def agent(terminal: str, pane: str, workspace: str = "w1", tab: str = "t1") -> Agent:
    return Agent(terminal, pane, workspace, tab)


class TreeTests(unittest.TestCase):
    def test_empty_input_ignores_unknown_cycles(self) -> None:
        self.assertEqual(build_rows([], {"missing": "missing"}), [])

    def test_missing_ancestor_ends_chain_and_becomes_root(self) -> None:
        records = [agent("child", "p1"), agent("parent", "p2")]
        rows = build_rows(
            records, {"child": "parent", "parent": "missing", "missing": "child"}
        )
        self.assertEqual([row.agent.terminal_id for row in rows], ["parent", "child"])
        self.assertEqual([row.branch_path for row in rows], ["v1:0", "v1:00"])

    def test_workspace_boundary_breaks_apparent_cycle(self) -> None:
        records = [agent("a", "p1"), agent("b", "p2"), agent("c", "p3", "w2")]
        rows = build_rows(records, {"a": "b", "b": "c", "c": "a"})
        self.assertEqual([row.agent.terminal_id for row in rows], ["b", "a", "c"])
        self.assertEqual(
            [row.prefix for row in rows], ["\u200b└─ ", "\u200b   └─ ", "\u200b└─ "]
        )

    def test_interleaved_workspaces_keep_input_order_and_global_ranks(self) -> None:
        records = [
            agent("a-child", "p1", "w2"),
            agent("b-root", "p2"),
            agent("a-root", "p3", "w2"),
            agent("b-child", "p4"),
            agent("a-other", "p5", "w2"),
        ]
        rows = build_rows(records, {"a-child": "a-root", "b-child": "b-root"})
        self.assertEqual(
            [row.agent.terminal_id for row in rows],
            ["a-root", "a-child", "a-other", "b-root", "b-child"],
        )
        self.assertEqual([row.order for row in rows], [f"{i:08d}" for i in range(5)])
        self.assertEqual(
            [row.branch_path for row in rows],
            ["v1:1", "v1:10", "v1:0", "v1:0", "v1:00"],
        )

    def test_cycle_and_depth_errors_preserve_check_order(self) -> None:
        with self.assertRaisesRegex(ValueError, "^link graph at 'a' contains a cycle$"):
            validate_graph([agent("a", "p")], {"a": "a"})
        records = [agent(str(i), f"p{i}") for i in range(MAX_DEPTH)]
        links = {str(i): str((i + 1) % MAX_DEPTH) for i in range(MAX_DEPTH)}
        with self.assertRaisesRegex(
            ValueError, f"^link graph at '0' exceeds depth {MAX_DEPTH}$"
        ):
            validate_graph(records, links)

    def test_depth_first_prefixes_and_stable_orders(self) -> None:
        records = [
            agent("root", "p1"),
            agent("child", "p2"),
            agent("grand", "p3"),
            agent("sibling", "p4"),
        ]
        rows = build_rows(records, {"child": "root", "grand": "child"})
        self.assertEqual(
            [row.agent.terminal_id for row in rows],
            ["root", "child", "grand", "sibling"],
        )
        self.assertEqual(rows[1].prefix, "\u200b│  └─ ")
        self.assertEqual(rows[2].prefix, "\u200b│     └─ ")
        self.assertEqual(
            [row.branch_path for row in rows],
            ["v1:1", "v1:10", "v1:100", "v1:0"],
        )
        self.assertEqual(
            [row.order for row in rows],
            ["00000000", "00000001", "00000002", "00000003"],
        )

    def test_branch_path_marks_sibling_continuation(self) -> None:
        records = [agent("root", "p1"), agent("first", "p2"), agent("last", "p3")]
        rows = build_rows(records, {"first": "root", "last": "root"})
        self.assertEqual([row.branch_path for row in rows], ["v1:0", "v1:01", "v1:00"])

    def test_cross_workspace_and_orphan_are_roots(self) -> None:
        records = [agent("root", "p1"), agent("other", "p2", "w2")]
        rows = build_rows(records, {"other": "root"})
        self.assertEqual([row.prefix for row in rows], ["\u200b└─ ", "\u200b└─ "])

    def test_malformed_cycle_is_rejected(self) -> None:
        records = [agent("a", "p1"), agent("b", "p2")]
        with self.assertRaises(ValueError):
            build_rows(records, {"a": "b", "b": "a"})

    def test_link_validation_rejects_self_cross_workspace_and_cycle(self) -> None:
        child = agent("child", "p2")
        parent = agent("parent", "p1")
        with self.assertRaises(ValueError):
            validate_link(child, child, {}, {child.terminal_id: child})
        with self.assertRaises(ValueError):
            validate_link(
                child, agent("other", "p3", "w2"), {}, {child.terminal_id: child}
            )
        with self.assertRaises(ValueError):
            validate_link(
                child, parent, {"parent": "child"}, {"child": child, "parent": parent}
            )

    def test_model_shape_validation(self) -> None:
        with self.assertRaises(StateShapeError):
            Agent.from_record({"pane_id": "p1"})
        with self.assertRaises(StateShapeError):
            LinkState.from_json({"enabled": "yes", "links": {}})
        self.assertEqual(parse_agents([]), [])

    def test_duplicate_ids_and_full_graph_depth_are_rejected(self) -> None:
        duplicate = [
            {"terminal_id": "a", "pane_id": "p", "workspace_id": "w", "tab_id": "t"}
        ] * 2
        with self.assertRaises(ValueError):
            parse_agents(duplicate)
        valid_records = [agent(str(index), f"p{index}") for index in range(16)]
        valid_links = {str(index): str(index - 1) for index in range(1, 16)}
        self.assertEqual(
            len(build_rows(valid_records, valid_links)), len(valid_records)
        )
        self.assertEqual(
            build_rows(valid_records, valid_links)[-1].branch_path,
            "v1:" + "0" * 16,
        )
        records = [agent(str(index), f"p{index}") for index in range(17)]
        links = {str(index): str(index - 1) for index in range(1, 17)}
        with self.assertRaises(ValueError):
            validate_graph(records, links)
