# AI.SPECS.ADDONS — Addon Documentation Specs
# TEMPLATE-OWNED INSTRUCTION FILE — contains no repo data. Overwritten
#   wholesale on template upgrade, exactly like the AI.*.py scripts; never
#   hand-edit it in a working repo (edits belong in the template repository).
# READ ON DEMAND: when a maintenance prompt from AI.SESSION.md's MAINTENANCE
#   PROMPTS block is invoked — never at session start. AI.canary.py reports
#   SPECS MISSING when this file is absent.
#
# IMPACT DEFINITIONS (for the IMPACT field used in each addon block):
#   Judged by one question: what happens to standard Odoo flows if this addon
#   misbehaves or is removed? This field appears in both AI.CUSTOM.md and
#   in individual README.AI.md files (intentional — see NOTE ON DUPLICATION).
#   Minor        : additive and self-contained — UI tweaks, reports, fields no
#                  other logic depends on; removal loses convenience, never the
#                  correctness of standard flows
#   Intermediate : extends standard workflows or the data model in ways other
#                  processes rely on, without replacing core behavior; standard
#                  flows still complete without it and data stays intact
#   Major        : overrides or replaces standard behavior in core business
#                  flows (e.g. write/create/action overrides on central models,
#                  changed posting or validation logic), or owns data or
#                  processes production depends on; malfunction or removal
#                  breaks standard flows
#
# TYPE DEFINITIONS (for the TYPE field used in each addon block):
#   Read-Only   : reads standard or permanent custom tables without modifying them;
#                 mutually exclusive with Updates — if any permanent table is written
#                 to or any new HTTP controller that writes data exists, use Updates instead;
#                 download/export controllers that only read data are classified as Read-Only
#   Updates     : creates, modifies, or deletes records in standard or permanent custom
#                 tables; includes new HTTP controllers that write data
#   Override    : changes the behaviour of standard Odoo logic (method overrides,
#                 compute replacements, controller patches)
#   UI          : changes what users see without affecting data or business logic
#                 (view changes, template modifications, CSS, menu items)
#   Integration : connects or coordinates between modules without owning its own
#                 business logic
#
# APP DEFINITIONS (for the APP field used in each addon block):
#   Single value only — pick the primary Odoo app this addon serves from a
#   business/management perspective, not a technical one. When an addon touches
#   multiple apps, choose the one that owns the primary business object or workflow.
#   This field appears in both AI.CUSTOM.md and in individual README.AI.md files
#   (intentional — see NOTE ON DUPLICATION).
#   Valid values: the "# APPS (baseline …):" data line near the top of
#     AI.CUSTOM.md (just below its COUNTRIES line). The list lives there — repo
#     data, preserved across template upgrades; the semantics live here.
#     Refresh rules and line format: see that line's note.
#   Note: Platform is reserved for cross-app integrators with no single business owner
#
# WHAT BELONGS IN AI.CUSTOM.md (the repo-data file — since the v9 split
#   it carries only data; the instruction home is AI.SESSION.md):
#   - Addon folder name, README path, STATUS, dependencies, last updated date
#     STATUS is required on every block — exactly one of two values, compared
#     character for character (see the block template):
#       STATUS: active
#         (meaning: installed and active in production — this parenthetical
#          is explanation only, never written on the STATUS line)
#       STATUS: not installed/active in Odoo — disregard unless explicitly asked
#         (that whole sentence IS the value, verbatim)
#   - Addon purpose (one line)
#   - Addon impact to Odoo application, select from only these options: Minor, Intermediate,
#     or Major (semantics: see IMPACT DEFINITIONS above)
#   - Addon type (comma-separated, from fixed set: Read-Only, Updates, Override, UI, Integration)
#   - Model names and inherit type (abstract/concrete, _inherit/_name)
#   - Field names only (no descriptions)
#   - Method signatures with [NEW]/[OVR] tag only; include HTTP route inline for controller methods; no descriptions or explanations
#   - View filenames and per-record: model, view type (e.g. list/form/search/kanban/calendar/pivot/graph/gantt/qweb — "list" is the 18.0+ name of the former tree view), record ID, and inherit_id if present — no descriptions
#   - Static asset file paths — paths only, no descriptors: the widget or
#     class an asset defines or extends is judgment and belongs in
#     README.AI.md prose (--write owns the ASSETS lines and emits bare paths)
#   - Cron jobs as a dedicated CRON block: record ID and schedule — no descriptions
#   - External dependencies as EXTERNAL_DEPS: python: [pkg, ...] and/or js: [pkg, ...] — omit if none
#   - SQL constraints as CONSTRAINT: name (type) under the model block — omit if none
#   - Security records as a SECURITY section — one per line, kind-prefixed:
#     group/privilege (record ID), ir.rule (record ID, model, domain),
#     ir.model.access (model + granted perms) — no descriptions; omit if none
#   - User-invokable UI commands the addon registers from JS (e.g. HTML-editor
#     powerbox "/" commands) as a COMMANDS section — command name + one-line
#     effect, plus where they are registered; omit if none (unextractable
#     from JS, hence hand-owned)
#   Guiding principle: answers "what exists?" — inventory only, no explanations
#   Exact block syntax: see the >>ADDON: BLOCK TEMPLATE at the end of this
#   file — every block must follow it.
#
# WHAT BELONGS IN README.AI.md (individual addon file in addon folder):
#   - Addon purpose (expanded prose — the strict one-liner lives in the master block)
#   - Addon business context
#   - Addon impact to Odoo application, select from only these options: Minor, Intermediate,
#     or Major (semantics: see IMPACT DEFINITIONS above)
#   - Addon type (comma-separated, from fixed set: Read-Only, Updates, Override, UI, Integration)
#   - APP and UPDATED header fields (duplicated from the master block — see NOTE
#     ON DUPLICATION; AI.canary.py compares the two UPDATED dates and the
#     IMPACT/TYPE/APP values — DATE MISMATCH / README MISMATCH on disagreement)
#   - Method one-liners explaining what each method does and why
#   - Business logic narrative, data flow, design decisions
#   - Known quirks, gotchas, edge cases, limitations
#   - Where to find the addon in the Odoo UI (menu path, button, app)
#   - Staging setup: what Odoo.sh neutralization breaks for this module
#     (email aliases, outbound mail servers, external connectors, API keys)
#     and numbered post-rebuild steps to restore the module to a working
#     state; never omit ("no special setup required" is a valid entry)
#   - Configuration or setup requirements for an Odoo demo database
#   - End-to-end demo script: an ordered list of steps a person follows to
#     demonstrate the module to a stakeholder in a meeting — starting from
#     login, ending with the key outcome; specific enough to run without
#     preparation; never omit (a one-liner is fine for trivial modules)
#   Guiding principle: answers "what does it do and why?" — context and explanation only
#   Exact file layout: see the README.AI.md FILE FORMAT spec below.
#
# README.AI.md FILE FORMAT (⚠️ = load-bearing, parsed by AI.canary.py):
#   Header (all "#" comment lines, in this order, nothing before them):
#     Line 1 : # README.AI — <addon_folder_name>
#     Line 2 : # UPDATED: YYYY-MM-DD
#       ⚠️  AI.canary.py reads the FIRST "UPDATED:" occurrence that is
#           followed by a date-SHAPED YYYY-MM-DD value — matched anywhere
#           in a line, NOT only at line start; a shape-valid but unreal
#           date (e.g. month 13) is still the one read, and is reported
#           as invalid rather than skipped in favor of a later valid
#           date — and compares it to the addon's block UPDATED in
#           AI.CUSTOM.md (DATE MISMATCH when they differ). Keep the date
#           on line 2 so no body text can shadow it, and never write the
#           string "UPDATED:" anywhere above it (conservative on
#           purpose — simpler than remembering the shape-match nuance).
#     Line 3 : # IMPACT: <Minor|Intermediate|Major — semantics: IMPACT DEFINITIONS>
#     Line 4 : # TYPE: <comma-separated, from the TYPE DEFINITIONS fixed set>
#     Line 5 : # APP: <one value from the "# APPS (baseline …):" data line>
#       ⚠️  AI.canary.py compares lines 3–5 to the block's IMPACT/TYPE/APP
#           values (README MISMATCH when they differ; TYPE compares as an
#           unordered comma-list). Each field is read from its FIRST
#           line-start "# <FIELD>:" occurrence — anchored at line start,
#           unlike UPDATED's anywhere-in-a-line match — so never write
#           those strings at the start of a line further down the file
#           (mid-sentence mentions are harmless for these three).
#     No STATUS line — production install status lives ONLY in the master
#     >>ADDON: block; a copy here would be a third sync point to drift.
#   Body sections ("## " headings). The required sections below appear in this
#   order; any number of addon-specific free-form sections may sit between
#   UI Location and Design Decisions & Gotchas (data flow, controllers,
#   report layouts, … — their names are not standardized):
#     ## Purpose                       first body section
#     ## Business Context
#     ## UI Location                   navigation path to the feature in Odoo
#                                      (menu, app, button); orients any reader
#                                      before the narrative that follows
#     <free-form sections>
#     ## Design Decisions & Gotchas    quirks, edge cases, limitations
#     ## Staging Setup                 (a) what Odoo.sh neutralization does to
#                                      this module (mail servers, aliases,
#                                      connectors, API keys); (b) numbered
#                                      post-rebuild steps to restore it; never
#                                      omit — "no special setup required" is valid
#     ## Demo Setup                    configuration/setup needed on an Odoo
#                                      demo database; when none is needed, say
#                                      so and note what demo data will or will
#                                      not exercise — never omit this section
#     ## Demo Script                   end-to-end ordered walkthrough for a
#                                      stakeholder demo: starting point, key
#                                      steps, expected outcome; never omit
#
# NOTE ON DUPLICATION:
#   Some fields (e.g. PURPOSE, IMPACT, TYPE, APP, UPDATED) appear in both AI.CUSTOM.md and in individual
#   README.AI.md files. This is intentional — individual files are designed to be
#   self-contained and human-readable without needing to cross-reference the master.
#   AI.canary.py keeps the duplicated values in sync: UPDATED via DATE MISMATCH,
#   IMPACT/TYPE/APP via README MISMATCH (PURPOSE is prose, expanded in the
#   README — not machine-compared).
#
# MAINTENANCE:
#   AI.CUSTOM.md's header UPDATED date (its line 2) = the date that file was
#   last modified, for any reason — bump it on every edit to that file.
#   Adding an addon   → analyze it, insert a block in AI.CUSTOM.md in alphabetical order with STATUS matching production
#                       state: active if installed in production, otherwise the not-installed value (verbatim,
#                       see the block template) plus a matching entry in the NOT INSTALLED IN PRODUCTION list —
#                       a brand-new addon not yet deployed is not installed; create README.AI.md in its folder;
#                       for a BRAND-NEW addon, set the manifest version to <odoo-version>.1.0.0 (matching the
#                       ODOO header line, e.g. 19.0.1.0.0); for a PRE-EXISTING addon being documented (canary or
#                       survey discovery), leave its manifest version untouched — documenting is not a code
#                       change (if its version does not follow the <odoo-version>.x.y.z format, flag it to the
#                       user rather than rewriting it);
#                       hand-write only the JUDGMENT fields (STATUS, UPDATED, PURPOSE, IMPACT, TYPE, APP,
#                       README pointer) plus SECURITY/COMMANDS notes; then run
#                       python3 AI/AI.gen_inventory.py --write <name> to generate the block's inventory
#                       portion (see THE GENERATED INVENTORY SECTION in the block template notes) and
#                       verify with python3 AI/AI.gen_inventory.py --check;
#                       update UPDATED date and the COVERAGE line;
#                       derive interactions with other addons and Studio customizations live from
#                       AI.CUSTOM.md and AI.STUDIO.md (per CONFLICT CHECKING in AI.SESSION.md — the
#                       DOC.CONFLICTS.* files are never a source for this), flag them to the user, then run
#                       python3 AI/AI.gen_conflicts.py --write to regenerate DOC.CONFLICTS.Addons.md
#                       (it derives the interactions and merges in the decisions recorded in
#                       AI.CONFLICTS.md; record a disposition for anything it reports as undisposed),
#                       and regenerate DOC.CONFLICTS.Studio.md by hand if AI.STUDIO.md exists
#                       (Studio is not yet covered by the generator; the Studio register's stamp
#                       includes the addons hash, so any substantive block change stales it —
#                       whether or not the addon touches Studio)
#   Modifying an addon → regenerate the block's inventory with python3 AI/AI.gen_inventory.py --write <name>
#                        (blocks not yet carrying a generated INVENTORY section get one — see THE
#                        GENERATED INVENTORY SECTION in the block template notes), review the judgment
#                        fields and README.AI.md prose by hand, and verify with --check; the UPDATED date MUST be set
#                        to today in BOTH files — AI.CUSTOM.md and README.AI.md — every time either
#                        file changes; updating only one is always wrong, even if the other file was
#                        not modified in this session (AI.canary.py reports a DATE MISMATCH when
#                        the two dates differ);
#                        known benign STALE case: commits are user-triggered and may land days after
#                        the docs were updated — the canary then reports STALE although the docs are
#                        current; verify they are, then set both UPDATED dates to the commit date;
#                        bump the version in the addon's __manifest__.py (format: <odoo-version>.x.y.z
#                        matching the ODOO header line of AI.CUSTOM.md, e.g. 19.0 → 19.0.1.0.0 —
#                        increment z for patches; y for features, resetting z to 0; x for breaking
#                        changes or major rewrites, resetting y and z to 0)
#                        ONLY when code files change (Python, XML, JS, CSV, CSS/SCSS); do NOT bump the version
#                        for documentation-only changes (README.AI.md, AI.CUSTOM.md block updates);
#                        this same file-type set drives AI.canary.py's STALE check (its git pathspec
#                        extension list) — when changing one, change the other; commits touching only
#                        other file types (e.g. .po translations) never trigger STALE;
#                        derive interactions with other addons and Studio customizations live from
#                        AI.CUSTOM.md and AI.STUDIO.md (per CONFLICT CHECKING in AI.SESSION.md — the
#                        DOC.CONFLICTS.* files are never a source for this), flag any changed interactions to the user, then
#                        run python3 AI/AI.gen_conflicts.py --write to regenerate
#                        DOC.CONFLICTS.Addons.md (recording a disposition in AI.CONFLICTS.md for
#                        anything it reports as undisposed), and regenerate (if AI.STUDIO.md exists)
#                        DOC.CONFLICTS.Studio.md by hand (the Studio register's
#                        stamp includes the addons hash, so any substantive block change stales
#                        it — whether or not the addon touches Studio)
#   Removing an addon  → delete its block in AI.CUSTOM.md, its README.AI.md, and its entry in the NOT INSTALLED
#                        IN PRODUCTION list (if present — leaving it would misread as a documentation
#                        gap), update UPDATED date and the COVERAGE line;
#                        regenerate DOC.CONFLICTS.Addons.md and (if AI.STUDIO.md exists)
#                        DOC.CONFLICTS.Studio.md from the current inventory — regeneration
#                        drops the removed addon's entries automatically
#   Block order: alphabetical by addon folder name; every block sits BELOW the
#     "end of header" delimiter line at the bottom of AI.CUSTOM.md's header —
#     never above its COVERAGE line. (Load-bearing: the addons SOURCE-HASH spans from the
#     first ">>ADDON:" line to the end of AI.CUSTOM.md, so a block placed above
#     COVERAGE pulls header lines into the hash and stales derived files on
#     unrelated header edits.)
#   Keep method signatures minimal in AI.CUSTOM.md's blocks — descriptions go
#   in README.AI.md only
#
#   After any SUBSTANTIVE change to the >>ADDON: blocks in AI.CUSTOM.md (add/
#   modify/remove — anything other than an UPDATED-date-only bump), regenerate
#   all four summary files below (mechanical — run: python3 AI/AI.gen_summaries.py,
#   which generates and stamps them) and DOC.CONFLICTS.Addons.md (AI prompt —
#   conflict analysis is judgment work). Also regenerate
#   DOC.CONFLICTS.Studio.md when either the >>ADDON: blocks or AI.STUDIO.md
#   substantively change — but only where AI.STUDIO.md exists: a repo with no
#   Studio documentation must not have DOC.CONFLICTS.Studio.md at all
#   (AI.canary.py reports one as a STALE STUDIO DOC leftover, and its studio
#   stamp component could not even be computed). This existence condition
#   governs every "regenerate DOC.CONFLICTS.Studio.md" instruction — in the
#   rules above and in any other procedure that invokes them.
#   Changes limited to AI.CUSTOM.md's header data lines, to the
#   instruction files (AI.SESSION.md, the AI.SPECS.* files), and
#   UPDATED-date-only bumps do NOT require
#   regeneration — the summaries and conflict reports derive solely from the
#   substantive addon inventory. This is enforced mechanically, not by memory:
#   the SOURCE-HASH freshness stamps exclude UPDATED lines, so AI.canary.py
#   flags exactly the drift that matters and nothing else (see DERIVED-FILE
#   FRESHNESS below) — the canary's ⚠️ STALE DERIVED report is the trigger of
#   record for regeneration.
#   The four DOC.CUSTOM.by.* summary files are GENERATED by AI.gen_summaries.py
#   — never hand-written; the specs below document its output, and the script
#   is their executable form (change the two together). Shared conventions
#   (the DOC.CONFLICTS.* files have their own format — see CONFLICT REPORTS
#   below): ⚠️ appended to addon name if STATUS: not installed, Purpose
#   trimmed to its first 80 characters when longer (any '|' then escaped
#   as \| — a bare pipe would break the markdown table cell), every
#   "alphabetical" sort case-insensitive (eCommerce/eLearning group under
#   E, never after Website; custom addon names may carry uppercase —
#   the fixed non-alphabetical orders below are unaffected), N and total
#   taken from the COVERAGE line (COVERAGE
#   counts only blocks whose folder exists on disk, so during a FOLDER
#   MISSING state the header count and the table rows can briefly disagree —
#   the canary flags that state; resolve it rather than adjusting counts).
#   Common header: Line 1 = file title, Line 2 = # <N> of <total> documented · Updated: <YYYY-MM-DD> · ⚠️ = not installed in production
#     (Updated = the date the file was regenerated)
#   Line 3 = # SOURCE-HASH: <components> — the freshness stamp; obtain current
#     component values with: python3 /home/odoo/src/user/AI/AI.canary.py --stamp
#     (see DERIVED-FILE FRESHNESS below for which components each file carries)
#
#   DOC.CUSTOM.by.App.md — /home/odoo/src/user/AI/DOC.CUSTOM.by.App.md
#     Title  : # Custom Addons Summary — by App
#     Groups : one ## <APP> section per distinct APP value, alphabetical by APP name
#     Table  : Addon | Impact | Type | Purpose  (4 columns)
#     Sort   : alphabetical by addon name within each section
#
#   DOC.CUSTOM.by.Impact.md — /home/odoo/src/user/AI/DOC.CUSTOM.by.Impact.md
#     Title  : # Custom Addons Summary — by Impact
#     Groups : ## Major, ## Intermediate, ## Minor  (in that order, not
#              alphabetical; a group with no addons is omitted)
#     Table  : Addon | App | Type | Purpose  (4 columns)
#     Sort   : alphabetical by addon name within each section
#
#   DOC.CUSTOM.by.Alpha.md — /home/odoo/src/user/AI/DOC.CUSTOM.by.Alpha.md
#     Title  : # Custom Addons Summary — Alphabetical
#     Groups : none — single flat table
#     Table  : Addon | App | Impact | Type | Purpose  (5 columns)
#     Sort   : alphabetical by addon name across all addons
#
#   DOC.CUSTOM.by.Type.md — /home/odoo/src/user/AI/DOC.CUSTOM.by.Type.md
#     Title  : # Custom Addons Summary — by Type
#     Groups : ## Integration, ## Override, ## Read-Only, ## UI, ## Updates
#              (alphabetical; a group with no addons is omitted)
#              addons appear once per type — a multi-type addon appears in multiple sections
#     Table  : Addon | App | Impact | Purpose  (4 columns)
#     Sort   : alphabetical by addon name within each section
#
# DERIVED-FILE FRESHNESS (SOURCE-HASH stamps):
#   Every derived file carries a stamp line near the top:
#     # SOURCE-HASH: <component>=<12-hex> [<component>=<12-hex>]
#   Components and what they hash (all computed by AI.canary.py):
#     addons     = the >>ADDON: block region of AI.CUSTOM.md, EXCLUDING UPDATED
#                  lines — so date-only bumps never invalidate derived files
#     studio     = AI.STUDIO.md content, excluding its BUILT/UPDATED date
#                  header lines and its EXPORT-HASH line (re-recording the
#                  export hash never stales the Studio-derived summaries)
#     enterprise = the installed Enterprise module list + COUNTRIES line of
#                  AI.CUSTOM.md (computed and embedded automatically by
#                  AI.gen_enterprise.py; AI.canary.py delegates to it)
#   Which files carry which components:
#     DOC.CUSTOM.by.*.md, DOC.CONFLICTS.Addons.md : addons
#     DOC.STUDIO.analysis.md, DOC.STUDIO.by.*.md  : studio
#     DOC.CONFLICTS.Studio.md                     : addons + studio
#     AI.ENTERPRISE.md                            : enterprise (auto-stamped)
#   When regenerating any derived file, obtain the current component values:
#     python3 /home/odoo/src/user/AI/AI.canary.py --stamp
#   and write the stamp as line 3 of the regenerated file. (Exceptions —
#   self-stamping generators, never hand-copy their stamps: AI.ENTERPRISE.md
#   is stamped by AI.gen_enterprise.py within its generated header, and the
#   DOC.CUSTOM.by.* files are stamped by AI.gen_summaries.py at line 3 —
#   AI.canary.py locates a stamp by its "# SOURCE-HASH:" line anywhere in
#   the file, so placement is convention, not load-bearing.) AI.canary.py recomputes the hashes on every
#   run and reports ⚠️ STALE DERIVED for any existing derived file whose stamp
#   is missing or no longer matches its sources. Missing derived FILES are
#   reported separately as 📄 MISSING DERIVED, with expectations conditional
#   on the sources: addon-derived files are expected once at least one
#   >>ADDON: block exists; Studio-derived files once AI.STUDIO.md exists AND
#   the export folder is non-empty (an orphaned AI.STUDIO.md — folder absent
#   or empty — expects nothing: STALE STUDIO DOC owns that state, and its
#   restore-or-delete remediation must not compete with a "create" one);
#   AI.STUDIO.md itself once studio_customization/ exists and is non-empty —
#   an empty export folder is treated as absent, per STEP S1; AI.ENTERPRISE.md
#   once the INSTALLED MODULES section has been populated. Each report
#   includes how to create the missing file.
#
# CONFLICT DISPOSITIONS (AI.CONFLICTS.md — repo DATA, never regenerated):
#   The decisions half of conflict checking, and the AUTHORITATIVE format for
#   the file (its own header is a pointer here, not a second copy).
#   WHY IT IS A SEPARATE FILE, twice over: a DERIVED file cannot carry
#   decisions, because regeneration destroys them; and it cannot live inside
#   AI.CUSTOM.md either, because AI.canary.py's addons_source_hash() hashes
#   from the first >>ADDON: line to end of file, so editing one reason string
#   would stale all four DOC.CUSTOM.by.* summaries.
#   Created by: python3 AI/AI.canary.py --init (new repo) or --init-conflicts
#   (a repo that already has AI.CUSTOM.md). Never overwritten; absent from the
#   template for the same reason AI.CUSTOM.md is (INSTALL.PROCEDURE.md).
#   One block per INTERACTION — not per pair. Four addons sharing one method
#   is ONE entry; pairwise entries would give one fact several identities.
#
#     >>CONFLICT: <natural key>
#       ADDONS:   comma list of every participating addon
#       STATUS:   Accepted | Deferred | Fixed | Withdrawn
#       DECIDED:  YYYY-MM-DD (human) | YYYY-MM-DD (AI)
#       REASON:   why the decision is what it is
#       EVIDENCE: file:line facts a later reader can RE-CHECK
#
#   ⚠️  The KEY is COMPUTED, never assigned — it is the natural key
#       AI.gen_conflicts.py emits (<model>::<method>, <model>::field:<name>,
#       view::<target>, or a bare <model>). Every other ID scheme in this
#       system takes max+1 and is matched by a human; that cannot work when a
#       script must pair a disposition to its interaction automatically.
#   ⚠️  ADDONS: is what makes an entry SELF-INVALIDATING. The judgment was made
#       about those participants; if a fifth addon joins, the key is unchanged
#       but the decision no longer covers reality, and AI.canary.py reports
#       DISPOSITION OUTDATED so it is revisited rather than silently trusted.
#   ⚠️  EVIDENCE: exists because "no action needed" is prose nothing can
#       re-check, while "each override calls super() — x/models/y.py:31" is a
#       claim that can be. STATUS values are validated by the canary; an
#       unrecognized one is reported as STALE DISPOSITION.
#   DECIDED: records WHO. An AI may assess — much of what looks like judgment
#   is readable from code — but a High-severity interaction the client would
#   have to fund needs (human).
#   Canary checks (check 20): UNDISPOSED, DISPOSITION OUTDATED, STALE
#   DISPOSITION. A repo with no derived interactions is never asked for this
#   file at all.
#
# CONFLICT REPORTS:
#   Two human-readable reference files documenting known interactions and risks
#   across addons and Studio customizations. Primarily for human reference.
#   AI access policy: see the DOC.* ACCESS POLICY section in AI.SESSION.md —
#   never read at session start; on-demand reads fine; never
#   authoritative (the live derivation wins).
#   Freshness is canary-verified: every derived file carries a SOURCE-HASH stamp
#   (see DERIVED-FILE FRESHNESS above) and AI.canary.py reports ⚠️ STALE DERIVED
#   when a stamp no longer matches the sources; a Studio-derived file that
#   outlives its source (DOC.STUDIO.* / DOC.CONFLICTS.Studio.md present while
#   AI.STUDIO.md is gone) is reported as ⚠️ STALE STUDIO DOC instead — its
#   stamp is unjudgeable without the source, so the leftover itself is the
#   finding.
#   Regenerate both when instructed by the MAINTENANCE rules above.
#
#   FORMAT (both registers share it):
#     Line 1 : # DOC.CONFLICTS.<Addons|Studio>.md — <register title>
#     Line 2 : # <N> entries · Updated: <YYYY-MM-DD>
#              (Updated = the date the file was regenerated)
#     Line 3 : # SOURCE-HASH: <components per DERIVED-FILE FRESHNESS above>
#     Then   : a usage note that states the access policy rather than
#              contradicting it — this file is a regenerated human reference;
#              the AI re-derives conflicts live per CONFLICT CHECKING (in
#              AI.SESSION.md), and on any disagreement the live derivation
#              wins. For DOC.CONFLICTS.Addons.md the generator now writes
#              this note itself; the rule below still governs
#              DOC.CONFLICTS.Studio.md, which is still hand-regenerated.
#              Do NOT write
#              "read this file before modifying an addon" or similar.
#     Then   : the SEVERITY legend, verbatim:
#              🔴 Functional risk  — may cause bugs or unexpected behavior; assess before proceeding
#              🟡 Design overlap   — no immediate breakage; coordination awareness required
#              ⚠️  Potential        — unconfirmed; flag to user before proceeding
#              ✅ Intentional      — by design; no action needed; documented for clarity
#     Body   : one ## section per severity level present, in the fixed order
#              🔴 Functional Risks · 🟡 Design Overlaps · ⚠️ Potential ·
#              ✅ Intentional (omit levels with no entries); entries within a
#              section separated by "---"
#     Entry  : ### <short descriptive title>
#              Severity: <marker>
#              Models: <affected models; non-model artifacts allowed,
#                       e.g. "(controller — WebsiteSale)">
#              Addons involved: <addon folder names, comma-separated>
#              Studio feature: <field/automation/view summary>  (Studio register only)
#              What: <factual description of the interaction>
#              Watch out for: <the specific risk or coordination note>
#     Empty  : when a register has no entries, keep the header and write a
#              single body line: (no known conflicts or interactions)
#
#   DOC.CONFLICTS.Studio.md — /home/odoo/src/user/AI/DOC.CONFLICTS.Studio.md
#     Addon ↔ Studio conflict and interaction register.
#     Exists only while AI.STUDIO.md exists — never create it in a repo
#     without Studio documentation (AI.canary.py reports one as a STALE
#     STUDIO DOC leftover).
#     Regenerate when: the >>ADDON: blocks in AI.CUSTOM.md or AI.STUDIO.md
#     substantively change (the canary's ⚠️ STALE DERIVED report is the
#     trigger of record).
#
#   DOC.CONFLICTS.Addons.md — /home/odoo/src/user/AI/DOC.CONFLICTS.Addons.md
#     Addon ↔ Addon interaction register. GENERATED — do not hand-write it:
#       python3 AI/AI.gen_conflicts.py --write
#     Regenerate when: the >>ADDON: blocks in AI.CUSTOM.md substantively change
#     (the canary's ⚠️ STALE DERIVED report is the trigger of record), or when
#     a disposition in AI.CONFLICTS.md changes.
#     It does NOT follow the Common header above (that shape counts documented
#     addons, which says nothing about interactions). The generator writes its
#     own: title, then a counts line (interactions · undisposed · addons ·
#     Updated), then the SOURCE-HASH line. The stamp is read from
#     AI.canary.py's own addons_source_hash, so the two cannot disagree.
#     WHAT IT CONTAINS, and the split that matters: the FACTS are derived from
#     the blocks (which addons share a model, method name, field name or view
#     inheritance target); the JUDGMENTS come from AI.CONFLICTS.md, the repo
#     DATA file that records what was decided about each interaction and why.
#     This file merely displays the two together. Never write a decision here
#     — it is regenerated wholesale, so the decision would be destroyed. That
#     is not hypothetical: the register this replaced defined an
#     "✅ Intentional — by design" tier inside a derived file, and a
#     regeneration either lost it or forced the next AI to re-invent a
#     judgment it had no standing to make.
#
# ═══ >>ADDON: BLOCK TEMPLATE — synthetic example, NOT a real addon ═══════════
#   Every >>ADDON: block in AI.CUSTOM.md (below its header) must follow this
#   exact format.
#   Syntax rules (load-bearing — AI.canary.py parses these):
#     · ">>ADDON: <folder_name>" at column 0 (not #-commented) starts a block
#     · "STATUS:" and "UPDATED: YYYY-MM-DD" must appear exactly as spelled here
#       (AI.canary.py reports MALFORMED BLOCK when either line is missing,
#       the UPDATED date is not a parsable YYYY-MM-DD, or
#       the STATUS value is not one of the two allowed values — compared
#       character for character: 'active' lowercase, or the not-installed
#       sentence verbatim; that sentence is mirrored in AI.canary.py's
#       NOT_INSTALLED_STATUS constant — change the two places together)
#     · "CREATED: YYYY-MM-DD" records when the addon FIRST APPEARED, and is
#       required on every block. It is reported differently from every other
#       required field, deliberately: a MISSING CREATED gets its own
#       AI.canary.py category (MISSING CREATED) rather than MALFORMED BLOCK,
#       because every other required field must be AUTHORED by a human while
#       this one is DERIVABLE from git history — so its remedy is a command,
#       not a writing task, and the report names that command. An UNPARSABLE
#       CREATED does fall under MALFORMED BLOCK: repairing a wrong date is a
#       human job like the rest. Set it when the addon is first documented.
#       For addons documented before this field existed, backfill once with
#         python3 AI/AI.canary.py --backfill-created --branch <production-branch>
#       which derives each date from first appearance on the PRODUCTION
#       branch (dev branches are routinely deleted after merge, so production
#       is the only durable record), previews every value and asks before
#       writing. Two properties of that derived date matter and are not
#       defects: it is a FIRST-APPEARANCE date, so a bulk relocation commit
#       stamps everything it moved with the move's date rather than the
#       authorship date; and addons with no history on the branch are
#       REPORTED, never guessed. The value is written once, reviewed by a
#       human at that prompt, and never re-derived — so correct it by hand
#       where the derivation is wrong rather than expecting a later run to.
#     · single-value fields (README, STATUS, UPDATED, CREATED, PURPOSE,
#       IMPACT, TYPE, APP, DEPENDS, DEPENDS_CUSTOM, EXTERNAL_DEPS) at most
#       once per block —
#       where a script parses one, parsing is last-wins, so a duplicate
#       silently overrides the intended value; the unparsed ones simply drift
#       apart. AI.canary.py reports any of them duplicated as MALFORMED BLOCK
#       (the unparsed names are mirrored in its SINGLE_VALUE_UNPARSED_FIELDS
#       constant — change the two places together). MODEL: and its FIELDS/
#       METHODS/CONSTRAINT sub-lines, VIEWS, ASSETS, and CRON legitimately
#       repeat — once per model, view file, or record, as in the example below
#     · PURPOSE, IMPACT, TYPE, and APP are required on every block, like
#       STATUS, UPDATED and CREATED (AI.canary.py reports a missing one as
#       MALFORMED BLOCK — except CREATED, which has its own category for the
#       reason given above): the README.AI.md header duplicates them and every
#       DOC.CUSTOM.by.* summary groups or tabulates by them — an omitted
#       value has no defined rendering there. IMPACT, TYPE, and APP values
#       are validated against the fixed sets (IMPACT DEFINITIONS options,
#       TYPE DEFINITIONS — including the Read-Only/Updates exclusion — and
#       the "# APPS (baseline …):" data line)
#   This template is #-commented on every line so that no tool or reader
#   mistakes it for a real block. Omit any INVENTORY field that does not
#   apply (DEPENDS, DEPENDS_CUSTOM, EXTERNAL_DEPS, MODEL and its sub-lines,
#   VIEWS, ASSETS, CRON); the required fields listed in the syntax rules
#   above may never be omitted. README: belongs to neither list: a
#   fixed-convention pointer, always present, always
#   "<folder_name>/README.AI.md" — AI.canary.py never parses the line (it
#   checks the README.AI.md FILE directly: existence, UPDATED date, and
#   IMPACT/TYPE/APP headers), but omitting it loses the block's pointer to
#   the deeper doc.
#   SECURITY and COMMANDS are optional hand-owned sections in the same
#   inventory-only style (formats: the WHAT BELONGS list above): they sit
#   OUTSIDE the machine-checked field list — AI.gen_inventory.py neither
#   generates nor verifies them (--check names them in an advisory ◻︎ note
#   as not checked) — so keep them OUTSIDE the INVENTORY:…END_INVENTORY:
#   markers, where --write would wipe them.
#
#   THE GENERATED INVENTORY SECTION (machine-owned):
#     python3 AI/AI.gen_inventory.py --write <name> maintains the inventory
#     mechanically instead of by hand: it rewrites the header DEPENDS,
#     DEPENDS_CUSTOM, and EXTERNAL_DEPS lines in place (a hand-written
#     "js: [...]" tail on EXTERNAL_DEPS is unextractable and preserved
#     verbatim) and owns a marker-delimited section inside the block:
#       INVENTORY: (machine-generated by AI.gen_inventory.py --write — …)
#         …MODEL/CONTROLLER/VIEWS/ASSETS/CRON lines, plus UNEXTRACTED
#         honesty notes for what extraction cannot see…
#       END_INVENTORY:
#     Everything between the two markers is regenerated wholesale on each
#     --write — NEVER hand-edit there; hand content outside the markers is
#     never touched. UPDATED dates are judgment and are never written by
#     the tool. Hand-written inventory sections (as in the example below)
#     remain valid — AI.gen_inventory.py --check accepts both forms — but
#     are legacy once a block carries a generated section: when next
#     touching such a block, move any prose worth keeping from the hand
#     inventory lines into README.AI.md and delete the hand lines; the
#     generated section is the inventory of record. Descriptive prose
#     (what a method/asset is FOR) is judgment — it belongs in
#     README.AI.md, never between the markers.
#
#   >>ADDON: example_sale_extras
#     README: example_sale_extras/README.AI.md
#     STATUS: active
#         (the other allowed value, verbatim after the "STATUS: " prefix:
#          not installed/active in Odoo — disregard unless explicitly asked
#          — read: neither installed nor active; "in Odoo" means the
#          production database, matching the NOT INSTALLED IN PRODUCTION
#          list. The wording is frozen — it is compared character for
#          character, see the syntax rules above)
#     UPDATED: 2026-07-11
#     CREATED: 2026-03-04
#         (when the addon first appeared — set at first
#          documentation; never changes afterwards, unlike UPDATED)
#     PURPOSE: One-line description of what the addon does
#     IMPACT: Intermediate
#     TYPE: Updates, Override, UI
#     APP: Sales
#     DEPENDS: sale_management, stock
#     DEPENDS_CUSTOM: example_base_addon
#     EXTERNAL_DEPS: python: [requests]  js: [chart.js]
#     MODEL: sale.order (_inherit, concrete)
#       FIELDS: x_priority_level, delivery_notes
#       CONSTRAINT: check_priority_range (CHECK)
#       METHODS:
#         [OVR] def write(self, vals)
#         [NEW] def action_expedite(self)
#     MODEL: example.dashboard (_name, transient)
#       METHODS:
#         [NEW] def get_data(self)  route=/example/dashboard/data (JSON, auth=user)
#     SECURITY:
#       group: example_sale_extras.group_expedite_manager
#       ir.rule: example_dashboard_company_rule  example.dashboard  domain=[('company_id','in',company_ids)]
#       ir.model.access: example.dashboard (full CRUD for group_expedite_manager)
#     VIEWS: views/sale_order_views.xml
#       sale.order | form | example_sale_extras.sale_order_form_expedite | inherit_id: sale.view_order_form
#       example.dashboard | qweb | example_sale_extras.dashboard_template
#     ASSETS: static/src/js/dashboard_widget.js
#     CRON: example_sale_extras.ir_cron_expedite_check — every 1 hour
# ═════════════════════════════════════════════════════════════════════════════
#
