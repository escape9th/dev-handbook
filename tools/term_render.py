"""Render terminal-style screenshots for the tutorials.

A "scene" is one terminal card. Lines are typed:
  prompt  -> command the user typed (shown with a $ prefix)
  out     -> normal output
  ok      -> green output
  err     -> red output
  note    -> grey comment line
"""
import json
import pathlib
import re
import subprocess
import sys

from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
PROFILE = r"G:\deepseek harness\dev-handbook\.edgeprofile"

PAGE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
  html,body{{margin:0;padding:0;background:#0b0f14;}}
  .wrap{{padding:18px;}}
  .term{{background:#0d1117;border:1px solid #30363d;border-radius:10px;overflow:hidden;
        font-family:Consolas,"Cascadia Mono","Microsoft YaHei",monospace;font-size:15px;}}
  .bar{{background:#161b22;border-bottom:1px solid #30363d;padding:8px 14px;color:#8b949e;
       font-size:13px;display:flex;align-items:center;gap:8px;}}
  .dot{{width:11px;height:11px;border-radius:50%;display:inline-block;}}
  .d1{{background:#ff5f56}} .d2{{background:#ffbd2e}} .d3{{background:#27c93f}}
  pre{{margin:0;padding:16px 18px;color:#c9d1d9;line-height:1.65;white-space:pre-wrap;word-break:break-word;}}
  .p{{color:#7ee787;}} .o{{color:#c9d1d9;}} .ok{{color:#3fb950;}}
  .e{{color:#f85149;}} .n{{color:#6e7681;font-style:italic;}}
</style></head><body><div class="wrap">
<div class="term">
  <div class="bar"><span class="dot d1"></span><span class="dot d2"></span><span class="dot d3"></span>
    <span style="margin-left:8px">{title}</span></div>
  <pre>{body}</pre>
</div></div></body></html>"""


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def build_html(scene):
    prefix = scene.get("prefix", "$ ")
    body = []
    for kind, text in scene["lines"]:
        if kind == "prompt":
            body.append(f'<span class="p">{esc(prefix + text)}</span>')
        elif kind == "ok":
            body.append(f'<span class="ok">{esc(text)}</span>')
        elif kind == "err":
            body.append(f'<span class="e">{esc(text)}</span>')
        elif kind == "note":
            body.append(f'<span class="n"># {esc(text)}</span>')
        else:
            body.append(f'<span class="o">{esc(text)}</span>')
    return PAGE.format(title=esc(scene.get("title", "terminal")), body="\n".join(body))


def crop(path):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    bg = im.getpixel((w - 2, h - 2))
    last = 0
    px = im.load()
    for y in range(h - 1, -1, -1):
        row_differs = any(
            abs(px[x, y][0] - bg[0]) + abs(px[x, y][1] - bg[1]) + abs(px[x, y][2] - bg[2]) > 12
            for x in range(0, w, 3))
        if row_differs:
            last = y
            break
    im.crop((0, 0, w, min(h, last + 18))).save(path)


def render(scenes, outdir, width=1060, height=1500):
    out = pathlib.Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    tmp = out / "_scene.html"
    made = []
    for sc in scenes:
        tmp.write_text(build_html(sc), encoding="utf-8")
        png = out / (sc["name"] + ".png")
        if png.exists():
            png.unlink()
        subprocess.run([
            EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
            "--no-first-run", "--no-default-browser-check",
            f"--user-data-dir={PROFILE}",
            f"--window-size={width},{height}", "--virtual-time-budget=3000",
            f"--screenshot={png}", tmp.resolve().as_uri(),
        ], capture_output=True)
        if png.exists():
            crop(png)
            made.append((sc["name"], png.stat().st_size))
            print(f"  ok {sc['name']:<22} {png.stat().st_size:>7} bytes")
        else:
            print(f"  FAIL {sc['name']}")
    tmp.unlink(missing_ok=True)
    return made
