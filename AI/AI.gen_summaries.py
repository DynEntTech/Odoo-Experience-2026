#!/usr/bin/env python3
"""
AI.gen_summaries.py
Generates the four DOC.CUSTOM.by.* summary files from the >>ADDON: blocks
in AI.CUSTOM.md, each stamped with the current 'addons' SOURCE-HASH.

Usage:
    python3 AI/AI.gen_summaries.py

Writes the files in place, atomically (tmp + rename — no shell redirection,
and no truncated or empty-file hazards):
    DOC.CUSTOM.by.App.md      grouped by APP, alphabetical
    DOC.CUSTOM.by.Impact.md   grouped Major → Intermediate → Minor
    DOC.CUSTOM.by.Alpha.md    single flat table
    DOC.CUSTOM.by.Type.md     grouped by TYPE — an addon appears once per type

Everything here is deterministic re-formatting of block data — no judgment.
The output format is specified in AI.SPECS.ADDONS.md (DOC.CUSTOM.by.* specs);
this script is the executable form of that spec — change the two together.
The DOC.CONFLICTS.* registers are NOT generated here: conflict analysis is
judgment work, done by AI prompt.

Parsing, hashing, and the COVERAGE read are imported from AI.canary.py
(parse_addons, addons_source_hash, parse_coverage) so the two scripts can
never disagree on definitions. Value VALIDATION stays the canary's job —
this script refuses only when rendering would be undefined:

Refuses (exit 1, nothing written) when:
  - AI.CUSTOM.md has no >>ADDON: blocks (nothing to summarize)
  - any block is missing STATUS, PURPOSE, IMPACT, TYPE, or APP, or the
    COVERAGE line is missing/unparsable — run AI.canary.py, fix its
    findings, then re-run

Conventions implemented (mirrored in AI.SPECS.ADDONS.md):
  - ⚠️ appended to the addon name when its STATUS is not installed
    (classified the same lax way as the canary's STATUS cross-check)
  - PURPOSE trimmed to its first 80 characters when longer (the same cap
    AI.gen_enterprise.py uses for manifest summaries), then any '|'
    backslash-escaped (markdown table-cell safety)
  - a typo'd IMPACT/TYPE/APP value renders as-is (or, in by.Type, drops
    from the fixed groups) — the canary reports it as MALFORMED BLOCK
"""

import importlib.util
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ADDONS_AI = SCRIPT_DIR / "AI.CUSTOM.md"

IMPACT_ORDER = ("Major", "Intermediate", "Minor")   # fixed, not alphabetical
TYPE_ORDER = ("Integration", "Override", "Read-Only", "UI", "Updates")  # alphabetical


def _canary():
    """Load AI.canary.py as a module — shared parser and hash definitions."""
    spec = importlib.util.spec_from_file_location(
        "ai_canary", SCRIPT_DIR / "AI.canary.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def display_name(name, info):
    """Addon name, with ⚠️ appended when not installed in production
    (same lax classification as the canary's STATUS cross-check)."""
    status = info["status"] or ""
    return f"{name} ⚠️" if status.lower().startswith("not installed") else name


def purpose(info):
    # trim first (the 80-char cap applies to the visible text), then escape
    # '|' as \| — a bare pipe would silently shift every later cell in the
    # markdown table row (mirrored in AI.SPECS.ADDONS.md's shared
    # conventions — change the two together)
    return (info["purpose"] or "").strip()[:80].rstrip().replace("|", "\\|")


def table(rows, headers):
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def main():
    canary = _canary()
    addons = canary.parse_addons(ADDONS_AI)
    if not addons:
        sys.stderr.write(
            "ERROR: no >>ADDON: blocks in AI.CUSTOM.md — nothing to "
            "summarize; the DOC.CUSTOM.by.* files are not expected yet.\n")
        return 1
    bad = sorted(a for a, i in addons.items()
                 if not all((i["status"], i["purpose"], i["impact"],
                             i["type"], i["app"])))
    coverage = canary.parse_coverage(ADDONS_AI)
    if bad or coverage is None:
        sys.stderr.write(
            "ERROR: cannot generate — rendering would be undefined:\n"
            + (f"  blocks missing required fields: {', '.join(bad)}\n"
               if bad else "")
            + ("  COVERAGE line missing or unparsable\n"
               if coverage is None else "")
            + "Run AI.canary.py, fix its findings, then re-run.\n")
        return 1

    n, total = coverage
    today = date.today().strftime("%Y-%m-%d")
    stamp = f"# SOURCE-HASH: addons={canary.addons_source_hash(ADDONS_AI)}"
    head2 = (f"# {n} of {total} documented · Updated: {today} · "
             f"⚠️ = not installed in production")
    # alphabetical by addon name throughout — case-insensitive: custom
    # folder names may carry uppercase (see the FORMAT note in AI.SESSION.md)
    items = sorted(addons.items(), key=lambda kv: kv[0].lower())

    files = {}

    parts = ["# Custom Addons Summary — by App", head2, stamp]
    # case-insensitive: eCommerce/eLearning sort under E, never after Website
    for app in sorted({i["app"] for _, i in items}, key=str.lower):
        rows = [[display_name(a, i), i["impact"], i["type"], purpose(i)]
                for a, i in items if i["app"] == app]
        parts += ["", f"## {app}", "",
                  table(rows, ["Addon", "Impact", "Type", "Purpose"])]
    files["DOC.CUSTOM.by.App.md"] = "\n".join(parts) + "\n"

    parts = ["# Custom Addons Summary — by Impact", head2, stamp]
    for imp in IMPACT_ORDER:
        rows = [[display_name(a, i), i["app"], i["type"], purpose(i)]
                for a, i in items if i["impact"] == imp]
        if rows:
            parts += ["", f"## {imp}", "",
                      table(rows, ["Addon", "App", "Type", "Purpose"])]
    files["DOC.CUSTOM.by.Impact.md"] = "\n".join(parts) + "\n"

    rows = [[display_name(a, i), i["app"], i["impact"], i["type"], purpose(i)]
            for a, i in items]
    files["DOC.CUSTOM.by.Alpha.md"] = "\n".join(
        ["# Custom Addons Summary — Alphabetical", head2, stamp, "",
         table(rows, ["Addon", "App", "Impact", "Type", "Purpose"])]) + "\n"

    parts = ["# Custom Addons Summary — by Type", head2, stamp]
    for t in TYPE_ORDER:
        rows = [[display_name(a, i), i["app"], i["impact"], purpose(i)]
                for a, i in items
                if t in [x.strip() for x in i["type"].split(",")]]
        if rows:
            parts += ["", f"## {t}", "",
                      table(rows, ["Addon", "App", "Impact", "Purpose"])]
    files["DOC.CUSTOM.by.Type.md"] = "\n".join(parts) + "\n"

    for fname, content in files.items():
        tmp = SCRIPT_DIR / (fname + ".tmp")
        try:
            tmp.write_text(content, encoding="utf-8")
            tmp.replace(SCRIPT_DIR / fname)   # atomic — never a truncated summary
        except BaseException:
            tmp.unlink(missing_ok=True)      # no stray .tmp after a failed run
            raise
        print(f"wrote {fname}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
