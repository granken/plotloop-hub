#!/usr/bin/env python3
"""Execute due loops and write their run archives.

    ⚠️  SCAFFOLD — NOT IMPLEMENTED.

This is the one part of the Hub that cannot be written before the 30-day
validation gate answers a question we do not yet have data for: whether loops
run *in* the Hub (hosted, one runner for everyone) or *from* the Hub (each
person's own agent, Hub stores only the evidence).

Those two designs need different code, and picking one now would be guessing.
See docs/SPEC.md §10 (validation gate) and §5 (run evidence).

What it must do once the shape is decided:

  1. Read every loops/*/loop.yaml, select those due per trigger.schedule.
  2. Invoke the loop through whatever runtime was chosen, passing credentials
     from the environment — never from the loop definition (SPEC.md §0.3).
  3. Write runs/YYYY/MM/YYYY-MM-DD-<run-id>/ containing:
       output.md      — the de-identified result
       manifest.json  — run_id, started_at, ended_at, status, runtime,
                        workflow_run_url, commit_sha, input_hash, output_hash,
                        items_count, cost
       sources.json   — per-source URL, fetch time, content hash
  4. Record the REAL started_at. GitHub delays scheduled runs; the nominal cron
     time is not what happened (SPEC.md §8).
  5. Write nothing when there is no new material — that is both the append-only
     rule and the product rule "无新意不发".
  6. Never write runs/ for a pattern-only loop (SPEC.md §1).

Exits 1 so nothing downstream mistakes an unimplemented step for a clean run.
"""

import sys

BANNER = """\
run_loops.py 尚未实现 —— 这是有意的。

Loop 的执行模型要等 30 天验证闸门的结果才能定：
  A. 托管执行  —— Hub 提供 runner，所有人的 loop 在这里跑
  B. 自持执行  —— 各自的 Agent 在自己环境跑，Hub 只存运行证据

两种设计的代码不一样，现在选就是猜。见 docs/SPEC.md §10。

当前可用的是契约与校验链路：
  scripts/validate_loop.py     校验投稿是否合规（已实现）
  scripts/check_staleness.py   检测 loop 是否悄悄停产（已实现）
  scripts/update_health.py     从运行档案回算健康度（已实现）
  scripts/build_site.py        生成目录站与 feed（脚手架）
"""


def main() -> int:
    print(BANNER, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
