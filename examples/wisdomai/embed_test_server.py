"""Local harness for testing WisdomAI iframe embeds.

Serves a single page that embeds a WisdomAI `/embed/...` URL in an iframe, and
a `/api/wisdom-token` endpoint that mints the session JWT **server-side** via
`impersonateUser` — mirroring the split the docs require, where the permanent
access key never reaches the browser.

    .venv/bin/python examples/embed_test_server.py proddemo
    .venv/bin/python examples/embed_test_server.py proddemo --email someone@x.com
    .venv/bin/python examples/embed_test_server.py proddemo --path /embed/search

Then open http://localhost:8765. The page has a path box so you can try embed
routes without restarting, an app picker that resolves an app id to its backing
dashboard, and a live log of the `REQUEST_JWT_TOKEN` / `JWT_TOKEN_RESPONSE`
postMessage handshake described in the Session Management docs.

Embed routes (verified against the live tenant, not all of them documented):

    /embed/search                     full app: search + dashboards + chat
    /embed/dashboards                 dashboard list
    /embed/dashboards/<dashboardId>   one dashboard
    /embed/chat/<conversationId>      one conversation
    /apps/embed/<APP_ID>              a Live app  (NOT /embed/apps/<id> — 404s)

Read-only: this fires `impersonateUser` (a Query) and `apps` (a Query). It
creates no users and mutates nothing.
"""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from wisdomai import Client
from wisdomai.errors import WisdomAIError

PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>WisdomAI embed test</title>
<style>
  :root { color-scheme: light dark; }
  body { margin:0; font:14px/1.45 ui-sans-serif,system-ui,sans-serif; display:flex; flex-direction:column; height:100vh; }
  header { padding:10px 14px; border-bottom:1px solid #8883; display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
  input,select,button { font:inherit; padding:5px 8px; }
  #path { flex:1; min-width:320px; font-family:ui-monospace,monospace; }
  main { flex:1; display:flex; min-height:0; }
  iframe { flex:1; border:0; }
  #log { width:380px; border-left:1px solid #8883; overflow:auto; padding:8px 10px;
         font:12px/1.5 ui-monospace,monospace; white-space:pre-wrap; }
  .t { opacity:.55 }
  .err { color:#d33 }
  .ok { color:#2a2 }
</style></head><body>
<header>
  <strong>__TENANT__</strong>
  <span class="t">as __EMAIL__</span>
  <select id="apps"><option value="">— pick an app —</option></select>
  <input id="path" value="__PATH__">
  <button id="go">Load</button>
  <button id="refresh">Force token refresh</button>
</header>
<main>
  <iframe id="f" allow="microphone; camera; clipboard-write"></iframe>
  <div id="log"></div>
</main>
<script>
const ORIGIN = "__ORIGIN__";
const f = document.getElementById('f');
const logEl = document.getElementById('log');

function log(msg, cls) {
  const t = new Date().toISOString().slice(11, 19);
  logEl.insertAdjacentHTML('beforeend',
    `<div class="${cls||''}"><span class="t">${t}</span> ${msg}</div>`);
  logEl.scrollTop = logEl.scrollHeight;
}

async function getToken() {
  const r = await fetch('/api/wisdom-token');
  const d = await r.json();
  if (d.error) throw new Error(d.error);
  return d;
}

// Decode the exp claim so we can show when the postMessage refresh should fire.
function expOf(jwt) {
  try { return JSON.parse(atob(jwt.split('.')[1].replace(/-/g,'+').replace(/_/g,'/'))).exp; }
  catch (e) { return null; }
}

// A real host caches the token and reuses it until it is near expiry, rather
// than minting a fresh one per request. `?respond=` switches that behaviour so
// we can tell a broken handshake apart from a broken embed:
//   same (default) — reply with the very token already in the iframe URL
//   fresh          — mint a new token for every REQUEST_JWT_TOKEN
//   none           — never reply, and see whether the URL token alone suffices
const RESPOND = new URLSearchParams(location.search).get('respond') || 'same';
let currentToken = null;

async function load() {
  const path = document.getElementById('path').value.trim();
  try {
    const d = await getToken();
    currentToken = d.token;
    const exp = expOf(d.token);
    log(`token minted for ${d.email} (…${d.token.slice(-8)})`
        + (exp ? `, expires ${new Date(exp*1000).toISOString().slice(11,19)}Z` : ''), 'ok');
    const url = ORIGIN + path + (path.includes('?') ? '&' : '?') + 'token=' + encodeURIComponent(d.token);
    log(`loading ${path}   [respond=${RESPOND}]`);
    f.src = url;
    // Did anything paint? A cross-origin frame hides its DOM, but a frame that
    // never finishes still reports zero scroll height changes; log a heartbeat
    // so a slow-but-alive load is distinguishable from a hung one.
    let n = 0;
    clearInterval(window.__hb);
    window.__hb = setInterval(() => {
      n += 15;
      log(`still framed after ${n}s`);
      if (n >= 90) clearInterval(window.__hb);
    }, 15000);
  } catch (e) { log('token error: ' + e.message, 'err'); }
}

f.addEventListener('load', () => log('iframe fired load for ' + new URL(f.src).pathname));

// The refresh handshake from the Session Management docs. WisdomAI posts
// REQUEST_JWT_TOKEN ~10s before expiry with targetOrigin '*', so validating
// event.origin here is on us.
window.addEventListener('message', async (event) => {
  if (event.origin !== ORIGIN) return;
  log('← postMessage ' + JSON.stringify(event.data).slice(0, 300));
  if (event.source !== f.contentWindow) return;
  if (event.data?.type !== 'REQUEST_JWT_TOKEN') return;
  if (RESPOND === 'none') { log('(not replying — respond=none)'); return; }
  try {
    let token = currentToken;
    if (RESPOND === 'fresh' || !token) token = (await getToken()).token;
    f.contentWindow.postMessage({ type: 'JWT_TOKEN_RESPONSE', token }, ORIGIN);
    log('→ JWT_TOKEN_RESPONSE sent (…' + token.slice(-8) + ')'
        + (token === currentToken ? ' [same as URL token]' : ' [freshly minted]'), 'ok');
  } catch (e) { log('refresh failed: ' + e.message, 'err'); }
});

document.getElementById('go').onclick = load;
document.getElementById('refresh').onclick = async () => {
  // Simulate what WisdomAI asks for, without waiting ~1h for real expiry.
  try {
    const d = await getToken();
    f.contentWindow.postMessage({ type: 'JWT_TOKEN_RESPONSE', token: d.token }, ORIGIN);
    log('→ JWT_TOKEN_RESPONSE sent unprompted (…' + d.token.slice(-8) + ')', 'ok');
  } catch (e) { log('refresh failed: ' + e.message, 'err'); }
};

fetch('/api/apps').then(r => r.json()).then(d => {
  if (d.error) { log('app list error: ' + d.error, 'err'); return; }
  const sel = document.getElementById('apps');
  for (const a of d.apps) {
    const o = document.createElement('option');
    o.value = a.dashboardId;
    o.dataset.appId = a.id;
    o.textContent = (a.name || '(unnamed)') + '  — ' + a.owner
      + (a.workspace ? '  [' + a.workspace + ']' : '');
    sel.appendChild(o);
  }
  log(d.apps.length + ' app(s) loaded into the picker');
  // Live apps embed at /apps/embed/<APP_ID> — NOT /embed/apps/<id> (that 404s).
  // The backing dashboard (/embed/dashboards/<dashboardId>) is the fallback for
  // tenants whose build predates the live-app embed route.
  sel.onchange = () => {
    if (!sel.value) return;
    const appId = sel.selectedOptions[0].dataset.appId;
    document.getElementById('path').value = '/apps/embed/' + appId;
    log('app ' + appId + ' (fallback dashboard: /embed/dashboards/' + sel.value + ')');
  };
});

load();
</script></body></html>
"""


def build_handler(client: Client, email: str, path: str, workspace_id: str | None):
    origin = f"https://{client.host}"

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: str | int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _json(self, obj: dict, code: int = 200) -> None:
            self._send(code, json.dumps(obj).encode(), "application/json")

        def do_GET(self) -> None:  # noqa: N802
            route = urlparse(self.path).path
            if route == "/":
                html = (
                    PAGE.replace("__ORIGIN__", origin)
                    .replace("__TENANT__", client.host)
                    .replace("__EMAIL__", email)
                    .replace("__PATH__", path)
                )
                self._send(200, html.encode(), "text/html; charset=utf-8")
            elif route == "/api/wisdom-token":
                who = parse_qs(urlparse(self.path).query).get("email", [email])[0]
                try:
                    token = client.impersonate_user(who)
                except (WisdomAIError, Exception) as e:  # surface to the page
                    self._json({"error": f"{type(e).__name__}: {e}"}, 500)
                    return
                print(f"  minted JWT for {who} (…{token[-8:]})", flush=True)
                self._json({"token": token, "email": who})
            elif route == "/api/apps":
                # A tenant can have several workspaces (staging has two), in
                # which case `default_workspace_id()` refuses to guess — so
                # aggregate across all of them unless one was named explicitly.
                try:
                    if workspace_id:
                        targets = [{"id": workspace_id, "name": workspace_id}]
                    else:
                        targets = client.workspaces()
                    apps = []
                    for ws in targets:
                        for a in client.list_apps(ws["id"]):
                            apps.append(
                                {
                                    "id": a["id"],
                                    "name": a["name"],
                                    "dashboardId": a["dashboardId"],
                                    "owner": (a.get("owner") or {}).get("email", ""),
                                    "workspace": ws.get("name", ""),
                                }
                            )
                except Exception as e:
                    self._json({"error": f"{type(e).__name__}: {e}"}, 500)
                    return
                self._json({"apps": apps})
            else:
                self._send(404, b"not found", "text/plain")

        def log_message(self, fmt, *args):  # quieter than the default
            return

    return Handler


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("deployment")
    ap.add_argument("--email", help="user to impersonate (default: the key's own user)")
    ap.add_argument(
        "--path",
        default="/embed/search",
        help="embed path to load first, e.g. /embed/search, "
        "/embed/dashboards/<id>, /apps/embed/<APP_ID>",
    )
    ap.add_argument("--workspace-id", help="workspace for the app picker")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()

    client = Client.for_deployment(args.deployment)
    email = args.email or client.current_user()["email"]

    handler = build_handler(client, email, args.path, args.workspace_id)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"tenant     https://{client.host}")
    print(f"embedding  {args.path}  as  {email}")
    print(f"open       http://localhost:{args.port}")
    print("Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
