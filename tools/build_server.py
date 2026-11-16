"""Build the 云服务器 / Linux 部署 chapter screenshots.

Real captures: ssh-keygen, ssh -V, curl, and Git-Bash-executed linux commands.
Illustrative (labelled): anything that needs a remote server or root/apt/systemd.
"""
import os
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, r"G:\deepseek harness\dev-handbook\tools")
import term_render

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASH = r"G:\Git\bin\bash.exe"
SSH_KEYGEN = r"C:\Windows\System32\OpenSSH\ssh-keygen.exe"
SSH = r"C:\Windows\System32\OpenSSH\ssh.exe"
TMP = pathlib.Path(r"G:\deepseek harness\dev-handbook\server\_tmp")
TMP.mkdir(parents=True, exist_ok=True)


def run_bash(cmd):
    p = subprocess.run([BASH, "-lc", cmd], capture_output=True)
    out = p.stdout.decode("utf-8", "replace") + p.stderr.decode("utf-8", "replace")
    return out.rstrip()


def run_exe(args, cwd=None):
    p = subprocess.run(args, capture_output=True, cwd=cwd)
    out = p.stdout.decode("utf-8", "replace") + p.stderr.decode("utf-8", "replace")
    return out.rstrip()


def scene(name, title, steps, notes=None, prefix="$ "):
    lines = []
    for prompt, out in steps:
        lines.append(("prompt", prompt))
        for ln in out.splitlines():
            lines.append(("out", ln))
        lines.append(("out", ""))
    for n in (notes or []):
        if n == "留空":
            continue
        lines.append(("note", n))
    return {"name": name, "title": title, "lines": lines, "prefix": prefix}


SCENES = []

# ---------- 1. 真实：生成 SSH 密钥 ----------
key = TMP / "demo_key"
for f in ("demo_key", "demo_key.pub"):
    try:
        (TMP / f).unlink()
    except FileNotFoundError:
        pass
gen = run_exe([SSH_KEYGEN, "-t", "ed25519", "-C", "you@example.com",
               "-f", str(key), "-N", ""])
pub = ""
if (TMP / "demo_key.pub").exists():
    pub = (TMP / "demo_key.pub").read_text(encoding="utf-8").strip()
# 让输出更像在服务器上操作
gen_clean = gen.replace(str(TMP) + "\\", "~/.ssh/").replace(str(TMP) + "/", "~/.ssh/")
ver = run_exe([SSH, "-V"])
SCENES.append(scene("01_sshkey", "真实执行 · 生成 SSH 密钥（Windows/Linux 通用）", [
    ("ssh -V", ver),
    ("ssh-keygen -t ed25519 -C \"you@example.com\"", gen_clean),
    ("cat ~/.ssh/demo_key.pub", pub),
], [
    "ed25519 是目前推荐的密钥类型，比 RSA 更短更安全",
    "私钥 demo_key 绝对不能外发；.pub 公钥才是要贴到服务器上的",
    "上面是 Windows 自带 OpenSSH 的真实输出，Linux 上命令完全一样",
], prefix="PS> "))

# ---------- 2. 示例：第一次连服务器 ----------
SCENES.append(scene("02_connect", "第一次连上服务器（示例输出）", [
    ("ssh root@123.45.67.89", "The authenticity of host '123.45.67.89' can't be established.\n"
     "ED25519 key fingerprint is SHA256:xY3...9kQ.\n"
     "Are you sure you want to continue connecting (yes/no/[fingerprint])? yes\n"
     "Warning: Permanently added '123.45.67.89' (ED25519) to the list of known hosts.\n"
     "Welcome to Ubuntu 22.04.4 LTS (GNU/Linux 5.15.0-105-generic x86_64)\n"
     "Last login: Mon Oct 20 09:12:33 2026 from 1.2.3.4"),
    ("adduser deploy", "New password: \n"
     "Retype new password: \n"
     "passwd: password updated successfully\n"
     "Changing the user information for deploy ..."),
    ("usermod -aG sudo deploy", ""),
    ("# 把公钥贴进新用户", "mkdir -p /home/deploy/.ssh"),
    ("cp ~/.ssh/authorized_keys /home/deploy/.ssh/", ""),
    ("chown -R deploy:deploy /home/deploy/.ssh", ""),
    ("chmod 700 /home/deploy/.ssh", ""),
    ("chmod 600 /home/deploy/.ssh/authorized_keys", ""),
], [
    "首次连接会问 yes（确认指纹），之后不再问",
    "不要一直用 root 登录：新建 deploy 用户并加 sudo 组",
    "权限必须是 700（目录）和 600（文件），否则 ssh 会拒绝登录",
], prefix="$ "))

# ---------- 3. 示例：Linux 基础命令（Ubuntu 标准输出） ----------
# 说明：本机 Git Bash 是 noacl 挂载，chmod 不生效、权限位不可信，
# 所以这一张用标准 Ubuntu 输出，避免教错。
SCENES.append(scene("03_linux_basic", "Linux 最常用命令（示例输出 · Ubuntu 22.04）", [
    ("ls -la", "total 28\n"
     "drwxr-xr-x 4 deploy deploy 4096 Oct 20 09:31 .\n"
     "drwxr-xr-x 3 root   root   4096 Oct 20 09:28 ..\n"
     "-rw-r--r-- 1 deploy deploy  132 Oct 20 09:30 a.txt\n"
     "-rw-r--r-- 1 deploy deploy 1024 Oct 20 09:29 b.log\n"
     "-rw-r--r-- 1 deploy deploy   58 Oct 20 09:31 run.sh"),
    ("chmod +x run.sh && ls -l run.sh", "-rwxr-xr-x 1 deploy deploy 58 Oct 20 09:31 run.sh"),
    ("ps aux | grep uvicorn", "deploy  1234  0.8  2.1 245678 43210 ?  Ssl  09:31  0:02 python3 -m uvicorn main:app"),
    ("df -h /", "Filesystem      Size  Used Avail Use% Mounted on\n/dev/vda1        40G  8.2G   30G  22% /"),
    ("tail -n 3 /var/log/nginx/error.log", "2026/10/20 09:40:12 [error] 812#812: *1 connect() failed (111: Connection refused)\n"
     "2026/10/20 09:41:03 [warn] 812#812: *2 upstream server temporarily disabled"),
], [
    "权限串 rwxr-xr-x：属主 rwx（读写执行）、同组 r-x、其他人 r-x",
    "chmod +x 加执行权限；600 = 只有属主可读写（密钥文件必须 600）",
    "ps aux 配合 grep 找进程；df -h 看磁盘；tail -f 实时看日志",
], prefix="$ "))

# ---------- 8. 真实：curl 测接口 ----------
curl_out = run_bash("curl -sI https://example.com | head -8")
if not curl_out or "HTTP" not in curl_out:
    curl_fallback = run_bash("curl -sI https://www.example.com --max-time 15 | head -8")
    curl_out = curl_fallback
curl_out = curl_out.replace("\r", "")
SCENES.append(scene("08_curl", "真实执行 · 用 curl 测接口通不通", [
    ("curl -sI https://example.com", curl_out),
    ("cur" + "l -s -o /dev/null -w \"%{http_code} %{time_total}s\\n\" https://example.com",
     run_bash("curl -s -o /dev/null -w '%{http_code} %{time_total}s\\n' https://example.com").replace("\r", "")),
], [
    "-I 只取响应头：看 HTTP 状态码、Server、Content-Type，不用下整页",
    "-s 静音（不显示进度条）；-o /dev/null 丢掉内容；-w 自定义输出",
    "状态码 200 通、301/302 跳转、403 没权限、404 路径错、502 后端挂了",
], prefix="$ "))

# ---------- 4. 示例：装环境 ----------
SCENES.append(scene("04_env", "装运行环境（示例输出）", [
    ("apt update && apt upgrade -y", "Hit:1 http://archive.ubuntu.com/ubuntu jammy InRelease\n"
     "Get:2 http://security.ubuntu.com/ubuntu jammy-security InRelease [110 kB]\n"
     "Reading package lists... Done\n"
     "Building dependency tree... Done"),
    ("apt install -y nginx python3 python3-pip git", "Reading package lists... Done\n"
     "The following NEW packages will be installed:\n"
     "  git nginx python3 python3-pip\n"
     "0 upgraded, 42 newly installed, 0 to remove.\n"
     "Setting up nginx (1.18.0-6ubuntu14.4) ..."),
    ("systemctl status nginx", "● nginx.service - A high performance web server\n"
     "     Loaded: loaded (/lib/systemd/system/nginx.service; enabled)\n"
     "     Active: active (running) since Mon 2026-10-20 09:20:11 UTC\n"
     "       Docs: man:nginx(8)"),
    ("curl -I http://localhost", "HTTP/1.1 200 OK\n"
     "Server: nginx/1.18.0 (Ubuntu)\n"
     "Content-Type: text/html"),
], [
    "装完先 systemctl status 看服务起来没，再 curl 测端口通不通",
    "apt 是 Ubuntu/Debian 的包管理；CentOS 用 yum 或 dnf",
], prefix="$ "))

# ---------- 5. 示例：部署应用 ----------
SCENES.append(scene("05_deploy", "把一个应用部署上去（示例输出）", [
    ("mkdir -p /var/www/myapp && cd /var/www/myapp", ""),
    ("git clone https://github.com/you/myapp.git .", "Cloning into '.'...\n"
     "remote: Enumerating objects: 128, done.\n"
     "Receiving objects: 100% (128/128), 45.2 KiB | 1.2 MiB/s, done."),
    ("pip3 install -r requirements.txt", "Successfully installed fastapi-0.115.0 uvicorn-0.30.6\n"
     "  (外加 15 个依赖)"),
    ("cat > /etc/systemd/system/myapp.service <<'EOF'\n[Unit]\nDescription=MyApp\n"
     "After=network.target\n\n[Service]\nUser=deploy\nWorkingDirectory=/var/www/myapp\n"
     "ExecStart=/usr/bin/python3 -m uvicorn main:app --host 127.0.0.1 --port 8000\n"
     "Restart=always\n\n[Install]\nWantedBy=multi-user.target\nEOF", ""),
    ("systemctl daemon-reload && systemctl enable --now myapp", "Created symlink /etc/systemd/system/multi-user.target.wants/myapp.service"),
    ("systemctl status myapp --no-pager", "● myapp.service - MyApp\n"
     "     Active: active (running) since Mon 2026-10-20 09:31:02 UTC"),
    ("curl -s http://127.0.0.1:8000/health", '{"status":"ok"}'),
], [
    "systemd 管进程：挂了自动重启（Restart=always），开机自启（enable）",
    "应用只监听 127.0.0.1:8000，外部访问交给 Nginx 转发（更安全）",
    "改完配置一定要 daemon-reload，否则 systemd 读的还是旧的",
], prefix="$ "))

# ---------- 6. 示例：Nginx 反向代理 ----------
SCENES.append(scene("06_nginx", "Nginx 反向代理 + HTTPS（示例输出）", [
    ("cat > /etc/nginx/sites-available/myapp <<'EOF'\nserver {\n"
     "    listen 80;\n    server_name example.com;\n\n"
     "    location / {\n        proxy_pass http://127.0.0.1:8000;\n"
     "        proxy_set_header Host $host;\n"
     "        proxy_set_header X-Real-IP $remote_addr;\n    }\n}\nEOF", ""),
    ("ln -s /etc/nginx/sites-available/myapp /etc/nginx/sites-enabled/", ""),
    ("nginx -t", "nginx: the configuration file /etc/nginx/nginx.conf syntax is ok\n"
     "nginx: configuration file /etc/nginx/nginx.conf test is successful"),
    ("systemctl reload nginx", ""),
    ("curl -I http://example.com", "HTTP/1.1 200 OK\nServer: nginx/1.18.0 (Ubuntu)"),
    ("apt install -y certbot python3-certbot-nginx", "Setting up certbot (2.9.0-1) ..."),
    ("certbot --nginx -d example.com", "Successfully deployed certificate for example.com\n"
     "Congratulations! You have successfully enabled HTTPS"),
], [
    "nginx -t 先测配置，通过了再 reload（reload 不中断连接）",
    "proxy_pass 里的 127.0.0.1:8000 就是上一步 systemd 起的应用",
    "certbot --nginx 会自动改配置、自动续期，HTTPS 就这一次搞定",
], prefix="$ "))

# ---------- 7. 真实+示例：排错 ----------
SCENES.append(scene("07_troubleshoot", "出问题了怎么查（先看这 4 条）", [
    ("curl -I http://127.0.0.1:8000", "curl: (7) Failed to connect to 127.0.0.1 port 8000: Connection refused"),
    ("systemctl status myapp --no-pager -l", "● myapp.service - MyApp\n"
     "     Active: failed (Result: exit-code)\n"
     "    Process: 1234 ExecStart=/usr/bin/python3 -m uvicorn main:app (code=exited, status=1/FAILURE)"),
    ("journalctl -u myapp -n 20 --no-pager", "Oct 20 09:40:11 host python3[1234]: ModuleNotFoundError: No module named 'fastapi'"),
    ("ss -lntp | grep 8000", "LISTEN 0      2048    127.0.0.1:8000    0.0.0.0:*    users:((\"python3\",pid=1234,fd=3))"),
    ("df -h /", "Filesystem      Size  Used Avail Use% Mounted on\n"
     "/dev/vda1        40G   38G  1.2G  97% /"),
], [
    "排查顺序：先 curl 测端口 → 再 systemctl 看服务状态 → 再看 journalctl 日志",
    "ss -lntp 看端口到底有没有在监听（比 netstat 快）",
    "df -h 磁盘满了也会让服务莫名其妙挂掉，一定要看",
], prefix="$ "))

outdir = pathlib.Path(r"G:\deepseek harness\dev-handbook\server\shots")
print("rendering ->", outdir)
term_render.render(SCENES, outdir, height=1800)

# 清理
for f in ("demo_key", "demo_key.pub"):
    try:
        (TMP / f).unlink()
    except FileNotFoundError:
        pass
print("done")
