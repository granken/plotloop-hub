#!/usr/bin/env python3
"""Recompute each loop's health block from its run archive.

health is derived, never authored: the commit history is the evidence, and a
hand-written streak is exactly the kind of unverifiable claim this Hub exists to
avoid. validate_loop.py warns when these fields look hand-edited.

Usage:
    python3 scripts/update_health.py [--dry-run]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

REPO = Path(__file__).resolve().parent.parent

HEALTH_BLOCK = re.compile(r"^health:\n(?:[ \t]+.*\n?)*", re.MULTILINE)


def collect_runs(loop_dir: Path) -> list[tuple[dt.date, dict]]:
    runs: list[tuple[dt.date, dict]] = []
    for manifest in loop_dir.glob("runs/*/*/*/manifest.json"):
        try:
            date = dt.date.fromisoformat(manifest.parent.name[:10])
        except ValueError:
            continue
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
        runs.append((date, data))
    return sorted(runs, key=lambda r: r[0])


def streak(dates: list[dt.date], today: dt.date) -> int:
    """Consecutive days ending at today or yesterday.

    Yesterday still counts: a scheduled run can be delayed past midnight by
    GitHub's queue, and penalising that would make the metric noise.
    """
    if not dates:
        return 0
    unique = sorted(set(dates), reverse=True)
    if (today - unique[0]).days > 1:
        return 0
    count, cursor = 1, unique[0]
    for d in unique[1:]:
        if (cursor - d).days == 1:
            count += 1
            cursor = d
        else:
            break
    return count


def replay_rate(runs: list[tuple[dt.date, dict]]) -> float | None:
    """Success rate of runs explicitly marked as fresh-environment replays."""
    replays = [d for _, d in runs if d.get("replay") is True]
    if not replays:
        return None
    ok = sum(1 for d in replays if d.get("status") == "success")
    return round(ok / len(replays), 3)


def classify(loop_dir: Path, cfg: dict, runs: list, today: dt.date) -> dict:
    from check_staleness import period_days  # same repo, same assumptions

    if cfg.get("kind") != "public-feed":
        return {"last_run": None, "streak_days": 0, "runs_total": 0,
                "status": "unproven", "replay_success_rate": None}

    if not runs:
        return {"last_run": None, "streak_days": 0, "runs_total": 0,
                "status": "unproven", "replay_success_rate": None}

    dates = [d for d, _ in runs]
    last = max(dates)
    age = (today - last).days
    expected = period_days((cfg.get("trigger") or {}).get("schedule", "0 0 * * *"))
    rate = replay_rate(runs)

    if age > expected * 5:
        status = "broken"
    elif age > expected * 2:
        status = "stale"
    elif rate is not None and rate < 0.8:
        # SPEC.md §6: below 80% first-run success is not a healthy loop.
        status = "broken"
    else:
        status = "healthy"

    return {
        "last_run": last.isoformat(),
        "streak_days": streak(dates, today),
        "runs_total": len(runs),
        "status": status,
        "replay_success_rate": rate,
    }


def render(health: dict) -> str:
    def fmt(v):
        if v is None:
            return "null"
        if isinstance(v, bool):
            return "true" if v else "false"
        return str(v)

    lines = ["health:"]
    for key in ("last_run", "streak_days", "runs_total", "status", "replay_success_rate"):
        lines.append(f"  {key}: {fmt(health[key])}")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    today = dt.date.today()
    changed = 0

    for loop_dir in sorted(p for p in (REPO / "loops").iterdir() if p.is_dir()):
        cfg_path = loop_dir / "loop.yaml"
        if not cfg_path.exists():
            continue
        raw = cfg_path.read_text(encoding="utf-8")
        cfg = yaml.safe_load(raw) or {}

        health = classify(loop_dir, cfg, collect_runs(loop_dir), today)
        block = render(health)

        new = HEALTH_BLOCK.sub(block, raw) if HEALTH_BLOCK.search(raw) else raw.rstrip() + "\n\n" + block

        if new != raw:
            changed += 1
            print(f"  {cfg.get('id', loop_dir.name)}: {health['status']} "
                  f"(streak {health['streak_days']}, runs {health['runs_total']})")
            if not args.dry_run:
                cfg_path.write_text(new, encoding="utf-8")

    print(f"\n{changed} 个 loop 的 health 有变化" + ("（dry-run，未写入）" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
