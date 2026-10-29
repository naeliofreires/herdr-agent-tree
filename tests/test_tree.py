import unittest

from agent_tree.model import Agent, LinkState, StateShapeError
from agent_tree.tree import build_rows, parse_agents, validate_graph, validate_link


def agent(terminal: str, pane: str, workspace: str = "w1", tab: str = "t1") -> Agent:
    return Agent(terminal, pane, workspace, tab)


class TreeTests(unittest.TestCase):
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
