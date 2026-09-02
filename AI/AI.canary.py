#!/usr/bin/env python3
"""
AI.canary.py — AI.CUSTOM.md drift detector
Checks twenty things:
  1. Each documented addon's UPDATED date vs the last git commit touching
     code files in its folder (.py/.xml/.js/.csv/.css/.scss — deliberately
     the same set as AI.SPECS.ADDONS.md's version-bump rule (MAINTENANCE),
     so doc-only commits never flag; keep the two lists in sync). Known benign case: docs
     updated together with the code but committed on a later day (commits
     are user-triggered and may lag the work) — verify the docs are in
     fact current, then set both UPDATED dates to the commit date to
     clear the finding.
  2. Addon folders on disk (containing __manifest__.py) that are absent from the
     master file (studio_customization/ is excluded by name — a reference export,
     never an addon; see check 12 for its manifest hazard).
  3. Documented addons whose folder is absent from disk — removed or renamed
     without running the "Remove addon from documentation" prompt (reported
     as FOLDER MISSING).
  4. Documented addons whose folder exists but has no git history yet —
     reported as NO COMMITS, informational only: normal for a new addon
     awaiting its first commit (printed, exit status unaffected, ✅ all-clear
     withheld — see Exit status below).
  5. Each addon block's STATUS field vs the NOT INSTALLED IN PRODUCTION list in the
     header (the two must agree; on disagreement the block STATUS is authoritative;
     a listed name with no block at all is diagnosed by its folder: folder on
     disk = documentation gap, document the addon rather than delist it;
     no folder either = leftover from an addon removal, delete the entry).
  6. Each addon block's UPDATED date vs the UPDATED date in the addon's README.AI.md
     (the maintenance rules require the two to be updated together, always).
     Also reported under the same heading: a README.AI.md that is missing
     entirely, or whose UPDATED date is unparsable — every documented addon
     must have one per the MAINTENANCE rules in AI.SPECS.ADDONS.md.
  7. The COVERAGE line vs reality: N = on-disk addon folders that have a >>ADDON:
     block, total = on-disk addon folders containing __manifest__.py.
  8. Derived-file freshness: each existing derived file's SOURCE-HASH stamp vs a
     hash of its current sources (see DERIVED-FILE FRESHNESS in AI.SPECS.ADDONS.md).
     UPDATED lines are excluded from the hashes, so date-only bumps never flag.
  9. Derived files that are expected but missing, reported with instructions on
     how to create each. Expectations are conditional on the sources: addon-
     derived files are expected once >>ADDON: blocks exist, Studio-derived files
     once AI.STUDIO.md exists AND the export folder is non-empty (in the orphan
     state — doc without folder — check 14 owns the remediation, so nothing is
     "missing"; AI.STUDIO.md itself is expected once studio_customization/
     exists AND contains files — an empty folder is treated as absent, same as
     STEP S1), AI.ENTERPRISE.md once the INSTALLED MODULES section is populated.
 10. The hand-set '# ODOO:' header line in AI.CUSTOM.md vs the Odoo series
     detected from the environment (skipped off-platform). The manifest
     version-bump format derives from this line, so drift propagates wrong
     version numbers into new manifests.
 11. The '# APPS (baseline X.Y):' data line vs the version number on the
     '# ODOO:' header line. When the repo moves to a new Odoo version, the
     APP valid-values list must be refreshed against that version's apps and
     the baseline updated (skipped when the ODOO line itself is missing or
     unparsable — check 10 reports that).
 12. An active __manifest__.py inside studio_customization/ — the export
     procedure mandates renaming it to __manifest__.py.disabled; left active,
     Odoo tries to load the reference export as a real module on next startup.
 13. Each addon block's required lines: UPDATED, STATUS, PURPOSE, IMPACT,
     TYPE, and APP. The classification fields are required because the
     README.AI.md header duplicates them and every DOC.CUSTOM.by.* summary
     groups or tabulates by them — an omitted value has no defined rendering
     there; inventory fields (DEPENDS, DEPENDS_CUSTOM, EXTERNAL_DEPS, MODEL
     and its sub-lines, VIEWS, ASSETS, CRON) remain optional. A block missing
     any required line, or carrying a STATUS value other than the two allowed
     (exactly 'active', or the verbatim not-installed sentence —
     NOT_INSTALLED_STATUS below), is reported as MALFORMED BLOCK — otherwise
     a missing UPDATED silently exempts the addon from checks 1 and 6, and a
     missing/mistyped STATUS silently reads as active. An UPDATED line whose
     value is not a parsable YYYY-MM-DD date is reported as unparsable —
     distinct from missing, so the fix is to repair the line, not add one.
     The values of IMPACT, TYPE, and APP are also validated (against
     Minor/Intermediate/Major, the TYPE DEFINITIONS set including the
     Read-Only/Updates exclusion, and the '# APPS (baseline …):' data line
     respectively) — a typo'd value would otherwise surface only as
     a phantom group in a regenerated DOC.CUSTOM.by.* summary. Repeated
     single-value field lines within one block are also reported: the parsed
     fields (UPDATED, STATUS, PURPOSE, IMPACT, TYPE, APP) because parsing is
     last-wins — an unnoticed duplicate silently overrides the intended value
     — and the unparsed ones (README, DEPENDS, DEPENDS_CUSTOM, EXTERNAL_DEPS)
     because duplicated copies drift apart with no script to notice.
     Repeatable lines (MODEL and its FIELDS/METHODS/CONSTRAINT sub-lines,
     VIEWS, ASSETS, CRON) legitimately recur and are never counted.
 14. The studio_customization/ export vs AI.STUDIO.md: the EXPORT-HASH line
     recorded in AI.STUDIO.md's header is compared to a content hash of the
     current export folder — STALE STUDIO DOC means the export changed after
     the documentation was built ("re-exported but not re-documented"). Also
     reports two orphan states: AI.STUDIO.md exists while the export folder
     is absent or empty (the doc then describes an export no longer in the
     repo), and Studio-derived DOC.* files exist while AI.STUDIO.md itself
     is absent (leftovers of a half-done Studio removal — their stamps are
     unjudgeable without the source, so checks 8 and 9 cannot see them; the
     leftover existence itself is the finding). The remaining direction —
     Studio changed in the UI but never re-exported — is not detectable
     from the repo; STEP S1's session reminder covers it.
 15. AI.gen_enterprise.py availability: the generator is a required template
     file this script delegates to (ODOO version detection, the 'enterprise'
     hash, the installed-list populated-state test). When it is missing or
     fails to load, check 10 and the AI.ENTERPRISE.md parts of checks 8 and 9
     are disabled — reported as GENERATOR UNAVAILABLE so the disablement is
     never silent. (Off-platform is unaffected: a healthy generator loads
     fine there and check 10 skips on its own, by design.)
 16. Each addon block's IMPACT, TYPE, and APP values vs the same-named
     header lines in the addon's README.AI.md — the header duplicates them
     from the block (NOTE ON DUPLICATION in AI.SPECS.ADDONS.md), and check 6
     covers only UPDATED, so a value re-judged in one file could otherwise
     disagree with the other forever. A README missing one of the three
     header lines is reported here too. TYPE compares as an unordered
     comma-list (reordering is not drift); IMPACT and APP compare exactly.
     Like check 6, each field is read from its FIRST occurrence in the
     README — but anchored at line start ("# <FIELD>:"), unlike UPDATED's
     anywhere-in-a-line match (the README.AI.md FILE FORMAT spec documents
     both rules). Reported as README MISMATCH.
 17. Template-file availability — AI.SESSION.md, AI.SPECS.ADDONS.md,
     AI.SPECS.STUDIO.md,
     and AI.gen_summaries.py: files the sessions and maintenance prompts
     depend on (the instruction home,
     block template, file formats, regeneration rules, and the mechanical
     generator of the DOC.CUSTOM.by.* summaries). A missing one is reported
     as SPECS MISSING — the docs cannot be safely maintained without it.
 18. Inventory drift — each addon block's inventory lines (DEPENDS,
     DEPENDS_CUSTOM, EXTERNAL_DEPS, MODEL/FIELDS/METHODS/CONSTRAINT,
     VIEWS, ASSETS, CRON) vs the same facts extracted mechanically from
     the addon's code, by delegation: AI.gen_inventory.py --check runs as
     a subprocess and its ⚠️ findings are adopted VERBATIM — each prefixed
     with its addon name, replacing the tool's "== addon" group headers,
     so nothing is lost — and this check can never disagree with the
     standalone tool (promotion history and gate evidence are kept in the
     template repository). The tool's ◻︎ honesty notes (unextractable or
     out-of-scope material: SECURITY/COMMANDS sections, js EXTERNAL_DEPS,
     prose descriptors) are advisory, deliberately NOT findings, and
     appear only in the tool's own output. Undocumented folders and
     folderless blocks are owned by checks 2 and 3 — the tool skips them
     for the same reason. A missing AI.gen_inventory.py is reported as
     INVENTORY CHECKER UNAVAILABLE whenever there is anything to check
     (a bare repo stays quiet); a present-but-broken one is reported
     unconditionally — a crashing tool is a defect worth surfacing even
     with nothing to check. Like check 15, a disabled check is never
     silent. The same
     principle covers partial disablement: when the tool warns that its
     [NEW]/[OVR] def-grep failed, the TAG drift dimension went unchecked
     on a platform where it should have run — reported under the same
     heading. The tool's off-platform variant of that warning (standard
     trees absent) stays advisory: there the disablement is by design.
 19. Each addon's SPEC.AI.md — the behavioral contract defined by the
     SPEC.AI.md CONVENTION in AI.SESSION.md — vs the last git commit
     touching code files in its folder: same file set and machinery as
     check 1, so doc-only commits never flag. Only specs that EXIST are
     checked. SPEC STALE = code committed after the spec's UPDATED date
     (verify the spec still describes the addon's current intended
     behavior — amend it through approval if not — then bump the UPDATED
     line to the commit date: the bump is the attestation). SPEC
     MALFORMED = the required 'UPDATED: YYYY-MM-DD' first line is missing
     or unparsable — repaired, not duplicated — since without it the file
     silently escapes the STALE check. The ABSENCE of a SPEC.AI.md is
     deliberately NOT a finding here: this script only prints an
     informational "◻︎ SPEC coverage" line (exit status unaffected,
     ✅ all-clear NOT withheld — unlike ⬜ NO COMMITS) so the gap
     stays visible without blocking a clean run.
 20. Conflict DISPOSITIONS — the interactions AI.gen_conflicts.py derives from
     the >>ADDON: blocks (which addons share a model, method name, field name
     or view inheritance target) vs the decisions recorded in AI.CONFLICTS.md.
     This check judges NOTHING: a derived interaction is a fact, not a defect,
     and four addons touching one method is routinely correct architecture
     (one owns it [NEW], the others extend it [OVR]). It asks only whether
     someone has DECIDED about each interaction, and whether that decision
     still describes reality. UNDISPOSED = derived interaction with no
     >>CONFLICT: block. DISPOSITION OUTDATED = the block's ADDONS: set no
     longer matches the derived participants, so the judgment was made about a
     different situation. STALE DISPOSITION = a block whose interaction no
     longer derives, or whose STATUS is not one of
     Accepted/Deferred/Fixed/Withdrawn. A repo with no interactions needs no
     AI.CONFLICTS.md and is not asked for one; the file is required only once
     there is something to decide about. If AI.gen_conflicts.py is absent the
     whole check is skipped, like check 15's generator.
Run from anywhere — paths are derived from this script's own location.
Usage:
  python3 AI/AI.canary.py           run all checks
  python3 AI/AI.canary.py --stamp   print current SOURCE-HASH components to embed
                                 in regenerated derived files
  python3 AI/AI.canary.py --init-conflicts
                                 create the starter AI.CONFLICTS.md (the
                                 per-repo conflict DISPOSITION file). --init
                                 also creates it for a new repo; this flag
                                 exists so an EXISTING repo, whose
                                 AI.CUSTOM.md is already present, can create
                                 just this one when upgrading. Never
                                 overwrites — it holds decisions.
  python3 AI/AI.canary.py --init    create the v9 starter AI.CUSTOM.md in a
                                 fresh repo: ODOO line auto-detected from
                                 the environment (edition "Enterprise"),
                                 one country menu (1=us 2=ca 3=ph, Enter=1;
                                 multi-country repos pick the primary and
                                 hand-edit the line later), APPS baseline
                                 embedded. REFUSES if the file exists —
                                 init never overwrites (the template ships
                                 no AI.CUSTOM.md precisely so upgrades
                                 cannot clobber it; this flag is the only
                                 way the file comes into being).
                                 --defaults (or non-tty stdin) skips the
                                 menu and takes option 1 (us)
Setup guidance: while a repo's documentation setup is incomplete
(INSTALLED MODULES markers unpopulated, APPS baseline mismatched, a
Studio export without AI.STUDIO.md, addon folders with no >>ADDON:
blocks), normal runs print a 🔧 SETUP block sequencing the next steps —
including the survey script inline while the markers are unpopulated.
Informational: it affects neither the exit status nor the ✅ line
(prompt definitions live in AI.SESSION.md). A MISSING AI.CUSTOM.md is
its own finding (new repo → --init; existing repo → restore from git,
never re-init) and skips all other checks.
Exit status:
  0 = no actionable findings (⬜ NO COMMITS is informational only — a new
      addon awaiting its first commit — and does not affect the exit status;
      it is still printed, and the ✅ all-clear line is withheld. The
      ◻︎ SPEC coverage line and the 🔧 SETUP block are likewise
      informational and affect neither
      the exit status nor the ✅ line. --init: 0 = file created,
      1 = refused, e.g. the file already exists)
  1 = at least one actionable finding (including AI.CUSTOM.md MISSING)
"""

import hashlib
import subprocess
import re
import sys
from pathlib import Path
from datetime import date

# Self-locating: after the C30 move the scripts live in AI/ so SCRIPT_DIR is
# the AI/ subfolder; REPO_ROOT is its parent — the actual repository root
# where addon module directories live.  Both are needed: sibling AI.* files
# are resolved via SCRIPT_DIR, addon scanning via REPO_ROOT.
SCRIPT_DIR   = Path(__file__).resolve().parent
REPO_ROOT    = SCRIPT_DIR.parent
ADDONS_AI    = SCRIPT_DIR / "AI.CUSTOM.md"
CONFLICTS_AI = SCRIPT_DIR / "AI.CONFLICTS.md"

# Single-value block fields whose VALUES no script parses — tracked by
# parse_addons for duplication only, so check 13 can report a repeated line
# (two README lines drift apart with no script to notice). Mirrors the
# "single-value fields" syntax rule in AI.SPECS.ADDONS.md's block template —
# change the two places together. UPDATED/STATUS/PURPOSE/IMPACT/TYPE/APP are
# parsed (and duplicate-counted) separately in parse_addons — PURPOSE's text
# feeds AI.gen_summaries.py; repeatable lines
# (MODEL, FIELDS, METHODS, CONSTRAINT, VIEWS, ASSETS, CRON) legitimately
# recur — once per model, view file, or record — and are deliberately
# absent here. DEPENDS_CUSTOM precedes DEPENDS to keep the regex
# alternation unambiguous.
SINGLE_VALUE_UNPARSED_FIELDS = ("README", "DEPENDS_CUSTOM",
                                "DEPENDS", "EXTERNAL_DEPS")

def parse_addons(path):
    """Return { addon_name: {'updated': date|None, 'updated_bad': str|None,
    'created': date|None, 'created_bad': str|None,
    'status': str|None, 'purpose': str|None,
    'impact': str|None, 'type': str|None, 'app': str|None,
    'dups': {FIELD: count}} }.
    'updated_bad' carries the raw value of an UPDATED line whose date is not
    parsable YYYY-MM-DD — reported by check 13 as unparsable, distinct from
    a block with no UPDATED line at all. 'created'/'created_bad' work the same
    way for the CREATED line (when the addon first appeared). Note the
    deliberate asymmetry in how a MISSING one is reported: CREATED gets its
    OWN finding category, not MALFORMED BLOCK, because every other required
    field must be AUTHORED by a human while CREATED is DERIVABLE from git —
    so its remedy is a command (--backfill-created) rather than a writing
    task, and burying it among fields nobody can automate would hide that.
    An UNPARSABLE CREATED does stay with MALFORMED BLOCK: repairing a wrong
    date is a human job like the rest.
    Parsing is last-wins: a repeated field line within one block silently
    overrides the earlier one. 'dups' counts each field's occurrences so
    check 13 can report the duplication itself instead of letting the
    override pass silently (a copied block-template parenthetical was the
    classic way to get two STATUS lines). It also counts the single-value
    fields no script parses (SINGLE_VALUE_UNPARSED_FIELDS) — duplicated
    copies of those would drift apart with nothing to notice; repeatable
    lines (MODEL, FIELDS, METHODS, CONSTRAINT, VIEWS, ASSETS, CRON) are
    never counted."""
    addons = {}
    current = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r'^>>ADDON:\s+(\S+)', line)
            if m:
                current = m.group(1)
                addons[current] = {"updated": None, "updated_bad": None,
                                   "created": None, "created_bad": None,
                                   "status": None, "purpose": None,
                                   "impact": None, "type": None, "app": None,
                                   "dups": {}}
                continue
            if current:
                info = addons[current]
                m = re.match(r'^\s*UPDATED:\s*(.*?)\s*$', line)
                if m:
                    info["dups"]["UPDATED"] = info["dups"].get("UPDATED", 0) + 1
                    try:
                        info["updated"] = date.fromisoformat(m.group(1))
                    except ValueError:
                        info["updated_bad"] = m.group(1)
                    continue
                m = re.match(r'^\s*CREATED:\s*(.*?)\s*$', line)
                if m:
                    info["dups"]["CREATED"] = info["dups"].get("CREATED", 0) + 1
                    try:
                        info["created"] = date.fromisoformat(m.group(1))
                    except ValueError:
                        info["created_bad"] = m.group(1)
                    continue
                m = re.match(r'^\s*STATUS:\s*(.+?)\s*$', line)
                if m:
                    info["status"] = m.group(1)
                    info["dups"]["STATUS"] = info["dups"].get("STATUS", 0) + 1
                    continue
                m = re.match(r'^\s*(IMPACT|TYPE|APP|PURPOSE):\s*(.+?)\s*$', line)
                if m:
                    info[m.group(1).lower()] = m.group(2)
                    info["dups"][m.group(1)] = info["dups"].get(m.group(1), 0) + 1
                    continue
                m = re.match(r'^\s*(' + '|'.join(SINGLE_VALUE_UNPARSED_FIELDS)
                             + r'):', line)
                if m:
                    info["dups"][m.group(1)] = info["dups"].get(m.group(1), 0) + 1
    return addons


# Fixed vocabularies for the IMPACT and TYPE block fields — mirror the IMPACT
# options and the TYPE DEFINITIONS fixed set in AI.SPECS.ADDONS.md;
# change the two places together. (APP values come from the "# APPS
# (baseline …):" data line, parsed live by parse_apps_line — no second
# copy to keep in sync.)
IMPACT_VALUES = {"Minor", "Intermediate", "Major"}
TYPE_VALUES = {"Read-Only", "Updates", "Override", "UI", "Integration"}
# The exact not-installed STATUS value — mirrors the block template in
# AI.SPECS.ADDONS.md verbatim (em dash included); change the two places together.
# STATUS is validated strictly ('active' or this sentence, nothing else): the
# sentence carries a behavioral instruction ("disregard unless explicitly
# asked") that free-text variants would silently drop.
NOT_INSTALLED_STATUS = "not installed/active in Odoo — disregard unless explicitly asked"


def parse_not_installed_list(path):
    """
    Module names listed in the NOT INSTALLED IN PRODUCTION subsection of the
    header. Only bare-module-name lines ("#   <name>") count — prose comments
    and (NOT YET POPULATED) markers are ignored. Unlike standard Odoo module
    names, custom addon folder names may contain uppercase letters in any
    position, so the name pattern deliberately accepts uppercase letters
    (a character-class allowance — the regex is not re.IGNORECASE-compiled).

    Anchoring is structural: the subsection is located by its HEADER LINE
    SHAPE — line-start "#", indented ALL-CAPS name, colon at end of line —
    so a prose mention of the subsection name can never hijack the anchor.
    The capture ends at the next sibling subsection header of the same shape
    (any of them — reorder-proof) or at the "# COUNTRIES:" data line, with
    the "# APPS (baseline …):" data line as a fallback boundary: COUNTRIES
    may legally be absent ("missing or empty" per its note), and without a
    boundary the capture would run to end of file and read bare-word comment
    lines below — e.g. the survey script's "continue" — as phantom modules;
    the APPS line, unlike COUNTRIES, is policed to exist (check 11).
    Same approach as AI.gen_enterprise.parse_installed_enterprise —
    change the two together.
    """
    text = path.read_text(encoding="utf-8")
    m = re.search(
        r"^#[ \t]+NOT INSTALLED IN PRODUCTION\b[^\n]*:[ \t]*$"
        r"(.*?)"
        r"(?=^#[ \t]+(?:ODOO ENTERPRISE|ODOO COMMUNITY|ODOO THEMES|CUSTOM)\b[^\n]*:[ \t]*$"
        r"|^#\s*COUNTRIES\s*:|^#\s*APPS\s*\(baseline\b|\Z)",
        text, re.DOTALL | re.MULTILINE,
    )
    if not m:
        return set()
    # [ \t] (not \s): \s matches newlines, letting a bare-word NON-comment
    # line after a lone "#" line parse as a module — the format promises
    # "one module name per comment line", so enforce same-line.
    return set(re.findall(r'^#[ \t]+([A-Za-z][A-Za-z0-9_]+)[ \t]*$', m.group(1), re.MULTILINE))

def parse_coverage(path):
    """(N, total) from the COVERAGE line, or None if absent/unparsable."""
    m = re.search(r'^#\s*COVERAGE:\s*(\d+)\s+of\s+(\d+)',
                  path.read_text(encoding="utf-8"), re.MULTILINE)
    return (int(m.group(1)), int(m.group(2))) if m else None


# ── Derived-file freshness (SOURCE-HASH stamps) ─────────────────────────────
# Which derived files carry which hash components. A missing FILE is not
# staleness (creation is a setup/maintenance concern); only existing files
# with a missing or mismatching stamp are reported.
DERIVED_FILES = {
    "DOC.CUSTOM.by.App.md":    ("addons",),
    "DOC.CUSTOM.by.Impact.md": ("addons",),
    "DOC.CUSTOM.by.Alpha.md":  ("addons",),
    "DOC.CUSTOM.by.Type.md":   ("addons",),
    "DOC.CONFLICTS.Addons.md": ("addons",),
    "DOC.CONFLICTS.Studio.md": ("addons", "studio"),
    "DOC.STUDIO.analysis.md":  ("studio",),
    "DOC.STUDIO.by.App.md":    ("studio",),
    "DOC.STUDIO.by.Model.md":  ("studio",),
    "DOC.STUDIO.by.Fields.md": ("studio",),
    "AI.ENTERPRISE.md":        ("enterprise",),
    "DOC.PRODENV.md":          ("prodenv",),
}


# ── ONE-TIME MIGRATION (DELETE AFTER 2026-12-31) ───────────────────────────
# Renames a working repo's legacy DOC.STUDIO.md to DOC.STUDIO.analysis.md when
# the template rename lands. Self-disables on 2026-12-31: after that date this
# whole block is dead code — remove it, it is cleanup only.
_STUDIO_ANALYSIS_MIGRATION_CUTOFF = date(2026, 12, 31)


def migrate_studio_analysis_rename():
    if date.today() > _STUDIO_ANALYSIS_MIGRATION_CUTOFF:
        return
    old = SCRIPT_DIR / "DOC.STUDIO.md"
    new = SCRIPT_DIR / "DOC.STUDIO.analysis.md"
    if not old.exists():
        return
    if new.exists():
        print("⚠️  DOC.STUDIO.md and DOC.STUDIO.analysis.md both present — "
              "the new file is authoritative; delete the legacy DOC.STUDIO.md "
              "and commit the removal.")
        return
    old.rename(new)  # atomic same-dir rename; header rewrite is not needed —
                     # next regeneration emits the updated title, and the
                     # SOURCE-HASH line canary parses is unchanged
    print("ℹ️  MIGRATED: DOC.STUDIO.md → DOC.STUDIO.analysis.md "
          "(commit the rename)")


# Human-facing pointer created at the repo root (REPO_ROOT/README.AI.md) so a
# person browsing the repository is directed into the AI/ folder. This is a
# DIFFERENT file from the per-addon README.AI.md files (which live inside addon
# folders and ARE parsed by the canary for UPDATED/IMPACT/TYPE/APP); the root
# copy lives where addon discovery never scans, so it is never parsed, dated,
# or staled. Static content — create-once, never overwritten.
_ROOT_README_TEXT = """\
# AI-Assisted Development — Start Here

This repository is documented and reviewed with Claude. The machine-readable
instructions and the AI-generated documentation live in the **AI/** folder.

## AI-generated documentation (human-readable)

- **AI/DOC.CONFLICTS.*** — module conflict information
- **AI/DOC.CUSTOM.by.*** — customization summary
- **AI/DOC.STUDIO.by.*** — Studio customization summary
- **AI/DOC.STUDIO.analysis.md** — Studio customization analysis (risks & context)

## Where to go next

- **AI/AI.README.md** — read this for the full tour of the AI/ folder.
- In each addon folder, **README.AI.md** documents that specific module.
"""


def ensure_root_readme():
    """Create REPO_ROOT/README.AI.md if absent — a human pointer into the AI/
    folder. Create-once and never overwritten; not a derived file (no
    UPDATED/SOURCE-HASH), so it never goes stale."""
    root_readme = REPO_ROOT / "README.AI.md"
    if root_readme.exists():
        return
    root_readme.write_text(_ROOT_README_TEXT, encoding="utf-8")
    print("ℹ️  CREATED README.AI.md at the repo root (points to the AI/ folder "
          "— commit it)")


def _hash12(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def addons_source_hash(path):
    """Hash of the >>ADDON: block region, excluding UPDATED lines — ANY line
    beginning "UPDATED:" (the same line definition parse_addons uses), even
    one with a malformed date, so repairing a bad date never stales derived
    files. In a well-formed file the excluded set is identical to the former
    valid-date-only rule, so existing stamps are unaffected."""
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next((i for i, l in enumerate(lines) if l.startswith(">>ADDON:")), None)
    if start is None:
        return _hash12("")
    body = [l.rstrip() for l in lines[start:]
            if not re.match(r'\s*UPDATED:', l)]
    return _hash12("\n".join(body))


def studio_source_hash(path):
    """Hash of AI.STUDIO.md, excluding date header lines and the EXPORT-HASH
    line (re-recording the export hash must not flag the Studio-derived
    summaries — they derive from the inventory content, not the export
    stamp). None if absent.
    The exclusion is spacing-tolerant on purpose ("#" + any whitespace +
    field name) — a hand-typed spacing variant of a header line must still
    be excluded, or its date bumps would stale every Studio-derived file.
    Do not tighten; the AI.STUDIO.md FILE FORMAT note in AI.SPECS.STUDIO.md
    documents this exact rule — change the two places together."""
    if not path.exists():
        return None
    body = [l.rstrip()
            for l in path.read_text(encoding="utf-8", errors="ignore").splitlines()
            if not re.match(r'#\s*(UPDATED|BUILT|EXPORT-HASH):', l)]
    return _hash12("\n".join(body))


def studio_export_hash():
    """12-hex content hash of the studio_customization/ export folder
    (sorted relative file names + bytes). None when the folder is absent
    or empty — an empty export has nothing to document (STEP S1 treats it
    as absent too)."""
    folder = REPO_ROOT / "studio_customization"
    if not folder.is_dir():
        return None
    files = sorted(p for p in folder.rglob("*") if p.is_file())
    if not files:
        return None
    h = hashlib.sha256()
    for p in files:
        h.update(str(p.relative_to(folder)).encode("utf-8"))
        h.update(b"\0")
        h.update(p.read_bytes())
        h.update(b"\0")
    return h.hexdigest()[:12]


def check_studio_export_doc():
    """Compare the EXPORT-HASH recorded in AI.STUDIO.md's header against the
    current content hash of studio_customization/. Detects 're-exported but
    not re-documented', plus two orphan states: AI.STUDIO.md present while the
    export folder is absent or empty, and the inverse leftover — Studio-derived
    DOC.* files present while AI.STUDIO.md itself is absent (a half-done Studio
    removal; their studio stamps are unjudgeable without the source, so their
    existence is the finding — without this branch they would be invisible:
    STALE DERIVED skips unjudgeable components and MISSING DERIVED only expects
    these files while AI.STUDIO.md exists). Skipped only when AI.STUDIO.md is
    absent AND no Studio-derived file remains (STEP S3 and the MISSING DERIVED
    check own that state; a missing FOLDER is STEP S1's branch, and with no doc
    and no leftovers there is nothing to orphan). Returns a message or None."""
    cur = studio_export_hash()
    ai_studio = SCRIPT_DIR / "AI.STUDIO.md"
    if not ai_studio.exists():
        leftovers = sorted(f for f, comps in DERIVED_FILES.items()
                           if "studio" in comps and (SCRIPT_DIR / f).exists())
        if leftovers:
            return ("AI.STUDIO.md is absent but Studio-derived files remain "
                    f"({', '.join(leftovers)}) — they can no longer be verified or "
                    f"regenerated; either restore AI.STUDIO.md (from git history, or "
                    f"re-document the export per STEP S3 in AI.SESSION.md), or, if the "
                    f"Studio customizations are gone for good, delete these leftover "
                    f"files too")
        return None
    if cur is None:
        return ("AI.STUDIO.md exists but studio_customization/ is absent or empty — "
                "the doc describes an export that is no longer in the repo; either "
                "restore/re-export the folder (STUDIO EXPORT PROCEDURE in AI.SESSION.md) "
                "or, if the Studio customizations are gone for good, delete AI.STUDIO.md "
                "and ALL Studio-derived DOC.* files together, DOC.CONFLICTS.Studio.md "
                "included — it must not exist, and cannot be regenerated, without "
                "AI.STUDIO.md")
    text = ai_studio.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'^#\s*EXPORT-HASH:\s*([0-9a-f]{12})\b', text, re.MULTILINE)
    if not m:
        return (f"AI.STUDIO.md has no EXPORT-HASH header line, so re-exports are "
                f"undetectable — add it per the AI.STUDIO.md FILE FORMAT spec in "
                f"AI.SPECS.STUDIO.md (current export hash: {cur})")
    if m.group(1) != cur:
        return (f"studio_customization/ changed since AI.STUDIO.md was built "
                f"(recorded {m.group(1)}, current {cur}) — re-run the "
                f"\"Update Studio documentation\" prompt and update the "
                f"EXPORT-HASH line")
    return None


_GEN_MODULE = ("unloaded",)  # sentinel


def _gen_module():
    """Load AI.gen_enterprise.py as a module (cached). None if absent/broken.
    Enterprise-related checks delegate to it so the two scripts can never
    disagree on hash or populated-state definitions."""
    global _GEN_MODULE
    if _GEN_MODULE == ("unloaded",):
        gen = SCRIPT_DIR / "AI.gen_enterprise.py"
        if not gen.exists():
            _GEN_MODULE = None
        else:
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("ai_gen_enterprise", gen)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                _GEN_MODULE = mod
            except Exception:
                _GEN_MODULE = None
    return _GEN_MODULE


def enterprise_source_hash():
    """None if the generator is absent or unloadable (check is then skipped)."""
    mod = _gen_module()
    if mod is None:
        return None
    try:
        return mod.source_hash()
    except Exception:
        return None


def check_inventory_drift(anything_to_check):
    """Check 18 — INVENTORY DRIFT, delegated to AI.gen_inventory.py --check
    as a subprocess (its main() prints and loads this script itself, so a
    subprocess is the one integration that cannot fork the logic: the canary
    adopts the exact ⚠️ line texts a hand run would show, re-prefixed
    'addon: ' in place of the tool's '== addon' headers). Returns (findings,
    problem): findings are 'addon: text' strings from the tool's indented
    ⚠️ lines; problem is a message when the tool is missing or broke while
    there was anything to check, or when the tool's on-platform def-grep
    failure disabled its TAG drift dimension (never silent, mirroring
    check 15). The tool's ◻︎ honesty notes and its other unindented
    warnings are advisory and deliberately not adopted — the off-platform
    trees-absent variant of the heuristic warning included (the
    disablement is by design there)."""
    gen = SCRIPT_DIR / "AI.gen_inventory.py"
    if not gen.exists():
        if not anything_to_check:
            return [], None      # bare repo, nothing checkable — no noise
        return [], ("AI.gen_inventory.py is missing — inventory drift is "
                    "NOT checked until it is restored; restore it from the "
                    "template repository (or from git history: "
                    "git checkout -- AI.gen_inventory.py)")
    try:
        # 1800s budget: the tool's only hard time bounds are its two
        # [NEW]/[OVR] def-greps at 600s each (_grep_defs); extraction is
        # in-process and unbounded, so the remaining 600s is headroom, not
        # a limit the tool enforces. Keep this comfortably above the grep
        # sum — change the two budgets together; and never pass --no-tags
        # here: findings must match a hand run exactly
        proc = subprocess.run(
            [sys.executable, str(gen), "--check", "--root", str(REPO_ROOT)],
            capture_output=True, text=True, timeout=1800)
    except Exception as exc:
        return [], (f"AI.gen_inventory.py could not be run ({exc}) — "
                    f"inventory drift NOT checked")
    # Column-0 ⚠️ lines are the tool's own warnings/summary — advisory and
    # never adopted as findings, with ONE exception: the on-platform
    # def-grep failure. It silently disables the TAG drift dimension, and
    # a disabled check is never silent. Matched against the warning line
    # AI.gen_inventory.py's tag-oracle failure branch prints (the string
    # is mirrored there — change the two places together); the
    # off-platform variant ("standard source trees not found") carries no
    # "def-grep" and stays advisory — absent trees are by design there.
    tag_problem = None
    if any(line.startswith("⚠️") and "def-grep" in line
           for line in proc.stdout.splitlines()):
        tag_problem = ("AI.gen_inventory.py ran, but its [NEW]/[OVR] "
                       "def-grep over the standard source trees failed — "
                       "TAG drift NOT checked this run (all other inventory "
                       "dimensions were checked); retry: "
                       "python3 AI/AI.gen_inventory.py --check")
    if proc.returncode == 0:
        return [], tag_problem
    if proc.returncode == 1:
        findings, addon = [], "?"
        for line in proc.stdout.splitlines():
            if line.startswith("== "):
                addon = line[3:].strip()
            elif line.startswith("   ⚠️"):   # indented = per-addon finding
                findings.append(f"{addon}: {line.strip().lstrip('⚠️').strip()}")
        if not findings:
            return [], ("AI.gen_inventory.py exited 1 but no findings could "
                        "be parsed from its output — run it directly: "
                        "python3 AI/AI.gen_inventory.py --check")
        return findings, tag_problem
    # any other exit (2 = wrong root / block-splitter disagreement): surface it
    msg = " ".join((proc.stdout + proc.stderr).split())[:300]
    return [], (f"AI.gen_inventory.py --check failed (exit "
                f"{proc.returncode}): {msg or 'no output'} — inventory "
                f"drift NOT checked")


def current_hashes():
    return {
        "addons":     addons_source_hash(ADDONS_AI),
        "studio":     studio_source_hash(SCRIPT_DIR / "AI.STUDIO.md"),
        "enterprise": enterprise_source_hash(),
        "prodenv":    prodenv_source_hash(),
    }


def check_derived_freshness():
    """Return list of staleness messages for existing derived files."""
    cur = current_hashes()
    stale = []
    for fname, components in sorted(DERIVED_FILES.items()):
        f = SCRIPT_DIR / fname
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        if not text.strip():
            stale.append(f"{fname}: file is empty (likely a truncated shell "
                         f"redirection after a refused generation) — delete it, "
                         f"then regenerate once its sources are ready")
            continue
        m = re.search(r'^#\s*SOURCE-HASH:\s*(.+)$', text, re.MULTILINE)
        if not m:
            stale.append(f"{fname}: no SOURCE-HASH stamp — regenerate to add one")
            continue
        stamp = {}
        for kv in m.group(1).split():
            if "=" in kv:
                k, v = kv.split("=", 1)
                stamp[k] = v
        for comp in components:
            if cur.get(comp) is None:
                continue  # source unavailable — cannot judge this component
            if stamp.get(comp) != cur[comp]:
                stale.append(f"{fname}: {comp} stamp "
                             f"{stamp.get(comp) or '(absent)'} != current {cur[comp]}")
    return stale


def check_odoo_version():
    """Compare the hand-set '# ODOO:' header line in AI.CUSTOM.md against the
    Odoo series detected from the environment (delegated to the generator so
    the detection logic lives in one place). Returns a message or None.
    Skipped when the environment version is undetectable (dev checkout
    outside Odoo.sh) — nothing trustworthy to compare against."""
    mod = _gen_module()
    if mod is None:
        return None
    try:
        env_version = mod.detect_odoo_version()
    except Exception:
        return None
    if not env_version:
        return None
    text = ADDONS_AI.read_text(encoding="utf-8")
    m = re.search(r'^#\s*ODOO\s*:\s*(.+?)\s*$', text, re.MULTILINE)
    if not m:
        return (f"AI.CUSTOM.md has no '# ODOO:' header line — set it to the "
                f"repo's version and edition (environment is Odoo {env_version})")
    line = m.group(1)
    dm = re.search(r'(\d+\.\d+)', line)
    if not dm:
        return (f"'# ODOO: {line}' has no parsable version number — "
                f"environment is Odoo {env_version}")
    if dm.group(1) != env_version:
        return (f"'# ODOO: {line}' but the environment is Odoo {env_version} — "
                f"update the header line in AI.CUSTOM.md; the manifest "
                f"version-bump format derives from it")
    return None


def parse_apps_line(path):
    """(baseline, [app, ...]) from the '# APPS (baseline X.Y):' data line,
    or None if the line is absent or unparsable."""
    m = re.search(r'^#\s*APPS\s*\(baseline\s+(\d+\.\d+)\)\s*:\s*(.+?)\s*$',
                  path.read_text(encoding="utf-8"), re.MULTILINE)
    if not m:
        return None
    return (m.group(1), [a.strip() for a in m.group(2).split(',') if a.strip()])


def check_apps_baseline():
    """Compare the baseline on the '# APPS (baseline X.Y):' data line against
    the version number on the '# ODOO:' header line — both hand-set repo data
    in AI.CUSTOM.md. When the repo moves to a new Odoo version, the APP
    valid-values list must be refreshed against that version's apps and its
    baseline updated (refresh rules are in the APPS line's note). Returns a
    message or None. Skipped when the ODOO line is missing or has no parsable
    version — check_odoo_version() already reports that."""
    text = ADDONS_AI.read_text(encoding="utf-8")
    m = re.search(r'^#\s*ODOO\s*:\s*(.+?)\s*$', text, re.MULTILINE)
    if not m:
        return None
    dm = re.search(r'(\d+\.\d+)', m.group(1))
    if not dm:
        return None
    odoo_version = dm.group(1)
    parsed = parse_apps_line(ADDONS_AI)
    if parsed is None:
        return ("AI.CUSTOM.md has no parsable '# APPS (baseline X.Y):' data "
                "line — restore it (repo-data line in AI.CUSTOM.md; field semantics: "
                "APP DEFINITIONS in AI.SPECS.ADDONS.md)")
    baseline, apps = parsed
    if not apps:
        return (f"the '# APPS (baseline {baseline}):' line lists no apps — "
                f"refresh it against Odoo {odoo_version}'s apps")
    if baseline != odoo_version:
        return (f"APPS baseline is {baseline} but the ODOO header line says "
                f"{odoo_version} — refresh the '# APPS (baseline …):' list against Odoo "
                f"{odoo_version}'s apps and update its baseline")
    return None


def check_studio_manifest():
    """An active __manifest__.py inside studio_customization/ makes Odoo try
    to load the reference export as a real module on next startup. The STUDIO
    EXPORT PROCEDURE mandates renaming it to .disabled, so an active manifest
    is always an omission. Returns a message or None."""
    if (REPO_ROOT / "studio_customization" / "__manifest__.py").exists():
        return ("studio_customization/__manifest__.py is active — Odoo will try to "
                "load the reference export as a real module on next startup; rename it:\n"
                "   mv studio_customization/__manifest__.py "
                "studio_customization/__manifest__.py.disabled\n"
                "   then commit and push")
    return None


# Template-owned files the sessions and maintenance prompts depend on —
# the instruction home (AI.SESSION.md — since the v9 split, AI.CUSTOM.md
# carries only repo data and points here), the spec files (block
# template, file formats, regeneration rules), and the summaries
# generator — copied in at install and overwritten at upgrade. A missing
# one is reported rather than left silent: the documentation cannot be
# safely maintained without it.
SPEC_FILES = ("AI.SESSION.md", "AI.SPECS.ADDONS.md", "AI.SPECS.STUDIO.md",
              "AI.gen_summaries.py")


def check_spec_files():
    """Return a message naming any missing template spec file, else None."""
    missing = [f for f in SPEC_FILES if not (SCRIPT_DIR / f).exists()]
    if not missing:
        return None
    return (f"{', '.join(missing)} missing — template-owned file(s) the "
            f"sessions and maintenance prompts depend on (the instruction "
            f"home, the spec files, and the summaries generator); restore "
            f"from the template repository "
            f"(or from git history: git checkout -- <file>)")


def check_derived_missing():
    """Return [(filename, how_to_create)] for expected-but-missing derived files.
    Expectations are conditional on the existence of each file's sources, so a
    fresh template repo reports nothing until there is something to derive from."""
    text = ADDONS_AI.read_text(encoding="utf-8")
    has_blocks = bool(re.search(r'^>>ADDON:', text, re.MULTILINE))
    # Non-empty is the criterion, not is_dir(): an empty export folder is
    # treated as absent everywhere (STEP S1, studio_export_hash) — expecting
    # AI.STUDIO.md for it would instruct documenting a folder with nothing
    # to analyze. Delegating to studio_export_hash keeps one definition.
    studio_folder = studio_export_hash() is not None
    ai_studio = (SCRIPT_DIR / "AI.STUDIO.md").exists()
    # Populated-state check is scoped to the INSTALLED MODULES section and
    # delegated to the generator (the marker is also mentioned in prose
    # elsewhere in AI.CUSTOM.md and must not count). If the generator is
    # absent, AI.ENTERPRISE.md cannot be created — so it is not expected.
    gen = _gen_module()
    modules_populated = False
    if gen is not None:
        try:
            modules_populated = gen.installed_list_populated(ADDONS_AI)
        except Exception:
            modules_populated = False

    expected = []
    if has_blocks:
        for f in ("DOC.CUSTOM.by.App.md", "DOC.CUSTOM.by.Impact.md",
                  "DOC.CUSTOM.by.Alpha.md", "DOC.CUSTOM.by.Type.md"):
            expected.append((f, "run: python3 AI/AI.gen_summaries.py "
                                "(generates and stamps all four DOC.CUSTOM.by.* files)"))
        expected.append(("DOC.CONFLICTS.Addons.md",
                         "AI prompt: regenerate from the >>ADDON: blocks "
                         "(CONFLICT REPORTS spec / MAINTENANCE rules in AI.SPECS.ADDONS.md)"))
    if studio_folder and not ai_studio:
        expected.append(("AI.STUDIO.md",
                         "AI prompt: analyze studio_customization/ and create it "
                         "(STEP S3 in AI.SESSION.md's STUDIO CUSTOMIZATIONS — "
                         "SESSION CHECKS section)"))
    # Expect the Studio-derived files only while the full source chain is
    # intact (AI.STUDIO.md AND a non-empty export folder). In the orphan
    # state — AI.STUDIO.md present, folder absent/empty — creating files
    # from the orphaned doc would deepen the inconsistency; STALE STUDIO
    # DOC owns that state and its remediation (restore or delete).
    if ai_studio and studio_folder:
        for f in ("DOC.STUDIO.analysis.md", "DOC.STUDIO.by.App.md",
                  "DOC.STUDIO.by.Model.md", "DOC.STUDIO.by.Fields.md"):
            expected.append((f, "AI prompt: regenerate from AI.STUDIO.md "
                                "(specs in AI.SPECS.STUDIO.md)"))
        expected.append(("DOC.CONFLICTS.Studio.md",
                         "AI prompt: regenerate from the >>ADDON: blocks + AI.STUDIO.md "
                         "(CONFLICT REPORTS in AI.SPECS.ADDONS.md)"))
    if modules_populated:
        expected.append(("AI.ENTERPRISE.md",
                         "run: python3 AI/AI.gen_enterprise.py "
                         "(writes AI.ENTERPRISE.md in place, atomically)"))

    return [(f, how) for f, how in expected if not (SCRIPT_DIR / f).exists()]


def print_stamps():
    cur = current_hashes()
    print("Current SOURCE-HASH components — write the stamp as line 3 of each regenerated file:")
    print("  DOC.CONFLICTS.Addons.md:")
    print(f"    # SOURCE-HASH: addons={cur['addons']}")
    if cur["studio"] is not None:
        print("  DOC.STUDIO.analysis.md, DOC.STUDIO.by.*.md:")
        print(f"    # SOURCE-HASH: studio={cur['studio']}")
        print("  DOC.CONFLICTS.Studio.md:")
        print(f"    # SOURCE-HASH: addons={cur['addons']} studio={cur['studio']}")
    else:
        print("  (studio component unavailable — AI.STUDIO.md not found)")
    print("  AI.ENTERPRISE.md: stamped automatically by AI.gen_enterprise.py")
    print("  DOC.CUSTOM.by.*.md: stamped automatically by AI.gen_summaries.py")
    exp = studio_export_hash()
    if exp is not None:
        print("  AI.STUDIO.md header (records the export it documents):")
        print(f"    # EXPORT-HASH: {exp}")
    return 0


def find_addon_folders():
    """Return names of TOP-LEVEL subdirectories that contain a __manifest__.py
    file — the template requires addons to sit directly at the repo root, one
    folder per addon (nested layouts are outside every check here; see the
    COVERAGE definition in AI.SESSION.md).
    studio_customization/ is excluded by name: it is a Studio reference
    export, never an addon — even when its manifest was mistakenly left
    active. Check 12 reports that hazard on its own; excluding the folder
    here keeps the single mistake from also raising UNDOCUMENTED and
    COVERAGE MISMATCH symptoms (which would print above the root cause and
    suggest the wrong remediation)."""
    return sorted(
        p.parent.name
        for p in REPO_ROOT.glob("*/__manifest__.py")
        if p.parent.name != "studio_customization"
    )

def last_commit_date(addon_name):
    # Extension list mirrors AI.SPECS.ADDONS.md's version-bump "code files"
    # rule (MAINTENANCE — Python, XML, JS, CSV, CSS/SCSS) — doc-only commits
    # (README.AI.md) must never flag STALE. Change the two lists together.
    # %cs = committer date: matches the STALE check's "committed after
    # UPDATED" semantics and survives rebase/cherry-pick (author date %as
    # would keep the original writing date and hide post-docs landings).
    result = subprocess.run(
        ["git", "log", "-1", "--format=%cs", "--",
         f"{addon_name}/*.py",
         f"{addon_name}/*.xml",
         f"{addon_name}/*.js",
         f"{addon_name}/*.csv",
         f"{addon_name}/*.css",
         f"{addon_name}/*.scss"],
        cwd=REPO_ROOT, capture_output=True, text=True
    )
    s = result.stdout.strip()
    return date.fromisoformat(s) if s else None

def prodenv_source_hash():
    """12-hex SHA256 of the 5 permanent AI.PRODENV.*.md category files
    (date lines excluded). Returns None when no category files exist
    (PRODENV not yet synced from staging — check is then skipped)."""
    cat_names = [
        "AI.PRODENV.TEMPLATES.md",
        "AI.PRODENV.ACTIONS.md",
        "AI.PRODENV.CRONS.md",
        "AI.PRODENV.RULES.md",
        "AI.PRODENV.REPORTS.md",
    ]
    present = [SCRIPT_DIR / n for n in cat_names if (SCRIPT_DIR / n).exists()]
    if not present:
        return None
    import hashlib
    h = hashlib.sha256()
    for path in present:
        text = path.read_text(encoding="utf-8", errors="ignore")
        # Exclude 'Generated: YYYY-MM-DD' date lines so daily re-runs don't
        # stale DOC.PRODENV.md when the actual content is unchanged.
        text = re.sub(r'^Generated:.*$', '', text, flags=re.MULTILINE)
        h.update(text.encode("utf-8"))
    return h.hexdigest()[:12]


PRODENV_CATEGORY_FILES = [
    "AI.PRODENV.TEMPLATES.md",
    "AI.PRODENV.ACTIONS.md",
    "AI.PRODENV.CRONS.md",
    "AI.PRODENV.RULES.md",
    "AI.PRODENV.REPORTS.md",
]


def check_prodenv_files():
    """Return a message if the PRODENV category files are partially present.

    Three states:
      · All 5 absent  — fresh repo, SETUP guidance covers this; return None.
      · All 5 present — healthy; return None.
      · Some present, some missing — partial sync or accidental deletion;
        return an actionable message (contributes to exit 1).
    """
    present = [f for f in PRODENV_CATEGORY_FILES if (SCRIPT_DIR / f).exists()]
    missing = [f for f in PRODENV_CATEGORY_FILES if not (SCRIPT_DIR / f).exists()]
    if not present or not missing:
        return None   # all-absent or all-present — both fine
    return (
        f"{len(missing)} of 5 AI.PRODENV.*.md category file(s) missing: "
        f"{', '.join(missing)} — the files are generated together and must all "
        f"be present; a partial set means the sync was incomplete or files were "
        f"accidentally deleted. Re-run the full PRODENV sync from staging:\n"
        f"      python3 AI/AI.gen_prodenv.py | odoo-bin shell --no-http\n"
        f"      git add AI/AI.PRODENV.*.md\n"
        f"      git commit -m 'sync: PRODENV YYYY-MM-DD' && odoosh-push\n"
        f"   Then on dev:\n"
        f"      git fetch\n"
        f"      git checkout origin/<staging-branch> -- 'AI/AI.PRODENV.*.md'\n"
        f"      git add AI/AI.PRODENV.*.md && git commit && odoosh-push"
    )


def _read_prodenv_modules(modules_path):
    """Parse AI.PRODENV.MODULES.md. Returns a dict or None.

    Dict keys: enterprise, community, themes, custom_installed, custom_not
    (each a sorted list of bare module names), snapshot_date (str YYYY-MM-DD).

    Returns None if the file is absent, empty, or lacks the expected sections.
    State tags like '  [to upgrade]' are stripped — both machine parsers
    (gen_enterprise.py and parse_not_installed_list) require bare names only.
    """
    if not modules_path.exists():
        return None
    text = modules_path.read_text(encoding="utf-8", errors="ignore").strip()
    if not text:
        return None

    # Extract snapshot date from 'Generated: YYYY-MM-DD' header line
    date_m = re.search(r'^Generated:\s*(\d{4}-\d{2}-\d{2})', text, re.MULTILINE)
    snapshot_date = date_m.group(1) if date_m else date.today().isoformat()

    def _parse_subsection(heading):
        """Extract bare names from a '### <heading>' subsection."""
        m = re.search(
            r'^### ' + re.escape(heading) + r'[ \t]*\n(.*?)(?=^### |\Z)',
            text, re.DOTALL | re.MULTILINE,
        )
        if not m:
            return []
        names = []
        for line in m.group(1).splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            # Strip leading '  ' prefix and trailing '  [state]' tag
            name = re.sub(r'\s+\[.*?\]\s*$', '', stripped).strip()
            # Validate: must look like a module name
            if re.match(r'^[A-Za-z][A-Za-z0-9_]+$', name) and name != '(none)':
                names.append(name)
        return sorted(names)

    return {
        'enterprise':       _parse_subsection('ODOO ENTERPRISE'),
        'community':        _parse_subsection('ODOO COMMUNITY'),
        'themes':           _parse_subsection('ODOO THEMES'),
        'custom_installed': _parse_subsection('CUSTOM (installed)'),
        'custom_not':       _parse_subsection('CUSTOM (not installed in production)'),
        'snapshot_date':    snapshot_date,
    }


def _apply_prodenv_modules(custom_path, modules_path):
    """Apply AI.PRODENV.MODULES.md into AI.CUSTOM.md, then delete MODULES.md.

    Trigger: modules_path.exists() — existence means an unprocessed payload
    is waiting. Absence means 'no pending update' (already processed).

    Atomic order: write CUSTOM.md first (tmp+rename), delete MODULES.md second.
    If the write fails, MODULES.md is left intact so the next run retries.

    Returns (changed: bool, summary: str).
    """
    data = _read_prodenv_modules(modules_path)
    if data is None:
        return False, ""

    text = custom_path.read_text(encoding="utf-8")

    # Locate the INSTALLED MODULES block boundaries
    start_m = re.search(r'^# INSTALLED MODULES\b[^\n]*\n', text, re.MULTILINE)
    end_m   = re.search(r'^# COUNTRIES\b', text, re.MULTILINE)
    if not start_m or not end_m or start_m.start() >= end_m.start():
        print("⚠️  PRODENV MODULES: could not locate INSTALLED MODULES block in "
              "AI.CUSTOM.md — skipping (block structure may be malformed)")
        return False, ""

    # Build the replacement block
    def _subsection(header, names):
        lines = [f"#   {header}:"]
        for n in names:
            lines.append(f"#     {n}")
        if not names:
            lines.append("#     (none)")
        lines.append("#")
        return '\n'.join(lines)

    new_block = (
        f"# INSTALLED MODULES — production snapshot: {data['snapshot_date']}\n"
        "#   (format and list rules: AI.SESSION.md — INSTALLED MODULES sections)\n"
        "#   (auto-populated by AI.canary.py from AI/AI.PRODENV.MODULES.md)\n"
        "#\n"
        + _subsection(
            "ODOO ENTERPRISE (⚠️  API changes in this Odoo version may differ "
            "from training data — verify against source if behavior is non-obvious)",
            data['enterprise'],
        ) + "\n"
        + _subsection("ODOO COMMUNITY (well known)", data['community']) + "\n"
        + _subsection(
            "ODOO THEMES (website themes from /home/odoo/src/themes/)",
            data['themes'],
        ) + "\n"
        + _subsection(
            "CUSTOM (all in /home/odoo/src/user/ — documented in >>ADDON: blocks below)",
            data['custom_installed'],
        ) + "\n"
        + _subsection(
            "NOT INSTALLED IN PRODUCTION (in codebase but inactive)",
            data['custom_not'],
        ) + "\n"
    )

    new_text = text[:start_m.start()] + new_block + text[end_m.start():]

    # Atomic write of AI.CUSTOM.md
    tmp = custom_path.with_suffix(".md.tmp")
    tmp.write_text(new_text, encoding="utf-8")
    tmp.replace(custom_path)

    # Delete MODULES.md — consumed
    modules_path.unlink()

    counts = (
        f"{len(data['enterprise'])} enterprise, "
        f"{len(data['community'])} community, "
        f"{len(data['themes'])} themes, "
        f"{len(data['custom_installed'])} custom installed, "
        f"{len(data['custom_not'])} custom not-installed"
    )
    return True, counts


def _run_gen_enterprise():
    """Run AI.gen_enterprise.py as subprocess. Returns (ok: bool, output: str)."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "AI.gen_enterprise.py")],
        capture_output=True, text=True,
    )
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def _run_gen_prodenv_doc():
    """Run AI.gen_prodenv_doc.py as subprocess. Returns (ok: bool, output: str)."""
    gen_doc = SCRIPT_DIR / "AI.gen_prodenv_doc.py"
    if not gen_doc.exists():
        return False, "AI.gen_prodenv_doc.py not found"
    result = subprocess.run(
        [sys.executable, str(gen_doc)],
        capture_output=True, text=True,
    )
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def check_dispositions(addons_path, conflicts_path):
    """(undisposed, stale, outdated, missing_file) — pure, hence testable.

    Compares DERIVED interactions against RECORDED decisions. Judges nothing:
    an interaction is not a defect, and this function never says it is. It
    only answers "has someone decided about this, and does that decision still
    describe reality?".
    """
    undisposed, stale, outdated = [], [], []
    cmod = _conflicts_module()
    if cmod is None or not addons_path.exists():
        return undisposed, stale, outdated, False
    try:
        derived = cmod.derive(cmod.parse_addons(
            addons_path.read_text(encoding="utf-8")))
    except Exception:
        return undisposed, stale, outdated, False

    # A repo with no interactions needs no disposition file at all; only
    # require one once there is something to decide about.
    if derived and not conflicts_path.exists():
        return undisposed, stale, outdated, True

    disp = parse_conflicts(conflicts_path)
    derived_keys = {key for _kind, key in derived}
    for (_kind, key), parts in sorted(derived.items()):
        if key not in disp:
            undisposed.append(f"{key}  [{len(parts)} addons: "
                              f"{', '.join(sorted(parts))}]")
        elif disp[key]["addons"] and disp[key]["addons"] != set(parts):
            gained = sorted(set(parts) - disp[key]["addons"])
            lost = sorted(disp[key]["addons"] - set(parts))
            delta = ((f"joined: {', '.join(gained)}" if gained else "")
                     + ("; " if gained and lost else "")
                     + (f"left: {', '.join(lost)}" if lost else ""))
            outdated.append(f"{key}  ({delta})")
    for key, d in sorted(disp.items()):
        if key not in derived_keys:
            stale.append(f"{conflicts_path.name}:{d['line']}: {key}")
        elif d["status"] not in CONFLICT_STATUSES:
            stale.append(f"{conflicts_path.name}:{d['line']}: {key} — STATUS "
                         f"{d['status']!r} not one of "
                         f"{'/'.join(CONFLICT_STATUSES)}")
    return undisposed, stale, outdated, False


# ── Conflict dispositions (AI.CONFLICTS.md) ─────────────────────────────────
# The DATA half of conflict checking. AI.gen_conflicts.py DERIVES which addons
# meet; this file records what was DECIDED about each meeting, and why. The
# split exists because a derived file cannot carry decisions: it is
# regenerated, so any judgment written there is destroyed on the next run.
#
# It is deliberately a SEPARATE file rather than a section of AI.CUSTOM.md:
# addons_source_hash() hashes from the first >>ADDON: line to end of file, so
# dispositions appended there would sit inside that hash and editing one
# reason string would stale all four DOC.CUSTOM.by.* files.
_CONFLICTS_MODULE = ("unloaded",)


def _conflicts_module():
    """Import AI.gen_conflicts.py, or None if absent/unloadable.

    Imported rather than run as a subprocess because the canary needs the
    structured interactions, not the human-readable report. Absence disables
    the disposition checks rather than failing — same contract as the
    enterprise generator above.
    """
    global _CONFLICTS_MODULE
    if _CONFLICTS_MODULE == ("unloaded",):
        gen = SCRIPT_DIR / "AI.gen_conflicts.py"
        if not gen.exists():
            _CONFLICTS_MODULE = None
        else:
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "ai_gen_conflicts", gen)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                _CONFLICTS_MODULE = mod
            except Exception:
                _CONFLICTS_MODULE = None
    return _CONFLICTS_MODULE


CONFLICT_STATUSES = ("Accepted", "Deferred", "Fixed", "Withdrawn")


def parse_conflicts(path):
    """{natural_key: {addons, status, decided, reason, evidence, line}}.

    Keys are the natural keys AI.gen_conflicts.py derives (e.g.
    "res.users::_prepare_home_portal_values"), NOT sequential IDs — a script
    has to pair a disposition to its interaction without human matching.
    """
    if not path.exists():
        return {}
    out, cur = {}, None
    for n, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        m = re.match(r"^>>CONFLICT:\s*(\S+)", line)
        if m:
            cur = {"addons": set(), "status": None, "decided": None,
                   "reason": None, "evidence": None, "line": n}
            out[m.group(1)] = cur
            continue
        if cur is None:
            continue
        f = re.match(r"^\s+(ADDONS|STATUS|DECIDED|REASON|EVIDENCE):\s*(.*)$",
                     line)
        if f:
            key, val = f.group(1).lower(), f.group(2).strip()
            if key == "addons":
                cur["addons"] = {a.strip() for a in val.split(",") if a.strip()}
            else:
                cur[key] = val or None
    return out


INIT_CONFLICTS = """# AI.CONFLICTS - Repo Data (cross-addon interaction dispositions)
# \u26a0\ufe0f  AI: this file records DECISIONS, never derivations. What interacts is
#   derived live by AI.gen_conflicts.py from the >>ADDON: blocks; this file
#   says what was DECIDED about each interaction and why. Never regenerate it,
#   and never write a decision into DOC.CONFLICTS.Addons.md instead \u2014 that
#   file is regenerated wholesale and the decision would be destroyed.
#
#   Block format and field semantics: CONFLICT DISPOSITIONS in
#   AI.SPECS.ADDONS.md \u2014 the authoritative copy. Restating them here would
#   create a mirror pair to drift, the same reason AI.CUSTOM.md's header
#   points at the specs rather than repeating them.
#
#   See what needs deciding:  python3 AI/AI.gen_conflicts.py
#   Regenerate the readable register after deciding:
#                             python3 AI/AI.gen_conflicts.py --write
#
# \u2500\u2500\u2500\u2500\u2500 end of header \u2014 real >>CONFLICT: blocks follow BELOW this line \u2500\u2500\u2500\u2500\u2500
"""


def init_conflicts():
    """--init-conflicts: write the starter AI.CONFLICTS.md. Never overwrites."""
    if CONFLICTS_AI.exists():
        print("\u26d4 AI.CONFLICTS.md already exists \u2014 never overwritten.")
        print("   It holds decisions; restore a damaged one from git history:")
        print("      git checkout -- AI.CONFLICTS.md")
        return 1
    CONFLICTS_AI.write_text(INIT_CONFLICTS, encoding="utf-8")
    print("\u2705 created AI.CONFLICTS.md (empty disposition file)")
    print("   next: python3 AI/AI.gen_conflicts.py to see what needs disposing")
    return 0


# ── --init: generate the v9 starter AI.CUSTOM.md ──────────────────────
INIT_COUNTRIES = ("us", "ca", "ph")
APPS_BASELINE_LINE = "# APPS (baseline 19.0): Accounting, AI, Appointments, Appraisals, Approvals, Attendances, Barcode, Calendar, Contacts, CRM, Data Recycle, Databases, Discuss, Documents, eCommerce, eLearning, Email Marketing, Employees, Equity, ESG, Events, Expenses, Field Service, Fleet, Frontdesk, Helpdesk, Inventory, Invoicing, IoT, Knowledge, Live Chat, Lunch, Maintenance, Manufacturing, Marketing Automation, Marketing Card, Meeting Rooms, Online Jobs, Payroll, Phone, Planning, Platform, PLM, Point of Sale, Project, Purchase, Quality, Recruitment, Referrals, Rental, Repairs, Restaurant, Sales, Sign, Skills Management, SMS Marketing, Social Marketing, Studio, Subscriptions, Surveys, Time Off, Timesheets, To-Do, Website, WhatsApp Messaging"
INIT_MARKER = ('#     (NOT YET POPULATED — run the "Update installed '
               'modules list + Enterprise index" prompt)')
INIT_SUBSECTIONS = (
    "#   ODOO ENTERPRISE (⚠️  API changes in this Odoo version may differ from training data — verify against source if behavior is non-obvious):",
    "#   ODOO COMMUNITY (well known):",
    "#   ODOO THEMES (website themes from /home/odoo/src/themes/):",
    "#   CUSTOM (all in /home/odoo/src/user/ — documented in >>ADDON: blocks below):",
    "#   NOT INSTALLED IN PRODUCTION (in codebase but inactive):",
)
INIT_POINTER = (
    "# AI.CUSTOM - Repo Data",
    "# 🛑 AI INSTRUCTION — STOP: read AI/AI.SESSION.md BEFORE processing",
    "#    anything in this file. The session-start sequence, all field",
    "#    semantics, and every convention live in AI.SESSION.md. This file",
    "#    contains ONLY this repo's data. Reading this file without first",
    "#    reading AI.SESSION.md is an error — stop and read it now.",
    '#   Bump the "# UPDATED:" line below on every edit to this file.',
)
INIT_SENTINEL = ("# ───── end of header — real >>ADDON: blocks follow "
                 "BELOW this line ───────────")


def init_custom(defaults):
    """--init: write the v9 starter AI.CUSTOM.md. Never overwrites."""
    if ADDONS_AI.exists():
        print("⛔ AI.CUSTOM.md already exists — --init never overwrites it.")
        print("   Edit the existing file by hand, or restore a damaged one")
        print("   from git history: git checkout -- AI.CUSTOM.md")
        return 1

    # Odoo.sh environment guard — version detection requires the platform.
    # Running --init outside Odoo.sh produces a mis-stamped ODOO: line
    # (the fallback is the APPS baseline version, not the actual environment
    # version). Detected via the Odoo release file, which is present on
    # every Odoo.sh build and absent on local checkouts.
    _release = Path("/home/odoo/src/odoo/odoo/release.py")
    if not _release.exists():
        print("⛔ --init must be run inside the Odoo.sh shell.")
        print("   Version detection requires the platform — running locally")
        print("   would stamp the wrong Odoo version into AI.CUSTOM.md.")
        print("   Open the Odoo.sh shell for your dev build and run:")
        print("      python3 AI/AI.canary.py --init")
        return 1

    # ODOO line — no questions: environment-detected version, edition
    # constant "Enterprise" (the template assumes Odoo.sh Enterprise).
    version, detected = None, True
    mod = _gen_module()
    if mod is not None:
        try:
            version = mod.detect_odoo_version() or None
        except Exception:
            version = None
    if not version:
        version = re.search(r"baseline (\d+\.\d+)",
                            APPS_BASELINE_LINE).group(1)
        detected = False

    # COUNTRIES — the one question, as a menu; Enter = 1 = us. With
    # --defaults, or when stdin yields nothing (EOF — non-interactive
    # run without piped input), option 1 is taken silently.
    if defaults:
        country = INIT_COUNTRIES[0]
        asked = False
    else:
        asked = True
        print("Select this repo's country for localizations "
              "(the \"# COUNTRIES:\" line):")
        print("  1. us    2. ca    3. ph")
        print("  (multi-country? select the PRIMARY country now, then")
        print('   hand-edit the "# COUNTRIES:" line in AI.CUSTOM.md to a')
        print("   comma list later, e.g. \"us, ca\")")
        while True:
            try:
                choice = input("Choice [1]: ").strip() or "1"
            except EOFError:
                choice, asked = "1", False
            if choice in ("1", "2", "3"):
                country = INIT_COUNTRIES[int(choice) - 1]
                break
            print("  enter 1, 2, or 3")

    out = list(INIT_POINTER)
    out.append(f"# UPDATED: {date.today().isoformat()}")
    out.append(f"# ODOO: {version} Enterprise")
    out.append("#")
    out.append("# INSTALLED MODULES — production snapshot: (not yet taken)")
    out.append("#   (format and list rules: AI.SESSION.md — INSTALLED "
               "MODULES sections)")
    for header in INIT_SUBSECTIONS:
        out.append("#")
        out.append(header)
        out.append(INIT_MARKER)
    out.append("#")
    out.append(f"# COUNTRIES: {country}")
    out.append(APPS_BASELINE_LINE)
    out.append("# COVERAGE: 0 of 0 addons documented")
    out.append(INIT_SENTINEL)
    ADDONS_AI.write_text("\n".join(out) + "\n", encoding="utf-8")

    print(f"✅ created AI.CUSTOM.md (v9 starter) — ODOO: {version} "
          f"Enterprise"
          + ("" if detected else " (version NOT detected from the "
             "environment — APPS baseline used; hand-verify the line)")
          + f"; COUNTRIES: {country}"
          + ("" if asked else " (default)"))
    print("   hand-checks: the # ODOO: edition (Enterprise assumed) and,")
    print("   for multi-country repos, the # COUNTRIES: comma list")
    print("   next: python3 AI/AI.canary.py — its SETUP guidance walks the")
    print("   remaining setup steps")
    return 0


SPEC_UPDATED_RE = re.compile(r"^UPDATED:\s*(.+?)\s*$")

def check_spec_contracts(on_disk):
    """Check 19 — SPEC.AI.md staleness and format (the SPEC.AI.md
    CONVENTION in AI.SESSION.md defines the file; this script checks only
    the mechanical layer — dates vs git history — never content). Only
    files that EXIST are checked; absence is not a finding, only the
    informational ◻︎ SPEC coverage line.
    Returns (stale, malformed, with_spec_count)."""
    stale, malformed, with_spec = [], [], 0
    for addon in sorted(on_disk):
        spec_path = REPO_ROOT / addon / "SPEC.AI.md"
        if not spec_path.exists():
            continue
        with_spec += 1
        lines = spec_path.read_text(encoding="utf-8",
                                    errors="replace").splitlines()
        first = lines[0].strip() if lines else ""
        m = SPEC_UPDATED_RE.match(first)
        if not m:
            malformed.append(
                f"{addon}: SPEC.AI.md does not START with an UPDATED line "
                f"— insert, as line 1 of the file (above any title or "
                f"template content), exactly: UPDATED: YYYY-MM-DD "
                f"(e.g. 'UPDATED: 2026-01-31' — the date the spec was "
                f"written or last confirmed; SPEC.AI.md CONVENTION in "
                f"AI.SESSION.md)")
            continue
        try:
            updated = date.fromisoformat(m.group(1))
        except ValueError:
            malformed.append(
                f"{addon}: SPEC.AI.md UPDATED value '{m.group(1)}' is "
                f"unparsable — repair it to YYYY-MM-DD (do not add a "
                f"second UPDATED line)")
            continue
        # No git history yet → nothing to compare; the ⬜/🆕 checks own
        # that state.
        last = last_commit_date(addon)
        if last is not None and last > updated:
            stale.append((addon, updated, last))
    return stale, malformed, with_spec

def backfill_created(branch):
    """Fill in missing CREATED dates from a branch's git history.

    Derives each addon's date from when its folder FIRST APPEARED on the
    named branch. Two things about that date, both deliberate:
      · It is a first-appearance date, not an authorship date. A bulk move
        ("Move addons and update X") stamps every addon relocated that day
        with the move's date. That is usually still the right side of any
        convention boundary, but it is not literally when the code was
        written — so the value is written once, reviewed by a human here,
        and never re-derived afterwards.
      · The PRODUCTION branch is the right source because dev branches are
        routinely deleted after merge, leaving production the only durable
        record. Its name is asked for rather than guessed: it varies by repo,
        and odoo.sh's own notion of which branch is production is not visible
        from inside the container.
    Addons with no history on the branch (typically still under development)
    are REPORTED, never guessed — a wrong date frozen into documentation is
    worse than an absent one.
    """
    if not ADDONS_AI.exists():
        print("⚠️  AI.CUSTOM.md MISSING — nothing to backfill.")
        return 1
    if not branch:
        print("⚠️  --backfill-created requires --branch <production-branch>.")
        print("   The branch name is not guessed: it varies by repo, and")
        print("   odoo.sh's determination of it is not visible from here.")
        print("   Ask the human which branch is production, then re-run.")
        return 1
    if subprocess.run(["git", "rev-parse", "--verify", "--quiet", branch],
                      cwd=REPO_ROOT, capture_output=True).returncode != 0:
        print(f"⚠️  branch '{branch}' does not resolve in this repository.")
        print("   Check the name — a bad ref would otherwise look exactly like")
        print("   'no history for this addon' and silently produce no dates.")
        return 1

    addons = parse_addons(ADDONS_AI)
    targets = [a for a, i in sorted(addons.items())
               if i["created"] is None and i["created_bad"] is None]
    if not targets:
        print("✅  Every >>ADDON: block already has a CREATED date — nothing to do.")
        return 0

    derived, underivable = [], []
    for addon in targets:
        out = subprocess.run(
            ["git", "log", branch, "--diff-filter=A", "--format=%ad",
             "--date=short", "--", f"{addon}/"],
            cwd=REPO_ROOT, capture_output=True, text=True)
        dates = [l.strip() for l in out.stdout.splitlines() if l.strip()]
        if dates:
            derived.append((addon, dates[-1]))   # last line = earliest add
        else:
            underivable.append(addon)

    print(f"\nPreview — derived from first appearance on '{branch}':")
    for addon, d in derived:
        print(f"   CREATED: {d}   {addon}")
    if underivable:
        print(f"\n   No history on '{branch}' ({len(underivable)}) — NOT guessed, "
              f"set these by hand:")
        for addon in underivable:
            print(f"      {addon}")
    if not derived:
        print("\nNothing derivable. No changes written.")
        return 1

    print(f"\nWrite {len(derived)} CREATED line(s) into AI.CUSTOM.md? [y/N] ", end="")
    try:
        answer = input().strip().lower()
    except EOFError:
        answer = ""
    if answer not in ("y", "yes"):
        print("Aborted — no changes written.")
        return 1

    # Insert CREATED directly after each block's UPDATED line (both are dates;
    # keeping them adjacent matches the block template's ordering).
    pending = dict(derived)
    lines, current, out_lines = ADDONS_AI.read_text(encoding="utf-8").splitlines(True), None, []
    for line in lines:
        out_lines.append(line)
        m = re.match(r'^>>ADDON:\s+(\S+)', line)
        if m:
            current = m.group(1)
            continue
        if current and current in pending and re.match(r'^\s*UPDATED:', line):
            out_lines.append(f"CREATED: {pending.pop(current)}\n")
            current = None
    ADDONS_AI.write_text("".join(out_lines), encoding="utf-8")
    written = len(derived) - len(pending)
    print(f"✅  Wrote {written} CREATED line(s).")
    if pending:
        print(f"⚠️  {len(pending)} block(s) had no UPDATED line to anchor to — "
              f"add CREATED by hand: {', '.join(sorted(pending))}")
    return 0


def main():
    if "--stamp" in sys.argv[1:]:
        return print_stamps()
    if "--backfill-created" in sys.argv[1:]:
        args = sys.argv[1:]
        branch = (args[args.index("--branch") + 1]
                  if "--branch" in args and args.index("--branch") + 1 < len(args)
                  else None)
        return backfill_created(branch)
    if "--init-conflicts" in sys.argv[1:]:
        return init_conflicts()
    if "--init" in sys.argv[1:]:
        rc = init_custom("--defaults" in sys.argv[1:])
        # a new repo gets both data files; --init-conflicts exists separately
        # so an EXISTING repo (whose AI.CUSTOM.md is already present) can
        # create just this one when upgrading.
        if rc == 0 and not CONFLICTS_AI.exists():
            init_conflicts()
        return rc

    # One-time, self-disabling rename of a legacy DOC.STUDIO.md (see the
    # migration helper above). Runs before any check that reads the derived
    # files by name, so the file is seen under its new name this same run.
    migrate_studio_analysis_rename()

    # Ensure the human-facing root pointer exists (create-once). Runs before
    # the AI.CUSTOM.md guard so even a not-yet-initialized repo gets it.
    ensure_root_readme()

    # ── Auto-apply PRODENV module list (if MODULES.md is present) ───────────
    # AI.PRODENV.MODULES.md is a transient carrier synced from staging.
    # Existence = unprocessed payload. Process → write AI.CUSTOM.md → delete.
    # Runs before the ADDONS_AI existence check so a brand-new repo that just
    # received its first PRODENV sync can bootstrap its module list.
    _modules_path = SCRIPT_DIR / "AI.PRODENV.MODULES.md"
    if _modules_path.exists() and ADDONS_AI.exists():
        _applied, _summary = _apply_prodenv_modules(ADDONS_AI, _modules_path)
        if _applied:
            print(f"ℹ️  PRODENV MODULES APPLIED — {_summary}")
            print("    AI.PRODENV.MODULES.md deleted (consumed)")
            _ok, _out = _run_gen_enterprise()
            if _ok:
                print("ℹ️  AUTO-REGENERATED AI.ENTERPRISE.md from updated module list")
            else:
                print(f"⚠️  AI.gen_enterprise.py failed after PRODENV apply: "
                      f"{_out[:200]}")
            _ok2, _out2 = _run_gen_prodenv_doc()
            if _ok2:
                print("ℹ️  AUTO-REGENERATED DOC.PRODENV.md")
            else:
                print(f"⚠️  AI.gen_prodenv_doc.py failed: {_out2[:120]}")

    if not ADDONS_AI.exists():
        print("⚠️  AI.CUSTOM.md MISSING — the repo data file is absent; all "
              "other checks are skipped until it exists.")
        print("   New repo being set up:  python3 AI/AI.canary.py --init")
        print("   Existing repo: RESTORE it — do NOT re-init (a re-init "
              "starter has no")
        print("   addon blocks or module lists; the repo's data would be "
              "blanked):")
        print("      git checkout -- AI.CUSTOM.md")
        return 1

    addons = parse_addons(ADDONS_AI)
    documented = set(addons.keys())
    on_disk = set(find_addon_folders())

    stale, no_folder, no_commits = [], [], []
    undocumented = sorted(on_disk - documented)

    for addon, info in sorted(addons.items()):
        if not (REPO_ROOT / addon).exists():
            no_folder.append(addon)
            continue
        last = last_commit_date(addon)
        if last is None:
            no_commits.append(addon)
        elif info["updated"] and last > info["updated"]:
            stale.append((addon, info["updated"], last))

    # MISSING CREATED: its own category, deliberately NOT folded into
    # MALFORMED BLOCK. Every other required block field must be authored by a
    # human; CREATED is derivable from git history, so the remedy is one
    # command rather than a writing task, and the report can carry that
    # command. Folding it in would tell the reader "someone must write
    # something" when the truth is "run this".
    missing_created = [addon for addon, info in sorted(addons.items())
                       if info["created"] is None and info["created_bad"] is None]

    # MALFORMED BLOCK: required lines absent, or STATUS value unrecognized.
    # Without this, a missing UPDATED silently exempts the addon from the
    # STALE and DATE MISMATCH checks, and a missing or mistyped STATUS
    # silently reads as active — the dangerous default.
    malformed = []
    for addon, info in sorted(addons.items()):
        # An UPDATED line
        # with an unparsable date counts as PRESENT here and is reported
        # separately below — calling it "missing" could lead a fixer to add
        # a second UPDATED line instead of repairing the existing one.
        updated_present = (True if (info["updated"] is not None
                                    or info["updated_bad"] is not None) else None)
        missing = [name for name, val in (("UPDATED", updated_present),
                                          ("STATUS", info["status"]),
                                          ("PURPOSE", info["purpose"]),
                                          ("IMPACT", info["impact"]),
                                          ("TYPE", info["type"]),
                                          ("APP", info["app"])) if val is None]
        if missing:
            malformed.append(f"{addon}: block is missing {' and '.join(missing)}")
        if info["updated_bad"] is not None:
            malformed.append(
                f"{addon}: UPDATED value '{info['updated_bad']}' is unparsable — "
                f"use YYYY-MM-DD")
        if info["created_bad"] is not None:
            # An unparsable CREATED is a human repair job, so it belongs with
            # the other malformations — unlike a MISSING one, which is
            # derivable and reported in its own category below.
            malformed.append(
                f"{addon}: CREATED value '{info['created_bad']}' is unparsable — "
                f"use YYYY-MM-DD")
        for field, count in sorted(info["dups"].items()):
            if count > 1:
                malformed.append(
                    f"{addon}: block has {count} {field} lines — a single-value "
                    f"field, keep exactly one (where a script parses it, the last "
                    f"wins silently; a copied template parenthetical is the "
                    f"classic cause)")
        s = info["status"]
        if s is not None and s != "active" and s != NOT_INSTALLED_STATUS:
            malformed.append(
                f"{addon}: STATUS '{s}' is not an allowed value — use 'active' "
                f"(lowercase) or, verbatim: '{NOT_INSTALLED_STATUS}'")

    # IMPACT/TYPE/APP: fixed-vocabulary fields. The value checks below guard
    # on presence only to avoid double-reporting — a missing field is already
    # reported by the required-lines check above. A typo'd value would
    # otherwise surface only as a phantom group in a regenerated
    # DOC.CUSTOM.by.* summary, one generation cycle after the mistake.
    apps_parsed = parse_apps_line(ADDONS_AI)
    app_values = set(apps_parsed[1]) if apps_parsed else None  # None → check 11 reports the missing line
    for addon, info in sorted(addons.items()):
        if info["impact"] is not None and info["impact"] not in IMPACT_VALUES:
            malformed.append(
                f"{addon}: IMPACT '{info['impact']}' is not an allowed value — "
                f"use Minor, Intermediate, or Major")
        if info["type"] is not None:
            types = [t.strip() for t in info["type"].split(",") if t.strip()]
            bad = [t for t in types if t not in TYPE_VALUES]
            if bad:
                malformed.append(
                    f"{addon}: TYPE {', '.join(repr(t) for t in bad)} not in the fixed set "
                    f"(Read-Only, Updates, Override, UI, Integration)")
            if "Read-Only" in types and "Updates" in types:
                malformed.append(
                    f"{addon}: TYPE lists both Read-Only and Updates — mutually "
                    f"exclusive per TYPE DEFINITIONS in AI.SPECS.ADDONS.md")
        if info["app"] is not None and app_values is not None \
                and info["app"] not in app_values:
            malformed.append(
                f"{addon}: APP '{info['app']}' is not on the '# APPS (baseline …):' "
                f"data line (single value, exactly as listed there)")

    # STATUS cross-check: block STATUS (authoritative) vs header list.
    # Classification is deliberately laxer than validation above: any value
    # starting with "not installed" classifies as inactive (so a paraphrased
    # not-installed sentence — already reported as MALFORMED — still compares
    # as the documenter intended), while a missing or otherwise-invalid
    # STATUS is skipped entirely: its production state is unknowable until
    # check 13's MALFORMED finding is fixed, and reporting it here as
    # "says active" would be false. One finding per mistake.
    inactive_blocks = {a for a, info in addons.items()
                       if info["status"] and info["status"].lower().startswith("not installed")}
    listed = parse_not_installed_list(ADDONS_AI)
    status_mismatch = []
    for addon in sorted(inactive_blocks - listed):
        status_mismatch.append(
            f"{addon}: block STATUS says not installed, but missing from NOT INSTALLED IN PRODUCTION list")
    for addon in sorted((listed & documented) - inactive_blocks):
        if addons[addon]["status"] != "active":
            continue  # missing or invalid — already reported as MALFORMED BLOCK
        status_mismatch.append(
            f"{addon}: listed as NOT INSTALLED IN PRODUCTION, but block STATUS says active")
    for name in sorted(listed - documented):
        if (REPO_ROOT / name).exists():
            status_mismatch.append(
                f"{name}: listed as NOT INSTALLED IN PRODUCTION but has no >>ADDON: block — "
                f"a documentation gap: document it (AI prompt: Analyze and document "
                f"addon {name}), do not delist it")
        else:
            status_mismatch.append(
                f"{name}: listed as NOT INSTALLED IN PRODUCTION but has neither a "
                f">>ADDON: block nor a folder in the repo — a leftover from an addon "
                f"removal: delete the list entry (the \"Remove addon from "
                f"documentation\" prompt includes this step)")

    # DATE cross-check: block UPDATED vs README.AI.md UPDATED (must be equal).
    # README-header cross-check: block IMPACT/TYPE/APP vs the README header
    # lines that duplicate them (NOTE ON DUPLICATION in AI.SPECS.ADDONS.md) — a
    # value re-judged in one file must not silently disagree with the other.
    date_mismatch = []
    readme_mismatch = []
    for addon, info in sorted(addons.items()):
        folder = REPO_ROOT / addon
        if not folder.exists():
            continue  # already reported as FOLDER MISSING
        readme = folder / "README.AI.md"
        if not readme.exists():
            date_mismatch.append(
                f"{addon}: README.AI.md is missing — every documented addon needs "
                f"one (see AI.SPECS.ADDONS.md / the \"Analyze and "
                f"document addon\" prompt)")
            continue
        readme_text = readme.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r'UPDATED:\s*(\d{4}-\d{2}-\d{2})', readme_text)
        if not m:
            date_mismatch.append(f"{addon}: README.AI.md has no parsable UPDATED date")
        else:
            try:
                readme_date = date.fromisoformat(m.group(1))
            except ValueError:
                # shape-valid but not a real date (e.g. month 13) — report
                # it, never crash: one bad README must not silence all
                # checks (the block-side parser degrades the same way,
                # via updated_bad)
                readme_date = None
                date_mismatch.append(
                    f"{addon}: README.AI.md UPDATED '{m.group(1)}' is not a "
                    f"real date — use a valid YYYY-MM-DD")
            if readme_date is not None and info["updated"] \
                    and readme_date != info["updated"]:
                date_mismatch.append(
                    f"{addon}: block UPDATED {info['updated']} != README.AI.md UPDATED {m.group(1)}")
        for field in ("IMPACT", "TYPE", "APP"):
            block_val = info[field.lower()]
            if block_val is None:
                continue  # missing in the block — already reported as MALFORMED
            rm = re.search(r'^#\s*' + field + r':\s*(.+?)\s*$',
                           readme_text, re.MULTILINE)
            if not rm:
                readme_mismatch.append(
                    f"{addon}: README.AI.md has no '# {field}:' header line — "
                    f"required (see the README.AI.md FILE FORMAT in AI.SPECS.ADDONS.md)")
                continue
            readme_val = rm.group(1)
            if field == "TYPE":
                # unordered comma-list — reordering is not drift
                same = (sorted(t.strip() for t in block_val.split(',') if t.strip())
                        == sorted(t.strip() for t in readme_val.split(',') if t.strip()))
            else:
                same = block_val == readme_val
            if not same:
                readme_mismatch.append(
                    f"{addon}: block {field} '{block_val}' != README.AI.md "
                    f"{field} '{readme_val}'")

    # COVERAGE cross-check: header line vs reality
    coverage = parse_coverage(ADDONS_AI)
    actual = (len(documented & on_disk), len(on_disk))
    coverage_mismatch = None
    if coverage is None:
        coverage_mismatch = f"COVERAGE line missing or unparsable — actual: {actual[0]} of {actual[1]}"
    elif coverage != actual:
        coverage_mismatch = (f"COVERAGE line says {coverage[0]} of {coverage[1]}, "
                             f"actual: {actual[0]} of {actual[1]}")

    # DERIVED-FILE freshness: SOURCE-HASH stamps vs current sources
    stale_derived = check_derived_freshness()

    # Auto-fix AI.ENTERPRISE.md if stale — run gen_enterprise instead of reporting
    _ENT = "AI.ENTERPRISE.md"
    if any(_ENT in msg for msg in stale_derived):
        stale_derived = [m for m in stale_derived if _ENT not in m]
        _ok, _out = _run_gen_enterprise()
        if _ok:
            print(f"ℹ️  AUTO-REGENERATED {_ENT} (SOURCE-HASH stale)")
        else:
            stale_derived.append(f"{_ENT}: auto-regen failed — {_out[:120]}")

    # Auto-fix DOC.PRODENV.md if stale
    _DOC_PD = "DOC.PRODENV.md"
    if any(_DOC_PD in msg for msg in stale_derived):
        stale_derived = [m for m in stale_derived if _DOC_PD not in m]
        _ok2, _out2 = _run_gen_prodenv_doc()
        if _ok2:
            print(f"ℹ️  AUTO-REGENERATED {_DOC_PD} (SOURCE-HASH stale)")
        else:
            stale_derived.append(f"{_DOC_PD}: auto-regen failed — {_out2[:120]}")

    # DERIVED-FILE existence: expected (source present) but not found
    missing_derived = check_derived_missing()

    # Auto-fix AI.ENTERPRISE.md if missing
    if any(f == _ENT for f, _ in missing_derived):
        missing_derived = [(f, h) for f, h in missing_derived if f != _ENT]
        _ok, _out = _run_gen_enterprise()
        if _ok:
            print(f"ℹ️  AUTO-GENERATED {_ENT} (was missing)")
        else:
            missing_derived.append((_ENT, f"auto-gen failed: {_out[:120]}"))

    # Auto-fix DOC.PRODENV.md if missing
    if any(f == _DOC_PD for f, _ in missing_derived):
        missing_derived = [(f, h) for f, h in missing_derived if f != _DOC_PD]
        _ok2, _out2 = _run_gen_prodenv_doc()
        if _ok2:
            print(f"ℹ️  AUTO-GENERATED {_DOC_PD} (was missing)")
        else:
            missing_derived.append((_DOC_PD, f"auto-gen failed: {_out2[:120]}"))

    # ODOO header line vs environment-detected version
    odoo_mismatch = check_odoo_version()

    # APPS baseline vs the ODOO header line
    apps_mismatch = check_apps_baseline()

    # Active manifest hazard in studio_customization/
    studio_manifest = check_studio_manifest()

    # Export folder vs AI.STUDIO.md's recorded EXPORT-HASH
    stale_studio_doc = check_studio_export_doc()

    # Template spec files present (AI.SPECS.*.md)
    spec_problem = check_spec_files()

    # PRODENV category file completeness (partial sync / accidental deletion)
    prodenv_incomplete = check_prodenv_files()

    # GENERATOR availability: AI.gen_enterprise.py is a required template
    # file; without it the ODOO-line check, AI.ENTERPRISE.md freshness, and
    # the AI.ENTERPRISE.md existence expectation are all silently disabled —
    # report the disablement instead of letting a deleted or broken generator
    # suppress its own checks. (Off-platform is unaffected: a healthy
    # generator loads fine there and the ODOO check skips on its own.)
    gen_problem = None
    if _gen_module() is None:
        state = ("missing" if not (SCRIPT_DIR / "AI.gen_enterprise.py").exists()
                 else "present but failed to load")
        gen_problem = (f"AI.gen_enterprise.py is {state} — the ODOO version check, "
                       f"AI.ENTERPRISE.md freshness, and AI.ENTERPRISE.md existence "
                       f"checks are DISABLED until it is restored; restore it from "
                       f"the template repository (or from git history: "
                       f"git checkout -- AI.gen_enterprise.py)")

    # Check 18 — INVENTORY DRIFT (delegated: AI.gen_inventory.py --check)
    inventory_drift, inventory_problem = check_inventory_drift(
        bool(on_disk or documented))

    # Check 19 — SPEC.AI.md contracts (SPEC STALE / SPEC MALFORMED;
    # absence deliberately unchecked — only the ◻︎ SPEC coverage line)
    spec_stale, spec_malformed, addons_with_spec = check_spec_contracts(on_disk)

    # Check 20 — conflict DISPOSITIONS. Derivation is delegated to
    # AI.gen_conflicts.py (facts: which addons meet); this check only compares
    # those facts against the decisions recorded in AI.CONFLICTS.md. It never
    # judges whether an interaction is a defect — that is the whole point of
    # keeping derivation and disposition apart.
    (undisposed, stale_disposition, disposition_outdated,
     conflicts_missing) = check_dispositions(ADDONS_AI, CONFLICTS_AI)

    if stale:
        print(f"\n⚠️  STALE — committed after UPDATED date ({len(stale)}):")
        print("   (if the docs were updated with the change but committed later, they")
        print("    may be current — verify, then set both UPDATED dates to the commit date)")
        for addon, updated, last in stale:
            print(f"   {addon:<45}  UPDATED: {updated}  last commit: {last}")

    if undocumented:
        print(f"\n🆕 UNDOCUMENTED — addon folder on disk but absent from AI.CUSTOM.md ({len(undocumented)}):")
        for addon in undocumented:
            last = last_commit_date(addon)
            suffix = f"  last commit: {last}" if last else ""
            print(f"   {addon}{suffix}")

    if no_folder:
        print(f"\n❓ FOLDER MISSING — documented but not on disk ({len(no_folder)}):")
        for addon in no_folder:
            print(f"   {addon}")

    if no_commits:
        print(f"\n⬜ NO COMMITS — folder exists but no git history ({len(no_commits)}):")
        print("   (informational — normal for a new addon awaiting its first commit;")
        print("    does not affect the exit status)")
        for addon in no_commits:
            print(f"   {addon}")

    if missing_created:
        print(f"\n⚠️  MISSING CREATED — block has no CREATED date ({len(missing_created)}):")
        print("   (CREATED records when the addon first appeared. Unlike the other")
        print("    required block fields it is DERIVED, not authored — so this is a")
        print("    one-command fix, not a writing task. Ask the human for the name of")
        print("    this repo's PRODUCTION branch, then run:")
        print("        python3 AI/AI.canary.py --backfill-created --branch <production-branch>")
        print("    It previews every date it would write and asks before touching the")
        print("    file. Addons with no history on that branch are reported, never")
        print("    guessed — set those by hand. New addons should get CREATED when they")
        print("    are first documented, so this backfill is only for the historical")
        print("    ones; see AI.SPECS.ADDONS.md.)")
        for addon in missing_created:
            print(f"   {addon}: block is missing CREATED")

    if malformed:
        print(f"\n⚠️  MALFORMED BLOCK — required block lines missing or invalid ({len(malformed)}):")
        print("   (every >>ADDON: block requires UPDATED, STATUS, PURPOSE, IMPACT, TYPE,")
        print("    and APP — see the block template in AI.SPECS.ADDONS.md; a missing STATUS")
        print("    would otherwise read as active, a missing UPDATED exempts the addon")
        print("    from STALE checks, and the other four have no defined rendering in")
        print("    README.AI.md headers and DOC.CUSTOM.by.* summaries when absent)")
        for msg in malformed:
            print(f"   {msg}")

    if status_mismatch:
        print(f"\n⚠️  STATUS MISMATCH — block STATUS vs NOT INSTALLED IN PRODUCTION list ({len(status_mismatch)}):")
        print("   (where a block exists its STATUS is authoritative — reconcile the header")
        print("    list; a listed addon with no block needs documenting while its folder")
        print("    exists — with the folder gone too, it is a removal leftover to delist)")
        for msg in status_mismatch:
            print(f"   {msg}")

    if date_mismatch:
        print(f"\n⚠️  DATE MISMATCH — block UPDATED vs README.AI.md ({len(date_mismatch)}):")
        print("   (the maintenance rules require both to be updated together; a missing")
        print("    or date-less README.AI.md is reported here too — create/fix it rather")
        print("    than aligning dates)")
        for msg in date_mismatch:
            print(f"   {msg}")

    if readme_mismatch:
        print(f"\n⚠️  README MISMATCH — block IMPACT/TYPE/APP vs README.AI.md header ({len(readme_mismatch)}):")
        print("   (the README.AI.md header duplicates these fields from the block — see")
        print("    NOTE ON DUPLICATION in AI.SPECS.ADDONS.md; determine which side is correct")
        print("    and update the stale one, bumping both UPDATED dates)")
        for msg in readme_mismatch:
            print(f"   {msg}")

    if coverage_mismatch:
        print(f"\n⚠️  COVERAGE MISMATCH — {coverage_mismatch}")

    if stale_derived:
        print(f"\n⚠️  STALE DERIVED — SOURCE-HASH stamp missing or out of date ({len(stale_derived)}):")
        print("   (regenerate the file; get current stamps with: python3 AI/AI.canary.py --stamp)")
        for msg in stale_derived:
            print(f"   {msg}")

    if undisposed:
        print(f"\n🔀 UNDISPOSED — derived interaction with no decision "
              f"recorded ({len(undisposed)}):")
        print("   (these are FACTS, not defects — record a decision for each "
              "in AI.CONFLICTS.md;")
        print("    see them in full with: python3 AI/AI.gen_conflicts.py)")
        for msg in undisposed:
            print(f"   {msg}")

    if disposition_outdated:
        print(f"\n🔀 DISPOSITION OUTDATED — participants changed since the "
              f"decision ({len(disposition_outdated)}):")
        print("   (the judgment was made about a different set of addons; "
              "revisit and update ADDONS:)")
        for msg in disposition_outdated:
            print(f"   {msg}")

    if stale_disposition:
        print(f"\n🔀 STALE DISPOSITION — recorded decision with no matching "
              f"interaction ({len(stale_disposition)}):")
        print("   (the interaction is gone or the key/STATUS is wrong — "
              "delete the block or correct it)")
        for msg in stale_disposition:
            print(f"   {msg}")

    if missing_derived:
        print(f"\n📄 MISSING DERIVED — expected but not found ({len(missing_derived)}):")
        for fname, how in missing_derived:
            print(f"   {fname}")
            print(f"      create → {how}")

    if prodenv_incomplete:
        print(f"\n⚠️  PRODENV INCOMPLETE — {prodenv_incomplete}")

    if odoo_mismatch:
        print(f"\n⚠️  ODOO VERSION MISMATCH — {odoo_mismatch}")

    if apps_mismatch:
        print(f"\n⚠️  APPS BASELINE MISMATCH — {apps_mismatch}")

    if studio_manifest:
        print(f"\n⚠️  ACTIVE STUDIO MANIFEST — {studio_manifest}")

    if stale_studio_doc:
        print(f"\n⚠️  STALE STUDIO DOC — {stale_studio_doc}")

    if spec_problem:
        print(f"\n⚠️  SPECS MISSING — {spec_problem}")

    if gen_problem:
        print(f"\n⚠️  GENERATOR UNAVAILABLE — {gen_problem}")

    if inventory_drift:
        print(f"\n⚠️  INVENTORY DRIFT — block inventory vs addon code ({len(inventory_drift)}):")
        print("   (adopted verbatim from: python3 AI/AI.gen_inventory.py --check — classify")
        print("    each as doc rot or an extractor bug [fix AI.gen_inventory.py in the")
        print("    template repo]. Doc rot is fixed mechanically: run")
        print("    python3 AI/AI.gen_inventory.py --write, then review the judgment fields")
        print("    and bump both UPDATED dates if the change warrants it — see the")
        print("    MAINTENANCE rules in AI.SPECS.ADDONS.md; the tool's ◻︎ honesty notes")
        print("    are advisory and appear only in its own output)")
        for msg in inventory_drift:
            print(f"   {msg}")

    if inventory_problem:
        print(f"\n⚠️  INVENTORY CHECKER UNAVAILABLE — {inventory_problem}")

    if spec_stale:
        print(f"\n⚠️  SPEC STALE — code committed after SPEC.AI.md UPDATED date ({len(spec_stale)}):")
        print("   (verify the spec still describes the addon's CURRENT intended behavior")
        print("    — amend it through approval if not — then bump its UPDATED line to the")
        print("    commit date; the bump is the attestation. See the SPEC.AI.md CONVENTION")
        print("    in AI.SESSION.md)")
        for addon, updated, last in spec_stale:
            print(f"   {addon:<45}  UPDATED: {updated}  last commit: {last}")

    if spec_malformed:
        print(f"\n⚠️  SPEC MALFORMED — SPEC.AI.md UPDATED line missing or unparsable ({len(spec_malformed)}):")
        print("   (the very FIRST line of the file — above any title or template")
        print("    heading — must read exactly 'UPDATED: YYYY-MM-DD', e.g.")
        print("    'UPDATED: 2026-01-31': the date the spec was written or last")
        print("    confirmed against the code. Hand-made specs from a template")
        print("    usually just need this line inserted at the top; without it the")
        print("    spec silently escapes the SPEC STALE check)")
        for msg in spec_malformed:
            print(f"   {msg}")

    if on_disk:
        print(f"\n◻︎ SPEC coverage: {addons_with_spec} of {len(on_disk)} addon folders have SPEC.AI.md")
        print("   (informational — a missing SPEC.AI.md is not a canary finding;")
        print("    exit status unaffected)")

    # 🔧 SETUP guidance — state-driven next steps while the repo's
    # documentation setup is incomplete. Informational: exit status and
    # the ✅ all-clear are unaffected — the checks above judge what
    # EXISTS; this block only sequences what is still missing.
    setup = []
    custom_text = ADDONS_AI.read_text(encoding="utf-8")
    if "(NOT YET POPULATED" in custom_text:
        setup.append(
            "sync PRODENV from staging — module list auto-extracts on next "
            "canary run:\n"
            "      a. On STAGING:\n"
            "         python3 AI/AI.gen_prodenv.py | odoo-bin shell --no-http\n"
            "         git add AI/AI.PRODENV.*.md\n"
            "         git commit -m 'sync: production environment snapshot "
            "YYYY-MM-DD'\n"
            "         odoosh-push\n"
            "      b. On DEV:\n"
            "         git fetch\n"
            "         git checkout origin/<staging-branch> -- "
            "'AI/AI.PRODENV.*.md'\n"
            "         git add AI/AI.PRODENV.*.md\n"
            "         git commit -m 'sync: PRODENV from staging'\n"
            "         odoosh-push\n"
            "      then run: python3 AI/AI.canary.py\n"
            "      (auto-applies module list from AI.PRODENV.MODULES.md)")
    if apps_mismatch:
        setup.append(
            "ask the AI to refresh the \"# APPS (baseline …):\" line — it "
            "mismatches\n      the # ODOO: line (see APPS BASELINE "
            "MISMATCH above)")
    studio_dir = REPO_ROOT / "studio_customization"
    if (studio_dir.is_dir() and any(studio_dir.iterdir())
            and not (SCRIPT_DIR / "AI.STUDIO.md").exists()):
        setup.append(
            "ask the AI to run: \"Update Studio documentation\" — "
            "studio_customization/\n      exists but AI.STUDIO.md does not")
    if on_disk and not documented:
        setup.append(
            "ask the AI to run: \"Build documentation from scratch\" — "
            "addon folders\n      exist but no >>ADDON: blocks are "
            "documented")
    if conflicts_missing:
        setup.append(
            "run: python3 AI/AI.canary.py --init-conflicts — interactions are "
            "derived\n      but AI.CONFLICTS.md does not exist to record "
            "decisions in")

    if setup:
        print("\n🔧 SETUP — repo documentation setup incomplete; "
              f"next step(s) ({len(setup)}):")
        for i, step in enumerate(setup, 1):
            print(f"   {i}. {step}")
        print("   (informational — prompt definitions live in "
              "AI.SESSION.md's MAINTENANCE")
        print("    PROMPTS block; exit status and the ✅ line are "
              "unaffected)")

    if not any((stale, undocumented, no_folder, no_commits, malformed,
                missing_created,
                status_mismatch, date_mismatch, readme_mismatch,
                coverage_mismatch, stale_derived,
                missing_derived, odoo_mismatch, apps_mismatch, studio_manifest,
                stale_studio_doc, spec_problem, gen_problem,
                inventory_drift, inventory_problem,
                spec_stale, spec_malformed,
                undisposed, stale_disposition, disposition_outdated,
                prodenv_incomplete)):
        print("✅  All UPDATED dates are current and consistent. No undocumented addons. "
              "Block lines, STATUS fields, README headers, COVERAGE line, ODOO version line, "
              "and APPS baseline consistent. "
              "Block inventories match addon code (AI.gen_inventory.py --check). "
              "SPEC.AI.md contracts current where present. "
              "All expected derived files exist with current SOURCE-HASH stamps. "
              "No Studio hazards (manifest disabled, Studio docs match the export) "
              "and AI.SESSION.md, AI.gen_enterprise.py, AI.gen_summaries.py, and "
              "the AI.SPECS.* files are available.")

    return 1 if any((stale, undocumented, no_folder, malformed, missing_created,
                     status_mismatch,
                     date_mismatch, readme_mismatch, coverage_mismatch,
                     stale_derived,
                     missing_derived, odoo_mismatch, apps_mismatch,
                     studio_manifest, stale_studio_doc, spec_problem,
                     gen_problem, inventory_drift, inventory_problem,
                     undisposed, stale_disposition, disposition_outdated,
                     spec_stale, spec_malformed,
                     prodenv_incomplete)) else 0

if __name__ == "__main__":
    sys.exit(main())
