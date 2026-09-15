"""Formatting helpers and approval-gated MarketMate exports."""

import json
import re
from pathlib import Path


def text(value):
    # Escape HTML and Markdown metacharacters from untrusted product data.
    import html

    return re.sub(r"([\\\x60*_{}\[\]<>|])", r"\\\1", html.escape(str(value))).replace("\n", " ")


def claim_text(c):
    return f"{text(c.text)} [{c.source_id}]" if c else "Not verified"


def export_report(state, destination: Path):
    from market_research.market_reporting import render_market_report

    if not state.get("approved") or state.get("status") != "approved":
        raise PermissionError("Approve the current draft before export.")
    destination.mkdir(parents=True, exist_ok=True)
    for filename, content in (
        ("briefing.md", render_market_report(state)),
        ("briefing.json", json.dumps(state, indent=2, ensure_ascii=False)),
    ):
        temp = destination / (filename + ".tmp")
        temp.write_text(content, encoding="utf-8")
        temp.replace(destination / filename)
    return destination
