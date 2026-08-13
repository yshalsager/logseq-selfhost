import importlib.util
import os
import pathlib
import sqlite3
import tempfile
import unittest

MODULE = pathlib.Path(__file__).parents[1] / "server.py"
SPEC = importlib.util.spec_from_file_location("dashboard_server", MODULE)
server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(server)


class DashboardTest(unittest.TestCase):
    def test_collect_returns_redacted_aggregates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            graph_id = "graph-1"
            (root / "graphs" / graph_id).mkdir(parents=True)
            (root / "assets" / graph_id).mkdir(parents=True)
            index = sqlite3.connect(root / "index.sqlite")
            index.executescript("""
                create table users(id text, email text);
                create table graphs(graph_id text, graph_name text, schema_version text, graph_e2ee int,
                  graph_ready_for_use int, created_at int, updated_at int);
                create table daily_active_entities(day_utc text, entity_type text, entity_id text);
                insert into users values ('private-user', 'private@example.com');
                insert into graphs values ('graph-1', 'Work', '65', 1, 1, 1000, 2000);
            """)
            index.commit(); index.close()
            graph = sqlite3.connect(root / "graphs" / graph_id / "db.sqlite")
            graph.executescript("""
                create table tx_log(t int, tx text, created_at int);
                create table sync_meta(key text, value text);
                create table kvs(addr int, content text);
                insert into tx_log values (1, 'PRIVATE NOTE', 3000);
                insert into sync_meta values ('checksum', '1234567890abcdef');
                insert into kvs values (1, 'TOP SECRET');
            """)
            graph.commit(); graph.close()
            (root / "assets" / graph_id / "asset.bin").write_bytes(b"SECRET ASSET")
            original = server.DATA_DIR
            try:
                server.DATA_DIR = root
                result = server.collect()
            finally:
                server.DATA_DIR = original
            text = str(result)
            self.assertEqual(result["userCount"], 1)
            self.assertEqual(result["graphs"][0]["transactionCount"], 1)
            self.assertEqual(result["graphs"][0]["checksumSummary"], "1234...cdef")
            for secret in ("private@example.com", "private-user", "PRIVATE NOTE", "TOP SECRET", "SECRET ASSET"):
                self.assertNotIn(secret, text)


if __name__ == "__main__":
    unittest.main()
