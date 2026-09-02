═══ AI TOOLKIT — INSTALL GUIDE ═══════════════════════════════════════════════

This is the TEMPLATE repository. This file is the guide for
installing the AI toolkit into a customer repo; it is template-only and never
copied into a repo. Assumes an Odoo.sh Enterprise repo (paths under
/home/odoo/src/...). Every step below is performed by a human.

WHAT SHIPS: every AI.*-prefixed file in AI/ — the instruction files
(AI.SESSION.md, AI.SPECS.ADDONS.md, AI.SPECS.STUDIO.md, AI.README.md) and the
scripts (AI.canary.py, AI.gen_inventory.py, AI.gen_summaries.py,
AI.gen_conflicts.py, AI.gen_enterprise.py, AI.gen_prodenv.py,
AI.gen_prodenv_doc.py). The AI. prefix IS the ship marker.

WHAT DOES NOT SHIP: this file, and the per-repo data files AI.CUSTOM.md and
AI.CONFLICTS.md — those are GENERATED in the target repo at STEP I2, never
copied. Their absence from the template is what stops a copy from clobbering a
repo's own data. Do not hand-edit AI.SESSION.md in a repo (its "# TEMPLATE:"
line tracks the template revision).

═══ INSTALL STEPS ════════════════════════════════════════════════════════════

STEP I1 — Copy the shipped files into the target repo's AI/ subfolder:
    mkdir -p target-repo/AI
    cp AI/AI.* target-repo/AI/

STEP I2 — Generate the data file.
  ⚠️  Run in the Odoo.sh shell of the dev build, NOT a local checkout — the
  command detects the Odoo version from the platform and refuses off-platform.
    python3 AI/AI.canary.py --init
  It creates AI.CUSTOM.md and the (empty) AI.CONFLICTS.md and asks one
  question — the country menu (1=us 2=ca 3=ph; Enter=1). Then hand-check the
  two values the script cannot judge:
    · the "# ODOO:" edition text (Enterprise is assumed)
    · the "# COUNTRIES:" line — for a multi-country repo, edit it to a comma
      list (e.g. us, ca)

STEP I3 — Studio export (skip if the database has no Studio customizations).
  Follow the STUDIO EXPORT PROCEDURE in AI.SESSION.md: export from Odoo, place
  the files in studio_customization/, rename __manifest__.py to
  __manifest__.py.disabled, and push.

STEP I4 — Sync the production environment from STAGING (a production copy):
    a. On STAGING:
         python3 AI/AI.gen_prodenv.py | odoo-bin shell --no-http
       then commit and push the AI/AI.PRODENV.*.md files it writes (the script
       prints the exact git commands).
    b. On DEV: fetch and check out those AI/AI.PRODENV.*.md files, then run
         python3 AI/AI.canary.py
       It auto-applies the production module list into AI.CUSTOM.md and
       regenerates AI.ENTERPRISE.md and DOC.PRODENV.md.

STEP I5 — Hand off to the AI and verify. In the dev build's AI, enter:
    Read AI/AI.CUSTOM.md
  The AI runs the canary and guides the remaining setup — building the addon
  documentation blocks, the summaries, and the conflict register. Setup is
  done when
    python3 AI/AI.canary.py
  reports ✅ with no ⚠️/🆕/❓/📄 findings. (⬜ NO COMMITS and the ◻︎ SPEC
  coverage line are informational, not failures.)

═══ NOTE — Odoo version sensitivity ══════════════════════════════════════════

AI.gen_prodenv.py filters installed modules by ir.module.module.state in
['installed', 'to upgrade', 'to remove'] — stable across Odoo 16–19. On a new
Odoo major version, confirm those state strings still exist, or the extractor
silently under-counts. Check: the CUSTOM (installed) section should match
Settings > Apps.
