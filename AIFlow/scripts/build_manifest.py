#!/usr/bin/env python3
"""解析 ip_manifest.json（芯片根），输出 SoC 构建文件列表。

用法:
    python AIFlow/scripts/build_manifest.py [--manifest ip_manifest.json]
    python AIFlow/scripts/build_manifest.py --ips           # 只列 IP 版本
    python AIFlow/scripts/build_manifest.py --filelist      # 列出全部 IP RTL 文件
"""
import argparse
import json
import sys
from pathlib import Path

import sys
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent  # AIFlow/（共治管理层）
DEFAULT = ROOT.parent / "ip_manifest.json"  # 芯片根

RTL_EXTS = {".v", ".sv", ".vh", ".svh"}


def load(manifest: Path) -> dict:
    if not manifest.exists():
        raise SystemExit(f"manifest 不存在: {manifest}")
    return json.loads(manifest.read_text(encoding="utf-8"))


def resolve(manifest: Path, path: str) -> Path:
    p = Path(path)
    if not p.is_absolute():
        p = (manifest.parent / p).resolve()
    return p


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=str(DEFAULT))
    ap.add_argument("--ips", action="store_true", help="只列 IP 版本")
    ap.add_argument("--filelist", action="store_true", help="列出全部 IP RTL 文件")
    args = ap.parse_args()

    manifest = Path(args.manifest)
    data = load(manifest)
    print(f"# SoC 版本: {data['soc_version']}  (manifest: {manifest.resolve()})")

    for name, cfg in data["ips"].items():
        base = resolve(manifest, cfg["path"])
        if args.ips:
            print(f"{name}: {cfg['version']} mode={cfg['mode']} @ {base}")
            continue
        if args.filelist:
            if cfg["mode"] == "model":
                print(f"# {name}: model 模式，引用 {base}/model/")
                for f in sorted((base / "model").glob("*")):
                    if f.suffix in RTL_EXTS or f.suffix == ".svh":
                        print(f"  {f}")
            else:
                for f in sorted((base / "rtl").rglob("*")):
                    if f.suffix in RTL_EXTS:
                        print(f"  {f}")
            continue
        print(f"{name}: version={cfg['version']} mode={cfg['mode']} path={base}")
        if not base.exists():
            print(f"  !!! 路径不存在: {base}")


if __name__ == "__main__":
    main()