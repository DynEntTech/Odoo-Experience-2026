# AI.SPECS.STUDIO — Studio Documentation Specs
# TEMPLATE-OWNED INSTRUCTION FILE — contains no repo data. Overwritten
#   wholesale on template upgrade, exactly like the AI.*.py scripts; never
#   hand-edit it in a working repo (edits belong in the template repository).
# READ ON DEMAND: when a Studio documentation prompt is invoked — never at
#   session start. The session-start Studio checks (STEP S1–S4) live in
#   AI.SESSION.md's STUDIO CUSTOMIZATIONS — SESSION CHECKS section.
#   AI.canary.py reports SPECS MISSING when this file is absent.
#
# STUDIO CUSTOMIZATIONS:
#   Studio customizations are documented separately from custom addons, in two
#   companion files with distinct roles:
#
#   WHAT BELONGS IN AI.STUDIO.md (inventory — "what exists?"):
#     - All Studio-added fields (x_studio_*), automations, view modifications
#       (XPath extensions), saved filters, and other Studio-managed records
#     - The MODEL ↔ APP INDEX (see the FILE FORMAT spec below)
#     - Factual, format-driven entries — no explanations
#     - Regenerable by analyzing /home/odoo/src/user/studio_customization/ —
#       with one carried-over input: the MODEL ↔ APP INDEX app assignments
#       come from the previous revision of this file (or its git history)
#       whenever one exists; they are re-judged from scratch only when no
#       prior revision survives anywhere (see the index spec below)
#
#   AI.STUDIO.md FILE FORMAT (⚠️ = load-bearing, parsed or hashed by scripts):
#     Header (all "#" comment lines, in this order):
#       Line 1 : # AI.STUDIO — Odoo Studio Customizations
#       Line 2 : # BUILT: YYYY-MM-DD — the date of the Studio export this
#                file documents (DOC.STUDIO.analysis.md's STUDIO EXPORT FRESHNESS
#                section points at this date)
#       Line 3 : # EXPORT-HASH: <12-hex> — content hash of the
#                studio_customization/ export this file documents (current
#                value from: python3 /home/odoo/src/user/AI/AI.canary.py --stamp).
#                Re-record it whenever this file is rebuilt from a re-export.
#                AI.canary.py reports STALE STUDIO DOC when the folder no
#                longer matches — the detector for "re-exported but not
#                re-documented". The other direction (Studio changed in the
#                UI but never re-exported) is not detectable from the repo;
#                STEP S1's session reminder covers it.
#       Optional fourth line: # UPDATED: YYYY-MM-DD — when the file was last
#                edited on a later date than BUILT (omit otherwise)
#       ⚠️  AI.canary.py's studio hash excludes ONLY lines beginning with
#                "#", optional whitespace, then "BUILT:", "UPDATED:", or
#                "EXPORT-HASH:" — spacing-tolerant on purpose, so a
#                hand-typed spacing variant of a header line is still
#                excluded rather than staling every Studio-derived file
#                on its next date bump. Two obligations follow: dates and
#                the export hash must appear on those lines and nowhere
#                else in the file (or bumping them falsely flags all
#                Studio-derived files as STALE DERIVED), and no OTHER
#                line may begin that way (it would silently drop out of
#                the hash).
#       Then   : a short NOT-AN-INSTALLABLE-ADDON warning (the folder's
#                manifest is renamed .disabled; the XML files are reference
#                exports — the customizations live in the database), plus a
#                one-line pointer to this spec file (AI.SPECS.STUDIO.md) for
#                everything else. Do NOT restate the DOC.STUDIO.* specs,
#                regeneration rules, or companion-file descriptions in that
#                header — this spec file is their only home; restated copies
#                have been observed to drift into obsolete specs.
#     ## MODEL ↔ APP INDEX (required — first body section):
#       Table  : Model | App — one row per model touched by any Studio
#                customization, alphabetical by model
#       App    : a value from the "# APPS (baseline …):" data line in
#                AI.CUSTOM.md, assigned per the APP DEFINITIONS rules
#                (AI.SPECS.ADDONS.md) when the model first enters the index and
#                reused unchanged on later re-exports — this is what makes
#                DOC.STUDIO.by.App.md grouping deterministic instead of
#                re-judged at every regeneration. When rebuilding this file
#                from scratch, recover the previous assignments from git
#                history first; re-judge only models with no recorded
#                assignment anywhere
#     Body sections, in this order (omit a section with no entries):
#       ## CUSTOM FIELDS      : one ### <model> subsection per model,
#                alphabetical; table Field | Type | Label [+ Notes and/or
#                Related chain columns when relevant]; shared traits may be
#                noted at subsection level (e.g. "(all related, readonly)");
#                type notation as specified under DOC.STUDIO.by.Model.md below
#       ## AUTOMATIONS        : single table
#                Name | Active | Model | Trigger | Filter | Action
#       ## VIEW MODIFICATIONS : one ### <model> subsection per model,
#                alphabetical; table Inherits | View type [+ Active column
#                only when ✅/❌ variants coexist] | Modification
#                (Inherits = full XML ID of the inherit_id)
#       ## FILTERS            : single table Model | Name | Default | Domain
#       ## OTHER              : Studio-managed records fitting none of the
#                above (act-window view assignments, report stubs, Studio
#                export warnings), as short ### bullet subsections
#     Markers: ✅/❌ = active/archived Studio record · "—" = none/not applicable
#
#   WHAT BELONGS IN DOC.STUDIO.analysis.md (current-state analysis — "what is risky,
#   broken, or needs explanation right now?"):
#     Header (all "#" comment lines, in this order — exactly these three; add
#       no further header lines, the body sections start directly below.
#       "Updated:" lowercase is intentional, as in every derived-file header
#       (the DOC.* files and the generated AI.ENTERPRISE.md) — these files
#       are regenerated outputs, not hash sources; the uppercase
#       "# UPDATED:" form is reserved for the machine-read dates in
#       AI.CUSTOM.md, README.AI.md, and AI.STUDIO.md):
#       Line 1 : # DOC.STUDIO.analysis — Studio Customizations: Current Risks & Context
#       Line 2 : # Updated: <YYYY-MM-DD> · Source: studio_customization/ + AI.STUDIO.md
#                (Updated = the date the file was regenerated)
#       Line 3 : # SOURCE-HASH: studio=<hash>  (see DERIVED-FILE FRESHNESS)
#       Do NOT restate this file's purpose or regeneration rules in its
#       header — this section is their only home; restated copies have
#       been observed to drift (unversioned-release copies carried
#       COMPANION/PURPOSE/REGENERATION RULES blocks — drop them at
#       regeneration)
#     - Structural risks and active warnings derivable from the current export
#       (e.g. non-searchable related-field dependency chains)
#     - Field rationale and automation caveats
#     - Sections: KNOWN ISSUES, FIELD CONTEXT & RATIONALE, AUTOMATION NOTES,
#       STUDIO EXPORT FRESHNESS (a pointer to AI.STUDIO.md's BUILT date)
#     - NO historical or accumulative data: no observation dates, no
#       resolved-issue log, no production-warning history — git history is
#       the only record of the past
#     - Fully regenerable by analyzing studio_customization/ + AI.STUDIO.md
#
#   REGENERATION TRIGGER: whenever AI.STUDIO.md is substantively updated
#   (i.e. after every Studio re-export + documentation refresh — the canary's
#   ⚠️ STALE DERIVED report is the trigger of record), regenerate DOC.STUDIO.analysis.md and
#   the three DOC.STUDIO.by.* summaries specified below (DOC.STUDIO.by.*
#   SUMMARY SPECS), plus DOC.CONFLICTS.Studio.md (see CONFLICT REPORTS in
#   AI.SPECS.ADDONS.md).
#   An issue that no longer exists in the current export simply disappears on
#   regeneration.
#
#   DOC.STUDIO.by.* SUMMARY SPECS (all three derive solely from AI.STUDIO.md):
#     All files share:
#       Line 1 = file title (as given per file below)
#       Line 2 = # <counts> · Updated: <YYYY-MM-DD> · Source: AI.STUDIO.md
#                (Updated = the date the file was regenerated)
#       Line 3 = # SOURCE-HASH: studio=<hash>  (see DERIVED-FILE FRESHNESS above)
#       Markers: ✅/❌ = active/archived Studio record · "—" = none/not applicable
#
#     DOC.STUDIO.by.App.md — /home/odoo/src/user/AI/DOC.STUDIO.by.App.md
#       Title  : # Studio Customizations — by App
#       Line 2 : # <N> models across <M> apps · Updated: <date> · Source: AI.STUDIO.md
#       Groups : one ## <APP> section per app, alphabetical — each model's
#                app comes from AI.STUDIO.md's MODEL ↔ APP INDEX, never
#                re-judged at regeneration time
#       Table  : Model | Fields Added | Views Modified | Automations | Filters  (5 columns)
#       Cells  : terse counts + descriptors (e.g. "10 related (…)", "1 unused datetime");
#                view entries as <view type>[/<variant>] (summary), joined by " · ";
#                filters prefixed "default:" when set as a default filter
#       Sort   : alphabetical by model name within each section
#
#     DOC.STUDIO.by.Model.md — /home/odoo/src/user/AI/DOC.STUDIO.by.Model.md
#       Title  : # Studio Customizations — by Model
#       Line 2 : # <N> models touched · Updated: <date> · Source: AI.STUDIO.md
#       Groups : one ## <model> section per technical model name, alphabetical,
#                sections separated by "---"
#       Subsections per model (bold headers, included only when applicable):
#         **Custom Fields**      : Field | Type | Label [+ Notes and/or Related chain
#                                  columns when relevant; shared traits may be noted
#                                  at section level, e.g. "(all related, readonly)"]
#         **View Modifications** : Inherits | View type [+ Active column only when
#                                  ✅/❌ variants coexist] | Modification
#                                  (Inherits = full XML ID of the inherit_id)
#         **Automations**        : Name | Active | Trigger | Filter | Action
#         **Filters**            : Name | Default | Domain
#       Type notation: many2one → <comodel> · "<type> (computed)" · related
#                      chains as dotted paths
#
#     DOC.STUDIO.by.Fields.md — /home/odoo/src/user/AI/DOC.STUDIO.by.Fields.md
#       Title  : # Studio Customizations — Fields Reference
#       Line 2 : # <N> x_studio_* fields across <M> models · Updated: <date> · Source: AI.STUDIO.md
#       Header notes (after line 3): sort order; "(unused)" = exists in the
#                database but appears in no view; "(source)" = canonical field,
#                other models carry related relays of the same value
#       Groups : none — single flat table
#       Table  : Field | Model | Type | Label | Related / Computed  (5 columns)
#       Cells  : "unused" · "source [— details]" · "related: <chain>" ·
#                "depends: <expr>" (computed) · "—"
#       Sort   : alphabetical by field name, then by model (a field defined on
#                several models appears once per model)
#
