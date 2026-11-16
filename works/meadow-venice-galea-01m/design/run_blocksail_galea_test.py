"""Drive the actual built Blocksail battle page over a local Chrome debug socket."""
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

from PIL import Image

D = Path(__file__).resolve().parent
SCRATCH = Path("D:/Unity/Valhalla/scratchpad/galea1297")
sys.path.insert(0, str(SCRATCH / "python"))
from websocket import create_connection

PAGE = os.environ.get("GALEA_BATTLE_PAGE", "battle.html")
URL = f"http://127.0.0.1:49387/{PAGE}?debug=1&prefs=0&lerp=0"
CHROME = Path("C:/Program Files/Google/Chrome/Application/chrome.exe")


def main():
    assembly, oar = map(Path, sys.argv[1:3])
    timber = []
    for line in assembly.read_text(encoding="utf-8").splitlines():
        if line[:1].isdigit():
            x,y,z,_ = map(int,line.split(","))
            if z < 60:
                timber.append(x + 560*(y + 321*z))
    oar_cells = [list(map(int, line.split(",")[:3])) for line in oar.read_text(encoding="utf-8").splitlines()
                 if line[:1].isdigit()]
    scan = dict(layout=json.loads((D / "oar_layout.json").read_text()), timber=timber,
                oarCells=oar_cells)
    args = ["--headless=new", "--enable-unsafe-swiftshader", "--use-angle=swiftshader",
            "--remote-debugging-port=0", "--remote-allow-origins=http://localhost",
            "--window-size=1440,900", "--no-first-run", "--mute-audio", "about:blank"]
    with tempfile.TemporaryDirectory(dir=SCRATCH, ignore_cleanup_errors=True) as profile:
        chrome = subprocess.Popen([str(CHROME), "--user-data-dir="+profile, *args],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            port_file = Path(profile) / "DevToolsActivePort"
            for _ in range(200):
                if port_file.exists():
                    break
                time.sleep(.1)
            port = port_file.read_text().splitlines()[0]
            tabs = json.load(urlopen(f"http://127.0.0.1:{port}/json/list",timeout=10))
            sock = create_connection(tabs[0]["webSocketDebuggerUrl"], timeout=100, origin="http://localhost")
            seq = 0

            def msg(method, **params):
                nonlocal seq
                seq += 1
                sock.send(json.dumps(dict(id=seq, method=method, params=params)))
                while True:
                    response = json.loads(sock.recv())
                    if response.get("id") == seq:
                        if "error" in response:
                            raise RuntimeError(response["error"])
                        return response["result"]

            def evaluate(expression):
                result = msg("Runtime.evaluate", expression=expression,
                             awaitPromise=True, returnByValue=True)
                if result.get("exceptionDetails"):
                    raise RuntimeError(result["result"].get("description", result))
                return result.get("result", {}).get("value")

            def screenshot(filename):
                png = msg("Page.captureScreenshot", format="png", captureBeyondViewport=False)
                (D / filename).write_bytes(base64.b64decode(png["data"]))

            msg("Page.enable")
            msg("Page.navigate", url=URL)
            if os.environ.get("GALEA_DOCK_TRIAL"):
                for _ in range(210):
                    ready = evaluate("window.hostState?.error || (typeof frames[0]?.galeaProbe === 'function' && typeof hostStats === 'function')")
                    if isinstance(ready, str):
                        raise RuntimeError(ready)
                    if ready:
                        break
                    time.sleep(.6)
                else:
                    raise RuntimeError(evaluate("window.hostState"))
                sock.settimeout(175)
                print("Waiting for live Venice berth", flush=True)
                print(json.dumps(evaluate("window.galeaVenice = frames[0].galeaProbe(); galeaVenice.ready()"), ensure_ascii=False), flush=True)
                print("Drop and hold both anchors", flush=True)
                print(json.dumps(evaluate("galeaVenice.anchor()"), ensure_ascii=False), flush=True)
                screenshot("blocksail_galea_venice_anchor.png")
                print("Weigh anchors and use the normal docking control", flush=True)
                report = evaluate("galeaVenice.dock()")
                (D / "blocksail_galea_venice_trial.json").write_text(
                    json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                screenshot("blocksail_galea_venice_dock.png")
                print(json.dumps({"ok":report["ok"],"errors":report["errors"],
                                  "dock":report["stages"].get("dock", {}).get("result")}, ensure_ascii=False), flush=True)
                sock.close()
                if not report["ok"]:
                    raise RuntimeError("Venice sea trial failed")
                return

            for _ in range(100):
                if evaluate("Boolean(window.__game && typeof window.galeaProbe === 'function' && window.__vxk?.art)"):
                    break
                time.sleep(.3)
            else:
                raise RuntimeError(evaluate("[location.href, document.title, document.body.innerText.slice(-2000)]"))

            if os.environ.get("GALEA_STATION_TRIAL"):
                report = evaluate("galeaProbe()")
                (D / "blocksail_galea_station_layout.json").write_text(
                    json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
                print(json.dumps(report, ensure_ascii=False), flush=True)
                sock.close()
                return
            if os.environ.get("GALEA_GUN_TRIAL"):
                print("First volley", flush=True)
                print(json.dumps(evaluate("galeaProbe()"), ensure_ascii=False), flush=True)
                screenshot("blocksail_galea_first_volley.png")
                print("Reload and supply", flush=True)
                report = evaluate("galeaContinueFire()")
                report["source"] = PAGE
                (D / "blocksail_galea_gunnery.json").write_text(
                    json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                print(json.dumps(report, ensure_ascii=False), flush=True)
                sock.close()
                if not report["ok"]:
                    raise RuntimeError("Gunnery trial failed")
                return
            print("Straight leg", flush=True)
            print(evaluate(f"galeaProbe({json.dumps(scan)})"), flush=True)
            screenshot("blocksail_galea_sailing.png")
            evaluate("galeaCam(16,.63,250)")
            frames = []
            for count in ((0,) if os.environ.get("GALEA_SKIP_GIF") else (0, 17, 17, 17, 17, 17, 17, 17, 17)):
                evaluate(f"galeaAdvance({count})")
                filename = f"galea-frame-{len(frames):02}.png"
                screenshot(filename)
                with Image.open(D / filename) as src:
                    img = src.crop((230,130,1210,725))
                    img.thumbnail((800,500))
                    frames.append(img.convert("RGB"))
                (D / filename).unlink()
            if len(frames) > 1: frames[0].save(D / "blocksail_galea_oars.gif", save_all=True, append_images=frames[1:],
                           duration=283, loop=0)
            print("Turn and reverse legs", flush=True)
            report = evaluate("galeaMore()")
            frames[0].save(D / "blocksail_galea_close.png")
            report["source"] = URL.replace("http://127.0.0.1:49387/", "")
            (D / "blocksail_galea_trial.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",
                                                          encoding="utf-8")
            print(json.dumps(report,ensure_ascii=False), flush=True)
            sock.close()
        finally:
            chrome.terminate()
            chrome.wait(timeout=15)


if __name__ == "__main__":
    main()
