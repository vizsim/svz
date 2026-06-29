"""Headless-Screenshot via CDP, das ECHT auf geladene Tiles wartet (window.map).

usage: cdp_shot.py URL OUT.png WIDTH HEIGHT
Braucht websocket-client:  uv run --with websocket-client python cdp_shot.py ...
"""
import base64
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from websocket import create_connection

URL, OUT, W, H = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
PORT = 9333
CHROME = str(next(Path.home().glob(".cache/ms-playwright/chromium-*/chrome-linux64/chrome")))

proc = subprocess.Popen(
    [CHROME, "--headless=new", "--no-sandbox", "--disable-gpu-sandbox",
     "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
     "--hide-scrollbars", "--force-device-scale-factor=1",
     f"--window-size={W},{H}", f"--remote-debugging-port={PORT}",
     "--remote-allow-origins=*",
     "--user-data-dir=/tmp/cdp_profile", "about:blank"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)


def cmd(ws, _id, method, params=None):
    ws.send(json.dumps({"id": _id, "method": method, "params": params or {}}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == _id:
            return msg.get("result", {})


try:
    # auf DevTools warten, Page-Target holen
    for _ in range(60):
        try:
            targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json"))
            page = next((t for t in targets if t["type"] == "page"), None)
            if page:
                break
        except Exception:
            pass
        time.sleep(0.3)
    ws = create_connection(page["webSocketDebuggerUrl"], timeout=60, max_size=64 * 2**20)
    cmd(ws, 1, "Page.enable")
    cmd(ws, 2, "Runtime.enable")
    cmd(ws, 3, "Page.navigate", {"url": URL})

    expr = ("!!(window.map && window.map.isStyleLoaded && window.map.isStyleLoaded()"
            " && window.map.areTilesLoaded && window.map.areTilesLoaded())")
    ready = False
    for _ in range(90):  # bis ~45s
        r = cmd(ws, 100, "Runtime.evaluate", {"expression": expr, "returnByValue": True})
        if r.get("result", {}).get("value") is True:
            ready = True
            break
        time.sleep(0.5)
    time.sleep(1.5)  # kurz nachsetzen lassen
    shot = cmd(ws, 200, "Page.captureScreenshot", {"format": "png"})
    Path(OUT).write_bytes(base64.b64decode(shot["data"]))
    print(f"ready={ready} -> {OUT}")
finally:
    proc.terminate()
