"""Play a Scratch .sb3 file in the browser.

    kitty run game.sb3
    kitty run game.sb3 --verbose

Build a Kitty project into an .sb3 first, with `kitty build`. The player page
runs Scratch's own engine, which is bundled in vendor/, so the browser is the
only thing it needs: no Node.js, no git, and no internet connection. The file
is served from this computer only, at 127.0.0.1.
"""

from __future__ import annotations

import argparse
import io
import json
import mimetypes
import secrets
import sys
import threading
import time
import webbrowser
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
VENDOR = HERE / "vendor"
PLAYER = HERE / "player.html"
_LOG_LIMIT = 64 * 1024


class Project:
    """The .sb3 being played. load() reads it again; the page plays whichever version is newest."""

    def __init__(self, path, watch=False, verbose=False):
        self.path = Path(path)
        self.title = self.path.name
        self.watch = watch
        self.verbose = verbose
        self.token = secrets.token_urlsafe(16)
        self.lock = threading.Lock()
        self.version = 0
        self.data = None
        self.error = None
        self.summary = []
        self.stamp = None

    def load(self):
        """Read the .sb3. Returns True when it is a Scratch project."""
        self.stamp = self._stamp()
        try:
            data = self.path.read_bytes()
            summary = describe(data)
        except FileNotFoundError:
            error = f"not found: {self.path}"
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            error = f"{self.path.name} is not a Scratch .sb3 file ({exc})"
        else:
            with self.lock:
                self.data = data
                self.error = None
                self.summary = summary
                self.version += 1
            return True
        with self.lock:
            self.error = error
        return False

    def changed(self):
        return self._stamp() != self.stamp

    def _stamp(self):
        try:
            stat = self.path.stat()
        except OSError:
            return None
        return stat.st_mtime_ns, stat.st_size

    def status(self):
        with self.lock:
            return {
                "title": self.title,
                "version": self.version,
                "ready": self.data is not None,
                "error": self.error,
                "watch": self.watch,
                "verbose": self.verbose,
                "token": self.token,
            }


def describe(data):
    """Lines that sum up an .sb3: each sprite's costumes, sounds, scripts, and blocks."""
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        try:
            project = json.loads(archive.read("project.json").decode("utf-8"))
        except KeyError as exc:
            raise ValueError("it has no project.json") from exc
    lines = []
    for target in project.get("targets") or []:
        blocks = [block for block in (target.get("blocks") or {}).values() if isinstance(block, dict)]
        scripts = sum(1 for block in blocks if block.get("topLevel"))
        name = "Stage" if target.get("isStage") else f"sprite {target.get('name')}"
        lines.append(
            f"{name}: {len(target.get('costumes') or [])} costumes, {len(target.get('sounds') or [])} sounds, "
            f"{scripts} scripts, {len(blocks)} blocks, {len(target.get('variables') or {})} variables, "
            f"{len(target.get('lists') or {})} lists"
        )
    extensions = project.get("extensions") or []
    if extensions:
        lines.append("extensions: " + ", ".join(str(item) for item in extensions))
    shown = [monitor for monitor in project.get("monitors") or [] if isinstance(monitor, dict) and monitor.get("visible")]
    if shown:
        lines.append(f"monitors shown: {len(shown)}")
    return lines


def _size(count):
    if count < 1024:
        return f"{count} bytes"
    if count < 1024 * 1024:
        return f"{count / 1024:.1f} KB"
    return f"{count / 1024 / 1024:.1f} MB"


_PRINT = threading.Lock()


def _say(text):
    # The server answers requests on several threads; one write per line keeps lines whole.
    with _PRINT:
        sys.stdout.write(text + "\n")
        sys.stdout.flush()


def _handler(project):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path in ("/", "/index.html"):
                self._send(PLAYER.read_bytes(), "text/html; charset=utf-8")
            elif path == "/status":
                self._send(json.dumps(project.status()).encode("utf-8"), "application/json")
            elif path == "/project.sb3":
                with project.lock:
                    data = project.data
                if data is None:
                    self._error(404)
                else:
                    self._send(data, "application/octet-stream")
            elif path.startswith("/vendor/"):
                self._send_vendor(path[len("/vendor/"):])
            elif path.startswith("/chunks/"):
                # scratch-storage asks for its worker next to the page, not next to itself.
                self._send_vendor(path[1:])
            elif path == "/favicon.ico":
                self.send_response(204)
                self.send_header("Content-Length", "0")
                self.end_headers()
            else:
                self._error(404)

        def do_POST(self):
            # The page sends what happens in the project here, for --verbose.
            path, _, query = self.path.partition("?")
            if path != "/log" or not project.verbose or query != f"token={project.token}":
                self._error(403)
                return
            size = int(self.headers.get("Content-Length") or 0)
            if size > _LOG_LIMIT:
                self._error(413)
                return
            try:
                lines = json.loads(self.rfile.read(size).decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                self._error(400)
                return
            for line in lines if isinstance(lines, list) else []:
                _say(f"[player] {str(line)[:500]}")
            self.send_response(204)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def _send_vendor(self, relative):
            target = (VENDOR / relative).resolve()
            if not target.is_relative_to(VENDOR) or not target.is_file():
                self._error(404)
                return
            kind = "text/javascript; charset=utf-8" if target.suffix == ".js" else (
                mimetypes.guess_type(target.name)[0] or "application/octet-stream")
            self._send(target.read_bytes(), kind, cache=True)

        def _send(self, data, kind, cache=False):
            self.send_response(200)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "max-age=3600" if cache else "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)
            self._note(200, len(data))

        def _error(self, code):
            self.send_error(code)
            self._note(code, 0)

        def _note(self, code, size):
            if project.verbose and not self.path.startswith("/status"):
                _say(f"[server] {self.command} {self.path.split('?', 1)[0]} {code} {_size(size)}")

        def log_message(self, format, *args):
            pass

    return Handler


def serve(project, port=0):
    """Start serving project on 127.0.0.1 in a background thread. Returns the server."""
    server = ThreadingHTTPServer(("127.0.0.1", port), _handler(project))
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def main(argv=None):
    parser = argparse.ArgumentParser(prog="kitty run", description="Play a Scratch .sb3 file in your browser")
    parser.add_argument("source", help="the .sb3 file to play")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="print what the project and the player do while it plays")
    parser.add_argument("--watch", action="store_true", help="reload the page's project when the .sb3 file changes")
    parser.add_argument("--port", type=int, default=0, help="port on 127.0.0.1 (default: any free port)")
    parser.add_argument("--no-browser", action="store_true", help="print the address without opening a browser")
    args = parser.parse_args(argv)

    source = Path(args.source)
    if source.suffix.lower() != ".sb3":
        hint = f" Build it first: kitty build {args.source}" if source.suffix.lower() == ".py" or source.is_dir() else ""
        print(f"error: kitty run plays an .sb3 file.{hint}", file=sys.stderr)
        return 1
    project = Project(source, watch=args.watch, verbose=args.verbose)
    if not project.load():
        print(f"error: {project.error}", file=sys.stderr)
        return 1
    if args.verbose:
        _say(f"{project.title}: {_size(len(project.data))}")
        for line in project.summary:
            _say(f"  {line}")
    try:
        server = serve(project, args.port)
    except OSError as exc:
        print(f"error: could not use port {args.port}: {exc}", file=sys.stderr)
        return 1
    url = f"http://127.0.0.1:{server.server_port}/"
    _say(f"Playing {project.title} at {url}")
    _say(("Watching it for changes. " if args.watch else "") + "Press Ctrl+C to stop.")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        while True:
            time.sleep(0.5)
            if args.watch and project.changed():
                if project.load():
                    _say(f"Reloaded {project.title} at {time.strftime('%H:%M:%S')}")
                else:
                    _say(f"error: {project.error}")
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()
    return 0
