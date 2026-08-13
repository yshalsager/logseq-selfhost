#!/usr/bin/env python3
"""Read-only dashboard sidecar for the Logseq DB Sync Node Adapter."""

from __future__ import annotations

import base64
import datetime as dt
import hmac
import json
import mimetypes
import os
import pathlib
import sqlite3
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

DATA_DIR = pathlib.Path(os.getenv("DB_SYNC_DATA_DIR", "/data"))
STATIC_DIR = pathlib.Path(__file__).with_name("static")
HOST = os.getenv("DASHBOARD_HOST", "0.0.0.0")
PORT = int(os.getenv("DASHBOARD_PORT", "8080"))
BASE_PATH = "/" + os.getenv("DASHBOARD_BASE_PATH", "/dashboard").strip("/")
USERNAME = os.getenv("DASHBOARD_USERNAME", "")
PASSWORD = os.getenv("DASHBOARD_PASSWORD", "")


def validate_config() -> None:
    if bool(USERNAME) != bool(PASSWORD):
        raise SystemExit("DASHBOARD_USERNAME and DASHBOARD_PASSWORD must be set together")
    if not (1 <= PORT <= 65535):
        raise SystemExit("DASHBOARD_PORT must be between 1 and 65535")
    if not (DATA_DIR / "index.sqlite").is_file():
        raise SystemExit(f"missing Node Adapter index database: {DATA_DIR / 'index.sqlite'}")


def connect_ro(path: pathlib.Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=2)


def iso_time(timestamp: float | int | None, milliseconds: bool = False) -> str | None:
    if not timestamp:
        return None
    value = float(timestamp) / 1000 if milliseconds else float(timestamp)
    return dt.datetime.fromtimestamp(value, dt.timezone.utc).isoformat()


def table_exists(db: sqlite3.Connection, name: str) -> bool:
    return db.execute(
        "select 1 from sqlite_master where type = 'table' and name = ?", (name,)
    ).fetchone() is not None


def find_graph_db(graph_id: str) -> pathlib.Path | None:
    root = DATA_DIR / "graphs"
    direct = root / graph_id / "db.sqlite"
    if direct.is_file():
        return direct
    matches = [path for path in root.rglob("*.sqlite") if graph_id in str(path)] if root.is_dir() else []
    return min(matches, key=lambda path: len(str(path))) if matches else None


def checksum_summary(value: str | None) -> str | None:
    if not value:
        return None
    return f"{value[:4]}...{value[-4:]}" if len(value) > 10 else "present"


def graph_storage(path: pathlib.Path | None) -> dict[str, object]:
    result: dict[str, object] = {
        "dbSizeBytes": 0,
        "transactionCount": 0,
        "latestT": 0,
        "lastSyncAt": None,
        "checksumSummary": None,
    }
    if path is None:
        return result
    stat = path.stat()
    result["dbSizeBytes"] = stat.st_size
    result["lastSyncAt"] = iso_time(stat.st_mtime)
    with connect_ro(path) as db:
        if table_exists(db, "tx_log"):
            count, latest_t, created_at = db.execute(
                "select count(*), coalesce(max(t), 0), max(created_at) from tx_log"
            ).fetchone()
            result["transactionCount"] = int(count)
            result["latestT"] = int(latest_t)
            if created_at:
                result["lastSyncAt"] = iso_time(created_at, milliseconds=True)
        if table_exists(db, "sync_meta"):
            checksum = db.execute("select value from sync_meta where key = 'checksum'").fetchone()
            result["checksumSummary"] = checksum_summary(checksum[0] if checksum else None)
    return result


def asset_storage(graph_id: str) -> dict[str, object]:
    root = DATA_DIR / "assets" / graph_id
    files = [
        path for path in root.rglob("*")
        if path.is_file() and not path.name.endswith(".meta.json")
    ] if root.is_dir() else []
    return {
        "count": len(files),
        "sizeBytes": sum(path.stat().st_size for path in files),
        "lastUpdatedAt": iso_time(max((path.stat().st_mtime for path in files), default=0)),
    }


def collect() -> dict[str, object]:
    with connect_ro(DATA_DIR / "index.sqlite") as db:
        users = int(db.execute("select count(*) from users").fetchone()[0])
        rows = db.execute(
            "select graph_id, graph_name, schema_version, graph_e2ee, graph_ready_for_use, "
            "created_at, updated_at from graphs order by updated_at desc"
        ).fetchall()
        activity: dict[str, int] = {}
        if table_exists(db, "daily_active_entities"):
            activity = {
                f"{day}_{kind}": int(count)
                for day, kind, count in db.execute(
                    "select day_utc, entity_type, count(*) from daily_active_entities "
                    "where day_utc >= date('now', '-6 day') group by day_utc, entity_type"
                )
            }
    graphs = []
    for graph_id, name, schema, e2ee, ready, created_at, updated_at in rows:
        graphs.append({
            "id": graph_id,
            "name": name,
            "schemaVersion": schema,
            "e2ee": bool(e2ee),
            "ready": bool(ready),
            "createdAt": iso_time(created_at, milliseconds=True),
            "updatedAt": iso_time(updated_at, milliseconds=True),
            **graph_storage(find_graph_db(graph_id)),
            "assets": asset_storage(graph_id),
        })
    return {
        "schemaVersion": 1,
        "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "userCount": users,
        "graphCount": len(graphs),
        "dailyActivity": activity,
        "storageBytes": sum(
            path.stat().st_size for path in DATA_DIR.rglob("*") if path.is_file()
        ),
        "graphs": graphs,
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "LogseqSyncDashboard/1"

    def authenticated(self) -> bool:
        if not USERNAME:
            return True
        header = self.headers.get("Authorization", "")
        try:
            scheme, encoded = header.split(" ", 1)
            supplied = base64.b64decode(encoded, validate=True).decode("utf-8")
            username, password = supplied.split(":", 1)
        except (ValueError, UnicodeError):
            return False
        return scheme.lower() == "basic" and hmac.compare_digest(username, USERNAME) and hmac.compare_digest(password, PASSWORD)

    def send_security_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; connect-src 'self'; img-src 'self'; script-src 'self'; style-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")

    def send_body(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_security_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_HEAD(self) -> None:
        self.do_GET()

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/health":
            self.send_body(HTTPStatus.OK, b'{"ok":true}\n', "application/json")
            return
        if path == BASE_PATH:
            self.send_response(HTTPStatus.PERMANENT_REDIRECT)
            self.send_header("Location", BASE_PATH + "/")
            self.end_headers()
            return
        if not path.startswith(BASE_PATH + "/"):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not self.authenticated():
            self.send_response(HTTPStatus.UNAUTHORIZED)
            self.send_security_headers()
            self.send_header("WWW-Authenticate", 'Basic realm="Logseq Sync Dashboard"')
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        relative = path[len(BASE_PATH):]
        if relative == "/api/status":
            try:
                body = json.dumps(collect(), ensure_ascii=False, separators=(",", ":")).encode()
                self.send_body(HTTPStatus.OK, body, "application/json; charset=utf-8")
            except (OSError, sqlite3.Error):
                self.send_body(HTTPStatus.SERVICE_UNAVAILABLE, b'{"error":"status unavailable"}\n', "application/json")
            return
        relative = "/index.html" if relative == "/" else relative
        target = (STATIC_DIR / relative.lstrip("/")).resolve()
        if STATIC_DIR.resolve() not in target.parents or not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in {"application/javascript", "application/json"}:
            content_type += "; charset=utf-8"
        self.send_body(HTTPStatus.OK, target.read_bytes(), content_type)

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.address_string()} - {fmt % args}")


if __name__ == "__main__":
    validate_config()
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
