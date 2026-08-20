#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A3 接口规格完整性校验脚本 (node A3: 接口规格)

用法:
    python scripts/a3_check_interface.py \
        --pin  work/soc/docs/spec/spec-005-pins.csv \
        --map  work/soc/docs/spec/spec-005-memory-map.csv \
        --irq  work/soc/docs/spec/spec-005-irq.csv \
        --uc   work/soc/docs/spec/spec-002-use-cases.md \
        --spec work/soc/docs/spec/spec-005-interface-spec.md

检查项（对应详章 DoD）:
    1. 引脚重名      : pins.csv 中 pad_name 唯一; 复用功能信号 (alt_fn) 唯一
    2. 地址重叠      : memory-map.csv 中 mapped=yes 区域 base+size 无重叠、不越 32bit
    3. 中断号重复    : irq.csv 中 irq_num / irq_id 唯一
    4. 引用未定义信号: irq trigger_signal 若引用引脚必须存在于 pins.csv; BLOCK 引用合法
    5. 位宽不一致    : 同名信号位宽一致; GPIO 通道数 >= 16 (M-020); 中断源数满足 M-019
    6. 遗漏核对      : use-cases.md 全部 UC 在接口规格 §遗漏核对 表中有接口定义

输出: 各检查项结论 + DoD 判定 (接口清单冻结, 无遗漏, 无冲突)
"""
import argparse
import csv
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:  # pragma: no cover
    pass

UC_RE = re.compile(r"UC-[A-Z_]+-\d{3}")
BLOCK_RE = re.compile(r"BLOCK-(\d{2})")
HEX_RE = re.compile(r"^0x[0-9a-fA-F]+$")
VALID_BLOCKS = {f"BLOCK-{i:02d}" for i in range(1, 15)}
VALID_DIR = {"in", "out", "inout"}
VALID_ACCESS = {"RO", "R/W", "-", "PIO", "R"}


def read_csv(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def read_text(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return f.read()


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


def section_until(text, start_marker, stop_marker="## "):
    lines = text.splitlines()
    out = []
    in_sec = False
    for ln in lines:
        if ln.strip().startswith(start_marker):
            in_sec = True
        elif in_sec and ln.strip().startswith(stop_marker):
            break
        if in_sec:
            out.append(ln)
    return "\n".join(out)


def parse_hex(s):
    s = s.strip()
    if not s or s == "-":
        return None
    if not HEX_RE.match(s):
        return None
    return int(s, 16)


def strip_sig(name):
    """去除位选下标: gpio[0] -> gpio; spi_cs_n[0] -> spi_cs_n"""
    m = re.match(r"^(.+?)(?:\[\d+\])?$", name)
    return m.group(1)


# ---------------- 检查实现 ----------------

def check_pins(rows):
    issues = []
    pads = {}
    altfns = {}
    for r in rows:
        pad = r.get("pad_name", "").strip()
        alt = r.get("alt_fn", "").strip()
        w = r.get("width", "").strip()
        d = r.get("direction", "").strip()
        if not pad:
            issues.append("[P1] 存在空 pad_name 行")
            continue
        if pad in pads:
            issues.append(f"[P1] 引脚重名: {pad} 出现多次")
        pads[pad] = r
        if alt and alt != "-":
            # 复用功能信号按完整信号名（含位选）判唯一: spi_cs_n[0]/spi_cs_n[1] 是同一总线不同 slice,
            # 可合法映射到不同 pad, 不视为冲突; 完全同名才冲突
            if alt in altfns:
                issues.append(f"[P1] 复用功能信号重复映射: {alt} 同时出现在 {altfns[alt]} 与 {pad}")
            else:
                altfns[alt] = pad
        if d not in VALID_DIR:
            issues.append(f"[P5] 方向非法: {pad} direction={d}")
        if not w.isdigit() or int(w) < 1:
            issues.append(f"[P5] 位宽非法: {pad} width={w}")
    # 位宽一致性: 同名基信号(去掉位选)位宽必须一致
    widths = {}
    for r in rows:
        pad = r.get("pad_name", "").strip()
        w = r.get("width", "").strip()
        if not pad or not w.isdigit():
            continue
        key = strip_sig(pad)
        if key in widths and widths[key] != w:
            issues.append(f"[P5] 位宽不一致: {pad} width={w}, 先前 {key} width={widths[key]}")
        widths[key] = w
    # M-020: GPIO >= 16 通道
    gpio_n = sum(1 for p in pads if re.fullmatch(r"gpio\[\d+\]", p))
    if gpio_n < 16:
        issues.append(f"[P5] GPIO 通道数 {gpio_n} < M-020 要求 16")
    # M-019 需要的外部/定时器/软件中断源不在引脚层检查（irq 层检查）
    return issues, pads, altfns


def check_mem(rows):
    issues = []
    regions = []
    for r in rows:
        if r.get("mapped", "").strip().lower() != "yes":
            continue  # 非地址映射条目（如 SPI Flash 外部器件）跳过重叠检查
        mem_id = r.get("mem_id", "").strip()
        base = parse_hex(r.get("base_addr", ""))
        size = parse_hex(r.get("size", ""))
        if base is None or size is None:
            issues.append(f"[M2] 地址/大小非法: {mem_id} base={r.get('base_addr')} size={r.get('size')}")
            continue
        if base + size > 0x1_0000_0000:
            issues.append(f"[M2] 越界 32bit: {mem_id} base+size=0x{base + size:X}")
        regions.append((mem_id, base, base + size))
        blk = r.get("block", "").strip()
        if blk not in VALID_BLOCKS:
            issues.append(f"[M4] BLOCK 引用非法: {mem_id} block={blk}")
    regions.sort(key=lambda x: x[1])
    for i in range(1, len(regions)):
        prev_id, _, prev_end = regions[i - 1]
        cur_id, cur_base, _ = regions[i]
        if cur_base < prev_end:
            issues.append(f"[M2] 地址重叠: {cur_id}(base=0x{cur_base:X}) 与 {prev_id}(end=0x{prev_end:X}) 重叠")
    return issues


def check_irq(rows, pads, altfns):
    issues = []
    nums = {}
    ids = {}
    internal_sigs = set()
    for r in rows:
        iid = r.get("irq_id", "").strip()
        num = r.get("irq_num", "").strip()
        sig = r.get("trigger_signal", "").strip()
        blk = r.get("source_block", "").strip()
        if iid in ids:
            issues.append(f"[I3] irq_id 重复: {iid}")
        ids[iid] = r
        if num in nums:
            issues.append(f"[I3] 中断号重复: {num} 同时用于 {nums[num]} 与 {iid}")
        nums[num] = iid
        if not num.isdigit() or not (1 <= int(num) <= 31):
            issues.append(f"[I3] 中断号非法: {iid} irq_num={num} (应 1..31)")
        if blk not in VALID_BLOCKS:
            issues.append(f"[I4] BLOCK 引用非法: {iid} source_block={blk}")
        # 引用未定义信号: 内部信号必须带 (内部) 标记且自身声明; 否则必须在 pins.csv 存在
        if "(内部)" in sig:
            base = sig.replace("(内部)", "").strip()
            internal_sigs.add(base)
        else:
            base = strip_sig(sig)
            if base not in pads and base not in altfns:
                issues.append(f"[I4] 引用未定义信号: {iid} trigger_signal={sig} 未在 pins.csv 定义")
        m = r.get("maskable", "").strip()
        if m not in {"maskable", "non-maskable"}:
            issues.append(f"[I3] maskable 非法: {iid} maskable={m}")
    # 内部触发信号不得重复
    if len(internal_sigs) != len(rows):
        issues.append("[I4] 内部触发信号存在重复声明")
    # M-019: 中断源数 >=6 (外部>=4 + 定时器1 + 软件1)
    ext = sum(1 for r in rows if r.get("irq_name", "").startswith("GPIO_EXT"))
    tmr = sum(1 for r in rows if r.get("irq_name", "") == "TIMER0")
    sw = sum(1 for r in rows if r.get("irq_name", "") == "SW_INT")
    if len(rows) < 6 or ext < 4 or tmr < 1 or sw < 1:
        issues.append(f"[I3] 中断源数不满足 M-019: 总数={len(rows)} 外部(GPIO)={ext} 定时器={tmr} 软件={sw} (需 >=6, 外部>=4, 定时器>=1, 软件>=1)")
    return issues


def check_uc(uc_text, spec_text):
    """遗漏核对: use-cases.md 全部 UC 必须在接口规格 §遗漏核对 表中有定义"""
    all_uc = set(UC_RE.findall(uc_text))
    cov_block = section_until(spec_text, "## 8. 遗漏核对") if "## 8. 遗漏核对" in spec_text else ""
    if not cov_block:
        cov_block = section_until(spec_text, "## 9. 遗漏核对")
    covered = set()
    for row in table_rows(cov_block):
        if row and UC_RE.fullmatch(row[0]):
            covered.add(row[0])
    missing = sorted(all_uc - covered, key=lambda s: (s.split("-")[1], int(s.split("-")[2])))
    extra = sorted(covered - all_uc)
    return all_uc, covered, missing, extra


def main():
    ap = argparse.ArgumentParser(description="A3 接口规格校验")
    ap.add_argument("--pin", required=True)
    ap.add_argument("--map", required=True)
    ap.add_argument("--irq", required=True)
    ap.add_argument("--uc", required=True, help="spec-002-use-cases.md 路径 (遗漏核对)")
    ap.add_argument("--spec", required=True, help="spec-005-interface-spec.md 路径 (遗漏核对)")
    args = ap.parse_args()

    pin_rows = read_csv(args.pin)
    mem_rows = read_csv(args.map)
    irq_rows = read_csv(args.irq)
    uc_text = read_text(args.uc)
    spec_text = read_text(args.spec)

    print("=" * 62)
    print("[A3 check_interface] 接口规格校验报告")
    print("=" * 62)

    p_issues, pads, altfns = check_pins(pin_rows)
    m_issues = check_mem(mem_rows)
    i_issues = check_irq(irq_rows, pads, altfns)
    all_uc, covered, missing, extra = check_uc(uc_text, spec_text)

    gpio_pat = re.compile(r"gpio\[\d+\]")
    gpio_cnt = sum(1 for p in pads if gpio_pat.fullmatch(p))
    ext_cnt = sum(1 for r in irq_rows if r.get("irq_name", "").startswith("GPIO_EXT"))
    tmr_cnt = sum(1 for r in irq_rows if r.get("irq_name", "") == "TIMER0")
    sw_cnt = sum(1 for r in irq_rows if r.get("irq_name", "") == "SW_INT")
    mapped_cnt = sum(1 for r in mem_rows if r.get("mapped", "").strip().lower() == "yes")

    print(f"引脚条目数       : {len(pin_rows)} (GPIO 通道 {gpio_cnt})")
    print(f"存储映射条目数   : {len(mem_rows)} (地址映射 {mapped_cnt})")
    print(f"中断条目数       : {len(irq_rows)} (外部 {ext_cnt}/定时器 {tmr_cnt}/软件 {sw_cnt})")
    print(f"用例覆盖 (UC)    : {len(covered)}/{len(all_uc)}")
    print("-" * 62)
    print(f"[P 引脚] 重名/位宽/方向: " + ("OK" if not p_issues else "; ".join(p_issues)))
    print(f"[M 存储] 地址重叠/越界/引用: " + ("OK" if not m_issues else "; ".join(m_issues)))
    print(f"[I 中断] 号重复/引用/数量: " + ("OK" if not i_issues else "; ".join(i_issues)))
    print(f"[U 遗漏] UC 覆盖: " + ("OK, 无遗漏" if not missing and not extra else
                                    ("缺失: " + ", ".join(missing) if missing else "") +
                                    ("; 多余: " + ", ".join(extra) if extra else "")))
    print("-" * 62)
    print("DoD 判定 (A3: 接口清单冻结, 无遗漏, 无冲突):")
    failed = bool(p_issues or m_issues or i_issues or missing)
    print(f"  [A3-D1] 引脚名唯一/复用无冲突  : {'满足' if not p_issues else '未满足'}")
    print(f"  [A3-D2] 地址区间无重叠         : {'满足' if not m_issues else '未满足'}")
    print(f"  [A3-D3] 中断号唯一/数量达标    : {'满足' if not i_issues else '未满足'}")
    print(f"  [A3-D4] 引用信号均已定义       : {'满足' if not (p_issues or i_issues) else '未满足'}")
    print(f"  [A3-D5] 位宽一致               : {'满足' if not p_issues else '未满足'}")
    print(f"  [A3-D6] UC 无遗漏(全部有接口)  : {'满足' if not missing else '未满足'}")
    print("=" * 62)
    print("CONCLUSION: " + ("FAIL(存在冲突/遗漏, 需修正)" if failed else "PASS(冲突扫描零结果, 遗漏核对为空, 待人工评审签字)"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())