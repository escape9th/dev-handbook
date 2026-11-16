# Dev Handbook

新人最容易卡住的操作，用**真实截图 + 编号步骤**讲清楚。纯静态 HTML，双击 `index.html` 就能看。

## 包含的章节

| 章节 | 内容 | 截图来源 |
|---|---|---|
| [GitHub](github/index.html) | Fork / 提 PR / 审 PR / 合并 / 看版本 / 提 Issue | 真实仓库截图 |
| [Docker](docker/index.html) | 镜像与容器 / 生命周期 / Dockerfile / 端口与卷 / compose | 示例输出（本机未装 Docker） |
| [Redis](redis/index.html) | 连接 / 基础命令 / 三种数据结构 / 过期 / 陷阱 | 本机真实执行 |
| [SQL](sql/index.html) | 建表 / 查询 / JOIN / 聚合 / 安全改删 | 本机真实执行 |
| [云服务器 + Linux 部署](server/index.html) | 买机 / SSH 密钥 / Linux 命令 / systemd / Nginx / HTTPS / 排错 | 混合（SSH 密钥与 curl 真实，远程操作示例） |

## 怎么看

```bash
git clone <this-repo>
# 然后直接双击 index.html，或用浏览器打开
```

不需要装任何东西，纯静态页面。

## 目录结构

```
.
├── index.html              # 总目录
├── assets/handbook.css     # 共用样式
├── github/                 # 每章一个目录
│   ├── index.html
│   └── annotated/*.png
├── docker/
│   ├── index.html
│   └── shots/*.png
├── redis/
├── sql/
├── server/                 # 云服务器 + Linux 部署
└── tools/                  # 截图生成脚本
    ├── term_render.py      # 终端风格截图渲染器（共用）
    ├── build_redis.py      # 真实执行 memurai-cli 生成截图
    ├── build_sql.py        # 真实执行 SQLite 生成截图
    ├── build_docker.py     # 示例输出（本机无 Docker）
    └── build_server.py     # SSH 密钥/curl 真实执行 + 远程操作示例
```

## 截图是怎么来的

- **真实执行类**（Redis / SQL / 云服务器章节的 SSH 密钥与 curl）：脚本真的跑命令，把真实输出填进模板再截图 —— 图里的数据不是编的。
- **示例类**（Docker、以及服务器章节的 apt / systemctl / nginx / 远程连接）：本机没有对应环境，图中明确标注「示例输出」。
- **GitHub 类**：用无头 Edge 打开真实页面截图，再用 Pillow 画红框和编号。

重新生成：

```bash
python tools/build_redis.py
python tools/build_sql.py
python tools/build_docker.py
python tools/build_server.py
```

## 想加新章节？

1. 新建 `新章节/index.html`，引用 `../assets/handbook.css`
2. 截图放 `新章节/shots/`
3. 在根 `index.html` 加一张卡片

## License

MIT
