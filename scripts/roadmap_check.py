#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验 state/state-roadmap.md 的结构（RT 编号唯一/连续、字段齐全、状态与分类合法）。

用法:
    python scripts/roadmap_check.py            # 校验全部
    python scripts/roadmap_check.py --node RT-001   # 指定条目

退出码: 0 = 通过, 1 = 有错误
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROADMAP = ROOT / "state" / "state-roadmap.md"

FIELDS = ["标题", "分类", "状态", "来源", "动机", "方案概述", "期望收益", "影响范围", "关联", "处置建议"]
STATUS = {"idea", "planned", "in_progress", "adopted", "deferred", "rejected"}
CATEGORY = {"下一版增强", "架构备选", "流程改进", "技术预研"}

ENTRY_RE = re.compile(r"^###\s+(RT-\d+)\s+—\s*(.+)$")
FIELD_RE = re.compile(r"^-\s*([^：:]+)[：:]\s*(.*)$")


def parse_entries(text):
    entries = {}
    current = None
    for ln in text.splitlines():
        m = ENTRY_RE.match(ln.strip())
        if m:
            current = m.group(1)
            entries[current] = {"title": m.group(2).strip(), "fields": {}}
            continue
        if current:
            fm = FIELD_RE.match(ln.strip())
            if fm:
                entries[current]["fields"][fm.group(1).strip()] = fm.group(2).strip()
    return entries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", help="只校验指定 RT 编号")
    args = ap.parse_args()

    if not ROADMAP.exists():
        print(f"FATAL: roadmap 不存在: {ROADMAP}")
        return 1

    text = ROADMAP.read_text(encoding="utf-8")
    entries = parse_entries(text)

    if not entries:
        print("FAIL: roadmap 中没有任何 RT 条目")
        return 1

    ids = list(entries.keys())
    nums = sorted(int(i.split("-")[1]) for i in ids)
    errors = []

    # 编号唯一 + 连续（全局递增）
    if len(set(ids)) != len(ids):
        errors.append("RT 编号存在重复")
    expected = list(range(1, len(ids) + 1))
    if nums != expected:
        errors.append(f"RT 编号不连续: 实际 {nums}, 期望 {expected}")

    target = {args.node} if args.node else set(ids)
    for rid, ent in entries.items():
        if rid not in target:
            continue
        for f in FIELDS:
            if f not in ent["fields"] or not ent["fields"][f]:
                errors.append(f"{rid}: 缺少字段 [{f}]")
        st = ent["fields"].get("状态", "").split("（")[0].strip()
        if st and st not in STATUS:
            errors.append(f"{rid}: 状态 '{st}' 非法, 应为 {sorted(STATUS)}")
        cat = ent["fields"].get("分类", "").split("（")[0].strip()
        if cat and cat not in CATEGORY:
            errors.append(f"{rid}: 分类 '{cat}' 非法, 应为 {sorted(CATEGORY)}")

    if errors:
        print("FAIL:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"检查通过: {len(entries)} 个 RT 条目, 编号唯一连续, 字段/状态/分类合法")
    return 0


if __name__ == "__main__":
    sys.exit(main())
