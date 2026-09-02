# AI.SESSION - Template Instructions (session-start sequence and conventions)
# TEMPLATE: v13
#   The template revision of this instruction file. This file is
#   template-owned: template upgrades overwrite it WHOLESALE (the
#   INSTALL steps live in the template repository's
#   INSTALL.PROCEDURE.md) — never hand-edit it in a working repo; the
#   version advances only when an upgrade replaces the file (in the
#   template repository itself, it is bumped when instruction content
#   changes materially). v9 is the first split-format revision: this
#   repo's DATA lives in AI.CUSTOM.md (data lines, INSTALLED MODULES,
#   COVERAGE, and the >>ADDON: blocks — bump ITS "# UPDATED:" line on
#   every edit to it); the instructions live here.
#
# INSTALLED MODULES — FORMAT (for the section of that name in AI.CUSTOM.md;
#   required — scripts machine-parse part of that section; keep ALL
#   subsections to the same strict format so any future parsing change
#   needs no data cleanup):
#     one module name per comment line, e.g. "#   account_accountant" —
#     nothing else on the line after the leading "#" (no annotations or
#     prose); the parsers ignore any line whose comment content is not
#     exactly one module name. The inverse mostly holds — a comment line
#     whose entire content is a single bare word is parsed as a module
#     name when the word starts with a letter, is at least two characters
#     long, and contains only letters, digits, and underscores (the
#     Enterprise parser accepts lowercase words only; the not-installed
#     parser also accepts words containing uppercase letters anywhere in
#     the name, matching the naming allowance for custom folders): when
#     writing prose near these subsections, never leave one word alone on
#     a line, regardless of case (it can create a phantom module — a
#     false ✅ in AI.ENTERPRISE.md or a phantom STATUS MISMATCH finding).
#     Standard Odoo module names are lowercase; custom addon folders may
#     contain uppercase letters in any position and are listed exactly as
#     the folder is named — provided the name fits the grammar above. A
#     folder name outside it (a single character, a leading digit or
#     underscore, or characters outside that set, e.g. a hyphen) is
#     silently unparseable from these lists: never name a custom addon
#     that way (Odoo expects importable module names), and flag any
#     pre-existing one to the user instead of listing it there.
#     A subsection with no modules after the survey gets the single line
#     "#     (none)" — it distinguishes "surveyed, none found" from the
#     never-surveyed (NOT YET POPULATED) state. Parsers ignore it (the
#     parentheses disqualify it as a module name).
#
#     Which lines are load-bearing, and for which script (⚠️ the parsers
#     locate subsections by their header line SHAPE — line-start "#", the
#     indented ALL-CAPS name, then a ":" at end of line. Keep that shape
#     when editing the subsection header lines in AI.CUSTOM.md, and never
#     write an ALL-CAPS subsection name at the start of any other
#     colon-terminated comment line there; these bullets use mixed case
#     as belt-and-suspenders):
#       · the Enterprise subsection — parsed by AI.gen_enterprise.py: drives
#         the ✅ marks in AI.ENTERPRISE.md and the 'enterprise' SOURCE-HASH;
#         a malformed line silently un-installs that module in the index
#       · the Not-Installed-in-Production subsection — parsed by
#         AI.canary.py: drives the STATUS cross-check; a malformed line
#         causes phantom or missed STATUS MISMATCH findings
#       · the Community, Themes, and Custom subsections — parsed by no
#         script today; reference data (same strict format still required)
#       · every subsection's (NOT YET POPULATED) marker is machine-checked
#         (installed_list_populated — gates AI.ENTERPRISE.md generation)
#
#   The INSTALLED MODULES section is auto-populated by AI.canary.py from
#   AI.PRODENV.MODULES.md when that file is synced from staging. The
#   "(auto-populated by AI.canary.py ...)" comment on the snapshot line confirms
#   this. Do not hand-edit the subsection content — re-run the PRODENV sync to
#   update it (see INSTALL.PROCEDURE.md STEP I4 or AI.README.md — PRODENV section).
#
#   ⚠️  While a subsection still contains its (NOT YET POPULATED) marker, treat
#     production module state as UNKNOWN — do NOT assume "empty = nothing
#     installed". When production module state is relevant to the current
#     task, inform the user that the PRODENV sync has not been run yet
#     (see INSTALL.PROCEDURE.md STEP I4 — module list auto-populates on the next
#     canary run after the sync).
#
#   NOT INSTALLED IN PRODUCTION — list rules (for that subsection in
#     AI.CUSTOM.md): for documented addons the list mirrors the STATUS
#     field of their >>ADDON: blocks — if you change the list, also update
#     the corresponding block STATUS (and vice versa); on any
#     disagreement, the block STATUS is authoritative. A name may also
#     appear there before its block exists (the module survey found an
#     undocumented inactive addon): that is a documentation gap — resolve
#     it by running the "Analyze and document addon" prompt, never by
#     removing the name from the list while the addon's folder is still
#     in the repo. The opposite case — the folder itself has been removed
#     from the codebase — is not a gap: the "Remove addon from
#     documentation" prompt deletes the entry together with the block
#     (see the MAINTENANCE rules); a name left there with neither block
#     nor folder is a removal leftover to delete, not to re-document.
#     AI.canary.py cross-checks the list against the block STATUS fields
#     and the on-disk folders, and reports any mismatch at session start
#     with the remediation matching the cause.
#     A name may also be added manually while the (NOT YET POPULATED)
#     marker is still present (a brand-new addon documented before the
#     first survey — the MAINTENANCE rules require the entry). The marker
#     stays: it tracks survey knowledge of production, which is still
#     missing, so AI.ENTERPRISE.md generation remains correctly blocked.
#     When the survey is later applied, such manual entries are
#     reconciled, never blindly discarded (see step 2b of the survey
#     prompt below — a never-deployed addon is invisible to the survey
#     output).
#
# COUNTRIES — note (for the "# COUNTRIES:" data line in AI.CUSTOM.md):
#   Controls which uninstalled l10n_* modules appear in AI.ENTERPRISE.md.
#   Installed l10n_* modules always appear regardless of this setting.
#   Uninstalled l10n_* modules for unlisted countries are omitted — they
#   are irrelevant noise for this installation.
#   Shipped by the template as "us" — when this template is installed into a
#   new repo, verify the codes match that repo's actual countries. This is a
#   hand-set value no script can validate, and wrong codes never error — an
#   unknown code simply matches nothing. The symptoms are silent, one per
#   direction: a MISSING code hides that country's uninstalled l10n_* modules
#   from AI.ENTERPRISE.md; a SUPERFLUOUS (or mistyped-but-colliding) code
#   pollutes it with another country's modules — the exact noise this filter
#   exists to prevent.
#   If COUNTRIES is missing or empty, ALL uninstalled l10n_* modules are
#   omitted from AI.ENTERPRISE.md (and its header says so).
#   Format  : comma-separated lowercase country codes  (e.g.  us, ca, ph)
#   Codes   : derived from Enterprise module folder names — the part after
#             "l10n_" in /home/odoo/src/enterprise/. To see all available
#             codes run:
#               ls /home/odoo/src/enterprise/ | grep "^l10n_" | sed 's/l10n_//' | cut -d_ -f1 | sort -u
#
# APPS — note (for the "# APPS (baseline …):" data line in AI.CUSTOM.md):
#   The valid-values list for the APP field in every >>ADDON: block. Like
#   COUNTRIES above, the line is repo data — shipped populated by the
#   template, refreshed only when the repo's Odoo version differs from the
#   baseline. Field semantics: see APP DEFINITIONS in AI.SPECS.ADDONS.md.
#   The baseline is the Odoo version the list was last verified against;
#   when the repo's Odoo version differs from it, refresh the list against
#   the installed version's apps and update the baseline. AI.canary.py
#   compares the baseline to the version on AI.CUSTOM.md's "# ODOO:" line
#   and reports APPS BASELINE MISMATCH until they agree.
#   Derivation (how to refresh): the modules with 'application': True in the
#   manifests under /home/odoo/src/odoo/addons/ and /home/odoo/src/enterprise/,
#   by their manifest 'name' (short menu-style names where established, e.g.
#   IoT, PLM, Referrals) — EXCLUDING carrier and marketplace connector
#   modules ("... Shipping", "... Connector"): those are integrations, not
#   business areas; an addon extending them uses the owning app (usually
#   Inventory or Sales). Platform is a template-defined extra value, not a
#   manifest-derived app (see APP DEFINITIONS).
#   Format : "# APPS (baseline <odoo-version>): <comma-separated app names>"
#            — one single line, exactly as parsed by AI.canary.py
#
# SPEC FILES:
#   The documentation formats, the >>ADDON: block template, and the
#   maintenance procedures live in two template-owned companion files
#   (no repo data — overwritten wholesale on template upgrade; AI.canary.py
#   reports SPECS MISSING when either is absent — the same finding also
#   covers AI.gen_summaries.py, the summaries generator noted below, and
#   this file itself):
#     AI.SPECS.ADDONS.md — IMPACT/TYPE/APP definitions, the >>ADDON: block
#       template, README.AI.md format, MAINTENANCE rules, DOC.CUSTOM.by.*
#       and DOC.CONFLICTS.* specs, DERIVED-FILE FRESHNESS mechanics
#     AI.SPECS.STUDIO.md — AI.STUDIO.md format, DOC.STUDIO.analysis.md and
#       DOC.STUDIO.by.* specs
#   The four DOC.CUSTOM.by.* summaries themselves are GENERATED by
#   AI.gen_summaries.py (template-owned, like the other scripts) — never
#   hand-written.
#   AI.gen_inventory.py (template-owned) is the inventory drift checker:
#     python3 AI/AI.gen_inventory.py --check extracts each addon's inventory
#     (DEPENDS/DEPENDS_CUSTOM/EXTERNAL_DEPS lines, models/fields/methods/
#     constraints, views, assets, crons) from its code
#     and diffs it against the >>ADDON: blocks. AI.canary.py runs it as
#     check 18 and adopts its ⚠️ findings verbatim, prefixed with the
#     addon name (INVENTORY DRIFT), so every canary run covers it;
#     running it directly gives the same findings plus advisory ◻︎ honesty
#     notes (unextractable/out-of-scope material). Classify each finding as
#     doc rot (fix the block) or an extractor bug (fix the script in the
#     template repo). AI.canary.py reports INVENTORY CHECKER UNAVAILABLE
#     when the script is missing or broken, or when its on-platform
#     [NEW]/[OVR] def-grep fails (TAG drift is then unchecked while the
#     other inventory dimensions were still checked).
#     Its --write mode GENERATES each block's inventory portion (header
#     DEPENDS/DEPENDS_CUSTOM/EXTERNAL_DEPS lines rewritten in place + a
#     marker-delimited INVENTORY:…END_INVENTORY: section, machine-owned —
#     never hand-edit between the markers; UPDATED dates stay hand-owned).
#     The maintenance prompts use it: hand-write judgment, --write the
#     inventory, verify with --check (spec: THE GENERATED INVENTORY
#     SECTION in AI.SPECS.ADDONS.md).
#   Read the relevant spec file WHEN a maintenance prompt is invoked — never
#   at session start.
#
# AI PROMPTS:
#   AI instruction: AI.CUSTOM.md's header pointer directed you here. After
#   reading AI.CUSTOM.md (the repo data — its data lines and >>ADDON:
#   blocks) and this file, perform the following steps in order. This is
#   the COMPLETE session-start sequence — the Studio checks run as step 2
#   of this sequence, never before step 1:
#
#   1. Check for an in-flight task:
#      If /home/odoo/src/user/AI/WIP.md exists, read it and show its full contents
#      to the user immediately — before Studio-check output, canary output, or
#      anything else — so they can decide whether to resume or discard it.
#      Then continue with the remaining steps; do not act on the WIP task
#      itself unless the user asks.
#
#   2. Run the Studio checks:
#      Perform STEP S1 through STEP S4 of the STUDIO CUSTOMIZATIONS —
#      SESSION CHECKS section below, in order, showing the outputs those
#      steps require.
#
#   3. Run the drift detector and show its output to the user:
#        python3 /home/odoo/src/user/AI/AI.canary.py
#      If it reports any actionable finding (⚠️, 🆕, ❓, 📄 — the script
#      exits 1), highlight it clearly so the user is aware that addon docs
#      may be missing, out of date, or inconsistent. ⬜ NO COMMITS is
#      informational only (a new addon awaiting its first commit; exit 0,
#      the ✅ all-clear is withheld) — relay it without raising an alarm.
#      The ◻︎ SPEC coverage line is likewise informational (exit 0, ✅
#      unaffected): a missing SPEC.AI.md is not a canary finding — relay,
#      don't alarm.
#
#   4. AI.ENTERPRISE.md — an ON-DEMAND reference, NOT a session-start read:
#      /home/odoo/src/user/AI/AI.ENTERPRISE.md is the generated Enterprise module
#      index (✅ = installed in production; generated by AI.gen_enterprise.py).
#      Do not read it now — the installed-module truth is already in
#      AI.CUSTOM.md's INSTALLED MODULES section. Consult the index when it
#      earns its tokens: assessing whether an Enterprise module already
#      covers a requested feature, answering what is available vs installed,
#      or before building custom code that standard Enterprise might make
#      redundant. For API details (models, fields, methods), read the
#      source in /home/odoo/src/enterprise/ directly.
#      Existence and freshness are now self-healing: AI.canary.py auto-
#      regenerates AI.ENTERPRISE.md when it is missing or stale (SOURCE-HASH
#      mismatch) — no manual step needed. No action is needed in this
#      step — continue to step 4b.
#
#   4b. AI.PRODENV.*.md — ON-DEMAND production DB context (NOT a session-start read):
#      The following files contain full production record detail extracted from
#      staging. Read only the relevant file when the task demands it — do NOT
#      load them at session start (they can be large and most sessions do not
#      need them):
#        AI/AI.PRODENV.TEMPLATES.md  — mail templates (full bodies + recipients)
#        AI/AI.PRODENV.ACTIONS.md    — automated actions + server actions (with code)
#        AI/AI.PRODENV.CRONS.md      — scheduled actions (cron jobs)
#        AI/AI.PRODENV.RULES.md      — non-global record rules (domains + permissions)
#        AI/AI.PRODENV.REPORTS.md    — report metadata
#      When to read which file:
#        · template or report change request  → AI.PRODENV.TEMPLATES.md / .REPORTS.md
#        · writing code that may conflict with existing automations → AI.PRODENV.ACTIONS.md
#        · cron/scheduling questions          → AI.PRODENV.CRONS.md
#        · access or security questions       → AI.PRODENV.RULES.md
#      AI/DOC.PRODENV.md is the lightweight index (names + provenance only) — read
#      it first when you need to know what exists without loading full bodies, then
#      read the specific category file if the task needs detail.
#      These files are absent until the first PRODENV sync from staging; if absent,
#      treat production DB-resident records as unknown and inform the user.
#      DOC.PRODENV.md and AI.ENTERPRISE.md are auto-regenerated by canary when
#      stale or missing — no manual command needed.
#      No action is needed in this step — continue to step 5.
#
#   5. Not-installed-in-production list — session-start reminder:
#      Read the NOT INSTALLED IN PRODUCTION subsection from AI.CUSTOM.md.
#      - If the subsection still contains a (NOT YET POPULATED) marker: skip —
#        production module state is unknown; first-time setup is covered by the
#        "Update installed modules list + Enterprise index" maintenance prompt.
#      - If the subsection is populated but contains only "(none)": skip —
#        nothing to show.
#      - If entries exist: display the list together with the production
#        snapshot date from AI.CUSTOM.md's INSTALLED MODULES header. Then note:
#        · If a single addon has since been deployed to or removed from
#          production, use the "Addon <name> active or inactive in production"
#          maintenance prompt to update its status.
#        · If several modules changed, use the "Update production environment
#          context" maintenance prompt to sync a fresh PRODENV from staging —
#          the module list auto-updates on the next canary run.
#      Produce no other output for this step.
#
#   6. Finally, display the MAINTENANCE PROMPTS block below to the user as a
#      brief reminder. Apart from the outputs required by steps 1–5 and this
#      block, produce no other output — do not summarize addons, Studio
#      customizations, or any file contents.
#
#   (AI note — the block between the ── delimiters below is display material:
#   each bullet's guidance tells the HUMAN when to invoke that prompt and
#   what to do first (exports, pushes, surveys are theirs); it is never a
#   standing instruction to the AI. The AI acts only when the user actually
#   invokes a prompt. Where a procedure mixes actors it labels the steps
#   explicitly (e.g. the survey prompt's "HUMAN STEP" / "AI Prompt:") — do
#   NOT infer from those labels that unlabeled text elsewhere assigns steps
#   to the AI.)
#
#   ── MAINTENANCE PROMPTS (display this block verbatim to the user — the
#      bullet text under each prompt is addressed to the HUMAN) ──────────────
#   Documentation loaded. Use these prompts to keep it current:
#
#   · Write or update SPEC.AI.md for addon <name>
#       whenever a plan is approved that changes an addon's behavior — write
#       the spec into the addon folder together with the code, before commit
#       (SPEC.AI.md CONVENTION section below; the spec states agreed
#       behavior, never a description derived from the code — AI.canary.py
#       reports SPEC STALE when it lags the code)
#   · Analyze and document addon <name>
#       after adding a new addon, or when the canary reports an undocumented
#       addon folder (spec: AI.SPECS.ADDONS.md)
#   · Remove addon <name> from documentation
#       after removing an addon from the codebase; also deletes its entry
#       in the NOT INSTALLED IN PRODUCTION list, if it had one (spec:
#       AI.SPECS.ADDONS.md)
#   · Addon <name> active or inactive in production
#       after an addon has been, or will be, activated or deactivated in production;
#       updates BOTH the addon's block STATUS field and the NOT INSTALLED IN
#       PRODUCTION list — they must stay in sync (block STATUS is
#       authoritative; exact STATUS values: AI.SPECS.ADDONS.md)
#   · Update Studio documentation
#       after making changes in Odoo Studio: re-export and push per the
#       STUDIO EXPORT PROCEDURE (in the STUDIO CUSTOMIZATIONS — SESSION
#       CHECKS section below), then run this prompt (spec: AI.SPECS.STUDIO.md)
#   · Regenerate stale or missing derived files
#       whenever AI.canary.py reports STALE DERIVED or MISSING DERIVED entries:
#       AI.ENTERPRISE.md and DOC.PRODENV.md are self-healing — AI.canary.py
#       auto-regenerates them when stale or missing; no manual step is needed.
#       For the DOC.CUSTOM.by.* files run:
#         python3 /home/odoo/src/user/AI/AI.gen_summaries.py
#       For other derived files, regenerate by hand using current stamps from:
#         python3 /home/odoo/src/user/AI/AI.canary.py --stamp
#       Then re-run the canary and confirm it reports no actionable findings —
#       ✅, or ⬜ NO COMMITS as the only output (exit 0; the ⬜ withholds the
#       ✅ but is informational — a new addon awaiting its first commit)
#   · Build documentation from scratch
#       when starting fresh with no existing documentation (high token
#       usage; specs: both AI.SPECS.* files)
#   · Audit all addon documentation
#       verify and refresh AI.CUSTOM.md, all README.AI.md files, AI.STUDIO.md,
#       and all summary files (high token usage; specs: both AI.SPECS.* files)
#   ────────────────────────────────────────────────────────────────────────────
#
#   (note for humans reading this file directly)
#   The best habit is to run the relevant prompt immediately after each change —
#   before closing the session. Retroactive documentation is harder, slower, and
#   more error-prone than incremental updates at the time of change.
#
# WIP CONVENTION:
#   /home/odoo/src/user/AI/WIP.md is an in-flight task tracker owned entirely by the
#   AI. It exists only while a multi-step task is actively in progress. The AI
#   creates it, updates it, and deletes it — the user never needs to touch it.
#
#   FORMAT (strict — the first three lines always; BLOCKED_ON only when blocked):
#     TASK: <one-line description of what is being worked on>
#     DONE: <comma-separated list of completed steps, or "nothing yet">
#     NEXT: <the exact next action to take>
#     BLOCKED_ON: <what is needed from the user before proceeding — omit if not blocked>
#
#   LIFECYCLE RULES:
#   · CREATE WIP.md at the start of any task that requires 3+ distinct steps
#     or that spans model changes, view changes, and an odoo-bin -u together.
#   · UPDATE WIP.md after completing each step (update DONE, update NEXT).
#   · DELETE WIP.md immediately when the task is fully complete or cleanly
#     cancelled — never leave a stale WIP.md after work is done.
#   · At session load, if WIP.md exists, show it to the user first (see AI
#     PROMPTS above) so they can decide whether to resume or discard it.
#   · A stale WIP.md (task no longer relevant) should be deleted on user request
#     or when the user explicitly starts a different task.
#
# CONFLICT CHECKING:
#   How to identify and assess interactions between an addon and other addons
#   or Studio customizations:
#   - Cross-reference AI.CUSTOM.md for other addons that share the same MODEL entries
#   - Cross-reference AI.STUDIO.md for Studio fields, view modifications, or
#     automations on the same models (DOC.STUDIO.by.Model.md may be consulted
#     for orientation, but is never authoritative — see the DOC.* ACCESS
#     POLICY section below)
#   - Identify any write() override chains, view inheritance overlaps, field name
#     collisions, or conceptually duplicate fields before making any changes
#   - Flag discovered interactions to the user before proceeding
#
# DOC.* ACCESS POLICY:
#   Applies to ALL derived DOC.* files — the summaries and conflict registers
#   specified in the AI.SPECS.* files:
#   - never read them at session start — they add nothing then and waste tokens
#   - on-demand reads are fine (e.g. when the user asks about their contents)
#   - never authoritative: conflict checking always derives live from
#     AI.CUSTOM.md and AI.STUDIO.md per CONFLICT CHECKING above; on any
#     disagreement the live derivation wins — the derived file is stale and
#     must be regenerated
#
# LEGEND (for the >>ADDON: blocks in AI.CUSTOM.md):
#   [NEW] = new custom method (not in standard Odoo)
#   [OVR] = overrides an existing standard Odoo method
#   DEPENDS_CUSTOM = other addons in /home/odoo/src/user/ required by this addon
#   README.AI.md = full detailed file for this addon in each addon folder; read it when deeper context is needed
#   IMPACT / TYPE / APP = block classification fields — semantics and
#     allowed values in AI.SPECS.ADDONS.md (APP values: the "# APPS
#     (baseline …):" data line in AI.CUSTOM.md)
#
# 🛑 GIT COMMIT & PUSH RULES:
#   NEVER create a git commit unless the user explicitly asks for it.
#   NEVER run odoosh-push unless the user explicitly asks for it.
#   Completing a task (writing code, updating docs, fixing a bug) does NOT
#   constitute permission to commit. Always wait for an explicit instruction
#   such as "commit", "push", or "save this to git".
#
# MANIFEST CONVENTIONS:
#   When creating any new __manifest__.py file, set the author field to:
#     'author': "dynenttech.com via Claude Code"
#   The value is a template CONSTANT — one integrator building
#   customizations for many customer repos, so the same author applies
#   everywhere; if it ever changes, it changes here in the template and
#   reaches every repo through the normal upgrade overwrite. No script
#   validates it.
#
# ENVIRONMENT CONSTRAINTS (template-owned — odoo.sh platform facts, uniform
#   across repos; if the platform changes, this section updates fleet-wide
#   through the normal upgrade overwrite):
#   TEST EXECUTION: This dev environment can run Python tests
#   (TransactionCase, SingleTransactionCase, and HttpCase tests that only
#   make HTTP calls) via:
#     odoo-bin -u <module> --test-enable --stop-after-init --no-http
#   Chrome is present in this environment but resource-constrained — Tours
#   (start_tour / browser_js) and in-browser JS/Hoot tests fail here due to
#   resource limits. Do not attempt to run those here; write them if asked,
#   but leave them for a resource-adequate environment and verify client-side
#   changes manually via $ODOO_BUILD_URL.
#   Tell the user to run these Chrome-dependent tests (Tours / browser JS /
#   Hoot) during odoo.sh rebuilds, where the runner has adequate resources —
#   flag any such test the module carries or that you add, and remind the user
#   it will only be exercised on the next odoo.sh rebuild, not here.
#   HTTP SMOKE TESTS: curl is available in this environment and can reach
#   $ODOO_BUILD_URL — use it to smoke-test controllers, JSON-RPC endpoints,
#   and server-rendered pages (status codes, redirects, response content).
#   Two limits: curl does not execute JavaScript, so it never substitutes
#   for the Chrome-dependent verification above; and $ODOO_BUILD_URL serves
#   the code its server has loaded — local edits are not reflected there
#   until the server is restarted with them (schema changes need -u), so a
#   curl result against the build URL is evidence about the DEPLOYED state,
#   not the working tree. Authenticated endpoints need a session first
#   (e.g. /web/session/authenticate with a cookie jar); anonymous curl
#   covers public routes only.
#   BUILD LIFETIME AND WHAT SURVIVES IT: everything writable in this
#   container lives inside the odoo.sh BUILD directory — /tmp, /home/odoo
#   and /home/odoo/.cache all share the same build-scoped mount root
#   (/odoo/containers/<container>/builds/<build-id>/...). /home/odoo/src/user
#   is the ONLY path that crosses a rebuild, and it does so because it is a
#   git checkout, not because the filesystem preserves it.
#   Two consequences, and the second is the one that matters:
#   - /tmp is FINE for scratch and testing within a session. It is not wiped
#     between turns; it is destroyed with the build. Nor is there a better
#     scratch location: a directory under /home/odoo buys no durability over
#     /tmp, since both die with the same build, while costing the rule that
#     only /home/odoo/src/user may be modified.
#   - An odoo.sh REBUILD destroys the build AND starts a NEW AI SESSION. So
#     no work can straddle a rebuild in memory OR on disk: anything the next
#     session must have — findings, a plan, a handoff, a measurement worth
#     keeping — has to be COMMITTED to the repo before the rebuild, or it is
#     gone twice over. When a task requires a rebuild, write the handoff into
#     a repo file first and assume the reader starts cold with none of the
#     conversation.
#
# SPEC.AI.md CONVENTION:
#   Every custom addon carries a normative behavioral contract at
#   <addon>/SPEC.AI.md — the written outcome of the plan-mode agreement
#   that precedes coding: agree on a plan interactively, then write the
#   spec into the addon folder together with the code. It is the
#   counterpart of README.AI.md with the OPPOSITE direction of authority:
#   README.AI.md documents what the code IS and is updated to follow the
#   code (format: AI.SPECS.ADDONS.md); SPEC.AI.md states what the addon
#   MUST DO, and the code follows IT. On disagreement, either the code is
#   wrong or the agreement changed — a user decision, never a silent doc
#   update: do NOT "update the spec to match the code" as routine
#   maintenance (that is the README's rule and exactly what the spec must
#   never do); spec amendments happen only through an approved plan or an
#   approved review-divergence resolution.
#   ALTITUDE RULE: observable behaviors, flows, and business rules only —
#   what a user could verify from outside ("orders above the threshold
#   need a second approval", "the reminder goes out N days before
#   expiry"). No model/field/method inventory (the >>ADDON: block owns
#   that, machine-generated) and no implementation narrative
#   (README.AI.md owns that). Short is correct — 10–15 lines is a normal
#   size for a small addon; content below this altitude is a review
#   finding, not extra thoroughness.
#   FORMAT: the very FIRST line of the file must be "UPDATED: YYYY-MM-DD"
#   (above any title or template heading — a spec hand-made from a
#   template needs the line inserted at the top), then the behavior
#   content.
#   A LIVING document: it describes the addon's CURRENT intended behavior
#   as a whole — amended when scope changes, superseded content removed;
#   never an append-only pile of per-feature plans.
#   LIFECYCLE:
#   · CREATE or UPDATE it whenever an approved plan changes an addon's
#     behavior — written together with the code, before commit
#   · BUMP its UPDATED line when a code change is confirmed to still
#     match the spec, or when the spec is amended (AI.canary.py compares
#     it to the addon's git history and reports SPEC STALE / SPEC
#     MALFORMED — its check 19; spec ABSENCE is deliberately not a
#     canary finding, only the informational ◻︎ SPEC coverage line)
#
# STUDIO CUSTOMIZATIONS — SESSION CHECKS:
#   Studio customizations are documented separately from custom addons, in
#   AI.STUDIO.md (inventory) and DOC.STUDIO.analysis.md (current-state analysis).
#   Their file formats, summary specs, and regeneration rules live in
#   AI.SPECS.STUDIO.md — read it when a Studio maintenance prompt is
#   invoked, never at session start.
#
#   The following checks are invoked as step 2 of the AI PROMPTS session-start
#   sequence above — do not run them independently or before the WIP.md check:
#
#   STEP S1 — Check whether the folder exists:
#     Expected location: /home/odoo/src/user/studio_customization/
#     ⚠️  IMPORTANT: Use the Bash tool to check — do NOT use Glob or Read, as
#     those tools cannot detect directories. Run exactly:
#       ls /home/odoo/src/user/studio_customization/ 2>/dev/null && echo EXISTS || echo MISSING
#     Treat a listing that shows files as EXISTS. Treat "MISSING" or any error
#     as absent — and treat "EXISTS" with no files listed (empty folder) as
#     absent too: an empty export folder has nothing to analyze, follow the
#     MISSING branch.
#
#     STUDIO EXPORT PROCEDURE (canonical — other sections reference it;
#       performed by the human — the AI only recommends it):
#       1. Export Studio customizations from Odoo:
#          Settings → Technical → Studio → Export Customizations
#       2. Place the exported files in /home/odoo/src/user/studio_customization/
#       3. Immediately rename __manifest__.py → __manifest__.py.disabled
#       4. Commit and push (odoosh-push)
#
#     If MISSING:
#       Inform the user and recommend the STUDIO EXPORT PROCEDURE above
#       before proceeding.
#       Without the export, Studio-aware analysis will be incomplete.
#       Skip the AI.STUDIO.md read until resolved, and treat all Studio-derived
#       DOC.* files as stale (on-demand files anyway — see the DOC.* ACCESS
#       POLICY section).
#       If AI.STUDIO.md exists nonetheless, flag it to the user as orphaned —
#       it documents an export that is no longer in the repo; either the folder
#       must be restored/re-exported, or (if the Studio customizations are gone
#       for good) AI.STUDIO.md and the Studio-derived DOC.* files should be
#       deleted — all together: Studio-derived DOC.* files left behind after
#       AI.STUDIO.md is deleted can no longer be verified or regenerated, so
#       AI.canary.py reports the leftovers themselves. Both orphan states are
#       reported as STALE STUDIO DOC.
#
#     If EXISTS:
#       Remind the user that this export must be kept current — Studio changes
#       made in the Odoo UI are not automatically reflected here; re-export and
#       update whenever Studio customizations change. Then continue to STEP S2.
#
#   STEP S2 — Check for an active manifest file:
#     If __manifest__.py exists (exact name, no .disabled suffix):
#       ⚠️  An active __manifest__.py in studio_customization/ makes Odoo try
#       to load the folder as a module on next startup, which may cause
#       errors. Rename it NOW, without asking first — the STUDIO EXPORT
#       PROCEDURE mandates the rename, so an active manifest is always an
#       omission, never intent:
#         mv /home/odoo/src/user/studio_customization/__manifest__.py \
#            /home/odoo/src/user/studio_customization/__manifest__.py.disabled
#       Then notify the user of the rename and remind them to commit and push
#       it (per the GIT COMMIT & PUSH RULES, never commit or push yourself
#       unless explicitly asked). AI.canary.py reports the same hazard
#       (ACTIVE STUDIO MANIFEST) as a backstop for sessions where these
#       checks are not run. Once renamed, continue to STEP S3.
#
#     If only __manifest__.py.disabled exists: no action needed. Continue to STEP S3.
#
#   STEP S3 — Check whether AI.STUDIO.md exists:
#     If /home/odoo/src/user/AI/AI.STUDIO.md is MISSING:
#       The folder exists but has not been documented yet. Offer to analyze the
#       studio_customization/ folder and create AI.STUDIO.md (per the
#       AI.STUDIO.md FILE FORMAT spec in AI.SPECS.STUDIO.md). Also offer to
#       generate DOC.STUDIO.analysis.md, DOC.CONFLICTS.Studio.md, DOC.STUDIO.by.App.md,
#       DOC.STUDIO.by.Model.md, and DOC.STUDIO.by.Fields.md once AI.STUDIO.md
#       is created.
#
#     If EXISTS: you MUST automatically read it now:
#       /home/odoo/src/user/AI/AI.STUDIO.md
#       That file documents all Studio-added fields, automations, view
#       modifications, filters, and other Studio-managed records.
#       Then continue to STEP S4.
#
#   STEP S4 — Check whether DOC.STUDIO.analysis.md exists:
#     If /home/odoo/src/user/AI/DOC.STUDIO.analysis.md is MISSING (and AI.STUDIO.md exists):
#       Offer to regenerate it by analyzing studio_customization/ and
#       AI.STUDIO.md, using its standard sections (see WHAT BELONGS IN
#       DOC.STUDIO.analysis.md in AI.SPECS.STUDIO.md). No git recovery is needed —
#       the file is current-state only and fully regenerable.
#
#     If EXISTS: do not read it at startup — consult it on demand when an
#       x_studio_* field behaves unexpectedly or a production log references
#       a Studio field.
#
# COVERAGE — definition (for the "# COVERAGE:" line in AI.CUSTOM.md):
#   total = top-level addon folders in this repo containing __manifest__.py
#           (addons must sit directly at the repo root, one folder per addon —
#           this template's checks assume that layout; nested layouts such as
#           addons/<name>/ are invisible to addon discovery and get
#           misreported as FOLDER MISSING / COVERAGE MISMATCH)
#           (studio_customization/ is always excluded by name; its manifest is
#           additionally renamed .disabled per the STUDIO EXPORT PROCEDURE so
#           Odoo's loader ignores it — AI.canary.py reports ACTIVE STUDIO
#           MANIFEST when it is not)
#   N     = folders from that set that have a >>ADDON: block in AI.CUSTOM.md
#   Update AI.CUSTOM.md's COVERAGE line whenever a >>ADDON: block is added
#   or removed. AI.canary.py verifies it and reports a COVERAGE MISMATCH
#   on drift.
