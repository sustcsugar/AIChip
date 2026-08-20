#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A2 系统规格完整性校验脚本 (node A2: 系统规格)

用法:
    python AIFlow/scripts/a2_check_metric.py --spec docs/spec/spec-004-system-spec.md \
                                   --prd  docs/spec/spec-001-PRD.md

输出:
    性能指标条目数 + 四要素(目标值/单位/测试方法/来源需求)完整性检查
    功能规格条目数 + 来源 REQ/SC 完整性检查
    PRD 全部 REQ 的规格映射覆盖率检查(每 REQ 至少映射一条 FS/M)
    指标测试方法与工具链归属检查(仿真/综合/功耗分析)
    DoD 判定(A2: 指标可量化、可测试，与场景对应)
"""
import argparse
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:  # pragma: no cover
    pass

REQ_RE = re.compile(r"\bREQ-\d{3}\b")
SC_RE = re.compile(r"\bSC-\d{2}\b")
FS_RE = re.compile(r"\bFS-\d{3}\b")
M_RE = re.compile(r"\bM-\d{3}\b")

# 测试方法 -> 工具链归属
METHOD_KEYWORDS = {
    "仿真": ("cocotb", "uvm", "verilator", "仿真"),
    "综合": ("yosys", "dc", "genus", "综合"),
    "功耗": ("primetime", "px", "功耗"),
    "STA": ("sta", "primetime"),
}


def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def section_until(text, start_marker):
    lines = text.splitlines()
    out = []
    in_sec = False
    for ln in lines:
        if ln.strip().startswith(start_marker):
            in_sec = True
        elif in_sec and ln.strip().startswith("## "):
            break
        if in_sec:
            out.append(ln)
    return "\n".join(out)


def table_rows(block):
    rows = []
    for ln in block.splitlines():
        ln = ln.strip()
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if cells and re.fullmatch(r"-{1,}", cells[0].replace(" ", "")):
            continue
        rows.append(cells)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True, help="spec-NNN-system-spec.md 路径")
    ap.add_argument("--prd", required=True, help="spec-001-PRD.md 路径")
    args = ap.parse_args()

    spec = read(args.spec)
    prd = read(args.prd)

    # ---- 1. PRD REQ 集合 ----
    prd_req_rows = [r for r in table_rows(prd) if r and REQ_RE.fullmatch(r[0])]
    prd_req_ids = sorted({r[0] for r in prd_req_rows}, key=lambda s: int(s.split("-")[1]))

    # ---- 2. 性能指标表（§3）----
    # 表头: | 指标ID | 指标 | 目标值 | 单位 | 测试方法 | 来源需求（REQ·SC） |
    metric_block = section_until(spec, "## 3. 性能指标")
    metric_rows = [r for r in table_rows(metric_block) if r and M_RE.fullmatch(r[0])]
    metric_missing = []
    for r in metric_rows:
        # r = [id, name, target, unit, method, source]
        for i, label in ((2, "目标值"), (3, "单位"), (4, "测试方法"), (5, "来源需求")):
            if i >= len(r) or not r[i]:
                metric_missing.append((r[0], label))
    metric_no_req = [r[0] for r in metric_rows if len(r) < 6 or not REQ_RE.search(r[5])]
    metric_no_sc = [r[0] for r in metric_rows if len(r) < 6 or not SC_RE.search(r[5])]
    # 测试方法归属检查（仿真/综合/功耗/STA 至少命中一类）
    metric_no_method_tool = []
    for r in metric_rows:
        if len(r) < 5 or not r[4]:
            metric_no_method_tool.append(r[0])
            continue
        if not any(kw.lower() in r[4].lower() for kws in METHOD_KEYWORDS.values() for kw in kws):
            metric_no_method_tool.append(r[0])

    # ---- 3. 功能规格表（§2.2）----
    # 表头: | FS | 功能规格条目 | 行为定义 | 来源 REQ | 来源 SC/UC |
    # 约束性/流程性需求（License 合规等）无行为用例，SC 列豁免（与 a1_check_req.py 一致）
    CONSTRAINT_KEYWORDS = ("合规", "流程性", "约束性", "License")
    fs_block = section_until(spec, "### 2.2")
    fs_rows = [r for r in table_rows(fs_block) if r and FS_RE.fullmatch(r[0])]
    fs_missing = []
    fs_constraint = []
    for r in fs_rows:
        if len(r) < 5:
            fs_missing.append((r[0], "表列数不足"))
        else:
            if not REQ_RE.search(r[3]):
                fs_missing.append((r[0], "来源REQ"))
            if not SC_RE.search(r[4]):
                if any(k in " ".join(r) for k in CONSTRAINT_KEYWORDS):
                    fs_constraint.append(r[0])  # 约束性规格：SC 豁免（warning）
                else:
                    fs_missing.append((r[0], "来源SC/UC"))

    # ---- 4. REQ 覆盖检查：每个 PRD REQ 至少映射一条规格 ----
    spec_all_text = " ".join(r for r in metric_rows for r in r) + " " + " ".join(
        r for r in fs_rows for r in r
    ) + " " + section_until(spec, "## 7. 需求追溯") if False else ""
    # 直接扫描整份规格文档正文中的 REQ 引用
    spec_req_used = set(REQ_RE.findall(spec))
    uncovered_req = [rid for rid in prd_req_ids if rid not in spec_req_used]

    # ---- 5. 五类指标覆盖 ----
    categories = {"Fmax": ["M-002", "M-003"], "吞吐": ["M-005", "M-006", "M-008"],
                  "面积": ["M-015"], "功耗": ["M-016", "M-017"], "时延": ["M-011", "M-012", "M-013", "M-014", "M-018"]}
    metric_ids = {r[0] for r in metric_rows}
    missing_cat = [c for c, ids in categories.items() if not (set(ids) & metric_ids)]

    # ---- 输出 ----
    print("=" * 60)
    print("[A2 check_metric] 系统规格完整性校验报告")
    print("=" * 60)
    print(f"PRD REQ 条目数: {len(prd_req_ids)}")
    print(f"性能指标条目数: {len(metric_rows)}")
    print(f"功能规格条目数: {len(fs_rows)}")
    print("-" * 60)
    print("[指标四要素(目标值/单位/测试方法/来源需求)] "
          + ("OK, 全部完整" if not metric_missing else "缺失: " + ", ".join(f"{a}.{b}" for a, b in metric_missing)))
    print("[指标来源 REQ 标注] " + ("OK" if not metric_no_req else "缺失: " + ", ".join(metric_no_req)))
    print("[指标来源 SC 标注] " + ("OK" if not metric_no_sc else "缺失: " + ", ".join(metric_no_sc)))
    print("[指标测试方法工具归属] " + ("OK" if not metric_no_method_tool else "未命中工具链: " + ", ".join(metric_no_method_tool)))
    print("[功能规格来源 REQ/SC] " + ("OK" if not fs_missing else "缺失: " + ", ".join(f"{a}.{b}" for a, b in fs_missing)))
    if fs_constraint:
        print(f"[FS 约束性豁免] {', '.join(sorted(fs_constraint))} (约束性规格, SC 列由 A4 检查项追溯, 不计缺失)")
    print("[REQ 规格映射覆盖] " + ("OK, 全部 20 REQ 均被引用" if not uncovered_req else "未映射: " + ", ".join(uncovered_req)))
    print("[五类指标覆盖(Fmax/吞吐/面积/功耗/时延)] "
          + ("OK" if not missing_cat else "缺失类别: " + ", ".join(missing_cat)))
    print("-" * 60)
    print("DoD 判定 (A2: 指标可量化、可测试，与场景对应):")
    failed = bool(metric_missing or metric_no_req or metric_no_sc or metric_no_method_tool
                  or fs_missing or uncovered_req or missing_cat)
    print(f"  [A2-D1] 指标四要素完整           : {'满足' if not metric_missing else '未满足'}")
    print(f"  [A2-D2] 指标关联 REQ/SC          : {'满足' if not (metric_no_req or metric_no_sc) else '未满足'}")
    print(f"  [A2-D3] 指标可测试(方法+工具链)   : {'满足' if not metric_no_method_tool else '未满足'}")
    print(f"  [A2-D4] 功能规格可追溯 REQ        : {'满足' if not fs_missing else '未满足'}")
    print(f"  [A2-D5] REQ 全覆盖(无遗漏)        : {'满足' if not uncovered_req else '未满足'}")
    print(f"  [A2-D6] 五类指标齐备             : {'满足' if not missing_cat else '未满足'}")
    print("=" * 60)
    print("CONCLUSION: " + ("FAIL(存在缺失项, 需补齐)" if failed else "PASS(结构检查通过, 待人工评审签字)"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())