#!/usr/bin/env python3
"""RTL 编码规范机械性检查脚本。

基于 advance-rtl-coding-guidance 规范，对 Verilog/SystemVerilog 文件做
机械性检查，覆盖命名、always 块结构、常见反模式。

用法:
    python check_rtl_style.py <file.v> [<file2.v> ...]

输出分级:
    blocker     必须修改（latch 风险 / 不可综合 / 竞争）
    warning     应修改（风格 / 可读性 / 潜在问题）
    suggestion  可选改进

退出码: 0 = 无 blocker; 1 = 存在 blocker; 2 = 文件读取错误
"""

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Finding:
    level: str          # blocker / warning / suggestion
    rule: str           # 检查项编号（B1, C2 ...）
    line: int
    msg: str


@dataclass
class ModuleCheck:
    path: Path
    lines: list = field(default_factory=list)
    findings: list = field(default_factory=list)

    def add(self, level: str, rule: str, line: int, msg: str) -> None:
        self.findings.append(Finding(level, rule, line, msg))

    # ---------- 检查项 ----------

    def check_always_blocks(self) -> None:
        """A1: always 块命名; B6: 组合块敏感列表; C1: 时序块敏感列表。"""
        # 先收集所有 always 块范围（always 行 -> 匹配的 end）
        blocks = []   # (start_line, end_line, sens)
        stack = []
        for i, ln in enumerate(self.lines, 1):
            if re.search(r"always\s*@\s*\([^)]*\)", ln):
                m = re.search(r"always\s*@\s*\(([^)]*)\)", ln)
                blocks.append([i, None, m.group(1).strip()])
                stack.append(len(blocks) - 1)
            for b in stack:
                if blocks[b][1] is None and re.search(r"^\s*end\b", ln):
                    blocks[b][1] = i
                    stack.remove(b)
        for start, end, sens in blocks:
            # 组合块必须用 (*)
            if sens != "*" and not re.search(r"\*", sens):
                if "posedge" not in sens and "negedge" not in sens:
                    self.add("warning", "B6", start, f"组合逻辑敏感列表应使用 @(*)，当前: @({sens})")
            # A1: 块内是否有 PROC_ 命名标签
            seg = self.lines[start-1:end] if end else self.lines[start-1:start+8]
            if not any(re.search(r"begin\s*:\s*\w+", s) for s in seg):
                self.add("warning", "A1", start, "always 块缺少命名标签 begin : PROC_<name>")

    def check_nxt_pairing(self) -> None:
        """A2: nxt* 信号是否有对应寄存器。检查 'nxt\w+\s*=' 是否伴随 '\w+\s*<=\s*nxt'。"""
        nxt_assigned = set()
        nxt_consumed = set()
        for i, ln in enumerate(self.lines, 1):
            for m in re.finditer(r"(nxt\w+)\s*=", ln):
                nxt_assigned.add((m.group(1), i))
            for m in re.finditer(r"\b(\w+)\s*<=\s*nxt\w+", ln):
                nxt_consumed.add(m.group(1))
        # 如果存在 nxt 组合赋值但没有对应 x <= nxtx 消费，警告（简单启发式）
        if nxt_assigned and not nxt_consumed:
            first = sorted(nxt_assigned)[0]
            self.add("warning", "A2", first[1],
                     f"存在 nxt* 次态赋值({first[0]})但未发现 x <= nxtx 寄存消费，检查命名配对")

    def check_comb_default(self) -> None:
        """B1: 组合块默认值; B3: 组合块不改寄存器。"""
        in_comb = False
        comb_start = 0
        comb_nxt_targets = set()   # 该组合块内被赋值的 nxt* 信号
        comb_seg = []              # 组合块所有行
        for i, ln in enumerate(self.lines, 1):
            if re.search(r"always\s*@\s*\(\s*\*\s*\)", ln):
                in_comb = True
                comb_start = i
                comb_nxt_targets = set()
                comb_seg = []
                continue
            if in_comb:
                # 结束: 遇到 end 且缩进回退，或下一个 always/endmodule
                if re.match(r"^\s*end\b", ln) or "endmodule" in ln:
                    # B1 启发式: 组合块内有 nxt* 赋值，但找不到默认赋值模式
                    #   - 保持模式: "nxtx = x"（DWC 写法，右侧为去掉 nxt 前缀的对应名）
                    #   - 常量模式: "nxtx = 0 / 1'b0 / 1'b1 / N'dM"
                    #   - 全覆盖: 块内存在 case 的 default 分支
                    if comb_nxt_targets:
                        has_default = any(
                            re.search(r"\bnxt(\w+)\s*=\s*\1\b", s) for s in comb_seg
                        ) or any(
                            re.search(r"\b(nxt\w+)\s*=\s*(0|1'b0|1'b1|\d+'d\d+)\b", s)
                            for s in comb_seg
                        ) or any(
                            re.search(r"\bdefault\s*:", s) for s in comb_seg
                        )
                        if not has_default:
                            names = ", ".join(sorted(comb_nxt_targets))
                            self.add("warning", "B1", comb_start,
                                     f"组合块内 nxt* 信号({names})未见默认赋值(保持/常量/case-default)，潜在 latch 风险")
                    in_comb = False
                    continue
                comb_seg.append(ln)
                # 记录组合块内 nxt* 赋值
                for m in re.finditer(r"\b(nxt\w+)\s*=", ln):
                    comb_nxt_targets.add(m.group(1))
                # 组合块内对非 nxt 信号用 <=（寄存器赋值）-> 违规
                if re.search(r"\b(?!nxt)\w+\s*<=", ln) and "assign" not in ln:
                    self.add("blocker", "B3", i,
                             f"组合块内对非 nxt 信号使用 <= ({ln.strip()[:60]})，违反组合时序分离")
                # 组合块内 nxt 使用 <=（应使用 =）-> 违规
                if re.search(r"nxt\w+\s*<=", ln):
                    self.add("blocker", "B3", i, "组合块内 nxt* 使用了 <=，应使用 =")

    def check_case_default(self) -> None:
        """B4: case 必须有 default。"""
        case_stack = []
        for i, ln in enumerate(self.lines, 1):
            if re.search(r"\bcase\s*\(", ln):
                case_stack.append(i)
            if re.search(r"\bendcase\b", ln):
                if case_stack:
                    start = case_stack.pop()
                    # 检查 start..i 之间是否有 default
                    seg = self.lines[start-1:i]
                    if not any(re.search(r"\bdefault\b", s) for s in seg):
                        self.add("blocker", "B4", start, "case 缺少 default 分支")

    def check_sequential_assign(self) -> None:
        """C4: 时序块内只能用 <=。"""
        in_seq = False
        for i, ln in enumerate(self.lines, 1):
            if re.search(r"always\s*@\s*\([^)]*(posedge|negedge)[^)]*\)", ln):
                in_seq = True
                continue
            if in_seq:
                if re.match(r"^\s*end\b", ln) or "endmodule" in ln:
                    in_seq = False
                    continue
                # 时序块内出现非 <= 赋值（且非 for/function 等）-> 检查 = 赋值
                if re.search(r"\b\w+\s*=\s*[^=]", ln) and "assign" not in ln:
                    self.add("warning", "C4", i,
                             f"时序块内疑似使用阻塞赋值 = ({ln.strip()[:60]})，应使用 <=")

    def check_magic_numbers(self) -> None:
        """F5: 位宽/阈值魔数检测（启发式：宽度声明中的裸数字）。"""
        for i, ln in enumerate(self.lines, 1):
            # 端口/信号声明中的宽度 [N:0] 且 N 是字面量且非 31/7/15/3 等常见 -> 跳过
            # 仅提示：localparam 未带位宽
            if re.search(r"localparam\s+\w+\s*=\s*\d", ln) and not re.search(r"localparam\s+\[\d", ln):
                self.add("warning", "F5", i, "localparam 未带位宽声明，建议 [W-1:0]")

    def check_sync_reset_order(self) -> None:
        """C5: 同步复位在异步复位之后（启发式：else if 中出现 reset 字样）。"""
        for i, ln in enumerate(self.lines, 1):
            if re.search(r"else\s+if\s*\([^)]*(rst|reset|init|preset)[^)]*\)", ln, re.I):
                # 出现 else if 带 reset 字样的同步分支，提示确认顺序
                self.add("suggestion", "C5", i, "检测到同步复位分支，确认位于异步复位之后")

    # ---------- 主流程 ----------

    def run(self) -> None:
        self.check_always_blocks()
        self.check_nxt_pairing()
        self.check_comb_default()
        self.check_case_default()
        self.check_sequential_assign()
        self.check_magic_numbers()
        self.check_sync_reset_order()


def check_file(path: Path) -> ModuleCheck:
    mc = ModuleCheck(path=path)
    try:
        mc.lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as e:
        mc.add("blocker", "IO", 0, f"无法读取文件: {e}")
        return mc
    mc.run()
    return mc


def main(argv: list) -> int:
    # Windows 控制台 UTF-8 输出
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    if not argv:
        print(__doc__)
        return 2

    has_blocker = False
    total = 0
    for arg in argv:
        p = Path(arg)
        if not p.exists():
            print(f"[IO] 文件不存在: {arg}")
            has_blocker = True
            continue
        mc = check_file(p)
        total += len(mc.findings)
        print(f"\n===== {p} ({len(mc.findings)} findings) =====")
        for f in sorted(mc.findings, key=lambda x: (0 if x.level == "blocker" else 1 if x.level == "warning" else 2, x.line)):
            print(f"  [{f.level:10s}] {f.rule} L{f.line}: {f.msg}")
            if f.level == "blocker":
                has_blocker = True

    print(f"\n--- 完成: {len(argv)} 文件, {total} 项发现, blocker={has_blocker} ---")
    return 1 if has_blocker else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))