import json
import tempfile
import threading
import unittest
from pathlib import Path

from agent_tree.model import LinkState, StateShapeError
from agent_tree.storage import StateStore


class StorageTests(unittest.TestCase):
    def test_scoped_atomic_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = StateStore(Path(directory), "/tmp/one")
            second = StateStore(Path(directory), "/tmp/two")
            first.save(LinkState(True, {"child": "parent"}))
            self.assertTrue(first.load().enabled)
            self.assertEqual(first.load().links["child"], "parent")
            self.assertNotEqual(first.path, second.path)

    def test_malformed_file_reports_path_and_shape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = StateStore(Path(directory), "/tmp/socket")
            store.path.parent.mkdir(parents=True, exist_ok=True)
            store.path.write_text(json.dumps({"enabled": "bad"}), encoding="utf-8")
            with self.assertRaises(StateShapeError) as context:
                store.load()
            self.assertIn("enabled", str(context.exception))

    def test_concurrent_writes_leave_valid_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = StateStore(Path(directory), "/tmp/socket")

            def write_state(enabled: bool) -> None:
                with store.locked():
                    store.save(LinkState(enabled, {"child": "parent"}))

            threads = [
                threading.Thread(target=write_state, args=(index % 2 == 0,))
                for index in range(8)
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            loaded = store.load()
            self.assertIn(loaded.enabled, (True, False))
            self.assertEqual(loaded.links, {"child": "parent"})
