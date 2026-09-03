#!/usr/bin/env python3
"""Build index.json and the per-loop / global feeds.

Partially implemented: index.json is real, the HTML site is a scaffold.

index.json is the piece worth having first — it is the machine-readable catalogue
the "one-line install" depends on, and it is what any front end (or someone
else's front end) would be built against. The HTML can follow.

Usage:
    python3 scripts/build_site.py [--out site]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

REPO = Path(__file__).resolve().parent.parent
HUB_URL = "https://hub.plotloop.dev"

# Fields that are safe to expose regardless of a loop's visibility settings.
# Outputs and run contents are gated separately — see gate_outputs().
PUBLIC_META = ("id", "title", "summary", "category", "kind", "tags", "created")


def gate_outputs(cfg: dict) -> bool:
    """Default-private: anything not explicitly public stays private.

    SPEC.md §0.4. A missing visibility block must not read as consent.
    """
    vis = cfg.get("visibility") or {}
    return vis.get("outputs") == "public"


def latest_run(loop_dir: Path) -> dict | None:
    manifests = sorted(loop_dir.glob("runs/*/*/*/manifest.json"),
                       key=lambda p: p.parent.name, reverse=True)
    if not manifests:
        return None
    try:
        m = json.loads(manifests[0].read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return {
        "date": manifests[0].parent.name[:10],
        "status": m.get("status"),
        "items_count": m.get("items_count"),
        # The audit trail, not a proof. SPEC.md §5.
        "workflow_run_url": m.get("workflow_run_url"),
        "commit_sha": m.get("commit_sha"),
    }


def build_index() -> dict:
    entries = []
    for loop_dir in sorted(p for p in (REPO / "loops").iterdir() if p.is_dir()):
        cfg_path = loop_dir / "loop.yaml"
        if not cfg_path.exists():
            continue
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}

        entry = {k: cfg.get(k) for k in PUBLIC_META}
        entry["health"] = cfg.get("health") or {}
        entry["url"] = f"{HUB_URL}/l/{cfg.get('id')}"
        entry["install"] = (
            f"把 {HUB_URL}/l/{cfg.get('id')} 读完，"
            "按里面的 LOOP.md 在我的环境里搭一遍，缺什么参数问我。"
        )
        entry["requires"] = [
            {"key": r.get("key"), "secret": r.get("secret"), "purpose": r.get("purpose")}
            for r in (cfg.get("requires") or [])
        ]
        entry["dependencies"] = cfg.get("dependencies") or []

        # Staging: contract-valid but no Hub-hosted run yet. Carried in the
        # index so tooling can see it, flagged so no front end lists it as live.
        entry["listed"] = not (
            cfg.get("kind") == "public-feed"
            and (cfg.get("health") or {}).get("status") == "unproven"
        )

        # A feed URL is only advertised once there is something behind it —
        # both the author must have opted in AND a run must exist.
        if gate_outputs(cfg) and entry["listed"]:
            entry["latest_run"] = latest_run(loop_dir)
            entry["feed"] = f"{HUB_URL}/l/{cfg.get('id')}/feed.xml"
        else:
            entry["latest_run"] = None
            entry["feed"] = None
            entry["outputs_note"] = (
                "尚未产生可审计运行，暂不提供订阅" if not entry["listed"]
                else "产出私有；本 loop 只分享定义与脱敏样例"
            )

        entries.append(entry)

    listed = [e for e in entries if e["listed"]]
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "spec_version": "0.2",
        "count": len(listed),
        "staging_count": len(entries) - len(listed),
        "loops": entries,
    }


def _json_default(obj):
    # PyYAML turns `created: 2026-06-01` into a date, which json cannot encode.
    if isinstance(obj, (dt.date, dt.datetime)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=REPO / "site")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    index = build_index()
    payload = json.dumps(index, ensure_ascii=False, indent=2, default=_json_default) + "\n"
    (REPO / "index.json").write_text(payload, encoding="utf-8")
    (args.out / "index.json").write_text(payload, encoding="utf-8")

    print(f"index.json: {index['count']} 个 loop")
    for e in index["loops"]:
        gated = ("" if e["listed"] else "  [staging]") + ("" if e["feed"] else "  [产出私有]")
        print(f"  {e['id']}  {(e['health'] or {}).get('status')}{gated}")

    print("\n⚠️  HTML 站点生成尚未实现 —— 只产出了 index.json。", file=sys.stderr)
    print("    目录壳候选：minted-directory-astro", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
