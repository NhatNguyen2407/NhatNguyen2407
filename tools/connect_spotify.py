"""One-time local PKCE setup. Run on your own computer, never in Actions."""

import base64
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import secrets
import time
import urllib.parse
import urllib.request
import webbrowser

REDIRECT = "http://127.0.0.1:8765/callback"


def connect():
    client_id = input("Spotify app Client ID: ").strip()
    if not client_id:
        raise ValueError("A Client ID is required")
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    state = secrets.token_urlsafe(32)
    result = {}

    class Callback(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # The callback query contains an authorization code.

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            valid = parsed.path == "/callback" and secrets.compare_digest(params.get("state", [""])[0].encode(), state.encode())
            if not valid:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Unexpected callback. Return to the Spotify authorization tab.")
                return
            result.update(code=params.get("code", [None])[0], denied="error" in params)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Authorization received. Return to your local terminal; you can close this tab.")

    params = {"client_id": client_id, "response_type": "code", "redirect_uri": REDIRECT,
              "scope": "user-read-currently-playing user-top-read", "state": state,
              "code_challenge_method": "S256", "code_challenge": challenge}
    with HTTPServer(("127.0.0.1", 8765), Callback) as server:
        server.timeout = 1
        print("Opening Spotify. The app's redirect URI must be " + REDIRECT)
        webbrowser.open("https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params))
        deadline = time.monotonic() + 300
        while not result and time.monotonic() < deadline:
            server.handle_request()
    if not result.get("code") or result.get("denied"):
        raise RuntimeError("Authorization was not completed. No token was saved.")
    payload = urllib.parse.urlencode({"grant_type": "authorization_code", "client_id": client_id, "code": result["code"], "redirect_uri": REDIRECT, "code_verifier": verifier}).encode()
    request = urllib.request.Request("https://accounts.spotify.com/api/token", data=payload, headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(request, timeout=30) as response:
        token = json.load(response)
    path = Path(__file__).resolve().parents[1] / ".spotify-secrets.json"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump({"SPOTIFY_CLIENT_ID": client_id, "SPOTIFY_REFRESH_TOKEN": token["refresh_token"]}, handle, indent=2)
    print("Saved .spotify-secrets.json locally. Copy its values into GitHub Actions settings as described in docs/music-setup.md.")
    print("This local file is ignored by Git. Do not upload it or paste its contents into chat.")


if __name__ == "__main__":
    try:
        connect()
    except Exception:
        print("Spotify setup did not complete. Check the app, redirect URI and authorization, then retry locally. No credentials are printed.")
        raise SystemExit(1)
