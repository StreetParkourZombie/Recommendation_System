# -*- coding: utf-8 -*-
"""Chup screenshot dashboard Streamlit qua CDP (Chromium DevTools Protocol).

Streamlit render qua websocket -> `chrome --screenshot` chi duoc trang rong.
Cach nay: mo tab qua CDP, wait DOM co noi dung (Plotly + text), roi
Page.captureScreenshot voi captureBeyondViewport de chup ca trang dai.

Chay: python scripts/15_screenshot_dashboard.py [url] [out.png]
"""
import io, os, sys, json, time, base64, subprocess, shutil, tempfile, traceback
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import requests
import websocket

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
OUT = sys.argv[2] if len(sys.argv) > 2 else \
    r"D:\Master Exers\Big Data\Recomendation_System\docs\Project\Main\report\Big_Data\figures\fig9_dashboard.png"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PORT = int(os.environ.get("CDP_PORT", "9333"))
PROFILE = os.path.join(tempfile.gettempdir(), "oc_shot_profile")

if os.path.isdir(PROFILE):
    shutil.rmtree(PROFILE, ignore_errors=True)
os.makedirs(PROFILE, exist_ok=True)

proc = subprocess.Popen(
    [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
     "--window-size=1920,1200", "--remote-debugging-port=%d" % PORT,
     "--user-data-dir=" + PROFILE, "about:blank"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

ws_url = None
for _ in range(60):
    try:
        r = requests.get("http://127.0.0.1:%d/json/version" % PORT, timeout=2)
        ws_url = r.json()["webSocketDebuggerUrl"]
        break
    except Exception:
        time.sleep(0.5)
if not ws_url:
    print("KHONG ket noi duoc DevTools", flush=True)
    proc.kill(); sys.exit(2)
print("devtools:", ws_url, flush=True)

ws = websocket.create_connection(ws_url, timeout=90)
_id = [0]
pending = {}


def cmd(method, params=None, sess=None, timeout=90):
    _id[0] += 1
    mid = _id[0]
    msg = {"id": mid, "method": method, "params": params or {}}
    if sess:
        msg["sessionId"] = sess
    ws.send(json.dumps(msg))
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            ws.settimeout(max(1, timeout - (time.time() - t0)))
            resp = json.loads(ws.recv())
        except Exception as e:
            raise RuntimeError("recv timeout/fail on %s: %s" % (method, e))
        if resp.get("id") == mid:
            return resp
    raise RuntimeError("timeout waiting %s" % method)


def evaluate(sess, expr, by_value=True):
    r = cmd("Runtime.evaluate",
            {"expression": expr, "returnByValue": by_value,
             "awaitPromise": True}, sess)
    res = r.get("result", {}).get("result", {})
    if "exceptionDetails" in r.get("result", {}):
        return None
    return res.get("value")


PROBE = """(()=>{const b=document.body;
const svgs=document.querySelectorAll('.js-plotly-plot').length;
const tabs=document.querySelectorAll('[data-testid="stTabs"]').length;
const err=document.querySelectorAll('[data-testid="stException"]').length;
const txt=(b.innerText||'').trim();
const title=document.title;
return JSON.stringify({svgs,tabs,err,txtlen:txt.length,title,head:txt.slice(0,200),
 h:document.body.scrollHeight});})()"""

try:
    t = cmd("Target.createTarget", {"url": "about:blank"})
    tid = t["result"]["targetId"]
    s = cmd("Target.attachToTarget", {"targetId": tid, "flatten": True})["result"]["sessionId"]

    cmd("Page.enable", {}, s)
    cmd("Runtime.enable", {}, s)
    cmd("Log.enable", {}, s)
    cmd("Emulation.setDeviceMetricsOverride",
        {"width": 1920, "height": 1200, "deviceScaleFactor": 1, "mobile": False}, s)
    cmd("Page.navigate", {"url": URL}, s)
    print("navigate ->", URL, flush=True)

    deadline = time.time() + 180
    info = {}
    last = ""
    while time.time() < deadline:
        time.sleep(4)
        try:
            raw = evaluate(s, PROBE)
        except Exception as e:
            print("  probe err:", e, flush=True)
            continue
        if not raw:
            continue
        last = raw
        try:
            info = json.loads(raw)
        except Exception:
            continue
        print("  ", json.dumps(info, ensure_ascii=False)[:400], flush=True)
        if info.get("svgs", 0) >= 1 and info.get("txtlen", 0) > 300:
            break
        if info.get("err", 0) > 0:
            print("  !! app exception -> dung", flush=True)
            break

    # scroll het trang de trigger lazy render roi ve dau
    for _ in range(12):
        evaluate(s, "window.scrollBy(0, window.innerHeight)")
        time.sleep(0.6)
    evaluate(s, "window.scrollTo(0, 0)")
    time.sleep(2.5)

    h = evaluate(s, "Math.max(document.body.scrollHeight, 1200)") or 1200
    h = int(min(h, 14000))
    print("page height:", h, flush=True)
    cmd("Emulation.setDeviceMetricsOverride",
        {"width": 1920, "height": h + 60, "deviceScaleFactor": 1, "mobile": False}, s)
    time.sleep(2.5)

    shot = cmd("Page.captureScreenshot",
               {"format": "png", "captureBeyondViewport": True,
                "clip": {"x": 0, "y": 0, "width": 1920, "height": h + 60, "scale": 1}}, s)
    data = shot["result"]["data"]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "wb") as f:
        f.write(base64.b64decode(data))
    print("SAVED", OUT, os.path.getsize(OUT), "bytes", flush=True)
    print("final:", last[:400], flush=True)
except Exception:
    traceback.print_exc()
    sys.exit(3)
finally:
    try:
        ws.close()
    except Exception:
        pass
    try:
        proc.terminate()
    except Exception:
        pass
