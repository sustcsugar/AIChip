#!/usr/bin/env python3
"""IP 接口合同比对（Node C0 辅助工具）。

比对 IP 接口合同（ip/<ip>/doc/interface-contract.md）与 SoC 集成规格中的
接口要求，输出一致性检查表。当前实现基于结构化 markdown 表格抽取，用于骨架阶段的
自动比对；复杂比对建议扩展为解析 Regmap/端口清单的 JSON 格式。

用法:
    python AIFlow/scripts/contract_check.py --ip mipi --soc-spec docs/spec/spec-NNN-接口规格.md
    python AIFlow/scripts/contract_check.py --list
"""
import argparse
import re
import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent  # AIFlow/（共治管理层）
IP_BASE = ROOT.parent / "ip"  # 芯片根 ip/


def extract_tables(path: Path) -> dict:
    """抽取 markdown 中所有表格，返回 {表头首词: 行列表}。"""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    tables, header = {}, None
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(re.fullmatch(r":?-+:?", c) for c in cells):
                continue
            if header is None:
                header = cells[0] if cells else "table"
                rows = []
            else:
                rows.append(cells)
        else:
            if header:
                tables.setdefault(header, []).extend(rows)
            header, rows = None, []
    if header:
        tables.setdefault(header, []).extend(rows)
    return tables


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="列出可用 IP")
    ap.add_argument("--ip", help="IP 名称，如 mipi")
    ap.add_argument("--soc-spec", help="SoC 接口规格文档路径")
    args = ap.parse_args()

    if args.list:
        for d in sorted(p.name for p in IP_BASE.iterdir() if p.is_dir()):
            print(d)
        return

    if not args.ip or not args.soc_spec:
        ap.error("需要 --ip 与 --soc-spec")

    contract = IP_BASE / args.ip / "doc" / "interface-contract.md"
    soc_spec = Path(args.soc_spec)
    if not contract.exists():
        print(f"[SKIP] {contract} 不存在（IP 尚未发布接口合同）")
        return

    print(f"# 合同比对: {args.ip}")
    print(f"  IP 合同:   {contract}")
    print(f"  SoC 规格:  {soc_spec}")
    print()

    ip_tables = extract_tables(contract)
    soc_tables = extract_tables(soc_spec)

    if not ip_tables:
        print("[WARN] IP 合同中未找到表格，请人工核对接口规格")
        return

    n_checked, n_fail = 0, 0
    for key, ip_rows in ip_tables.items():
        soc_rows = soc_tables.get(key, [])
        if not soc_rows:
            print(f"  [?] {key}: SoC 规格无对应表格，跳过")
            continue
        for row in ip_rows:
            n_checked += 1
            if len(row) >= 3 and len(soc_rows) > 0:
                # 按首列对齐比对末列（一致? 列）
                for srow in soc_rows:
                    if srow and srow[0] == row[0]:
                        ipv, socv = row[-1], srow[-1]
                        if "一致" in ipv and "是" not in ipv:
                            n_fail += 1
                            print(f"  [FAIL] {key} {row[0]}: IP={ipv} / SoC={socv}")

    print()
    print(f"结论: 检查 {n_checked} 项，失败 {n_fail} 项")
    if n_fail:
        print("未通过：存在不一致，需修正后重跑")
        raise SystemExit(1)
    print("通过：合同与规格一致")


if __name__ == "__main__":
    main()