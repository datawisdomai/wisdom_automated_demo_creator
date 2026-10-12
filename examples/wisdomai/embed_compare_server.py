"""Side-by-side A/B harness for WisdomAI iframe embed routes.

`embed_test_server.py` frames one embed route at a time. This one frames
several at once so you can watch how different chat entry points behave
against the *same* impersonated user and the same browser storage — which is
what you need to answer questions like "does /embed/chat resume the user's
previous conversation while /embed/search starts a fresh one?".

    .venv/bin/python examples/embed_compare_server.py proddemo
    .venv/bin/python examples/embed_compare_server.py proddemo --email a@b.com
    .venv/bin/python examples/embed_compare_server.py proddemo \
        --paths /embed/search /embed/chat /chat/embed

Then open http://localhost:8766.

Why the panes are loaded one at a time by default
-------------------------------------------------
Every pane points at the same tenant origin, so they share one localStorage /
sessionStorage / cookie jar. If "resume the last conversation" turns out to be
client-side state rather than server-side, panes loaded simultaneously will
contaminate each other and whichever writes last wins. So each pane has its own
Load button, and "Run sequence" loads them in order with a gap. "Load all at
once" is there deliberately as the contaminating case, for contrast.

"Re-login (fresh tokens)" mints a new JWT per pane and reloads — the closest
thing to the customer's report, where a returning user gets a new session and
lands on their old chat instead of a new one.

Read-only on the API side: this fires `impersonateUser` (a Query) and nothing
else. It does NOT mutate anything. Note though that *loading a chat embed at
all* may cause the WisdomAI app itself to open a conversation — that is the
product's behaviour, not this script's.
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
<html><head><meta charset="utf-8"><title>WisdomAI embed A/B</title>
<style>
  :root { color-scheme: light dark; --line:#8883; }
  * { box-sizing:border-box; }
  body { margin:0; font:13px/1.45 ui-sans-serif,system-ui,sans-serif;
         display:flex; flex-direction:column; height:100vh; }
  header { padding:8px 12px; border-bottom:1px solid var(--line);
           display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
  header .sp { flex:1 }
  input,select,button { font:inherit; padding:4px 7px; }
  button { cursor:pointer; }
  main { flex:1; display:flex; min-height:0; }
  #panes { flex:1; display:flex; min-width:0; }
  .pane { flex:1; min-width:0; display:flex; flex-direction:column;
          border-right:1px solid var(--line); }
  .pane.hide { display:none; }
  .pane.solo { flex:1 } .pane.solo ~ .pane, body.hassolo .pane:not(.solo) { display:none; }
  .bar { padding:6px 8px; border-bottom:1px solid var(--line);
         display:flex; gap:6px; align-items:center; }
  .bar .p { flex:1; min-width:0; font-family:ui-monospace,monospace; }
  .tag { font-weight:700; font-family:ui-monospace,monospace; }
  .pane iframe { flex:1; border:0; width:100%; background:#fff; }
  .st { padding:3px 8px; font:11px/1.4 ui-monospace,monospace; opacity:.7;
        border-bottom:1px solid var(--line); white-space:nowrap; overflow:hidden;
        text-overflow:ellipsis; }
  #log { width:340px; border-left:1px solid var(--line); overflow:auto; padding:8px 10px;
         font:11px/1.5 ui-monospace,monospace; white-space:pre-wrap; }
  .t { opacity:.5 } .err { color:#d33 } .ok { color:#2a2 } .hi { color:#c60; font-weight:700 }
</style></head><body>
<header>
  <strong>__TENANT__</strong>
  <span class="t">as</span> <input id="email" value="__EMAIL__" size="22">
  <button id="seq">Run sequence</button>
  <button id="all">Load all at once</button>
  <button id="relogin" title="Mint new JWTs and reload every pane — simulates the user logging back in">Re-login (fresh tokens)</button>
  <button id="blank">Blank all</button>
  <span class="sp"></span>
  <button id="unsolo">Show all panes</button>
</header>
<main><div id="panes"></div><div id="log"></div></main>
<script>
const ORIGIN = "__ORIGIN__";
const PATHS  = __PATHS__;
const logEl  = document.getElementById('log');

function log(msg, cls) {
  const t = new Date().toISOString().slice(11, 19);
  logEl.insertAdjacentHTML('beforeend',
    `<div class="${cls||''}"><span class="t">${t}</span> ${msg}</div>`);
  logEl.scrollTop = logEl.scrollHeight;
}

async function mint() {
  const email = document.getElementById('email').value.trim();
  const r = await fetch('/api/wisdom-token?email=' + encodeURIComponent(email));
  const d = await r.json();
  if (d.error) throw new Error(d.error);
  return d;
}

// Build the panes.
const panes = PATHS.map((p, i) => {
  const tag = String.fromCharCode(65 + i);            // A, B, C…
  const el = document.createElement('div');
  el.className = 'pane';
  el.innerHTML = `
    <div class="bar">
      <span class="tag">${tag}</span>
      <input class="p" value="${p}">
      <button class="load">Load</button>
      <button class="solo" title="Show only this pane">⤢</button>
    </div>
    <div class="st">idle</div>
    <iframe allow="microphone; camera; clipboard-write"></iframe>`;
  document.getElementById('panes').appendChild(el);
  const o = {
    tag, el,
    input: el.querySelector('.p'),
    frame: el.querySelector('iframe'),
    stat:  el.querySelector('.st'),
    token: null, loads: 0,
  };
  el.querySelector('.load').onclick = () => load(o);
  el.querySelector('.solo').onclick = () => {
    const on = !o.el.classList.contains('solo');
    document.querySelectorAll('.pane').forEach(x => x.classList.remove('solo'));
    document.body.classList.toggle('hassolo', on);
    if (on) o.el.classList.add('solo');
  };
  // A cross-origin frame hides its DOM, so `load` count is the only in-page
  // signal that the app navigated itself (e.g. /embed/chat -> /embed/chat/<id>).
  o.frame.addEventListener('load', () => {
    if (!o.frame.src || o.frame.src === 'about:blank') return;
    o.loads++;
    o.stat.textContent = `${o.loads} load event(s) — ${o.path||''}`;
    log(`[${tag}] iframe load #${o.loads}`, o.loads > 1 ? 'hi' : '');
  });
  return o;
});

async function load(o, freshToken) {
  o.path = o.input.value.trim();
  try {
    if (freshToken || !o.token) o.token = (await mint()).token;
    o.loads = 0;
    o.stat.textContent = 'loading ' + o.path;
    const sep = o.path.includes('?') ? '&' : '?';
    o.frame.src = ORIGIN + o.path + sep + 'token=' + encodeURIComponent(o.token);
    log(`[${o.tag}] load ${o.path}  (token …${o.token.slice(-8)})`, 'ok');
  } catch (e) { log(`[${o.tag}] token error: ` + e.message, 'err'); }
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

document.getElementById('seq').onclick = async () => {
  log('— sequence: one pane at a time, 12s apart —', 'hi');
  for (const o of panes) { await load(o); await sleep(12000); }
};
document.getElementById('all').onclick = () => {
  log('— loading all panes simultaneously (shared storage WILL contaminate) —', 'hi');
  panes.forEach(o => load(o));
};
document.getElementById('relogin').onclick = async () => {
  log('— re-login: fresh JWT per pane, sequential reload —', 'hi');
  for (const o of panes) { await load(o, true); await sleep(12000); }
};
document.getElementById('blank').onclick = () => {
  panes.forEach(o => { o.frame.src = 'about:blank'; o.loads = 0; o.stat.textContent = 'blank'; });
  log('all panes blanked');
};
document.getElementById('unsolo').onclick = () => {
  document.querySelectorAll('.pane').forEach(x => x.classList.remove('solo'));
  document.body.classList.remove('hassolo');
};

// Token-refresh handshake. WisdomAI posts with targetOrigin '*', so checking
// event.origin is the host's job. An *immediate* REQUEST_JWT_TOKEN at boot
// means the token was rejected, not that it expired.
window.addEventListener('message', async (event) => {
  if (event.origin !== ORIGIN) return;
  const o = panes.find(x => x.frame.contentWindow === event.source);
  const who = o ? `[${o.tag}]` : '[?]';
  log(`${who} ← ` + JSON.stringify(event.data).slice(0, 200));
  if (event.data?.type !== 'REQUEST_JWT_TOKEN' || !o) return;
  try {
    event.source.postMessage({ type: 'JWT_TOKEN_RESPONSE', token: o.token }, ORIGIN);
    log(`${who} → JWT_TOKEN_RESPONSE (…${o.token.slice(-8)})`, 'ok');
  } catch (e) { log(`${who} refresh failed: ` + e.message, 'err'); }
});

log('ready — ' + PATHS.length + ' pane(s). "Run sequence" loads them one at a time.');
</script></body></html>
"""


def build_handler(client: Client, email: str, paths: list[str]):
    origin = f"https://{client.host}"

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code, body: bytes, ctype: str) -> None:
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
                    .replace("__PATHS__", json.dumps(paths))
                )
                self._send(200, html.encode(), "text/html; charset=utf-8")
            elif route == "/api/wisdom-token":
                who = parse_qs(urlparse(self.path).query).get("email", [email])[0]
                try:
                    token = client.impersonate_user(who)
                except (WisdomAIError, Exception) as e:
                    self._json({"error": f"{type(e).__name__}: {e}"}, 500)
                    return
                print(f"  minted JWT for {who} (…{token[-8:]})", flush=True)
                self._json({"token": token, "email": who})
            else:
                self._send(404, b"not found", "text/plain")

        def log_message(self, fmt, *args):
            return

    return Handler


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("deployment")
    ap.add_argument("--email", help="user to impersonate (default: the key's own user)")
    ap.add_argument(
        "--paths",
        nargs="+",
        default=["/embed/search", "/embed/chat", "/chat/embed"],
        help="embed paths to frame side by side",
    )
    ap.add_argument("--port", type=int, default=8766)
    args = ap.parse_args()

    client = Client.for_deployment(args.deployment)
    email = args.email or client.current_user()["email"]

    handler = build_handler(client, email, args.paths)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"tenant     https://{client.host}")
    print(f"as         {email}")
    for i, p in enumerate(args.paths):
        print(f"  pane {chr(65+i)}    {p}")
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
