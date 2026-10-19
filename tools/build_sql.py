"""Build SQL screenshots by really executing SQL against SQLite."""
import pathlib
import sqlite3
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import term_render

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def w(s):
    """Display width, Chinese counts as 2."""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in str(s))


def pad(s, width):
    s = str(s)
    return s + " " * max(0, width - w(s))


def table(cur):
    cols = [d[0] for d in cur.description] if cur.description else []
    rows = cur.fetchall()
    if not cols:
        if cur.rowcount is None or cur.rowcount < 0:
            return "OK"
        return f"{cur.rowcount} row(s) affected"
    widths = [max(w(c), *(w(r[i]) for r in rows)) if rows else w(c) for i, c in enumerate(cols)]
    out = [" | ".join(pad(c, widths[i]) for i, c in enumerate(cols))]
    out.append("-+-".join("-" * x for x in widths))
    for r in rows:
        out.append(" | ".join(pad(r[i], widths[i]) for i in range(len(cols))))
    out.append(f"({len(rows)} rows)")
    return "\n".join(out)


class Shell:
    def __init__(self):
        self.db = sqlite3.connect(":memory:")
        self.steps = []

    def __call__(self, sql):
        cur = self.db.execute(sql)
        try:
            res = table(cur)
        except sqlite3.ProgrammingError:
            res = f"{cur.rowcount} row(s) affected"
        self.steps.append((sql, res))
        return res


def scene(name, title, sh, notes):
    lines = []
    for sql, out in sh.steps:
        lines.append(("prompt", "sqlite> " + " ".join(sql.split())))
        for ln in out.splitlines():
            lines.append(("out", ln))
        lines.append(("out", ""))
    for n in notes:
        lines.append(("note", n))
    return {"name": name, "title": title, "lines": lines, "prefix": ""}


SCENES = []

# ---------- 1. 建表 / 插入 / 查询 ----------
s = Shell()
s("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
s("INSERT INTO users (name, age) VALUES ('小明', 18), ('小红', 24), ('老王', 31)")
s("SELECT * FROM users")
SCENES.append(scene("01_basic", "SQLite · 建表 + 插入 + 查询", s, [
    "CREATE TABLE 定义字段：id 是主键，name 文本，age 整数",
    "INSERT 一次插入多行（逗号分隔的括号组）",
    "SELECT * 取出全部；箭头左边是列名",
]))

# ---------- 2. 条件 / 排序 / 限制 ----------
s = Shell()
s("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
s("INSERT INTO users (name, age) VALUES ('小明', 18), ('小红', 24), ('老王', 31), ('阿珍', 26)")
s("SELECT name, age FROM users WHERE age >= 24 ORDER BY age DESC")
s("SELECT name FROM users LIMIT 2")
SCENES.append(scene("02_filter", "条件过滤 + 排序 + 限量", s, [
    "WHERE 筛选行，ORDER BY 排序（DESC 从大到小，默认 ASC）",
    "LIMIT 2 只取前 2 行，翻页时配合 OFFSET 使用",
    "顺序永远是 FROM → WHERE → GROUP BY → ORDER BY → LIMIT",
]))

# ---------- 3. 两表 JOIN ----------
s = Shell()
s("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
s("CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, item TEXT, amount REAL)")
s("INSERT INTO users (name) VALUES ('小明'), ('小红')")
s("INSERT INTO orders (user_id, item, amount) VALUES (1,'键盘',299), (1,'鼠标',99), (2,'显示器',1299)")
s("SELECT u.name, o.item, o.amount FROM users u JOIN orders o ON o.user_id = u.id")
SCENES.append(scene("03_join", "两表关联 JOIN（最常考也最常用）", s, [
    "users.id 是主键，orders.user_id 是指向它的外键",
    "JOIN ... ON 把两张表按「谁下的单」接起来",
    "u / o 是表别名，省得每次写全名",
]))

# ---------- 4. 聚合 / 更新 / 删除 ----------
s = Shell()
s("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
s("CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, amount REAL)")
s("INSERT INTO users (name) VALUES ('小明'), ('小红')")
s("INSERT INTO orders (user_id, amount) VALUES (1,299),(1,99),(2,1299)")
s("SELECT user_id, COUNT(*) AS orders, SUM(amount) AS total FROM orders GROUP BY user_id")
s("UPDATE orders SET amount = 199 WHERE id = 2")
s("DELETE FROM users WHERE id = 2")
SCENES.append(scene("04_aggregate", "统计 + 修改 + 删除", s, [
    "GROUP BY 按 user_id 分组，COUNT/SUM 算每组的单数和总额",
    "UPDATE ... WHERE 一定要带 WHERE，否则全表被改",
    "DELETE ... WHERE 同理，不带 WHERE 会清空整张表",
]))

if "--dry" in sys.argv:
    for sc in SCENES:
        print("=" * 60)
        print(sc["name"])
        for k, t in sc["lines"]:
            print(f"  [{k}] {t}")
    sys.exit(0)

outdir = pathlib.Path(__file__).parent.parent / "sql" / "shots"
print("rendering sql shots ->", outdir)
term_render.render(SCENES, outdir)
