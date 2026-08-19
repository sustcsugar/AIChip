---
name: ip-discipline
description: IP 只读纪律：强制任何 agent 不得修改 ip_manifest.json 锁定的 IP 源码。当任务涉及 work/ip/ 下的文件、或可能修改被 manifest 引用的 IP 目录时使用。也用于 SoC 侧 RTL 引用 IP 的合规检查。
---

# IP Discipline — IP 只读纪律

## 核心规则

**任何 agent 不得修改 `ip_manifest.json` 中锁定的 IP 目录内的文件。** 这是复用纪律的硬约束。

## 适用场景

- 编辑/写入 `work/ip/<ip>/` 下的任何文件（rtl/doc/tb/vip/model/constraint）
- 在 SoC 侧 RTL 中引用 IP 模块
- 需求变更涉及 IP 功能

## 执行规则

1. **修改 IP 前**：先读 `work/soc/ip_manifest.json`，确认目标是否被锁定
2. **锁定目录内**：一律拒绝修改。正确路径：
   - 需求变更 → 回 IP 项目，走 IP 项目内部收敛环 → 发布新版本 tag
   - SoC 侧适配 → 在 `work/soc/rtl/glue_logic/` 或 `work/soc/rtl/soc_top/` 做适配，不改 IP 本身
3. **升级版本**：IP 发布新版本后，在 manifest 更新 `version` 字段，并触发 C0 合同验证
4. **引用检查**：SoC RTL 引用 IP 路径必须来自 manifest（`python scripts/build_manifest.py` 解析），禁止硬编码路径

## 异常处理

- 若确需修改 IP（紧急 bug 且无发布流程）：
  1. 显式向人类报告，取得明确书面授权
  2. 记录到 `state/decisions.md`（含理由与授权人）
  3. 修复必须回流到 IP 项目，确保 IP 项目内修复生效，避免只改 SoC 侧拷贝