"""
Minimal HTTP API for the Docker Compose assignment.

Implemented using only the Python standard library. The server listens on
0.0.0.0:5000 and exposes four fixed endpoints:

    GET /health              -> 200 "OK"
    GET /square/<n>          -> 200 "<n*n>"        (e.g. /square/7  -> 49)
    GET /reverse/<text>      -> 200 "<reversed>"   (e.g. /reverse/docker-compose -> esopmoc-rekcod)
    GET /sum?x=<a>&y=<b>     -> 200 "<a+b>"        (e.g. /sum?x=13&y=29 -> 42)
"""

import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "5000"))


class APIHandler(BaseHTTPRequestHandler):
    def _send_text(self, status, body):
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        parts = [p for p in path.split("/") if p != ""]

        if path == "/health":
            self._send_text(200, "OK")
            return

        if len(parts) == 2 and parts[0] == "square":
            try:
                n = int(parts[1])
            except ValueError:
                self._send_text(400, "Bad Request")
                return
            self._send_text(200, str(n * n))
            return

        if len(parts) == 2 and parts[0] == "reverse":
            self._send_text(200, parts[1][::-1])
            return

        if parts[:1] == ["sum"] or path == "/sum":
            query = parse_qs(parsed.query)
            try:
                x = int(query["x"][0])
                y = int(query["y"][0])
            except (KeyError, IndexError, ValueError):
                self._send_text(400, "Bad Request")
                return
            self._send_text(200, str(x + y))
            return

        self._send_text(404, "Not Found")

    # Keep the container logs quiet/clean.
    def log_message(self, fmt, *args):
        return


def main():
    server = ThreadingHTTPServer((HOST, PORT), APIHandler)
    print(f"API listening on {HOST}:{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
