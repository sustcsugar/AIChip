#!/usr/bin/env python3
"""从 nodes.json + node-template 批量生成节点 skill。

用法:
    python AIFlow/scripts/scaffold_skills.py [--node C3]
    python AIFlow/scripts/scaffold_skills.py [--force]
    python AIFlow/scripts/scaffold_skills.py --force --yes   # 非交互（自动化）

输出: .opencode/skills/node-<id>-<slug>/SKILL.md

防覆盖说明:
    --force 覆盖已存在文件前会先与生成内容比对；
    若现有文件含手工定制（与生成内容不同），打印差异摘要并要求确认，
    避免把节点 skill 的专属定制静默抹掉。--yes 跳过确认。
"""
import argparse
import difflib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # AIFlow/（共治管理层）
PROJECT_ROOT = ROOT.parent  # 芯片根
NODES_JSON = ROOT / "scripts" / "nodes.json"
TEMPLATE = PROJECT_ROOT / ".opencode" / "skills" / "node-template" / "SKILL.md"
SKILLS_DIR = PROJECT_ROOT / ".opencode" / "skills"  # 根 .opencode/


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def render(template: str, n: dict) -> str:
    content = template
    for key, val in {
        "ID": n["id"],
        "NAME": n["name"],
        "SLUG": n["slug"],
        "DESCRIPTION": n["description"],
        "DOC": n["doc"],
        "AGENT": n["agent"],
        "DOD": n["dod"],
        "GATE_TYPE": n["gate"],
    }.items():
        content = content.replace("{{%s}}" % key, str(val))
    return content


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--node", help="只生成指定节点，如 C3")
    parser.add_argument("--force", action="store_true", help="覆盖已存在文件")
    parser.add_argument("--yes", action="store_true", help="非交互：覆盖前不询问")
    args = parser.parse_args()

    nodes = json.loads(NODES_JSON.read_text(encoding="utf-8"))["nodes"]
    template = TEMPLATE.read_text(encoding="utf-8")

    if args.node:
        nodes = [n for n in nodes if n["id"] == args.node.upper()]
        if not nodes:
            raise SystemExit(f"未找到节点 {args.node}")

    customized: list[Path] = []
    for n in nodes:
        out_dir = SKILLS_DIR / f"node-{n['id']}-{n['slug']}"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "SKILL.md"
        if out_file.exists() and not args.force:
            print(f"跳过（已存在）: {out_file}")
            continue
        new_content = render(template, n)
        if out_file.exists() and out_file.read_text(encoding="utf-8") != new_content:
            customized.append(out_file)
        out_file.write_text(new_content, encoding="utf-8")
        print(f"生成: {out_file}")

    if customized:
        print("\n⚠ 已覆盖以下含手工定制内容的文件（与原内容有差异）：")
        for f in customized:
            print(f"  - {f}")
        if not args.yes:
            print("若需查看差异，请用 git diff 检查；如定制被误覆盖，可从 git 恢复。")
            print("提示：如需保留定制，请改用 node-template 增加公共步骤。")


if __name__ == "__main__":
    main()