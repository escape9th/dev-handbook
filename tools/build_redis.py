"""Build real Redis screenshots by actually running memurai-cli."""
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import term_render

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLI = r"C:\Program Files\Memurai\memurai-cli.exe"


def run(*args):
    p = subprocess.run([CLI, *args], capture_output=True)
    b = p.stdout if p.stdout.strip() else p.stderr
    for enc in ("gbk", "utf-8"):
        try:
            return b.decode(enc).strip()
        except UnicodeDecodeError:
            continue
    return b.decode("gbk", "replace").strip()


def cmd(*args):
    """Return (prompt_text, output_text) using the real CLI."""
    return " ".join(["memurai-cli", *args]), run(*args)


def scene(name, title, steps, notes=None):
    lines = []
    for prompt, out in steps:
        lines.append(("prompt", prompt))
        for ln in out.splitlines():
            lines.append(("out", ln))
        lines.append(("out", ""))
    for n in (notes or []):
        lines.append(("note", n))
    return {"name": name, "title": title, "lines": lines}


# 先清掉上次的演示键
for k in run("keys", "demo:*").splitlines():
    if k:
        run("del", k)

SCENES = []

# ---- 1. 连接 + 字符串 ----
steps = [
    cmd("ping"),
    cmd("set", "demo:user:name", "小明"),
    cmd("get", "demo:user:name"),
    cmd("set", "demo:visits", "0"),
    cmd("incr", "demo:visits"),
    cmd("incr", "demo:visits"),
]
SCENES.append(scene("01_basic", "memurai-cli · Redis 8.2 (6379)", steps, [
    "PING = 测活，返回 PONG 说明连上了",
    "SET / GET = 存一个值、取一个值",
    "INCR = 数字自增，原子操作，不会丢计数",
]))

# ---- 2. 常见数据结构 ----
steps = [
    cmd("rpush", "demo:tasks", "写周报", "修bug", "发版"),
    cmd("lrange", "demo:tasks", "0", "-1"),
    cmd("hset", "demo:user:1", "name", "小红", "age", "18"),
    cmd("hgetall", "demo:user:1"),
    cmd("sadd", "demo:tags", "前端", "后端", "ai"),
    cmd("smembers", "demo:tags"),
]
SCENES.append(scene("02_types", "三种最常用的数据结构", steps, [
    "List  = 有序列表，RPUSH 从右边塞，LRANGE 取出全部",
    "Hash  = 一个对象，HSET 存字段，HGETALL 取全部",
    "Set   = 去重集合，SADD 加，SMEMBERS 列",
]))

# ---- 3. 过期、删除、查看 ----
steps = [
    cmd("set", "demo:code", "8888"),
    cmd("expire", "demo:code", "60"),
    cmd("ttl", "demo:code"),
    cmd("keys", "demo:*"),
    cmd("del", "demo:code"),
    cmd("exists", "demo:code"),
]
SCENES.append(scene("03_expire", "过期时间 / 删除 / 扫描", steps, [
    "EXPIRE 给 key 设过期秒数，TTL 查看还剩几秒（-2 = 已不存在）",
    "KEYS demo:* 扫描匹配的 key（线上别用 KEYS *，会卡住服务器）",
    "DEL 删除，EXISTS 判断是否还存在（0 = 没了）",
]))

# ---- 4. 服务信息 ----
info = run("info", "server")
keep = [ln for ln in info.splitlines() if ln.startswith(("redis_version", "memurai_version", "redis_mode", "os", "arch_bits"))]
steps = [("memurai-cli info server", "\n".join(keep))]
dbsize = run("dbsize")
steps.append(("memurai-cli dbsize", dbsize))
SCENES.append(scene("04_info", "看服务器信息", steps, [
    "INFO server = 版本/系统信息；DBSIZE = 当前库里有多少 key",
]))

if "--dry" in sys.argv:
    for sc in SCENES:
        print("=" * 60)
        print(sc["name"], "|", sc["title"])
        for k, t in sc["lines"]:
            print(f"  [{k}] {t!r}")
    sys.exit(0)

outdir = pathlib.Path(__file__).parent.parent / "redis" / "shots"
print("rendering redis shots ->", outdir)
term_render.render(SCENES, outdir)

# 清理演示数据
for k in run("keys", "demo:*").splitlines():
    if k:
        run("del", k)
print("cleaned demo keys")
