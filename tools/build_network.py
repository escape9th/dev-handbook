"""Build the 计算机网络 chapter screenshots (all real, captured on this machine)."""
import os
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import term_render

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


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


SCENES = []

# ---------- 1. ping（真实） ----------
ping = run(["ping", "-n", "4", "example.com"])
SCENES.append(scene("01_ping", "真实执行 · ping 测通不通", [
    ("ping -n 4 example.com", ping),
], [
    "第一行就告诉你域名解析到了哪个 IP（104.20.23.154）",
    "time = 往返延迟（ms），越小越快；TTL 每过一个路由器减 1",
    "Lost = 0% 说明一个包没丢；丢包多就是网络不稳",
    "ping 用的是 ICMP 协议，有些服务器会禁 ping，禁了不代表不通",
]))

# ---------- 2. DNS（真实，用可用的公共 DNS，避免暴露本机 DNS） ----------
dns = ""
for server in ("223.5.5.5", "114.114.114.114", "119.29.29.29"):
    got = run(["nslookup", "example.com", server])
    if "Addresses" in got and "timed out" not in got:
        dns = got
        dns_server = server
        break
if not dns:
    dns = run(["nslookup", "example.com"])
    dns = re.sub(r"Server:\s+\S+", "Server:  dns.local", dns)
    dns = re.sub(r"Address:\s+\d+\.\d+\.\d+\.\d+\s*$", "Address:  192.168.1.1", dns, flags=re.M)
    dns_server = "dns.local"
SCENES.append(scene("02_dns", "真实执行 · DNS 把域名变成 IP", [
    (f"nslookup example.com {dns_server}", dns),
], [
    "你输入 example.com，电脑先问 DNS：它的 IP 是多少？",
    "一个域名可以有多个 IP（这里 4 个），这叫负载均衡",
    "AAAA 记录是 IPv6，A 记录是 IPv4",
    "换 DNS 能解决一部分「网站打不开」的问题（如 223.5.5.5 / 119.29.29.29）",
]))

# ---------- 3. curl -v 完整链路（真实，最有教学价值） ----------
verbose = run(["curl", "-sv", "-o", os.devnull, "https://example.com"])
# 截取关键段落：解析 -> 连接 -> TLS -> 请求 -> 响应头
keep = []
started = False
for ln in verbose.splitlines():
    if "Host example.com:443 was resolved" in ln:
        started = True
    if not started:
        continue
    if ln.startswith("<") or ln.startswith(">") or ln.startswith("*"):
        keep.append(ln)
    if len(keep) > 26:
        break
SCENES.append(scene("03_curl_v", "真实执行 · 一次 HTTPS 请求的全过程", [
    ("curl -sv https://example.com", "\n".join(keep)),
], [
    "* 开头 = curl 自己打印的过程（不是服务器返回的）",
    "> 开头 = 你发给服务器的请求；< 开头 = 服务器返回的响应",
    "整个过程：解析域名 → 建立 TCP 连接 → TLS 握手 → 发 HTTP → 收响应",
]))

# ---------- 4. HTTP 响应头（真实） ----------
heads = run(["curl", "-sI", "https://example.com"])
SCENES.append(scene("04_headers", "真实执行 · HTTP 响应头是什么", [
    ("curl -sI https://example.com", heads),
], [
    "第一行 HTTP/1.1 200 OK：状态码 200 = 成功",
    "Content-Type 告诉浏览器这是网页（text/html）",
    "Server 是对方用什么软件（这里是 cloudflare）",
    "cf-cache-status: HIT 说明命中了 CDN 缓存，所以很快",
]))

# ---------- 5. tracert（真实） ----------
trace = run(["tracert", "-h", "8", "-w", "800", "example.com"], timeout=90)
SCENES.append(scene("05_tracert", "真实执行 · 数据包经过了哪些路由器", [
    ("tracert -h 8 example.com", trace),
], [
    "tracert（Linux 上叫 traceroute）看流量走了哪些节点",
    "每一行 = 一个路由器（跳），三个时间是三次探测的延迟",
    "* * * = 这个节点不响应（正常现象，不代表断网）",
    "第一跳 10.20.0.1 是你自己的路由器/网关",
]))

# ---------- 6. netstat / 端口（真实，只取监听） ----------
ns = run(["netstat", "-ano"])
listen = [ln for ln in ns.splitlines() if "LISTENING" in ln][:10]
SCENES.append(scene("06_ports", "真实执行 · 谁在监听端口", [
    ("netstat -ano | findstr LISTENING", "\n".join(listen)),
], [
    "0.0.0.0:端口 = 监听所有网卡（外部可访问）",
    "127.0.0.1:端口 = 只监听本机（外部访问不到）",
    "最后一列 PID = 进程号，用任务管理器或 tasklist 查是谁",
    "Linux 上对应命令是 ss -lntp（更快更好用）",
]))

outdir = pathlib.Path(__file__).parent.parent / "network" / "shots"
print("rendering network shots ->", outdir)
term_render.render(SCENES, outdir, height=1700)
