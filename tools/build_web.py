"""Build the 网页 chapter: real HTML source + real rendered pages via headless Edge."""
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import term_render

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
ROOT = pathlib.Path(__file__).parent.parent
DEMO = ROOT / "web" / "demo"
PROFILE = ROOT / ".edgeprofile"


def run(args, timeout=40):
    try:
        p = subprocess.run(args, capture_output=True, timeout=timeout)
        out = p.stdout.decode("utf-8", "replace") + p.stderr.decode("utf-8", "replace")
        return out.replace("\r\n", "\n").rstrip()
    except Exception as e:
        return f"<error: {e}>"


def scene(name, title, steps, notes=None, prefix="$ "):
    lines = []
    for prompt, out in steps:
        lines.append(("prompt", prompt))
        for ln in out.splitlines():
            lines.append(("out", ln))
        lines.append(("out", ""))
    for n in (notes or []):
        lines.append(("note", n))
    return {"name": name, "title": title, "lines": lines, "prefix": prefix}


# ---------- 示例页面 ----------
DEMO.mkdir(parents=True, exist_ok=True)

BODY = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>我的第一个网页</title>
  %s
</head>
<body>
  <h1>你好，网页</h1>
  <p>同一个 HTML 文件，加不加样式，差别就是这么大。</p>
  <h2>我要学什么</h2>
  <ul>
    <li>HTML —— 决定<em>有什么内容</em></li>
    <li>CSS —— 决定<em>长什么样子</em></li>
    <li>JavaScript —— 决定<em>能做什么交互</em></li>
  </ul>
  <p><a href="https://example.com">这是一个链接</a></p>
</body>
</html>
"""

CSS = """<style>
  body { margin:0; padding:40px; background:#0d1117; color:#e6edf3;
         font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif; line-height:1.8; }
  h1 { font-size:34px; margin:0 0 16px;
       background:linear-gradient(90deg,#58a6ff,#8b5cf6); -webkit-background-clip:text;
       -webkit-text-fill-color:transparent; }
  h2 { font-size:20px; margin:28px 0 10px; color:#58a6ff; }
  p  { color:#c9d1d9; max-width:640px; }
  strong { color:#fff; }
  em { color:#7ee787; font-style:normal; }
  ul { background:#161b22; border:1px solid #30363d; border-radius:12px;
       padding:18px 20px 18px 40px; max-width:600px; }
  li { margin:8px 0; }
  a  { display:inline-block; margin-top:8px; padding:10px 20px; border-radius:8px;
       background:#238636; color:#fff; text-decoration:none; font-size:14px; }
</style>"""

(DEMO / "raw.html").write_text(BODY % "", encoding="utf-8")
(DEMO / "styled.html").write_text(BODY % CSS, encoding="utf-8")


def shoot(html_name, out_name, w=1000, h=640):
    out = ROOT / "web" / "shots" / out_name
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    src = (DEMO / html_name).as_uri()
    subprocess.run([
        EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--no-first-run", "--no-default-browser-check",
        f"--user-data-dir={PROFILE}", f"--window-size={w},{h}",
        "--virtual-time-budget=3000", f"--screenshot={out}", src,
    ], capture_output=True, timeout=120)
    return out


shoot("raw.html", "04_no_css.png")
shoot("styled.html", "05_with_css.png")
print("rendered demo pages")

SCENES = []

# ---------- 1. 真实：一个网页的源码长什么样 ----------
src = run(["curl", "-s", "--max-time", "20", "https://example.com"])
src_lines = src.splitlines()[:18]
SCENES.append(scene("01_source", "真实执行 · 网页的“真身”是文本", [
    ("curl -s https://example.com", "\n".join(src_lines)),
], [
    "浏览器看到的网页，本质就是一段文本（HTML）",
    "curl 拿到的是「服务器原样返回的内容」，没经过浏览器渲染",
    "curl 是命令行里的浏览器 —— 只取内容，不画页面",
]))

# ---------- 2. 真实：浏览器发的请求头 ----------
verbose = run(["curl", "-sv", "-o", "NUL", "https://example.com"])
req = [ln for ln in verbose.splitlines() if ln.startswith(">") or ln.startswith("* Connected")]
SCENES.append(scene("02_request", "真实执行 · 浏览器到底发了什么", [
    ("curl -sv https://example.com", "\n".join(req[:9])),
], [
    "> 开头的是你发出去的内容（请求）",
    "GET / HTTP/1.1 = 我要根路径，用 HTTP/1.1 协议",
    "Host 告诉服务器你要访问哪个网站（一个 IP 上可能有很多站）",
    "Cookie / Authorization 等头就是登录态，别乱发给陌生人",
]))

outdir = ROOT / "web" / "shots"
print("rendering web terminal shots ->", outdir)
term_render.render(SCENES, outdir, height=1400)
print("done")
