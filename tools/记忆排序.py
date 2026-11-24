#!/usr/bin/env python3
"""Shared-memory ranking: score every memory line and generate AI共用/记忆/MEMORY.md,
the one page every AI agent reads at the start of a session.

Usage:
  python3 记忆排序.py <vault root>          generate the file only, no git
  python3 记忆排序.py <vault root> --git    pull first, then commit and push only MEMORY.md
Each memory is one line in a topic file under AI共用/记忆/, inside a "## 记忆"
section, tagged: (类型 type: 规矩 rule | 现状 fact ｜ 重要度 importance 0.1-1.0 ｜
确认 last confirmed YYYY-MM-DD ｜ 写者 written by ｜ 来源 source).
Score = importance x freshness. Rules never decay (freshness 1); facts halve
every 30 days, because facts go stale and rules don't. A fact not confirmed for
30 days is listed as "needs re-checking". The top 15 by score are "always loaded";
the rest stay in their topic files. Full rules: AI共用/记忆规矩.md.

共用记忆排序：算每条记忆的当前分，生成 AI共用/记忆/MEMORY.md。

用法：
  python3 记忆排序.py <知识库根目录>            只生成文件，不碰 git
  python3 记忆排序.py <知识库根目录> --git      先 pull，生成后只提交 MEMORY.md 并推送

规则见 AI共用/记忆规矩.md：
  当前分 = 重要度 × 新鲜度；规矩类新鲜度恒为 1，现状类每 30 天减半。
  现状类超过 30 天没确认 → 待复核。常驻取当前分前 15 条。
"""
import re
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

常驻条数 = 15   # lines always loaded. 常驻条数
半衰天数 = 30   # half-life of a fact, in days. 现状类的半衰期
复核天数 = 30   # a fact older than this needs re-checking. 超过这么多天没确认就待复核
TZ = timezone(timedelta(hours=8))   # UTC+8

# One memory line: "- content（类型：…｜重要度：…｜确认：…｜写者：…｜来源：…）"
# 一条记忆的格式。

标签 = re.compile(
    r"^- (?P<内容>.+?)（类型：(?P<类型>规矩|现状)｜重要度：(?P<重要度>[01](?:\.\d+)?)"
    r"｜确认：(?P<确认>\d{4}-\d{2}-\d{2})｜写者：(?P<写者>[^｜]+)｜来源：(?P<来源>.+)）\s*$"
)


def 读描述(文本):
    """The `description:` from a file's front matter.  读 front matter 里的 description。"""
    m = re.match(r"^---\n(.*?)\n---\n", 文本, re.S)
    if not m:
        return ""
    for 行 in m.group(1).splitlines():
        if 行.startswith("description:"):
            return 行.split(":", 1)[1].strip().strip('"')
    return ""


def 扫描(目录, 今天):
    """Parse every topic file. Returns (memories with scores, malformed lines,
    old-format files without a "## 记忆" section, [(file, description)]).
    Malformed lines are reported, never silently dropped or guessed.
    扫描所有主题文件，算分；格式不对的列出来，不猜。"""
    记忆, 格式不对, 旧格式文件, 文件表 = [], [], [], []
    for 文件 in sorted(目录.glob("*.md")):
        if 文件.name == "MEMORY.md":
            continue
        文本 = 文件.read_text(encoding="utf-8")
        文件表.append((文件.name, 读描述(文本)))
        if "\n## 记忆" not in 文本:
            旧格式文件.append(文件.name)
            continue
        在记忆段 = False
        for 行号, 行 in enumerate(文本.splitlines(), 1):
            if 行.startswith("## "):
                在记忆段 = 行.strip() == "## 记忆"
                continue
            if not 在记忆段 or not 行.startswith("- "):
                continue
            m = 标签.match(行)
            if not m:
                格式不对.append(f"{文件.name} 第 {行号} 行")
                continue
            d = m.groupdict()
            重要度 = float(d["重要度"])
            if not 0.1 <= 重要度 <= 1.0:
                格式不对.append(f"{文件.name} 第 {行号} 行（重要度超出 0.1–1.0）")
                continue
            天数 = (今天 - date.fromisoformat(d["确认"])).days
            # Rules don't decay; facts halve every 半衰天数 days.  规矩不衰减；现状每半衰期减半。
            新鲜度 = 1.0 if d["类型"] == "规矩" else 0.5 ** (max(天数, 0) / 半衰天数)
            记忆.append({
                **d, "重要度": 重要度, "天数": 天数, "分": 重要度 * 新鲜度,
                "文件": 文件.name,
                "待复核": d["类型"] == "现状" and 天数 >= 复核天数,
            })
    return 记忆, 格式不对, 旧格式文件, 文件表


def 生成(目录, 今天):
    """Build MEMORY.md: always-loaded top lines, needs-re-checking list, format
    problems, and an index of all topic files.  生成 MEMORY.md 的全文。"""
    记忆, 格式不对, 旧格式文件, 文件表 = 扫描(目录, 今天)
    排序 = sorted(记忆, key=lambda x: (-x["分"], x["文件"]))
    出 = [
        f"# 共用记忆总目录（脚本生成，不要手改；生成于 {datetime.now(TZ):%Y-%m-%d %H:%M}）",
        "",
        "> 规矩见 `AI共用/记忆规矩.md`。要改记忆，改下面列的主题文件；这一页每天由 `工具/记忆排序/记忆排序.py` 重算。",
        "",
        f"## 常驻（当前分前 {常驻条数} 条，每次开工都读）",
        "",
    ]
    for x in 排序[:常驻条数]:
        复核 = "，待复核" if x["待复核"] else ""
        出.append(f"- {x['内容']}〔{x['分']:.2f}，{x['类型']}{复核}，见 [{x['文件'][:-3]}]({x['文件']})〕")
    if not 排序:
        出.append("- （还没有记忆）")
    出 += ["", f"## 待复核（现状类，超过 {复核天数} 天没确认；先核对再用，核完改「确认」日期）", ""]
    复核表 = [x for x in 排序 if x["待复核"]]
    出 += [f"- {x['内容']}〔{x['天数']} 天前确认，见 [{x['文件'][:-3]}]({x['文件']})〕" for x in 复核表] or ["- （没有）"]
    if 格式不对 or 旧格式文件:
        出 += ["", "## 格式要修（没参与排序）", ""]
        出 += [f"- {s}：标签格式不对" for s in 格式不对]
        出 += [f"- {s}：没有「## 记忆」段，按记忆规矩改写" for s in 旧格式文件]
    出 += ["", "## 全部主题文件", ""]
    出 += [f"- [{名[:-3]}]({名}) — {描述 or '（没写描述）'}" for 名, 描述 in 文件表]
    出 += ["", f"<!-- 共 {len(记忆)} 条记忆，常驻 {min(len(排序), 常驻条数)} 条，待复核 {len(复核表)} 条 -->", ""]
    return "\n".join(出)


def 去掉时间(文本):
    """Drop the "generated at" timestamp, so an unchanged page isn't rewritten
    (and committed) every day.  去掉生成时间，内容没变就不重写、不提交。"""
    return re.sub(r"生成于 [^）]*）", "", 文本)


def git(根, *参数):
    """Run git in the vault, capturing output.  在知识库里跑 git。"""
    return subprocess.run(["git", "-C", str(根), *参数], capture_output=True, text=True)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    根 = Path(sys.argv[1]).expanduser()
    用git = "--git" in sys.argv
    目录 = 根 / "AI共用" / "记忆"
    目标 = 目录 / "MEMORY.md"
    相对 = "AI共用/记忆/MEMORY.md"

    # With --git, skip this run instead of fighting another writer: a git lock,
    # local edits to MEMORY.md, or a pull that isn't a fast-forward.
    # --git 时遇到 git 锁、MEMORY.md 有本地改动、pull 不能快进，都跳过这次，不硬来。
    if 用git:
        if (根 / ".git" / "index.lock").exists():
            print("有 git 锁，跳过这次"); return
        if git(根, "status", "--porcelain", "--", 相对).stdout.strip():
            print("MEMORY.md 有没提交的改动，跳过这次"); return
        r = git(根, "pull", "--ff-only", "-q")
        if r.returncode != 0:
            print("git pull 失败，跳过这次：", r.stderr.strip()); return

    新 = 生成(目录, datetime.now(TZ).date())
    旧 = 目标.read_text(encoding="utf-8") if 目标.exists() else ""
    if 去掉时间(新) == 去掉时间(旧):
        print("内容没变，不写"); return
    目标.write_text(新, encoding="utf-8")
    print("已生成", 目标)

    if 用git:
        git(根, "add", "--", 相对)
        r = git(根, "commit", "-q", "-m", f"记忆排序：{datetime.now(TZ):%Y-%m-%d}", "--", 相对)
        if r.returncode != 0:
            print("提交失败：", r.stderr.strip()); return
        r = git(根, "push", "-q")
        print("已提交并推送" if r.returncode == 0 else "已提交，推送失败：" + r.stderr.strip())


if __name__ == "__main__":
    main()
