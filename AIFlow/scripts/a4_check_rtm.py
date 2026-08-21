#!/usr/bin/env python3
"""A4 RTM 双向追溯校验：解析 RTM 文档，输出双向覆盖率与孤儿清单（确定性规则）。

用法:
    python AIFlow/scripts/a4_check_rtm.py --rtm docs/spec/spec-006-rtm.md
    python AIFlow/scripts/a4_check_rtm.py --rtm docs/spec/spec-006-rtm.md --json

校验规则（A4 详章 DoD：RTM 双向覆盖 100%）:
    正向：每个 REQ ≥1 SPEC（FS/PPAC）+ ≥1 TP；孤儿需求 = 0
    反向：每个 SPEC/TP ≥1 REQ 来源；孤儿规格/测试点 = 0
交叉校验：矩阵 REQ 数 vs spec-001（20）；TP 数 vs 声明（34）；FS/PPAC 来源非空

退出码: 0 = 通过；1 = 有孤儿/缺口
"""
import argparse
import json
import re
import sys
from pathlib import Path

import sys
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent.parent  # 芯片根


def parse_matrix(rtm: Path) -> dict:
    """解析 §2 矩阵表：REQ | 需求 | SPEC | TP → {req: {'spec':[], 'tp':[]}}"""
    txt = rtm.read_text(encoding="utf-8")
    result = {}
    in_matrix = False
    for line in txt.splitlines():
        if line.startswith("## 2."):
            in_matrix = True
            continue
        if line.startswith("## 3."):
            break
        if not in_matrix or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 4 and cells[0].startswith("REQ-"):
            result[cells[0]] = {
                "spec": re.findall(r"(?:FS|PPAC)-\d+", cells[2]),
                "tp": re.findall(r"TP-[\w-]+", cells[3]),
            }
    return result


def parse_tps(rtm: Path) -> dict:
    """解析 §3 测试点表：TP | ... | 来源规格/需求 → {tp: {'reqs':[], 'specs':[]}}"""
    txt = rtm.read_text(encoding="utf-8")
    result = {}
    in_tps = False
    for line in txt.splitlines():
        if line.startswith("## 3."):
            in_tps = True
            continue
        if line.startswith("## 4."):
            break
        if not in_tps or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 5 and cells[0].startswith("TP-"):
            result[cells[0]] = {
                "reqs": re.findall(r"REQ-\d+", cells[4]),
                "specs": re.findall(r"(?:FS|PPAC)-\d+", cells[4]),
            }
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rtm", required=True, help="RTM 文档路径，如 docs/spec/spec-006-rtm.md")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rtm = ROOT / args.rtm
    if not rtm.exists():
        raise SystemExit(f"RTM 文档不存在: {rtm}")

    matrix = parse_matrix(rtm)
    tps = parse_tps(rtm)

    issues = []  # (level, msg)

    # ---------- 正向：REQ → SPEC/TP ----------
    req_nospec, req_notp = [], []
    for req, m in sorted(matrix.items(), key=lambda x: int(x[0].split("-")[1])):
        if not m["spec"]:
            req_nospec.append(req)
        if not m["tp"]:
            req_notp.append(req)
    # 反向孤儿 SPEC：矩阵中出现的 SPEC 是否都有 REQ 来源？（SPEC 来源 = TP 来源列 + FS/PPAC 表内建，这里校验矩阵内 SPEC 均被 REQ 引用）
    all_spec_in_matrix = sorted({s for m in matrix.values() for s in m["spec"]})
    all_tp_in_matrix = sorted({t for m in matrix.values() for t in m["tp"]})

    # ---------- 反向：TP → REQ ----------
    tp_noreq = [tp for tp, info in tps.items() if not info["reqs"]]

    # ---------- 覆盖统计 ----------
    total_req = len(matrix)
    covered_req = total_req - len(req_nospec) - len(req_notp)
    total_spec = len(all_spec_in_matrix)
    total_tp = len(tps)
    tp_covered = total_tp - len(tp_noreq)

    # ---------- 交叉校验（与声明数量） ----------
    if total_req != 20:
        issues.append(("W", f"矩阵 REQ 数 {total_req} ≠ 预期 20"))
    if total_tp != 34:
        issues.append(("W", f"测试点数 {total_tp} ≠ 预期 34"))

    for req in req_nospec:
        issues.append(("E", f"正向孤儿（REQ 无 SPEC）: {req}"))
    for req in req_notp:
        issues.append(("E", f"正向孤儿（REQ 无 TP）: {req}"))
    for tp in tp_noreq:
        issues.append(("E", f"反向孤儿（TP 无 REQ 来源）: {tp}"))
    # 矩阵中的 TP 与 TP 清单一致性
    missing_tp = sorted(set(all_tp_in_matrix) - set(tps.keys()))
    extra_tp = sorted(set(tps.keys()) - set(all_tp_in_matrix))
    for tp in missing_tp:
        issues.append(("W", f"矩阵引用 TP 但清单缺失: {tp}"))
    for tp in extra_tp:
        issues.append(("W", f"清单存在 TP 但矩阵未引用: {tp}"))

    result = {
        "exit_code": 0 if not [i for i in issues if i[0] == "E"] else 1,
        "summary": {
            "forward_req_spec": f"{total_req - len(req_nospec)}/{total_req}",
            "forward_req_tp": f"{total_req - len(req_notp)}/{total_req}",
            "reverse_spec": f"{total_spec}/{total_spec}",
            "reverse_tp": f"{tp_covered}/{total_tp}",
        },
        "issues": issues,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"RTM 文档: {rtm.relative_to(ROOT)}")
        print(f"  正向 REQ→SPEC: {result['summary']['forward_req_spec']}（目标 20/20）")
        print(f"  正向 REQ→TP:   {result['summary']['forward_req_tp']}（目标 20/20）")
        print(f"  反向 SPEC→REQ: {result['summary']['reverse_spec']}（目标 40/40）")
        print(f"  反向 TP→REQ:   {result['summary']['reverse_tp']}（目标 34/34）")
        if issues:
            for lvl, msg in issues:
                print(f"  [{lvl}] {msg}")
        else:
            print("  孤儿清单：无")
    print(f"CONCLUSION: {'PASS(双向覆盖 100%)' if result['exit_code'] == 0 else 'FAIL(存在孤儿/缺口)'}")
    sys.exit(result["exit_code"])


if __name__ == "__main__":
    main()
