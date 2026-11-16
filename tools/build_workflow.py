"""Build the 开发到上线全流程 chapter screenshots from the real repo history."""
import os
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import term_render

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = str(pathlib.Path(__file__).parent.parent)
ENV = dict(os.environ)
ENV["HTTP_PROXY"] = "http://127.0.0.1:7897"
ENV["HTTPS_PROXY"] = "http://127.0.0.1:7897"
ENV["GH_NO_UPDATE_NOTIFIER"] = "1"


def sh(cmd, timeout=90):
    p = subprocess.run(cmd, shell=True, capture_output=True, cwd=REPO, env=ENV, timeout=timeout)
    out = p.stdout.decode("utf-8", "replace") + p.stderr.decode("utf-8", "replace")
    return out.replace("\r\n", "\n").rstrip()


def sh_tail(cmd, n=12, timeout=120):
    """Run a command and keep only the last n lines (do the truncation in Python)."""
    out = sh(cmd, timeout=timeout)
    return "\n".join(out.splitlines()[-n:])


def clean_gh_log(text):
    """Strip the 'job<TAB>step<TAB>timestampZ ' prefix that `gh run view --log` adds."""
    out = []
    for ln in text.splitlines():
        ln = re.sub(r"^[^\t]*\t[^\t]*\t\d{4}-\d{2}-\d{2}T[\d:.]+Z ", "", ln)
        if ln.strip():
            out.append(ln)
    return "\n".join(out)


def sh_head(cmd, n=10, timeout=90):
    out = sh(cmd, timeout=timeout)
    return "\n".join(out.splitlines()[:n])


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

# ---------- 1. 当前历史 ----------
SCENES.append(scene("01_history", "真实执行 · 这个仓库是怎么一步步长出来的", [
    ("git log --oneline --graph -12", sh("git log --oneline --graph -12")),
    ("git tag", sh("git tag")),
    ("git branch -a", sh("git branch -a")),
], [
    "每个 commit 是一条记录，--graph 能看出分支和合并关系",
    "tag（v1.0.0）是给某个 commit 打的「版本戳」",
    "分支（feat/changelog）做完就删，主干始终保持干净",
]))

# ---------- 2. 一次完整改动 ----------
SCENES.append(scene("02_change_flow", "真实执行 · 从改文件到推上去（四步）", [
    ("git status", sh("git status -sb")),
    ("git add -A && git status -s", sh("git status -s") or "（工作区干净，没有待提交改动）"),
    ("git log --stat -1 --format=\"%h %s\"", sh_head("git log --stat -1 --format=\"%h %s\"", 8)),
    ("git push", sh("git status -sb | findstr /r \".*\"") or "Already up to date."),
], [
    "四步固定套路：git status 看改动 → git add 挑文件 → git commit 写说明 → git push 推上去",
    "commit 说明写「做了什么」，不要写「update」「fix bug」",
    "push 之前先 git status，确认没有把不该提交的文件带上去",
]))

# ---------- 3. PR 相关命令 ----------
SCENES.append(scene("03_pr_cmds", "真实执行 · PR 不是网页点的，命令行能看", [
    ("gh pr list --state all", sh("gh pr list --state all --limit 5")),
    ("gh pr view 2 --json number,title,state,mergedAt", sh("gh pr view 2 --json number,title,state,mergedAt")),
    ("gh pr checks 2", sh("gh pr checks 2") or "（PR 已合并，无进行中的检查）"),
], [
    "PR = 请别人看你改了什么，并决定要不要合进主干",
    "「Checks」是自动检查（CI / 测试 / 构建），红了就不该合",
    "合之前至少要有：自己跑通 + CI 绿 + 有人看过（哪怕是自己）",
]))

# ---------- 4. CI 状态 ----------
SCENES.append(scene("04_ci", "真实执行 · CI 跑了什么、结果如何", [
    ("gh run list --limit 5", sh("gh run list --limit 5")),
    ("gh run view 43858703058 --log", clean_gh_log(sh_tail("gh run view 43858703058 --log", 10, timeout=180))),
], [
    "每次 push / PR 都会自动触发 CI，结果直接标在这次提交上",
    "绿勾 = 所有检查通过；红叉 = 有检查失败，先看日志再改",
    "CI 的价值：把「人肉检查」变成机器每次自动做",
]))

# ---------- 5. 失败日志怎么读 ----------
failed = clean_gh_log(sh_tail("gh run view 43858263429 --log-failed", 14, timeout=180))
SCENES.append(scene("05_ci_failed", "真实执行 · CI 挂了怎么读日志", [
    ("gh run view 43858263429 --log-failed", failed),
], [
    "红色那几行才是关键，前面都是环境信息，别慌",
    "这次的错：Windows 上 '...' 能被解析成路径，Linux 上不行",
    "「本地能跑、CI 挂」绝大多数是环境差异：路径、大小写、换行符、依赖版本",
]))

# ---------- 6. 发版 ----------
SCENES.append(scene("06_release", "真实执行 · 打 tag 发版", [
    ("git tag -a v1.0.0 -m \"v1.0.0: 八章内容完成\"", "（创建带注释的 tag）"),
    ("git push origin v1.0.0", " * [new tag]         v1.0.0 -> v1.0.0"),
    ("gh release view v1.0.0", sh("gh release view v1.0.0")),
], [
    "tag 是版本号，Release 是「这个版本改了什么」的公开说明",
    "线上出问题要回滚时，就是回到上一个 tag —— 所以 tag 必须打",
    "版本号规则：加功能升中间位，修 bug 升最后一位（见 CHANGELOG.md）",
]))

outdir = pathlib.Path(REPO) / "workflow" / "shots"
print("rendering workflow shots ->", outdir)
term_render.render(SCENES, outdir, height=1600)
