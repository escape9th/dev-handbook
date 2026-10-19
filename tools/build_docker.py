"""Build the Docker chapter screenshots.

Docker is NOT installed on this machine, so every card here is explicitly
labelled as an illustrative example — never passed off as a real capture.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import term_render

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

NOTE = "示例输出：本机未安装 Docker，以上为命令与预期结果示意"

SCENES = [
    {"name": "01_lifecycle", "title": "Docker · 容器生命周期（示例输出）", "lines": [
        ("prompt", "docker run -d --name web -p 8080:80 nginx"),
        ("out", "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"),
        ("note", "留空"),
        ("prompt", "docker ps"),
        ("out", "CONTAINER ID   IMAGE          STATUS          PORTS                  NAMES"),
        ("out", "a1b2c3d4e5f6   nginx:latest   Up 12 seconds   0.0.0.0:8080->80/tcp   web"),
        ("note", "留空"),
        ("prompt", "docker stop web"),
        ("out", "web"),
        ("prompt", "docker rm web"),
        ("out", "web"),
        ("note", "留空"),
        ("note", "run = 建并启动；-d 后台跑；-p 8080:80 把本机 8080 映射到容器 80"),
        ("note", "ps 只看运行中的（加 -a 看全部）；stop 停；rm 删容器（镜像还在）"),
        ("note", NOTE),
    ]},
    {"name": "02_dockerfile", "title": "Docker · 写 Dockerfile 并构建（示例输出）", "lines": [
        ("prompt", "cat Dockerfile"),
        ("out", "FROM python:3.12-slim"),
        ("out", "WORKDIR /app"),
        ("out", "COPY requirements.txt ."),
        ("out", "RUN pip install --no-cache-dir -r requirements.txt"),
        ("out", "COPY . ."),
        ("out", 'CMD ["python", "main.py"]'),
        ("note", "留空"),
        ("prompt", "docker build -t myapp:v1 ."),
        ("out", "[+] Building 12.3s (9/9) FINISHED"),
        ("out", " => [1/5] FROM docker.io/library/python:3.12-slim"),
        ("out", " => [2/5] WORKDIR /app"),
        ("out", " => [3/5] COPY requirements.txt ."),
        ("out", " => [4/5] RUN pip install --no-cache-dir -r requirements.txt"),
        ("out", " => [5/5] COPY . ."),
        ("out", " => exporting to image"),
        ("out", "Successfully tagged myapp:v1"),
        ("note", "留空"),
        ("note", "FROM 选基础镜像；WORKDIR 设工作目录；COPY 复制文件；RUN 构建时执行"),
        ("note", "CMD 是容器启动时执行的命令；-t myapp:v1 给镜像起名字和版本"),
        ("note", "COPY requirements.txt 单独放前面，改代码时不用重装依赖（缓存）"),
        ("note", NOTE),
    ]},
    {"name": "03_port_volume", "title": "Docker · 端口映射与数据卷（示例输出）", "lines": [
        ("prompt", "docker run -d --name site -p 8080:80 -v /data/html:/usr/share/nginx/html nginx"),
        ("out", "f0e1d2c3b4a5968778695a4b3c2d1e0f"),
        ("note", "留空"),
        ("prompt", "docker inspect site --format '{{json .Mounts}}'"),
        ("out", '[{"Type":"bind","Source":"/data/html","Destination":"/usr/share/nginx/html"}]'),
        ("note", "留空"),
        ("prompt", "curl -I http://localhost:8080"),
        ("out", "HTTP/1.1 200 OK"),
        ("out", "Server: nginx/1.27.0"),
        ("note", "留空"),
        ("note", "-p 本机端口:容器端口 —— 左边是你能访问的，右边是容器内服务的"),
        ("note", "-v 本机目录:容器目录 —— 容器删了数据还在，这就是「数据卷」的作用"),
        ("note", NOTE),
    ]},
    {"name": "04_compose", "title": "Docker Compose · 一条命令起整套（示例输出）", "lines": [
        ("prompt", "cat docker-compose.yml"),
        ("out", "services:"),
        ("out", "  web:"),
        ("out", "    build: ."),
        ("out", "    ports: ['8080:80']"),
        ("out", "    depends_on: [db]"),
        ("out", "  db:"),
        ("out", "    image: postgres:16"),
        ("out", "    environment:"),
        ("out", "      POSTGRES_PASSWORD: secret"),
        ("out", "    volumes: ['dbdata:/var/lib/postgresql/data']"),
        ("out", "volumes:"),
        ("out", "  dbdata:"),
        ("note", "留空"),
        ("prompt", "docker compose up -d"),
        ("out", "[+] Running 3/3"),
        ("out", " ✔ Network app_default  Created    0.1s"),
        ("out", " ✔ Container app-db-1   Started    1.2s"),
        ("out", " ✔ Container app-web-1  Started    0.8s"),
        ("note", "留空"),
        ("prompt", "docker compose down"),
        ("out", "[+] Running 3/3"),
        ("out", " ✔ Container app-web-1  Removed"),
        ("out", " ✔ Container app-db-1   Removed"),
        ("out", " ✔ Network app_default  Removed"),
        ("note", "留空"),
        ("note", "compose 用一个 yml 描述「多容器怎么组合」，up 起、down 停并清理"),
        ("note", "depends_on 控制启动顺序；volumes 声明具名卷，数据持久化"),
        ("note", NOTE),
    ]},
]

# drop the placeholder blank lines that were written as notes
for sc in SCENES:
    sc["lines"] = [(k, t) for (k, t) in sc["lines"] if t != "留空"]

outdir = pathlib.Path(__file__).parent.parent / "docker" / "shots"
print("rendering docker shots ->", outdir)
term_render.render(SCENES, outdir, height=1700)
