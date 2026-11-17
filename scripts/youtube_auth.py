#!/usr/bin/env python3
"""Obtiene UNA VEZ el refresh token de YouTube (flujo OAuth para app de escritorio, con PKCE).

Uso (en un computador con navegador):
    YT_CLIENT_ID=... YT_CLIENT_SECRET=... python3 scripts/youtube_auth.py

Abre la URL que imprime, acepta los permisos con la cuenta del canal y copia el
refresh token que aparece al final. Guardalo como GitHub Secret `YT_REFRESH_TOKEN`.
NUNCA lo subas al repositorio. Alternativa sin Python: ver docs/youtube-setup.md (OAuth Playground).
"""
import base64
import hashlib
import json
import os
import secrets
import sys
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.force-ssl"]
PORT = 8765


def main() -> int:
    try:
        client_id, client_secret = os.environ["YT_CLIENT_ID"], os.environ["YT_CLIENT_SECRET"]
    except KeyError as e:
        print(f"Falta la variable {e}", file=sys.stderr)
        return 2
    redirect = f"http://127.0.0.1:{PORT}"
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": client_id, "redirect_uri": redirect, "response_type": "code",
        "scope": " ".join(SCOPES), "access_type": "offline", "prompt": "consent",
        "code_challenge": challenge, "code_challenge_method": "S256", "state": state})
    got = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            got.update({k: v[0] for k, v in q.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("Listo, puedes cerrar esta pestana y volver a la terminal.".encode())

        def log_message(self, *a):
            pass

    print("Abre esta URL en el navegador y acepta los permisos:\n\n" + url + "\n")
    HTTPServer(("127.0.0.1", PORT), Handler).handle_request()
    if got.get("state") != state or "code" not in got:
        print("Autorizacion fallida:", got, file=sys.stderr)
        return 1
    data = urllib.parse.urlencode({
        "code": got["code"], "client_id": client_id, "client_secret": client_secret,
        "redirect_uri": redirect, "grant_type": "authorization_code", "code_verifier": verifier}).encode()
    with urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=data)) as r:
        tok = json.loads(r.read())
    if "refresh_token" not in tok:
        print("Google no devolvio refresh_token. Revoca el acceso previo en "
              "https://myaccount.google.com/permissions y reintenta.", file=sys.stderr)
        return 1
    print("YT_REFRESH_TOKEN =", tok["refresh_token"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
