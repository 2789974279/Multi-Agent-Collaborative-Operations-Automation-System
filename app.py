from __future__ import annotations

import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from core.orchestrator import Orchestrator
from core.repository import Repository
from core.schemas import ValidationError, parse_task_payload


BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "operations.db"
WORKFLOW_PATH = BASE_DIR / "config" / "workflows.json"


repo = Repository(DB_PATH)
orchestrator = Orchestrator(repo, WORKFLOW_PATH)


class AppHandler(BaseHTTPRequestHandler):
    server_version = "MultiAgentOps/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/health":
            self.send_json({"ok": True, "service": "multi-agent-ops"})
            return

        if path == "/api/agents":
            self.send_json({"agents": orchestrator.list_agents(), "workflows": orchestrator.workflows})
            return

        if path == "/api/tasks":
            self.send_json({"tasks": repo.list_tasks()})
            return

        if path.startswith("/api/tasks/"):
            task_id = self.extract_task_id(path)
            if task_id is None:
                self.send_error_json(404, "Task not found")
                return
            task = repo.get_task(task_id)
            if not task:
                self.send_error_json(404, "Task not found")
                return
            self.send_json({"task": task, "events": repo.list_events(task_id)})
            return

        self.serve_static(path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/tasks":
            try:
                payload = self.read_json()
                task_input = parse_task_payload(payload, orchestrator.workflows)
                task = repo.create_task(task_input)
            except ValidationError as exc:
                self.send_error_json(400, str(exc))
                return
            except json.JSONDecodeError:
                self.send_error_json(400, "Invalid JSON body")
                return
            self.send_json({"task": task}, status=201)
            return

        if path.startswith("/api/tasks/") and path.endswith("/run"):
            task_id = self.extract_task_id(path.removesuffix("/run"))
            if task_id is None or not repo.get_task(task_id):
                self.send_error_json(404, "Task not found")
                return
            result = orchestrator.run_task(task_id)
            self.send_json(result)
            return

        self.send_error_json(404, "Endpoint not found")

    def read_json(self) -> dict:
        length = int(self.headers.get("content-length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw or "{}")

    def serve_static(self, path: str) -> None:
        relative = "index.html" if path in ("", "/") else path.lstrip("/")
        target = (PUBLIC_DIR / relative).resolve()
        if not str(target).startswith(str(PUBLIC_DIR.resolve())) or not target.exists() or target.is_dir():
            self.send_error(404)
            return

        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, status: int, message: str) -> None:
        self.send_json({"error": message}, status=status)

    def extract_task_id(self, path: str) -> int | None:
        parts = [part for part in path.split("/") if part]
        if len(parts) < 3:
            return None
        try:
            return int(parts[2])
        except ValueError:
            return None

    def log_message(self, format: str, *args: object) -> None:
        if os.environ.get("APP_DEBUG") == "1":
            super().log_message(format, *args)


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    repo.initialize()
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8765"))
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"Multi-Agent Ops running at http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
