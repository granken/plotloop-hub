#!/usr/bin/env python3
"""Detect loops that have quietly stopped producing.

Called weekly by keepalive.yml. Exits 1 when anything is stale or broken, which
is what makes the workflow open an issue.

The failure this guards against is silent: a loop whose source site changed
layout keeps "succeeding" while producing nothing, and a schedule disabled by
GitHub's 60-day inactivity rule produces no error at all. Neither shows up
anywhere unless something explicitly looks for missing output.

Usage:
    python3 scripts/check_staleness.py [--out SUMMARY_FILE]
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

REPO = Path(__file__).resolve().parent.parent

# Nominal period per cron shape, in days. Coarse on purpose — this is a
# staleness alarm, not a scheduler.
def period_days(cron: str) -> float:
    fields = cron.split()
    if len(fields) != 5:
        return 1.0
    minute, hour, dom, month, dow = fields
    if dom == "*" and dow == "*" and hour == "*":
        return 1 / 24
    if dom == "*" and dow == "*":
        return 1.0
    if dow != "*":
        return 7.0
    return 30.0


def latest_run_date(loop_dir: Path) -> dt.date | None:
    dates: list[dt.date] = []
    for manifest in loop_dir.glob("runs/*/*/*/manifest.json"):
        # Directory name is YYYY-MM-DD-<id>; trust the path, not the JSON,
        # so a malformed manifest still counts as evidence of a run.
        stem = manifest.parent.name
        try:
            dates.append(dt.date.fromisoformat(stem[:10]))
        except ValueError:
            continue
    return max(dates) if dates else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, help="append a Markdown summary here")
    args = ap.parse_args()

    today = dt.date.today()
    rows: list[tuple[str, str, str]] = []
    problems = 0

    loops_dir = REPO / "loops"
    for loop_dir in sorted(p for p in loops_dir.iterdir() if p.is_dir()):
        cfg_path = loop_dir / "loop.yaml"
        if not cfg_path.exists():
            continue
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        slug = cfg.get("id", loop_dir.name)
        kind = cfg.get("kind")

        # pattern-only loops never publish runs; absence of output is correct.
        if kind != "public-feed":
            rows.append((slug, "—", "pattern-only，不参与健康度"))
            continue

        status = (cfg.get("health") or {}).get("status")
        if status == "unproven":
            rows.append((slug, "unproven", "尚未在 Hub 内产生可审计运行记录"))
            continue

        last = latest_run_date(loop_dir)
        if last is None:
            problems += 1
            rows.append((slug, "broken", "public-feed 但没有任何 run"))
            continue

        expected = period_days((cfg.get("trigger") or {}).get("schedule", "0 0 * * *"))
        age = (today - last).days

        if age > expected * 5:
            problems += 1
            rows.append((slug, "broken", f"已 {age} 天无新产出（周期约 {expected:g} 天）"))
        elif age > expected * 2:
            problems += 1
            rows.append((slug, "stale", f"已 {age} 天无新产出（周期约 {expected:g} 天）"))
        else:
            rows.append((slug, "healthy", f"最近产出 {last}"))

    lines = ["## Loop 健康度检查", "", f"检查日期：{today}", "",
             "| loop | 状态 | 说明 |", "|---|---|---|"]
    lines += [f"| `{s}` | {st} | {note} |" for s, st, note in rows]
    lines.append("")
    lines.append(
        f"**{problems} 个 loop 需要处理。**" if problems
        else "**全部正常。**"
    )
    report = "\n".join(lines)

    print(report)
    if args.out:
        with args.out.open("a", encoding="utf-8") as fh:
            fh.write(report + "\n")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
