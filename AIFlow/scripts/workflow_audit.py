#!/usr/bin/env python3
"""治理层流程骨架确定性审计 — workflow audit

规则化校验（替代 AI 自由判断），所有检查可复现、无随机性。
覆盖：节点注册表 / 详章 / skill / agent / SOP 索引 / tracker / 引用完整性 / 脚手架一致性 / 模板资产。

用法:
    python AIFlow/scripts/workflow_audit.py            # 全量审计（默认）
    python AIFlow/scripts/workflow_audit.py --json     # JSON 输出（供自动化/CI）
    python AIFlow/scripts/workflow_audit.py --node C3  # 单节点审计
    python AIFlow/scripts/workflow_audit.py --summary  # 仅结论

退出码: 0 = 通过；1 = 有 Warning；2 = 有 Blocker
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent   # 芯片根
AIFLOW = ROOT / "AIFlow"
SKILLS = ROOT / ".opencode" / "skills"
AGENTS = ROOT / ".opencode" / "agent"
DOC = AIFLOW / "doc"
STATE = AIFLOW / "state"
NODES_JSON = AIFLOW / "scripts" / "nodes.json"
SOP = DOC / "SOP.md"
TRACKER = STATE / "state-tracker.md"

# 已知定制 skill（scaffold 渲染一致性检查时排除；A1/A2 手工定制 + 6 个拥有专属模板的 skill）
KNOWN_CUSTOM = {"A1", "A2", "B7", "C0", "C1", "C3", "D1"}

SEV_BLOCKER, SEV_WARN, SEV_INFO = "Blocker", "Warning", "Info"
VALID_TRACKER_STATES = {"pending", "in_progress", "waiting_review", "passed", "iterating"}


def load_nodes() -> list[dict]:
    return json.loads(NODES_JSON.read_text(encoding="utf-8"))["nodes"]


class Audit:
    def __init__(self):
        self.issues: list[dict] = []

    def add(self, sev: str, check: str, msg: str, node: str = ""):
        self.issues.append({"severity": sev, "check": check, "message": msg, "node": node})

    @property
    def blockers(self):
        return [i for i in self.issues if i["severity"] == SEV_BLOCKER]

    @property
    def warnings(self):
        return [i for i in self.issues if i["severity"] == SEV_WARN]

    @property
    def infos(self):
        return [i for i in self.issues if i["severity"] == SEV_INFO]


def expand_range(m):
    """'A1-A5' -> ['A1'..'A5']；'C0' -> ['C0']"""
    if "-" in m:
        a, b = m.split("-")
        pre, sa, sb = a[0], a[1:], b[1:]
        return [f"{pre}{i:0{len(sa)}d}" for i in range(int(sa), int(sb) + 1)]
    return [m]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", help="只审计指定节点")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    ap.add_argument("--summary", action="store_true", help="仅输出结论")
    args = ap.parse_args()

    a = Audit()
    nodes = load_nodes()
    if args.node:
        nodes = [n for n in nodes if n["id"] == args.node.upper()]
        if not nodes:
            raise SystemExit(f"未找到节点 {args.node}")

    required_fields = {"id", "slug", "name", "phase", "agent", "doc", "description", "dod", "gate"}

    # ---------- W1 注册表完整性 ----------
    seen_ids = set()
    for n in nodes:
        nid = n.get("id", "")
        if nid in seen_ids:
            a.add(SEV_BLOCKER, "W1", f"节点 ID 重复: {nid}", nid)
        seen_ids.add(nid)
        miss = required_fields - set(n.keys())
        if miss:
            a.add(SEV_BLOCKER, "W1", f"缺少字段 {sorted(miss)}", nid)
        valid_gates = {"评审", "检查", "人工签字"}
        if n.get("gate") not in valid_gates:
            a.add(SEV_WARN, "W1", f"gate 取值非法: {n.get('gate')}（应为 {sorted(valid_gates)}）", nid)
        if not re.fullmatch(r"[A-H]\d+", nid):
            a.add(SEV_WARN, "W1", f"ID 格式异常（应为 [A-H]\\d+）: {nid}", nid)

    # ---------- W2 详章存在 ----------
    for n in nodes:
        p = DOC / n["doc"]
        if not p.exists():
            a.add(SEV_BLOCKER, "W2", f"详章不存在: AIFlow/doc/{n['doc']}", n["id"])

    # ---------- W3 skill 存在 ----------
    for n in nodes:
        s = SKILLS / f"node-{n['id']}-{n['slug']}" / "SKILL.md"
        if not s.exists():
            a.add(SEV_BLOCKER, "W3", f"skill 不存在: {s.relative_to(ROOT)}", n["id"])

    # ---------- W4 skill frontmatter ----------
    for n in nodes:
        s = SKILLS / f"node-{n['id']}-{n['slug']}" / "SKILL.md"
        if not s.exists():
            continue
        txt = s.read_text(encoding="utf-8")
        m = re.search(r"^---\nname:\s*(.+)\n", txt)
        if not m or m.group(1).strip() != f"node-{n['id']}-{n['slug']}":
            a.add(SEV_BLOCKER, "W4", f"frontmatter name 与目录名不一致: {m.group(1) if m else '无'}", n["id"])
        if "description:" not in txt:
            a.add(SEV_BLOCKER, "W4", "缺少 description", n["id"])

    # ---------- W5 agent 存在 ----------
    for n in nodes:
        ag = AGENTS / f"{n['agent']}.md"
        if not ag.exists():
            a.add(SEV_BLOCKER, "W5", f"agent 文件不存在: {n['agent']}.md", n["id"])

    # ---------- W6 agent 职责范围（description 声明 vs nodes.json 归属）----------
    by_agent = {}
    for n in nodes:
        by_agent.setdefault(n["agent"], set()).add(n["id"])
    for agent_file in sorted(AGENTS.glob("*.md")):
        ag = agent_file.stem
        if ag == "orchestrator":  # 主 agent，不归属节点，跳过
            continue
        if ag not in by_agent:
            a.add(SEV_WARN, "W6", f"agent 未归属任何节点: {ag}")
            continue
        txt = agent_file.read_text(encoding="utf-8")
        claimed = set()
        for m in re.finditer(r"（([A-H]\d+(?:-[A-H]\d+)?)(?:,\s*([A-H]\d+(?:-[A-H]\d+)?))?）", txt):
            for g in m.groups():
                if g:
                    claimed.update(expand_range(g))
        expected = by_agent[ag]
        missing = sorted(expected - claimed)
        extra = sorted(claimed - expected)
        if missing:
            a.add(SEV_WARN, "W6", f"agent 职责声明遗漏节点: {missing}", ag)
        if extra:
            a.add(SEV_WARN, "W6", f"agent 职责声明含未归属节点: {extra}", ag)

    # ---------- W7 SOP 索引一致性 ----------
    sop_txt = SOP.read_text(encoding="utf-8") if SOP.exists() else ""
    for n in nodes:
        if n["id"] not in sop_txt:
            a.add(SEV_BLOCKER, "W7", f"SOP 索引缺少节点: {n['id']}", n["id"])
        if n["doc"] not in sop_txt:
            a.add(SEV_BLOCKER, "W7", f"SOP 索引缺少详章链接: {n['doc']}", n["id"])
    # SOP 中的链接目标存在
    if SOP.exists():
        for m in re.finditer(r"\]\((阶段[A-H][^)]+\.md)\)", sop_txt):
            if not (DOC / m.group(1)).exists():
                a.add(SEV_WARN, "W7", f"SOP 链接目标不存在: {m.group(1)}")

    # ---------- W8 tracker 覆盖 ----------
    tr = TRACKER.read_text(encoding="utf-8") if TRACKER.exists() else ""
    for n in nodes:
        if f"## {n['id']} " not in tr and f"## {n['id']}　" not in tr:
            a.add(SEV_BLOCKER, "W8", f"tracker 缺少节点条目: {n['id']}", n["id"])
    # 状态值合法
    for m in re.finditer(r"## ([A-H]\d+)\s+[^\n]+\n- 状态:\s*(\S+)", tr):
        nid, st = m.group(1), m.group(2)
        if st not in VALID_TRACKER_STATES:
            a.add(SEV_WARN, "W8", f"tracker 非法状态值: {nid} = {st}", nid)

    # 阶段汇总 vs 节点状态一致性
    phase_nodes = {}
    for n in load_nodes():
        phase_nodes.setdefault(n["id"][0], []).append(n["id"])
    for m in re.finditer(r"\| ([A-H]) \| (\d+) \| ([^|]+) \|", tr):
        ph, cnt, desc = m.group(1), int(m.group(2)), m.group(3).strip()
        expected_cnt = len(phase_nodes.get(ph, []))
        if cnt != expected_cnt:
            a.add(SEV_WARN, "W8", f"阶段汇总节点数与 nodes.json 不一致: {ph} 表={cnt} 实际={expected_cnt}")
            continue
        # 若摘要写"全部 pending"但实际有 passed/in_progress/waiting_review，则矛盾
        if "全部 pending" in desc:
            actual = [nid for nid in phase_nodes.get(ph, []) if re.search(rf"## {nid}(?=\s)[^\n]*\n- 状态:\s+(?!pending)", tr, re.M)]
            if actual:
                a.add(SEV_WARN, "W8", f"阶段汇总写'全部 pending'但实际非 pending: {ph} → {actual}")

    # ---------- W13 tracker 前置依赖无悬空 ----------
    node_ids = {n["id"] for n in nodes}
    for m in re.finditer(r"## ([A-H]\d+)\s+[^\n]+\n- 前置:\s*([^\n]+)", tr):
        nid, deps = m.group(1), m.group(2)
        if deps.strip() in ("无", "TBD", ""):
            continue
        for d in re.findall(r"[A-H]\d+", deps):
            if d not in node_ids:
                a.add(SEV_WARN, "W13", f"tracker 前置依赖悬空: {nid} 依赖不存在的 {d}", nid)

    # ---------- W12 阶段目录完整性 ----------
    phase_dirs = {"A": "阶段A-需求与规格", "B": "阶段B-架构与集成规划", "C": "阶段C-微架构与RTL",
                  "D": "阶段D-验证", "E": "阶段E-综合与约束", "F": "阶段F-STA时序收敛",
                  "G": "阶段G-签核与交付", "H": "阶段H-物理设计"}
    for n in nodes:
        ph = n["id"][0]
        if ph in phase_dirs and not (DOC / phase_dirs[ph]).exists():
            a.add(SEV_BLOCKER, "W12", f"阶段目录不存在: {phase_dirs[ph]}", n["id"])

    # ---------- W9 引用完整性（governance 引用路径存在）----------
    ref_files = list(SKILLS.rglob("SKILL.md")) + list(AGENTS.glob("*.md")) + list(STATE.glob("*.md")) + [ROOT / "README.md"]
    for p in ref_files:
        if not p.exists():
            continue
        txt = p.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"`(AIFlow/[^`\s]+)`", txt):
            ref = m.group(1)
            if any(c in ref for c in "<>{}*?"):  # 占位符/通配符（{{DOC}}、<id>、*）跳过
                continue
            rp = ROOT / ref
            if not rp.exists():
                a.add(SEV_WARN, "W9", f"引用路径不存在: {ref}（来自 {p.relative_to(ROOT)}）")
        for m in re.finditer(r"\]\(\.\./\.\./(AIFlow/[^)]+)\)", txt):
            rp = ROOT / m.group(1)
            if not rp.exists():
                a.add(SEV_WARN, "W9", f"链接目标不存在: {m.group(1)}（来自 {p.relative_to(ROOT)}）")

    # ---------- W11 模板资产存在 ----------
    for p in sorted(SKILLS.rglob("SKILL.md")):
        txt = p.read_text(encoding="utf-8")
        for m in re.finditer(r"`(assets/templates/[^`\s]+\.md)`", txt):
            if not (p.parent / m.group(1)).exists():
                a.add(SEV_WARN, "W11", f"skill 引用的模板资产不存在: {m.group(1)}（来自 {p.relative_to(ROOT)}）")

    # ---------- W10 脚手架一致性 ----------
    try:
        tpl = (SKILLS / "node-template" / "SKILL.md").read_text(encoding="utf-8")
        for n in load_nodes():
            if n["id"] in KNOWN_CUSTOM:
                continue
            content = tpl
            for key, val in {"ID": n["id"], "NAME": n["name"], "SLUG": n["slug"], "DESCRIPTION": n["description"],
                             "DOC": n["doc"], "AGENT": n["agent"], "DOD": n["dod"], "GATE_TYPE": n["gate"]}.items():
                content = content.replace("{{%s}}" % key, str(val))
            cur = (SKILLS / f"node-{n['id']}-{n['slug']}" / "SKILL.md").read_text(encoding="utf-8")
            if content != cur:
                a.add(SEV_WARN, "W10", f"skill 与脚手架渲染不一致（可能漂移或含未登记定制）: node-{n['id']}-{n['slug']}", n["id"])
    except Exception as e:  # noqa: BLE001
        a.add(SEV_WARN, "W10", f"脚手架一致性检查异常: {e}")

    # ---------- W15 速查表 90 覆盖 ----------
    q90 = DOC / "辅助文档" / "90-收敛判据速查表.md"
    if q90.exists():
        t90 = q90.read_text(encoding="utf-8")
        ids90 = set(re.findall(r"\| ([A-H]\d+) \|", t90))
        all_ids = {n["id"] for n in load_nodes()}
        for miss in sorted(all_ids - ids90):
            a.add(SEV_BLOCKER, "W15", f"90-收敛判据速查表 缺少节点: {miss}", miss)
        for extra in sorted(ids90 - all_ids):
            a.add(SEV_WARN, "W15", f"90-收敛判据速查表 含未注册节点: {extra}", extra)
    else:
        a.add(SEV_BLOCKER, "W15", "90-收敛判据速查表 不存在")

    # ---------- W16 职责矩阵 91 覆盖 ----------
    q91 = DOC / "辅助文档" / "91-人机职责分配矩阵.md"
    if q91.exists():
        t91 = q91.read_text(encoding="utf-8")
        ids91 = set()
        for m in re.finditer(r"\| [A-H] \| ([A-H]\d+(?:[–-][A-H]\d+)?)", t91):
            ids91.update(expand_range(m.group(1).replace("–", "-")))
        all_ids = {n["id"] for n in load_nodes()}
        for miss in sorted(all_ids - ids91):
            a.add(SEV_BLOCKER, "W16", f"91-人机职责分配矩阵 缺少节点: {miss}", miss)
        for extra in sorted(ids91 - all_ids):
            a.add(SEV_WARN, "W16", f"91-人机职责分配矩阵 含未注册节点: {extra}", extra)
    else:
        a.add(SEV_BLOCKER, "W16", "91-人机职责分配矩阵 不存在")

    # ---------- W17 术语表覆盖 ----------
    q92 = DOC / "辅助文档" / "92-术语与缩写表.md"
    CORE_ABBR = {"REQ", "SC", "UC", "OI", "FS", "M", "FP", "CP", "BLOCK",
                 "ADR", "RMP", "RCR", "DoD", "SOP", "RTM", "PRD", "Fsys",
                 "AXI4", "SPI", "QSPI", "SCLK", "PIO", "MMIO", "XIP", "RIB",
                 "UART", "IIC", "PWM", "GPIO", "JTAG", "SRAM", "CDC", "LEC",
                 "STA", "WNS", "TNS", "SDC", "DRC", "CTS", "RTL", "SoC", "IP", "MCU"}
    if q92.exists():
        t92 = q92.read_text(encoding="utf-8")
        # 解析表格首列缩写（支持 "/" 复合与混合大小写如 SoC/Fsys/DoD）
        defined = set()
        for line in t92.splitlines():
            if not line.startswith("|") or "---" in line:
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 2:
                continue
            for part in re.split(r"[/\s]+", cells[0]):
                if part:
                    defined.add(part)
        for miss in sorted(CORE_ABBR - defined):
            a.add(SEV_WARN, "W17", f"术语表缺少核心缩写: {miss}", miss)
    else:
        a.add(SEV_BLOCKER, "W17", "92-术语与缩写表 不存在")

    # ---------- W14 多余文档提示 ----------
    node_docs = {DOC / n["doc"] for n in load_nodes()}
    extra = []
    for p in sorted(DOC.rglob("*.md")):
        if p in node_docs or p.name == "SOP.md" or "辅助文档" in p.parts or "设计" in p.parts:
            continue
        extra.append(str(p.relative_to(DOC)))
    if extra:
        a.add(SEV_INFO, "W14", f"非节点文档（非错误，仅提示）: {extra}")

    # ---------- 输出 ----------
    if args.json:
        print(json.dumps({
            "exit_code": 2 if a.blockers else (1 if a.warnings else 0),
            "summary": {"blockers": len(a.blockers), "warnings": len(a.warnings), "infos": len(a.infos)},
            "issues": a.issues,
        }, ensure_ascii=False, indent=2))
    elif not args.summary:
        for i in a.issues:
            loc = f" [{i['node']}]" if i["node"] else ""
            print(f"[{i['severity']:7s}] {i['check']}{loc}: {i['message']}")
    print(f"\n结论: Blocker={len(a.blockers)} Warning={len(a.warnings)} Info={len(a.infos)}")
    sys.exit(2 if a.blockers else (1 if a.warnings else 0))


if __name__ == "__main__":
    main()
