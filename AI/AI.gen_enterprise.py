#!/usr/bin/env python3
"""
AI.gen_enterprise.py
Generates AI.ENTERPRISE.md — a reference index of all Enterprise modules
with their install status and a one-line manifest summary each.

Usage:
    python3 AI/AI.gen_enterprise.py

Writes AI.ENTERPRISE.md next to this script, atomically (tmp + rename —
never a truncated or empty index), and prints the same document to
stdout. Do not use a stdout redirect — it creates AI.ENTERPRISE.md at
the invoking directory (repo root) rather than in AI/ where it belongs.

Installed module list is read from AI.CUSTOM.md — not the database —
because this runs in a dev environment whose database does not reflect
the production module state.

Exit status:
  0 = index generated and written
  1 = refused — the INSTALLED MODULES section of AI.CUSTOM.md still
      contains a (NOT YET POPULATED) marker; nothing was written
"""

import ast
import hashlib
import re
import sys
from datetime import date
from pathlib import Path

# Self-locating: AI.CUSTOM.md sits next to this script, so it is found in any
# checkout of the repo. ENTERPRISE and ODOO_RELEASE point outside the repo at
# platform-installed sources (Odoo.sh layout) and stay absolute — off-platform
# the version is simply omitted and the module directory comes out empty.
ADDONS_AI    = Path(__file__).resolve().parent / "AI.CUSTOM.md"
OUTPUT       = Path(__file__).resolve().parent / "AI.ENTERPRISE.md"
ENTERPRISE   = Path("/home/odoo/src/enterprise")
ODOO_RELEASE = Path("/home/odoo/src/odoo/odoo/release.py")


# ---------------------------------------------------------------------------
# Detect the Odoo version from the environment
# ---------------------------------------------------------------------------

def detect_odoo_version() -> str:
    """
    Read the Odoo series (e.g. '19.0') from the environment's release.py,
    parsing the version_info tuple:  version_info = (19, 0, 0, FINAL, 0, '')
    Returns '' if the file is missing or unparsable — callers must degrade
    gracefully (omit the version rather than fail).
    """
    try:
        text = ODOO_RELEASE.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    m = re.search(r'^version_info\s*=\s*\(\s*(\d+)\s*,\s*(\d+)', text, re.MULTILINE)
    return f"{m.group(1)}.{m.group(2)}" if m else ""

# ---------------------------------------------------------------------------
# Parse installed Enterprise module list from AI.CUSTOM.md
# ---------------------------------------------------------------------------

def parse_installed_enterprise(path: Path) -> set:
    """
    Extract the list of installed Enterprise module names from the
    ODOO ENTERPRISE subsection at the top of AI.CUSTOM.md.

    Anchoring is structural, not positional: the subsection is located by its
    HEADER LINE SHAPE — line-start "#", indented ALL-CAPS name, then a colon
    at end of line (e.g. "#   ODOO ENTERPRISE (⚠️ ...):"). The capture ends at
    the next sibling subsection header of the same shape (any of them,
    including ODOO THEMES — reorder-proof) or at the "# COUNTRIES:" data
    line, with the "# APPS (baseline …):" data line as a fallback boundary
    (COUNTRIES may legally be absent; without a boundary the capture would
    run on and read bare-word comment lines below as phantom modules — the
    APPS line, unlike COUNTRIES, is policed to exist by AI.canary.py's
    check 11; same terminator set as AI.canary.parse_not_installed_list —
    change the two together). A mere prose mention of the subsection name
    can never hijack the anchor, because prose does not form a
    header-shaped line.

    Format requirement (documented in AI.SESSION.md's INSTALLED MODULES
    section): one bare module name per comment line. Any line containing
    anything other than a single bare lowercase module name — prose,
    annotations, placeholders such as "(NOT YET POPULATED ...)" — is ignored.
    (Enterprise module names are always lowercase; the uppercase allowance
    for custom addon folders applies only to the canary's not-installed list.)
    """
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r"^#[ \t]+ODOO ENTERPRISE\b[^\n]*:[ \t]*$"
        r"(.*?)"
        r"(?=^#[ \t]+(?:ODOO COMMUNITY|ODOO THEMES|CUSTOM|NOT INSTALLED IN PRODUCTION)\b[^\n]*:[ \t]*$"
        r"|^#\s*COUNTRIES\s*:|^#\s*APPS\s*\(baseline\b|\Z)",
        text, re.DOTALL | re.MULTILINE,
    )
    if not match:
        return set()
    block = match.group(1)
    # One bare module name per line: "#   <name>" and nothing else.
    # [ \t] (not \s): \s matches newlines, letting a bare-word NON-comment
    # line after a lone "#" line parse as a module — enforce same-line.
    return set(re.findall(r'^#[ \t]+([a-z][a-z0-9_]+)[ \t]*$', block, re.MULTILINE))


# ---------------------------------------------------------------------------
# Parse active country codes from AI.CUSTOM.md
# ---------------------------------------------------------------------------

def parse_countries(path: Path) -> set:
    """
    Extract the set of lowercase country codes from the COUNTRIES line in
    AI.CUSTOM.md.  Example line:  # COUNTRIES: us, ca, ph
    Returns {'us', 'ca', 'ph'}.  Returns empty set if line is absent.
    """
    text = path.read_text(encoding="utf-8")
    match = re.search(r'^#\s*COUNTRIES\s*:\s*(.+)$', text, re.MULTILINE)
    if not match:
        return set()
    return {c.strip().lower() for c in match.group(1).split(',') if c.strip()}


def installed_list_populated(path: Path = None) -> bool:
    """
    True when the INSTALLED MODULES section of AI.CUSTOM.md no longer contains
    a (NOT YET POPULATED) marker. Two guards distinguish real markers from
    prose MENTIONS of the marker (which appear both inside the section's own
    warning text and in the maintenance prompt): the search is scoped to the
    section, and only lines that BEGIN with the marker count — a real marker
    is a line of the form "#   (NOT YET POPULATED — run the ... prompt)",
    while prose embeds the phrase mid-sentence. The section anchor is
    line-anchored ("^# INSTALLED MODULES") so prose mentions of the section
    name cannot shift the search region. The end boundary is the
    "# COUNTRIES:" data line, with the "# APPS (baseline …):" data line as
    fallback — COUNTRIES may legally be absent ("missing or empty" per its
    note), and without the fallback the scope would silently widen to the
    whole file (same terminator approach as parse_installed_enterprise
    above — change the two together). AI.canary.py imports this function
    so the two scripts can never disagree on what "populated" means.
    """
    text = (path or ADDONS_AI).read_text(encoding="utf-8")
    m = re.search(r"^#[ \t]*INSTALLED MODULES\b(.*?)"
                  r"(?=^#\s*COUNTRIES\s*:|^#\s*APPS\s*\(baseline\b)",
                  text, re.DOTALL | re.MULTILINE)
    region = m.group(1) if m else text
    # [ \t] (not \s) — a real marker has "#" and the marker on one line.
    return not re.search(r'^#[ \t]*\(NOT YET POPULATED', region, re.MULTILINE)


def source_hash() -> str:
    """
    12-hex SOURCE-HASH 'enterprise' component: a hash of everything this
    generator's output depends on inside AI.CUSTOM.md — the installed
    Enterprise module list and the COUNTRIES line. Embedded in the generated
    AI.ENTERPRISE.md header; AI.canary.py imports this function and compares,
    so the two scripts can never disagree on the hash definition.
    """
    installed = parse_installed_enterprise(ADDONS_AI)
    countries = parse_countries(ADDONS_AI)
    basis = "\n".join(sorted(installed)) + "\n|countries:" + ",".join(sorted(countries))
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:12]


def include_in_directory(name: str, installed: set, countries: set) -> bool:
    """
    Return True if a module should appear in the directory listing.
      - Always include installed modules.
      - Always include non-l10n modules.
      - For uninstalled l10n_* modules: include only if the country code
        (first segment after l10n_) is in the countries set.
    """
    if name in installed:
        return True
    if not name.startswith("l10n_"):
        return True
    # Extract country code: l10n_us_reports → us,  l10n_ph_check_printing → ph
    # Note: with an empty countries set, ALL uninstalled l10n_* are omitted.
    code = name[5:].split("_")[0]
    return code in countries


# ---------------------------------------------------------------------------
# Parse __manifest__.py for a one-line summary
# ---------------------------------------------------------------------------

def manifest_summary(manifest_path: Path) -> str:
    try:
        d = ast.literal_eval(manifest_path.read_text(encoding="utf-8", errors="ignore"))
        text = d.get("summary", "") or d.get("description", "")
        return text.strip().splitlines()[0].strip()[:80] if text.strip() else ""
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not installed_list_populated():
        sys.stderr.write(
            "ERROR: cannot generate AI.ENTERPRISE.md — the INSTALLED MODULES section\n"
            "of AI.CUSTOM.md still contains a (NOT YET POPULATED) marker, so the\n"
            "production install status is UNKNOWN. Generating now would mark every\n"
            "module as not installed, which is misleading.\n"
            "\n"
            "Fix:\n"
            "  1. Run the \"Update installed modules list + Enterprise index\" prompt\n"
            "     documented in AI.SESSION.md (survey production, populate the\n"
            "     INSTALLED MODULES subsections, remove the markers).\n"
            "  2. Re-run: python3 AI/AI.gen_enterprise.py\n"
            "\n"
            "Nothing was written. Note: if this run was invoked with the legacy\n"
            "'> AI.ENTERPRISE.md' redirection, the shell has already truncated that\n"
            "file to empty — delete it: rm AI.ENTERPRISE.md (AI.canary.py flags the\n"
            "stampless empty file as STALE DERIVED anyway).\n")
        return 1

    today     = date.today().strftime("%Y-%m-%d")
    version   = detect_odoo_version()
    installed = parse_installed_enterprise(ADDONS_AI)
    countries = parse_countries(ADDONS_AI)

    # Collect all enterprise module folders + summaries
    all_modules: dict = {}
    for manifest in sorted(ENTERPRISE.glob("*/__manifest__.py")):
        folder = manifest.parent.name
        all_modules[folder] = manifest_summary(manifest)

    # ── Header ──────────────────────────────────────────────────────────────
    L = []
    w = L.append
    vlabel = f"Odoo {version} " if version else "Odoo "
    w(f"# AI.ENTERPRISE — {vlabel}Enterprise Module Directory")
    # "Updated:" lowercase — the derived-file convention (see the casing note
    # in AI.SPECS.STUDIO.md's DOC.STUDIO.analysis.md header spec): uppercase "# UPDATED:" is
    # reserved for machine-read dates; nothing machine-reads this line.
    w(f"# Updated: {today}")
    if version:
        w(f"# ODOO: {version} (detected from odoo/release.py at generation time)")
    else:
        w("# ODOO: (undetected — odoo/release.py not readable at generation time)")
    w(f"# SOURCE: {ENTERPRISE}/")
    w(f"# INSTALLED LIST SOURCE: {ADDONS_AI}")
    w(f"# SOURCE-HASH: enterprise={source_hash()}")
    w(f"# COUNTRIES FILTER: {', '.join(sorted(countries)) if countries else '(none set — uninstalled l10n_* omitted; set COUNTRIES in AI.CUSTOM.md)'}")
    w("#")
    w("# PURPOSE: Reference index of all Enterprise modules — what exists and what")
    w("#   is installed in production. (test_* scaffolding modules are omitted.)")
    w("#   ✅ = installed in production   (no mark) = available but not installed")
    w("#   Uninstalled l10n_* modules for countries not in COUNTRIES filter are omitted.")
    w("#   AI ACCESS: on-demand reference — consult when assessing Enterprise module")
    w("#   availability; never read at session start (per the AI PROMPTS sequence")
    w("#   in AI.SESSION.md).")
    w("#")
    w("# MAINTENANCE: Re-run whenever the production installed module list changes.")
    w("#   That is the same trigger as the 'Update installed modules list +")
    w("#   Enterprise index' prompt in AI.SESSION.md — run both together:")
    w("#     python3 AI/AI.gen_enterprise.py")
    w("#     (writes this file in place, atomically)")
    w("# ─────────────────────────────────────────────────────────────────────────────")
    w("")

    # ── Module directory ────────────────────────────────────────────────────
    w("## MODULE DIRECTORY")
    w("")
    for name, summary in all_modules.items():
        if name.startswith("test_"):
            continue
        if not include_in_directory(name, installed, countries):
            continue
        mark = "✅" if name in installed else "  "
        w(f"  {mark} {name:<55} {summary}")
    w("")
    doc = "\n".join(L) + "\n"

    # Atomic write (tmp + rename — never a truncated or empty index), then
    # the same document to stdout: the legacy '> AI.ENTERPRISE.md' form
    # keeps working (the redirect's fd points at the pre-rename inode, so
    # the file seen on disk is the atomic write's; redirecting elsewhere
    # yields an identical copy). The progress notice goes to stderr only —
    # a notice on stdout would corrupt legacy redirected runs.
    tmp = OUTPUT.with_name(OUTPUT.name + ".tmp")
    try:
        tmp.write_text(doc, encoding="utf-8")
        tmp.replace(OUTPUT)
    except BaseException:
        tmp.unlink(missing_ok=True)   # no stray .tmp after a failed run
        raise
    sys.stdout.write(doc)
    sys.stderr.write(f"wrote {OUTPUT}\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
