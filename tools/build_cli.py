"""Build the 命令行 chapter screenshots. Everything here is real output."""
import pathlib
import shutil
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import term_render

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASH = r"G:\Git\bin\bash.exe"
DEMO = pathlib.Path.home() / "cli-demo"


def bash(cmd):
    p = subprocess.run([BASH, "-lc", cmd], capture_output=True)
    out = p.stdout.decode("utf-8", "replace") + p.stderr.decode("utf-8", "replace")
    return out.replace("\r\n", "\n").rstrip()


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


# 每次从干净目录开始
if DEMO.exists():
    shutil.rmtree(DEMO, ignore_errors=True)
DEMO.mkdir(parents=True, exist_ok=True)
D = f'cd "$HOME/cli-demo" && '

SCENES = []

# ---------- 1. 我在哪 / 有什么 / 怎么进 ----------
s1 = [
    ("cd ~/cli-demo && pwd", bash(D + "pwd")),
    ("touch 笔记.txt 数据.csv && mkdir 备份", bash(D + "touch 笔记.txt 数据.csv && mkdir 备份 && echo ok")),
    ("ls", bash(D + "ls")),
    ("ls -l", bash(D + "ls -l")),
    ("cd 备份 && pwd", bash(D + "cd 备份 && pwd")),
    ("cd .. && pwd", bash(D + "cd .. && pwd")),
]
SCENES.append(scene("01_navigate", "真实执行 · 我在哪、有什么、怎么进", s1, [
    "pwd = 我现在在哪个目录（Print Working Directory）",
    "ls 列文件；ls -l 看详情（大小、时间、权限）",
    "cd 进目录，cd .. 回上一级，cd ~ 回家目录",
    "路径里的 / 是分隔符（Windows 的 \\ 在命令行里要写成 / 或 \\\\）",
]))

# ---------- 2. 写文件 / 看文件 ----------
s2 = [
    ("echo \"第一行\" > 笔记.txt", bash(D + "echo \"第一行\" > 笔记.txt && echo ok")),
    ("cat 笔记.txt", bash(D + "cat 笔记.txt")),
    ("echo \"第二行\" >> 笔记.txt", bash(D + "echo \"第二行\" >> 笔记.txt && echo ok")),
    ("cat 笔记.txt", bash(D + "cat 笔记.txt")),
    ("wc -l 笔记.txt", bash(D + "wc -l 笔记.txt")),
]
SCENES.append(scene("02_write", "真实执行 · 写文件与看文件", s2, [
    "> 是覆盖写入（原来内容没了）；>> 是追加",
    "cat 看整个文件；文件大用 less（按 q 退出）",
    "wc -l 数行数，wc -c 数字节",
]))

# ---------- 3. 管道 | ----------
s3 = [
    ("printf \"banana\\napple\\ncherry\\napple\\n\" > 水果.txt", bash(D + "printf 'banana\\napple\\ncherry\\napple\\n' > 水果.txt && echo ok")),
    ("cat 水果.txt", bash(D + "cat 水果.txt")),
    ("cat 水果.txt | sort", bash(D + "cat 水果.txt | sort")),
    ("cat 水果.txt | sort | uniq -c", bash(D + "cat 水果.txt | sort | uniq -c")),
    ("cat 水果.txt | wc -l", bash(D + "cat 水果.txt | wc -l")),
]
SCENES.append(scene("03_pipe", "真实执行 · 管道 | 是命令行的灵魂", s3, [
    "| 把左边命令的输出，当成右边命令的输入",
    "sort 排序；uniq -c 去重并计数（必须先 sort 才能正确去重）",
    "一条命令只做一件事，用 | 串起来 —— 这是 Unix 的哲学",
]))

# ---------- 4. 查找 ----------
s4 = [
    ("grep apple 水果.txt", bash(D + "grep apple 水果.txt")),
    ("grep -rn \"第二行\" .", bash(D + "grep -rn '第二行' .")),
    ("find . -name \"*.txt\"", bash(D + "find . -name '*.txt'")),
]
SCENES.append(scene("04_find", "真实执行 · 找内容、找文件", s4, [
    "grep 找内容：grep 关键词 文件",
    "grep -r 递归找目录，-n 显示行号 —— 查代码最常用",
    "find 找文件：find 目录 -name \"*.后缀\"",
    "Windows 自带的是 findstr，PowerShell 用 Select-String",
]))

# ---------- 5. 环境变量 ----------
s5 = [
    ("echo $PATH", bash("echo $PATH | cut -c1-160")),
    ("which git", bash("which git")),
    ("which python", bash("which python")),
    ("java -version 2>&1 | head -1", bash("java -version 2>&1 | head -1")),
]
SCENES.append(scene("05_env", "真实执行 · 环境变量 PATH 是什么", s5, [
    "PATH 是一串目录，用 : 分隔（Windows 是 ;）",
    "你敲 git，系统按 PATH 里的顺序一个个目录找，找到就执行",
    "「命令找不到」= 那个程序不在 PATH 里，加进去或写全路径",
    "which 就是问：这个命令到底在哪",
]))

# ---------- 6. PowerShell 对照 ----------
PS = "powershell -NoProfile -Command "


def ps(cmd):
    p = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True)
    out = p.stdout.decode("utf-8", "replace") + p.stderr.decode("utf-8", "replace")
    return out.replace("\r\n", "\n").rstrip()


s6 = [
    ("Get-ChildItem", ps("Set-Location $HOME\\cli-demo; Get-ChildItem | Select-Object -First 5 | Format-Table Name,Length -AutoSize")),
    ("Get-ChildItem -Filter *.txt", ps("Set-Location $HOME\\cli-demo; Get-ChildItem -Filter *.txt | Select-Object Name")),
    ("$env:PATH -split ';' | Select-Object -First 4", ps("$env:PATH -split ';' | Select-Object -First 4")),
    ("Select-String -Path *.txt -Pattern '第二行'", ps("Set-Location $HOME\\cli-demo; Select-String -Path *.txt -Pattern '第二行' | Select-Object Filename,Line")),
]
SCENES.append(scene("06_powershell", "真实执行 · Windows PowerShell 对照表", s6, [
    "PowerShell 用「动词-名词」命名：Get-ChildItem = ls，Select-String = grep",
    "输出是对象不是纯文本，可以用 | Select-Object 挑字段",
    "想用 Linux 那套命令：装 Git Bash 或 WSL，或者记住上面对照",
], prefix="PS> "))

outdir = pathlib.Path(__file__).parent.parent / "cli" / "shots"
print("rendering cli shots ->", outdir)
term_render.render(SCENES, outdir, height=1700)
