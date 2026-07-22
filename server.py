#!/usr/bin/env python3
"""sam-canvas live bridge — serves a shared Excalidraw canvas in the browser.

You draw in a real Excalidraw canvas in the browser; your scene autosaves to a shared
`.excalidraw` file. Your AI coding agent writes diagram answers by merging `ada-*` elements
into the same file (via canvas.py); the page polls and shows them within ~1s. Ownership is
split so it is race-safe: the PAGE only writes NON-`ada-` elements, the AGENT only writes
`ada-*` elements — the file is always the union of both.

Env:
  SAM_CANVAS_FILE   path to the shared canvas file (default ./canvas.excalidraw)
  SAM_CANVAS_PORT   port to serve on (default 3899)
Bind is loopback-only (127.0.0.1).
"""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE_DIR, "web")
CANVAS = os.environ.get("SAM_CANVAS_FILE", os.path.join(os.getcwd(), "canvas.excalidraw"))
PORT = int(os.environ.get("SAM_CANVAS_PORT", "3899"))

BLANK = {"type": "excalidraw", "version": 2, "source": "sam-canvas", "elements": [],
         "appState": {"viewBackgroundColor": "#ffffff", "gridSize": 20}, "files": {}}


def is_ada(el):
    return str(el.get("id", "")).startswith("ada-")


def load():
    if not os.path.exists(CANVAS):
        os.makedirs(os.path.dirname(CANVAS) or ".", exist_ok=True)
        with open(CANVAS, "w", encoding="utf-8") as f:
            json.dump(BLANK, f)
    with open(CANVAS, encoding="utf-8") as f:
        return json.load(f)


def save(data):
    with open(CANVAS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        b = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(b)

    def log_message(self, format, *args):
        pass  # quiet

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/index"):
            with open(os.path.join(ASSETS, "index.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        elif self.path.startswith("/canvas"):
            self._send(200, json.dumps(load()))
        else:
            self._send(404, "not found", "text/plain")

    def do_POST(self):
        if self.path.startswith("/canvas"):
            n = int(self.headers.get("Content-Length", "0"))
            try:
                scene = json.loads(self.rfile.read(n) or b"{}")
            except Exception:
                return self._send(400, '{"error":"bad json"}')
            page_els = scene.get("elements", [])
            page_files = scene.get("files") or {}
            disk = load()
            disk_ada = [e for e in disk.get("elements", []) if is_ada(e)]      # agent's half, preserved
            page_nonada = [e for e in page_els if not is_ada(e)]               # human's half, updated
            disk["elements"] = page_nonada + disk_ada
            # files: page images (human) as base; agent's image files from disk stay authoritative
            disk_files = disk.get("files") or {}
            ada_fids = {e.get("fileId") for e in disk_ada if e.get("type") == "image" and e.get("fileId")}
            kept_agent = {fid: disk_files[fid] for fid in ada_fids if fid in disk_files}
            disk["files"] = {**page_files, **kept_agent}
            bg = (scene.get("appState") or {}).get("viewBackgroundColor")
            if bg:
                disk.setdefault("appState", {})["viewBackgroundColor"] = bg
            save(disk)
            self._send(200, '{"ok":true}')
        else:
            self._send(404, "not found", "text/plain")


if __name__ == "__main__":
    print(f"sam-canvas canvas → http://localhost:{PORT}   (file: {CANVAS})")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
