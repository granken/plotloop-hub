#!/usr/bin/env python3
"""Validate every loop under loops/ against the PlotLoop Hub contract.

Runs on external PRs with NO secrets available. See docs/SPEC.md §7.
Exit code 0 = all clear, 1 = at least one loop rejected.

Usage:
    python3 scripts/validate_loop.py [loops_dir]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

REPO = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO / "schema" / "loop.schema.json"

# The six LOOP.md sections, in order. Titles must match exactly — the
# receiving Agent locates parameters by these headings.
REQUIRED_SECTIONS = [
    "目标",
    "需要你提供",
    "信源",
    "触发",
    "产出格式与投递",
    "验收标准",
]

# Fenced blocks tagged with an executable language. LOOP.md declares intent;
# it never ships code. See SPEC.md §0 principle 2.
EXECUTABLE_FENCE = re.compile(
    r"^[ \t]*(?:```|~~~)[ \t]*"
    r"(bash|sh|zsh|shell|console|python|py|ruby|perl|node|js|javascript|ts|"
    r"typescript|powershell|ps1|bat|cmd|php|lua|r)\b",
    re.IGNORECASE | re.MULTILINE,
)

# Credential shapes. Deliberately broad — a false positive costs one review
# comment, a false negative leaks a live key.
SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("OpenAI-style key", re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}")),
    ("Anthropic key", re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{16,}")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}")),
    ("Slack token", re.compile(r"\bxox[abposr]-[A-Za-z0-9\-]{10,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Feishu app secret", re.compile(r"\b(?:cli_[a-z0-9]{16,}|[A-Za-z0-9]{32})\s*[:=]\s*['\"]?[A-Za-z0-9]{20,}")),
    ("Private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("JWT", re.compile(r"\bey[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}")),
    ("Inline assignment", re.compile(
        r"(?i)\b(api[_-]?key|secret|token|password|passwd|app[_-]?secret)\b\s*[:=]\s*"
        r"['\"][^'\"\s<>{}$]{12,}['\"]"
    )),
]

# Internal hosts must not leak through a public loop definition.
INTERNAL_URL = re.compile(
    r"https?://(?:localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|"
    r"172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+|[^/\s]*\.(?:internal|corp|intra|local))\b",
    re.IGNORECASE,
)

# Placeholders are the whole point of the "需要你提供" table — don't flag them.
PLACEHOLDER = re.compile(
    r"(?i)(<[^>]{1,40}>|\{\{[^}]{1,40}\}\}|\$\{?[A-Z_][A-Z0-9_]*\}?|"
    r"your[_-]|example|placeholder|xxx+|\*{4,}|\.{4,})"
)


class Report:
    def __init__(self, slug: str) -> None:
        self.slug = slug
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def ok(self) -> bool:
        return not self.errors


def scan_secrets(text: str, where: str, rep: Report) -> None:
    for line_no, line in enumerate(text.splitlines(), 1):
        if PLACEHOLDER.search(line):
            continue
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(line):
                rep.error(f"{where}:{line_no} 疑似泄漏凭证（{label}）——收录零容忍")
        if INTERNAL_URL.search(line):
            rep.error(f"{where}:{line_no} 含内部/私有网络地址")


def check_loop_md(path: Path, rep: Report) -> None:
    if not path.exists():
        rep.error("缺少 LOOP.md")
        return

    text = path.read_text(encoding="utf-8")
    scan_secrets(text, "LOOP.md", rep)

    if EXECUTABLE_FENCE.search(text):
        rep.error(
            "LOOP.md 含可执行代码块 —— 契约只允许声明。"
            "接收方 Agent 会照读这份文件，代码块是注入面（SPEC.md §0.2 / §7）"
        )

    headings = re.findall(r"^##[ \t]+(.+?)[ \t]*$", text, re.MULTILINE)
    normalized = [h.strip() for h in headings]
    missing = [s for s in REQUIRED_SECTIONS if s not in normalized]
    if missing:
        rep.error(f"LOOP.md 缺少必需小节（标题需一字不差）：{', '.join(missing)}")

    present = [h for h in normalized if h in REQUIRED_SECTIONS]
    expected_order = [s for s in REQUIRED_SECTIONS if s in present]
    if present != expected_order:
        rep.warn(f"LOOP.md 小节顺序与规范不一致：{present}")


def check_loop_yaml(path: Path, slug: str, rep: Report) -> dict | None:
    if not path.exists():
        rep.error("缺少 loop.yaml")
        return None

    raw = path.read_text(encoding="utf-8")
    scan_secrets(raw, "loop.yaml", rep)

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        rep.error(f"loop.yaml 解析失败：{exc}")
        return None

    if not isinstance(data, dict):
        rep.error("loop.yaml 顶层必须是对象")
        return None

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    for field in schema["required"]:
        if field not in data:
            rep.error(f"loop.yaml 缺少必填字段：{field}")

    if data.get("id") != slug:
        rep.error(f"loop.yaml 的 id ({data.get('id')!r}) 与目录名 ({slug!r}) 不一致")

    category = data.get("category")
    allowed = schema["properties"]["category"]["enum"]
    if category is not None and category not in allowed:
        rep.error(f"category {category!r} 不在 v1 枚举内：{allowed}")

    kind = data.get("kind")
    if kind is not None and kind not in ("public-feed", "pattern-only"):
        rep.error(f"kind {kind!r} 非法")

    # Default-private: a missing outputs field is treated as private, not public.
    vis = data.get("visibility")
    if isinstance(vis, dict):
        if "outputs" not in vis:
            rep.warn("visibility.outputs 缺省 —— 按 private 处理（SPEC.md §0.4）")
        if vis.get("outputs") == "public" and kind == "pattern-only":
            rep.error("pattern-only 的 loop 不得把 outputs 设为 public")
    else:
        rep.error("loop.yaml 缺少 visibility 段")

    # requires must declare names only, never values.
    for i, req in enumerate(data.get("requires") or []):
        if not isinstance(req, dict):
            rep.error(f"requires[{i}] 必须是对象")
            continue
        for field in ("key", "secret", "purpose"):
            if field not in req:
                rep.error(f"requires[{i}] 缺少 {field}")
        if "value" in req or "default" in req:
            rep.error(f"requires[{i}] 出现 value/default —— 契约禁止携带参数值")

    return data


def check_evidence(loop_dir: Path, data: dict | None, rep: Report) -> None:
    """Listing requires run evidence, not just a prompt. SPEC.md §0.5 / §5.

    A public-feed loop cannot produce Hub-hosted runs before it is merged, and
    cannot be merged without runs — so `status: unproven` is a staging state:
    the contract is checked, the loop is accepted into the repo, but
    build_site.py keeps it out of the public listing until a real run lands.
    """
    if not data:
        return
    kind = data.get("kind")
    status = (data.get("health") or {}).get("status")

    if kind == "public-feed":
        runs = sorted(loop_dir.glob("runs/*/*/*/manifest.json"))
        if not runs:
            if status == "unproven":
                rep.warn(
                    "public-feed 尚无运行档案 —— 按 staging 处理，"
                    "在产生第一次 GitHub-hosted run 之前不会公开展示"
                )
            else:
                rep.error(
                    f"kind: public-feed 且 status={status!r} 必须有真实运行档案 "
                    "(runs/YYYY/MM/YYYY-MM-DD-<id>/manifest.json)；"
                    "尚未跑过请把 health.status 设为 unproven"
                )
        elif status == "unproven":
            rep.warn("已有运行档案但 status 仍是 unproven —— 应由 update_health.py 回算")
        for manifest in runs:
            try:
                m = json.loads(manifest.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                rep.error(f"{manifest.relative_to(loop_dir)} 不是合法 JSON：{exc}")
                continue
            for field in ("run_id", "started_at", "status", "runtime"):
                if field not in m:
                    rep.error(f"{manifest.relative_to(loop_dir)} 缺少 {field}")
            # v1 only trusts GitHub-hosted runs; self-reported runs are not evidence.
            if m.get("status") == "success" and m.get("runtime") == "github-actions":
                if not m.get("workflow_run_url"):
                    rep.error(
                        f"{manifest.relative_to(loop_dir)} 标称 github-actions 成功运行"
                        " 但没有 workflow_run_url —— 无法审计"
                    )
            if not (loop_dir / manifest.parent / "output.md").exists():
                rep.error(f"{manifest.parent.relative_to(loop_dir)} 缺少 output.md")

    elif kind == "pattern-only":
        samples = [p for p in loop_dir.glob("samples/*") if p.is_file()]
        if not samples:
            rep.error("kind: pattern-only 必须有非空 samples/（脱敏样例产出）")
        for s in samples:
            scan_secrets(s.read_text(encoding="utf-8", errors="replace"),
                         f"samples/{s.name}", rep)
        if (loop_dir / "runs").exists():
            rep.error("pattern-only 的 loop 不得包含 runs/（产出必须私有）")


def validate(loop_dir: Path) -> Report:
    rep = Report(loop_dir.name)
    check_loop_md(loop_dir / "LOOP.md", rep)
    data = check_loop_yaml(loop_dir / "loop.yaml", loop_dir.name, rep)
    if not (loop_dir / "README.md").exists():
        rep.error("缺少 README.md")
    check_evidence(loop_dir, data, rep)
    return rep


def main() -> int:
    loops_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "loops"
    if not loops_dir.is_dir():
        print(f"找不到 loops 目录：{loops_dir}", file=sys.stderr)
        return 1

    dirs = sorted(p for p in loops_dir.iterdir() if p.is_dir() and not p.name.startswith("."))
    if not dirs:
        print("loops/ 下没有任何 loop")
        return 0

    failed = 0
    for d in dirs:
        rep = validate(d)
        if rep.ok and not rep.warnings:
            print(f"  ok      {rep.slug}")
        elif rep.ok:
            print(f"  ok(warn) {rep.slug}")
        else:
            failed += 1
            print(f"  FAIL    {rep.slug}")
        for w in rep.warnings:
            print(f"            warn: {w}")
        for e in rep.errors:
            print(f"            error: {e}")

    print(f"\n{len(dirs)} 个 loop，{failed} 个未通过")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
