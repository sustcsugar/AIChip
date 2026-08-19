#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A1 需求完整性校验脚本 (node A1: 需求与场景定义)

用法:
    python scripts/a1_check_req.py --prd work/soc/docs/spec/PRD.md \
                                --scen work/soc/docs/spec/use-cases.md \
                                [--oi work/soc/docs/spec/open-issues.md]

输出:
    REQ/SC/UC/OI 条目数
    open issue 列表
    未被任何 UC 覆盖的 REQ (遗漏列表)
    无 UC 覆盖的 SC (遗漏列表)
    正常/边界/异常 路径统计
    REQ ID 唯一性检查
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
# UC 编号二级结构: UC-<功能域>-NNN（功能域 = 短 slug，英文可含下划线；同域内 3 位递增）
# 负例保持不放松: 旧扁平格式 UC-001 / UC-01 等均不匹配（无功能域段或非 3 位序号）
UC_RE = re.compile(r"\bUC-[A-Z][A-Z0-9_]*-\d{3}\b")
OI_RE = re.compile(r"\bOI-\d{3}\b")

# 约束性/流程性需求关键词：此类需求不要求行为用例覆盖（由检查项追溯）
CONSTRAINT_KEYWORDS = ("合规", "流程性", "约束性", "License")


def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def section_until(text, start_marker):
    """返回从 start_marker 所在行起，到下一个 '## ' 节标题为止的文本块。"""
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
    """提取 markdown 表格数据行（跳过表头/分隔行/非表格行）。"""
    rows = []
    for ln in block.splitlines():
        ln = ln.strip()
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if cells and re.fullmatch(r"-{1,}", cells[0].replace(" ", "")):  # 分隔行
            continue
        rows.append(cells)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prd", required=True, help="PRD.md 路径")
    ap.add_argument("--scen", required=True, help="use-cases.md 路径")
    ap.add_argument("--oi", default=None, help="open-issues.md 路径")
    args = ap.parse_args()

    prd = read(args.prd)
    scen = read(args.scen)
    oi_text = read(args.oi) if args.oi else ""

    # ---- 1. REQ 集合（PRD 表格中所有 REQ 行）----
    req_rows = [r for r in table_rows(prd) if r and REQ_RE.fullmatch(r[0])]
    req_ids = [r[0] for r in req_rows]
    req_dup = sorted({x for x in req_ids if req_ids.count(x) > 1})

    # ---- 2. SC 集合（use-cases 场景清单节）----
    scen_block = section_until(scen, "## 1. 场景清单（SC）")
    sc_rows = [r for r in table_rows(scen_block) if r and SC_RE.fullmatch(r[0])]
    sc_ids = [r[0] for r in sc_rows]

    # ---- 3. UC 集合（use-cases 用例清单节）----
    uc_block = section_until(scen, "## 2. 用例清单（UC）")
    uc_rows = [r for r in table_rows(uc_block) if r and UC_RE.fullmatch(r[0])]
    # 用例表头: | UC | 名称 | 路径 | 关联 SC | 关联 REQ | 前置 | 步骤 | 期望结果 |
    uc_info = []  # (uc_id, path, sc_refs, req_refs, row)
    for r in uc_rows:
        uc_id = r[0]
        path = r[2] if len(r) > 2 else ""
        sc_refs = set(SC_RE.findall(r[3])) if len(r) > 3 else set()
        req_refs = set(REQ_RE.findall(r[4])) if len(r) > 4 else set()
        uc_info.append((uc_id, path, sc_refs, req_refs, r))
    uc_ids = [u[0] for u in uc_info]
    uc_dup = sorted({x for x in uc_ids if uc_ids.count(x) > 1})

    # ---- 4. OI 集合（仅"开放问题清单"节中状态为 open 的条目；
    #            已关闭登记表中的 OI 引用不视为未决）----
    oi_block = section_until(oi_text, "## 1. 开放问题清单")
    oi_rows = [r for r in table_rows(oi_block) if r and OI_RE.fullmatch(r[0])]
    oi_ids = sorted(
        {r[0] for r in oi_rows if len(r) > 4 and r[4].strip().lower() == "open"},
        key=lambda s: int(s.split("-")[1]),
    )

    # ---- 检查：SC 至少 1 个 UC 覆盖 ----
    uc_sc_all = set()
    for _, _, sc_refs, _, _ in uc_info:
        uc_sc_all |= sc_refs
    orphan_sc = [s for s in sc_ids if s not in uc_sc_all]

    # ---- 检查：REQ 至少 1 个 UC 覆盖（约束性需求豁免）----
    uc_req_all = set()
    for _, _, _, req_refs, _ in uc_info:
        uc_req_all |= req_refs
    req_constraint = set()
    req_orphan = []
    for rid, row in zip(req_ids, req_rows):
        if rid not in uc_req_all:
            if any(k in " ".join(row) for k in CONSTRAINT_KEYWORDS):
                req_constraint.add(rid)  # 约束性需求：豁免（warning）
            else:
                req_orphan.append(rid)

    # ---- 路径统计 ----
    path_count = {"正常": 0, "边界": 0, "异常": 0}
    for _, path, _, _, _ in uc_info:
        if path in path_count:
            path_count[path] += 1
        else:
            path_count["异常"] = path_count.get("异常", 0)  # 未知路径计入异常组之外
    # 未知路径单独统计
    unknown_paths = [p for _, p, _, _, _ in uc_info if p not in ("正常", "边界", "异常")]

    # ---- 输出 ----
    print("=" * 60)
    print("[A1 check_req] 需求完整性校验报告")
    print("=" * 60)
    print(f"REQ 条目数: {len(req_ids)}")
    print(f"SC  场景数: {len(sc_ids)}")
    print(f"UC  用例数: {len(uc_info)}")
    print(f"OI  open issue 数: {len(oi_ids)} ({', '.join(oi_ids) if oi_ids else '无'})")
    print("-" * 60)
    print("路径分布:", {k: v for k, v in path_count.items()},
          ("未知路径=" + str(unknown_paths)) if unknown_paths else "")
    print("路径分布(异常含未知):", path_count)
    print("-" * 60)
    print("[REQ ID 唯一性] " + ("重复: " + ", ".join(req_dup) if req_dup else "OK"))
    print("[UC ID 唯一性] " + ("重复: " + ", ".join(uc_dup) if uc_dup else "OK, 均符合 UC-<功能域>-NNN 且唯一"))
    print("[SC -> UC 覆盖] " + ("遗漏 SC: " + ", ".join(orphan_sc) if orphan_sc else "OK, 所有 SC 均有 UC 覆盖"))
    print("[REQ -> UC 覆盖] " + ("遗漏 REQ: " + ", ".join(req_orphan) if req_orphan else "OK, 无行为类 REQ 遗漏"))
    if req_constraint:
        print(f"[REQ 约束性豁免] {', '.join(sorted(req_constraint))} (流程性需求, 由检查项追溯, 不计遗漏)")
    print("-" * 60)
    print("DoD 判定:")
    failed = bool(oi_ids or orphan_sc or req_orphan or req_dup or uc_dup or unknown_paths)
    oi_status = "未满足" if oi_ids else "满足"
    sc_status = "未满足" if orphan_sc else "满足"
    req_status = "未满足" if req_orphan else "满足"
    print(f"  [A1-D1] 场景无未决 open issue : {oi_status} (当前 open {len(oi_ids)} 项, 须人工答复关闭)")
    print(f"  [A1-D2] 用例覆盖主要使用模式 : {sc_status} (每个 SC 均有 UC)")
    print(f"  [A1-D3] REQ 至少 1 UC 覆盖    : {req_status}")
    print(f"  [A1-D4] REQ ID 唯一规范        : {'满足' if not req_dup else '未满足'}")
    print(f"  [A1-D5] 正常/边界/异常三类齐全 : {'满足' if all(path_count.values()) else '未满足'}")
    print("=" * 60)
    print("CONCLUSION: " + ("FAIL(有未决 OI / 遗漏)" if failed else "PASS(结构检查通过, 待人工评审签字)"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
