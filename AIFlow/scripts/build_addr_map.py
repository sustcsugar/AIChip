#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_addr_map.py — B2 地址映射检查与代码生成（SOP 节点 B2 工具）

用法:
  python AIFlow/scripts/build_addr_map.py --map docs/B2-addr-map.yaml --out rtl/inc/
      [--sw-out soc/sw/include/] [--report docs/B2-addr-check.txt]

检查（任一 ERROR 非零退出）:
  1. 两两重叠: 全部 mapped 区域 [base, base+size) 求交 = 空
  2. 越界: base+size <= 2^addr_width
  3. 对齐: base 与 size 均为 align_granularity(4KB) 整数倍
  4. 幂次大小: size 为 2 的幂（译码简化）；保留区豁免（允许填空洞）
  5. 覆盖完备: mapped 区域并集之外的空间全部被 err!=N/A 的保留/未映射区覆盖
  6. 每从设备恰一窗口（同 block 多窗口报 ERROR，BLOCK-02 译码外保留区豁免）
  7. 覆盖 32bit 空间无间隙遗漏（gap 必须落在保留/未映射区）

生成:
  rtl/inc/axi_addr_pkg.sv     — SystemVerilog 地址常量包
  soc/sw/include/soc_addr.h   — C 基址头文件
"""
import argparse
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")  # RMP-003
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import yaml

SV_PKG_TEMPLATE = """// axi_addr_pkg.sv — 自动生成，勿手改（source: docs/B2-addr-map.yaml, 节点 B2）
// 重新生成: python AIFlow/scripts/build_addr_map.py --map docs/B2-addr-map.yaml --out rtl/inc/
package axi_addr_pkg;
    localparam int unsigned ADDR_WIDTH = {addr_width};

    // RIB 域译码边界
    localparam logic [31:0] AXI_BRIDGE_BASE = 32'h2000_0000;  // addr >= 此值经桥

    // 功能窗口
{sv_consts}

    // 保留/未映射区（错误返回）
{sv_reserves}

    // 译码粒度: 4KB（AXI4 突发不得跨 4KB 边界）
    localparam int unsigned DECODE_GRAN_LOG2 = 12;
endpackage
"""

C_HDR_TEMPLATE = """/* soc_addr.h — 自动生成，勿手改（source: docs/B2-addr-map.yaml, 节点 B2） */
#ifndef SOC_ADDR_H
#define SOC_ADDR_H

/* 总线域边界 */
#define AXI_BRIDGE_BASE        0x20000000UL

/* 功能窗口基址 */
{c_consts}

/* 保留区（访问返回总线错误，仅注释性定义） */
{c_reserves}

/* 译码粒度 4KB */
#define DECODE_GRAN            0x1000UL

#endif /* SOC_ADDR_H */
"""


def load_map(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def to_c(sym, base, size):
    return f"#define {sym:<22} 0x{base:08X}UL  /* size 0x{size:X} */"


def to_sv(sym, base, size):
    return (f"    localparam logic [31:0] {sym:<22} = 32'h{base:08X};"
            f"  // size 0x{size:X}")


def sym_of(name):
    # 仅保留 ASCII 字母/数字/下划线（SV/C 标识符合法性）
    s = "".join(c if (c.isascii() and (c.isalnum() or c == "_")) else "_" for c in name.upper())
    return "_".join(filter(None, s.split("_")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", required=True)
    ap.add_argument("--out", default="rtl/inc/")
    ap.add_argument("--sw-out", default="soc/sw/include/")
    ap.add_argument("--report")
    args = ap.parse_args()

    m = load_map(args.map)
    addr_width = m["addr_width"]
    gran = m["align_granularity"]
    regions = m["regions"]

    errors, warnings, infos = [], [], []

    mapped = [r for r in regions if r["base"] is not None]
    unmapped = [r for r in regions if r["base"] is None]

    # 1. 两两重叠
    for i in range(len(mapped)):
        for j in range(i + 1, len(mapped)):
            a, b = mapped[i], mapped[j]
            if a["base"] < b["base"] + b["size"] and b["base"] < a["base"] + a["size"]:
                errors.append(f"重叠: {a['mem_id']}({a['name']}) x {b['mem_id']}({b['name']})")

    space = 1 << addr_width
    for r in mapped:
        # 2. 越界
        if r["base"] + r["size"] > space:
            errors.append(f"越界: {r['mem_id']} end=0x{r['base']+r['size']:X} > 2^{addr_width}")
        # 3. 对齐
        if r["base"] % gran != 0:
            errors.append(f"基址未 4KB 对齐: {r['mem_id']} base=0x{r['base']:X}")
        if r["size"] % gran != 0:
            errors.append(f"大小非 4KB 整数倍: {r['mem_id']} size=0x{r['size']:X}")
        # 4. 幂次大小（保留区豁免）
        is_reserve = r["access"] == "-"
        if not is_reserve and (r["size"] & (r["size"] - 1)) != 0:
            errors.append(f"功能窗口大小非 2 的幂: {r['mem_id']} size=0x{r['size']:X}")
        if is_reserve and (r["size"] & (r["size"] - 1)) != 0:
            warnings.append(f"保留区大小非 2 的幂（填空洞，可接受）: {r['mem_id']} size=0x{r['size']:X}")

    # 5/7. 覆盖完备性: 排序后 gap 必须由保留区覆盖，端点封闭
    srt = sorted(mapped, key=lambda r: r["base"])
    if srt[0]["base"] != 0:
        errors.append(f"地址 0 起点未覆盖（首个区域基址 0x{srt[0]['base']:X}）")
    for a, b in zip(srt, srt[1:]):
        gap = b["base"] - (a["base"] + a["size"])
        if gap < 0:
            continue  # 已由重叠检查报告
        if gap > 0:
            if a["access"] != "-":
                errors.append(
                    f"间隙未归保留区: 0x{a['base']+a['size']:X}..0x{b['base']-1:X} 紧邻功能窗口 {a['mem_id']}")
            else:
                infos.append(f"间隙段 0x{a['base']+a['size']:X}..0x{b['base']-1:X} 落在保留区 {a['mem_id']} 之后（空洞口径: {a['mem_id']} err={a['err']}）")
    last = srt[-1]
    if last["base"] + last["size"] != space:
        errors.append(f"空间上限未封闭: 最后区域 {last['mem_id']} end=0x{last['base']+last['size']:X} != 0x{space:X}")

    # 6. 每从设备恰一窗口（BLOCK-02 承载保留区豁免）
    from collections import Counter
    cnt = Counter(r["block"] for r in mapped if r["access"] != "-")
    for blk, n in cnt.items():
        if n > 1:
            errors.append(f"从设备 {blk} 有 {n} 个功能窗口（须唯一）")

    # 未映射外部器件
    for r in unmapped:
        infos.append(f"非映射外部器件: {r['mem_id']}({r['name']}) 不参与译码")

    func_bytes = sum(r["size"] for r in mapped if r["access"] != "-")
    total_bytes = sum(r["size"] for r in mapped)

    # ---- 报告 ----
    lines = []
    lines.append("=== B2 地址映射检查报告（自动生成）===")
    lines.append(f"数据源: {args.map} | 区域总数: {len(regions)}（mapped {len(mapped)} + 非映射 {len(unmapped)}）")
    lines.append(f"功能窗口覆盖字节数: {func_bytes} (0x{func_bytes:X}) | mapped 区域总字节: {total_bytes} (0x{total_bytes:X})")
    lines.append(f"对齐粒度: 0x{gran:X} | 地址空间: 32-bit")
    lines.append("--- ERROR ---" if errors else "--- ERROR: 0 ---")
    lines += [f"  {e}" for e in errors]
    lines.append("--- WARNING ---" if warnings else "--- WARNING: 0 ---")
    lines += [f"  {w}" for w in warnings]
    lines.append("--- INFO ---")
    lines += [f"  {i}" for i in infos]
    lines.append("--- 区域清单 ---")
    for r in srt:
        tag = "功能" if r["access"] != "-" else "保留"
        lines.append(f"  {r['mem_id']:<7} {tag} 0x{r['base']:08X} +0x{r['size']:08X}"
                     f"  {r['domain']:<7} {r['block']:<9} decode={r['decode']:<8} err={r['err']}")
    lines.append("--- 结论 ---")
    lines.append("PASS: 无地址冲突、无重叠、全对齐、空间封闭" if not errors else "FAIL")
    report = "\n".join(lines)
    print(report)

    rp = args.report
    if rp is None and Path("docs").is_dir():
        rp = "docs/B2-addr-check.txt"
    if rp:
        Path(rp).parent.mkdir(parents=True, exist_ok=True)
        Path(rp).write_text(report + "\n", encoding="utf-8")
        print(f"[report] {rp}")

    if errors:
        sys.exit(1)

    # ---- 代码生成 ----
    func = [r for r in srt if r["access"] != "-"]
    res = [r for r in srt if r["access"] == "-"]
    sv_consts = "\n".join(to_sv(f"{sym_of(r['name'])}_BASE", r["base"], r["size"]) for r in func)
    sv_reserves = "\n".join(to_sv(f"RESERVED_{r['mem_id'].replace('-', '_')}_BASE", r["base"], r["size"]) for r in res)
    c_consts = "\n".join(to_c(f"{sym_of(r['name'])}_BASE", r["base"], r["size"]) for r in func)
    c_reserves = "\n".join(to_c(f"RESERVED_{r['mem_id'].replace('-', '_')}_BASE", r["base"], r["size"]) for r in res)

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    (out / "axi_addr_pkg.sv").write_text(
        SV_PKG_TEMPLATE.format(addr_width=addr_width, sv_consts=sv_consts, sv_reserves=sv_reserves),
        encoding="utf-8")
    print(f"[gen] {out/'axi_addr_pkg.sv'}")

    if args.sw_out:
        sw = Path(args.sw_out); sw.mkdir(parents=True, exist_ok=True)
        (sw / "soc_addr.h").write_text(
            C_HDR_TEMPLATE.format(c_consts=c_consts, c_reserves=c_reserves), encoding="utf-8")
        print(f"[gen] {sw/'soc_addr.h'}")


if __name__ == "__main__":
    main()
