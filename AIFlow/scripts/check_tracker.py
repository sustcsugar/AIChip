#!/usr/bin/env python3
"""校验 AIFlow/state/state-tracker.md 节点状态与前后置条件。

用法:
    python AIFlow/scripts/check_tracker.py                    # 检查全部节点
    python AIFlow/scripts/check_tracker.py --node C3          # 指定节点
    python AIFlow/scripts/check_tracker.py --summary          # 只看状态汇总

tracker.md 格式（每节点一节）:
```
## C3 RTL编码
- 状态: in_progress | waiting_review | passed | iterating
- 前置: A5, B6, C2   (必须 passed 的节点)
- 收敛指标: ...
```
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACKER = ROOT / "state" / "state-tracker.md"
NODES_JSON = ROOT / "scripts" / "nodes.json"


def parse_tracker() -> dict:
    if not TRACKER.exists():
        raise SystemExit(f"tracker 不存在: {TRACKER}")
    text = TRACKER.read_text(encoding="utf-8")
    sections = {}
    current = None
    for line in text.splitlines():
        m = re.match(r"^##\s+(\S+)\s+(.*)$", line.strip())
        if m:
            current = m.group(1)
            sections[current] = {"title": m.group(2), "status": None, "deps": []}
            continue
        if current:
            sm = re.match(r"^-\s*状态:\s*(\w+)", line.strip())
            if sm:
                sections[current]["status"] = sm.group(1)
            dm = re.match(r"^-\s*前置:\s*(.*)$", line.strip())
            if dm:
                raw = dm.group(1).strip()
                deps = [d.strip() for d in raw.split(",") if d.strip()]
                # 前置为"无/TBD/None/—"等非节点 ID 文本时视为无依赖
                if not deps or deps[0] in ("无", "TBD", "None", "-", "—"):
                    deps = []
                sections[current]["deps"] = deps
    return sections


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", help="指定节点 ID")
    ap.add_argument("--summary", action="store_true")
    args = ap.parse_args()

    all_sections = parse_tracker()
    if args.node:
        sections = {k: v for k, v in all_sections.items() if k.startswith(args.node.upper())}
    else:
        sections = all_sections

    if args.summary:
        for node, sec in sections.items():
            st = sec["status"] or "unknown"
            print(f"{node:<8} {st:<16} {sec['title']}")
        return

    errors = []
    for node, sec in sections.items():
        if sec["status"] is None:
            errors.append(f"{node}: 缺少状态字段")
            continue
        if sec["status"] in ("passed", "waiting_review"):
            for dep in sec["deps"]:
                d = all_sections.get(dep)
                if d is None:
                    errors.append(f"{node}: 前置节点 {dep} 未在 tracker 中定义")
                elif d["status"] != "passed":
                    errors.append(f"{node}: 前置节点 {dep} 状态为 {d['status']}，需 passed")

    if errors:
        print("检查未通过：")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print(f"检查通过：{len(sections)} 个节点前后置条件满足")


if __name__ == "__main__":
    main()