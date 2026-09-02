#!/usr/bin/env python3
"""AI.gen_prodenv_doc.py — Production environment index generator.

Reads the 5 permanent AI.PRODENV.*.md category files and generates
AI/DOC.PRODENV.md — a names-only index for fast AI lookup.

The index answers "what exists in production?" without loading full bodies
or code. When the AI needs full detail (template bodies, automation code,
record rule domains) it reads the specific category file directly.

Source files read:
  AI/AI.PRODENV.TEMPLATES.md
  AI/AI.PRODENV.ACTIONS.md
  AI/AI.PRODENV.CRONS.md
  AI/AI.PRODENV.RULES.md
  AI/AI.PRODENV.REPORTS.md

(AI.PRODENV.MODULES.md is intentionally excluded — it is transient and may
already have been deleted by AI.canary.py.)

Output:
  AI/DOC.PRODENV.md — names-only index with provenance tags; SOURCE-HASH on
  line 2 for canary staleness detection.

Usage:
  python3 AI/AI.gen_prodenv_doc.py

Exit status:
  0 = DOC.PRODENV.md written
  1 = no PRODENV category files found (nothing to index)

AI.canary.py runs this script automatically when:
  - AI.PRODENV.MODULES.md is applied (canary triggers it immediately after)
  - DOC.PRODENV.md is missing or stale (SOURCE-HASH mismatch)

Odoo version: 19.0
"""

import hashlib
import re
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT     = SCRIPT_DIR / "DOC.PRODENV.md"

CATEGORY_FILES = [
    ("TEMPLATES", SCRIPT_DIR / "AI.PRODENV.TEMPLATES.md"),
    ("ACTIONS",   SCRIPT_DIR / "AI.PRODENV.ACTIONS.md"),
    ("CRONS",     SCRIPT_DIR / "AI.PRODENV.CRONS.md"),
    ("RULES",     SCRIPT_DIR / "AI.PRODENV.RULES.md"),
    ("REPORTS",   SCRIPT_DIR / "AI.PRODENV.REPORTS.md"),
]

# Section heading patterns in each category file
SECTION_TITLES = {
    "TEMPLATES": [("Mail Templates",    "mail.template")],
    "ACTIONS":   [("Automated Actions", "base.automation"),
                  ("Server Actions",    "ir.actions.server")],
    "CRONS":     [("Scheduled Actions / Cron", "ir.cron")],
    "RULES":     [("Record Rules",      "ir.rule")],
    "REPORTS":   [("Reports",           "ir.actions.report")],
}


# ---------------------------------------------------------------------------
# Source hash
# ---------------------------------------------------------------------------

def _strip_generated_line(text: str) -> str:
    """Remove the 'Generated: YYYY-MM-DD' date line so hash is date-stable."""
    return re.sub(r'^Generated:.*$', '', text, flags=re.MULTILINE)


def source_hash() -> str:
    """12-hex SHA256 of the 5 category files (date lines excluded)."""
    h = hashlib.sha256()
    for _, path in CATEGORY_FILES:
        if path.exists():
            h.update(_strip_generated_line(
                path.read_text(encoding="utf-8", errors="ignore")
            ).encode("utf-8"))
    return h.hexdigest()[:12]


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_section(text: str, heading: str):
    """Extract entry lines from a '## <heading>' section.

    Returns a list of (name, tags_dict) where name is the record name and
    tags_dict contains optional keys: 'source', 'model', 'output'.

    A record starts with '### name  [source]' and is followed by metadata
    lines beginning with '- '.
    """
    # Find the section
    m = re.search(
        r'^## ' + re.escape(heading) + r'\b[^\n]*\n(.*?)(?=^## |\Z)',
        text, re.DOTALL | re.MULTILINE,
    )
    if not m:
        return []

    block = m.group(1)
    entries = []
    current_name = None
    current_tags = {}

    for line in block.splitlines():
        if line.startswith('### '):
            # Save previous entry
            if current_name is not None:
                entries.append((current_name, current_tags))
            # Parse: ### Name  [source tag]
            rest = line[4:].strip()
            src_m = re.search(r'(\[(?:UI-created|custom:[^\]]+|odoo:[^\]]+)\])\s*$', rest)
            if src_m:
                current_name = rest[:src_m.start()].strip()
                current_tags = {'source': src_m.group(1)}
            else:
                current_name = rest
                current_tags = {}
        elif line.startswith('- Model:') and current_name is not None:
            current_tags['model'] = line[8:].strip()
        elif line.startswith('- Output:') and current_name is not None:
            current_tags['output'] = line[9:].strip()

    if current_name is not None:
        entries.append((current_name, current_tags))

    return entries


def _format_entry(name: str, tags: dict) -> str:
    """Format one index line: '  Name  [source]  [model: X]  [output: Y]'"""
    parts = [f"  {name}"]
    if 'source' in tags:
        parts.append(tags['source'])
    if 'model' in tags:
        parts.append(f"[model: {tags['model']}]")
    if 'output' in tags:
        parts.append(f"[output: {tags['output']}]")
    return '  '.join(parts)


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate() -> int:
    """Generate DOC.PRODENV.md. Returns 0 on success, 1 if no source files."""
    present = [(key, path) for key, path in CATEGORY_FILES if path.exists()]
    if not present:
        print("AI.gen_prodenv_doc: no AI.PRODENV.*.md category files found — "
              "run AI.gen_prodenv.py on staging first.", file=sys.stderr)
        return 1

    present_names = [path.name for _, path in present]
    today = date.today().isoformat()
    shash = source_hash()

    lines = [
        "# Production Environment Index",
        f"# SOURCE-HASH: prodenv={shash}",
        f"Generated: {today}",
        f"Source: {', '.join(present_names)}",
        "",
        "For full detail (code, template bodies, rule domains) read the relevant",
        "category file in AI/. This index lists names and provenance only.",
        "",
    ]

    total_entries = 0

    for key, path in CATEGORY_FILES:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")

        for heading, _model in SECTION_TITLES.get(key, []):
            entries = _parse_section(text, heading)
            if not entries:
                continue
            # Extract count from the heading line if present (e.g. "Mail Templates  (12 active)")
            count_m = re.search(
                r'^## ' + re.escape(heading) + r'\b[^\n]*\((\d+)[^\)]*\)',
                text, re.MULTILINE,
            )
            count_str = f" ({count_m.group(1)})" if count_m else f" ({len(entries)})"
            lines.append(f"## {heading}{count_str}")
            for name, tags in entries:
                lines.append(_format_entry(name, tags))
            lines.append("")
            total_entries += len(entries)

    if total_entries == 0:
        print("AI.gen_prodenv_doc: category files exist but contain no ### entries.",
              file=sys.stderr)
        return 1

    content = "\n".join(lines)

    # Atomic write
    tmp = OUTPUT.with_suffix(".md.tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(OUTPUT)

    print(f"AI.gen_prodenv_doc: wrote {OUTPUT.name} "
          f"({total_entries} entries, SOURCE-HASH: prodenv={shash})")
    return 0


if __name__ == "__main__":
    sys.exit(generate())
