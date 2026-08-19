#!/usr/bin/env python3
"""从 nodes.json + node-template 批量生成节点 skill。

用法:
    python scripts/scaffold_skills.py [--node C3]
    python scripts/scaffold_skills.py [--force]

输出: .opencode/skills/node-<id>-<slug>/SKILL.md
"""
import argparse
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NODES_JSON = ROOT / "scripts" / "nodes.json"
TEMPLATE = ROOT / ".opencode" / "skills" / "node-template" / "SKILL.md"
SKILLS_DIR = ROOT / ".opencode" / "skills"


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--node", help="只生成指定节点，如 C3")
    parser.add_argument("--force", action="store_true", help="覆盖已存在文件")
    args = parser.parse_args()

    nodes = json.loads(NODES_JSON.read_text(encoding="utf-8"))["nodes"]
    template = TEMPLATE.read_text(encoding="utf-8")

    if args.node:
        nodes = [n for n in nodes if n["id"] == args.node.upper()]
        if not nodes:
            raise SystemExit(f"未找到节点 {args.node}")

    for n in nodes:
        out_dir = SKILLS_DIR / f"node-{n['id']}-{n['slug']}"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "SKILL.md"
        if out_file.exists() and not args.force:
            print(f"跳过（已存在）: {out_file}")
            continue
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
        out_file.write_text(content, encoding="utf-8")
        print(f"生成: {out_file}")


if __name__ == "__main__":
    main()