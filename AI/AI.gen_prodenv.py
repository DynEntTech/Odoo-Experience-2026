#!/usr/bin/env python3
"""AI.gen_prodenv.py — Production environment context extractor.

Generates per-category AI/AI.PRODENV.*.md files: structured markdown summaries
of records that live in the production database so the AI has accurate context for:
  (a) Conflict detection — custom modules vs existing automations/rules
  (b) Q&A — "do we have an automation that does X?"
  (c) Change requests — email templates and reports the AI needs to SEE
  (d) Security — record rules that affect what users can do

Output files (written directly to AI/ by the script body):
  AI.PRODENV.MODULES.md   — installed module list (TRANSIENT: consumed+deleted
                             by AI.canary.py on the next dev run; module list
                             written into AI.CUSTOM.md automatically)
  AI.PRODENV.TEMPLATES.md — mail.template records (full bodies)
  AI.PRODENV.ACTIONS.md   — base.automation + ir.actions.server (non-standard)
  AI.PRODENV.CRONS.md     — ir.cron (scheduled actions)
  AI.PRODENV.RULES.md     — ir.rule (non-global record rules)
  AI.PRODENV.REPORTS.md   — ir.actions.report (metadata only)

DOC.PRODENV.md (the names-only index) is generated separately by
AI.gen_prodenv_doc.py, which reads the 5 permanent files above.
AI.canary.py runs gen_prodenv_doc automatically after processing MODULES.

Provenance tags on every record:
  [UI-created]   — no ir.model.data entry; exists only in DB (outside git)
  [custom: mod]  — shipped by repo custom module (already in git)
  [odoo: mod]    — shipped by a standard Odoo module

Studio customisations are NOT extracted here — they are covered by the Studio
project export (AI.STUDIO.md). Records owned by a studio module appear as
[odoo: studio_customization] and are listed for completeness only.

Usage — run on STAGING (production copy; NEVER on dev, which has no
production data). The script body is piped to odoo-bin shell, which writes
the output files directly to disk:

    python3 AI/AI.gen_prodenv.py | odoo-bin shell --no-http
    git add AI/AI.PRODENV.*.md
    git commit -m "sync: production environment snapshot YYYY-MM-DD"
    odoosh-push

Sync the resulting files to the dev branch (substitute your staging branch name):
    git fetch
    git checkout origin/<staging-branch> -- 'AI/AI.PRODENV.*.md'
    git add AI/AI.PRODENV.*.md
    git commit -m "sync: PRODENV from staging"
    odoosh-push

On the next `python3 AI/AI.canary.py` run in dev, AI.PRODENV.MODULES.md is
automatically applied to AI.CUSTOM.md (module list updated) and then deleted.
AI.ENTERPRISE.md and DOC.PRODENV.md are regenerated at the same time.

GITIGNORE: AI.PRODENV.*.md is gitignored in the template repo (like AI.CUSTOM.md).
In customer repos all files ARE committed. See AI.SESSION.md for the maintenance
prompt.

Odoo version: 19.0
"""
import sys

# ─────────────────────────────────────────────────────────────────────────────
# EXTRACT_SCRIPT — the body piped to odoo-bin shell.
# Uses the Odoo shell's `env` variable (available automatically).
# Writes files directly to AI_PATH using open() — no stdout redirect needed.
# Odoo startup logs go to stderr (terminal only, not captured).
# ─────────────────────────────────────────────────────────────────────────────

EXTRACT_SCRIPT = r'''
# AI.gen_prodenv extraction body — Odoo 19.0
# Runs inside odoo-bin shell. Do not execute with plain python3.
import os
from datetime import datetime

try:
    from odoo.modules.module import get_module_path
except ImportError:
    def get_module_path(name, display_warning=True):
        return ''

USER_PATH = '/home/odoo/src/user/'
AI_PATH   = '/home/odoo/src/user/AI/'
INSTALLED_NOW = ('installed', 'to upgrade', 'to remove')
TODAY = datetime.now().strftime('%Y-%m-%d')

HEADER_COMMON = (
    f"Generated: {TODAY}\n"
    "Source: staging (production copy)\n"
    "Odoo: 19.0\n"
    "Provenance: [UI-created]=DB-only  |  [custom:X]=repo module X  |  [odoo:X]=standard Odoo X\n"
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _source(model_name, rec_id):
    """[UI-created] / [custom: mod] / [odoo: mod] provenance tag."""
    xid = env['ir.model.data'].search(
        [('model', '=', model_name), ('res_id', '=', rec_id)], limit=1)
    if not xid:
        return '[UI-created]'
    path = get_module_path(xid.module, display_warning=False) or ''
    if path.startswith(USER_PATH):
        return f'[custom: {xid.module}]'
    return f'[odoo: {xid.module}]'


def _safe(val, default=''):
    try:
        return val if val else default
    except Exception:
        return default


def _domain(d):
    try:
        s = str(d) if d and d not in ('[]', False, None) else '[]'
        return s
    except Exception:
        return '(unparseable)'


def _model_name(rec, field='model_id'):
    try:
        m = getattr(rec, field, None)
        return m.model if m else '?'
    except Exception:
        return '?'


def _indent(text, prefix='    '):
    """Indent a multi-line code block."""
    if not text:
        return ''
    return '\n'.join(prefix + ln for ln in text.strip().splitlines())


def _write(filename, content):
    """Write a file to AI_PATH atomically (tmp + rename)."""
    path = AI_PATH + filename
    tmp  = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(content)
    os.replace(tmp, path)


# ── AI.PRODENV.MODULES.md ─────────────────────────────────────────────────────

enterprise, community, themes, custom_installed, custom_not = [], [], [], [], []

for m in env['ir.module.module'].search([], order='name'):
    path = get_module_path(m.name, display_warning=False) or ''
    if not path:
        continue
    is_installed = m.state in INSTALLED_NOW
    src_dir = os.path.dirname(path)
    state_tag = '' if m.state == 'installed' else f'  [{m.state}]'
    entry = (m.name, state_tag)
    if path.startswith(USER_PATH):
        (custom_installed if is_installed else custom_not).append(entry)
        continue
    if not is_installed:
        continue
    if '/src/enterprise' in src_dir:
        enterprise.append(entry)
    elif '/src/themes' in src_dir:
        themes.append(entry)
    else:
        community.append(entry)

mod_lines = [
    "# Production Environment — Installed Modules",
    f"Generated: {TODAY}",
    "Source: staging (production copy)",
    "NOTE: This file is consumed by AI.canary.py on the next dev run and deleted.",
    "      The module list is written into AI.CUSTOM.md automatically.",
    "      Do not hand-edit this file.",
    "",
]
for label, lst in [
    ('ODOO ENTERPRISE', enterprise),
    ('ODOO COMMUNITY', community),
    ('ODOO THEMES', themes),
    ('CUSTOM (installed)', custom_installed),
    ('CUSTOM (not installed in production)', custom_not),
]:
    mod_lines.append(f"### {label}")
    for name, stag in sorted(lst):
        mod_lines.append(f"  {name}{stag}")
    if not lst:
        mod_lines.append("  (none)")
    mod_lines.append("")

_write('AI.PRODENV.MODULES.md', '\n'.join(mod_lines))


# ── AI.PRODENV.TEMPLATES.md ───────────────────────────────────────────────────

templates = env['mail.template'].search([('active', '=', True)], order='name')
tpl_lines = [
    "# Production Environment — Mail Templates",
    HEADER_COMMON,
    f"## Mail Templates  ({len(templates)} active)",
    "",
]

for t in templates:
    src = _source('mail.template', t.id)
    tpl_lines.append(f"### {t.name}  {src}")
    tpl_lines.append(f"- Model: {_safe(t.model, '?')}")
    if _safe(t.subject):
        tpl_lines.append(f"- Subject: {t.subject}")
    if _safe(t.email_to):
        tpl_lines.append(f"- To: {t.email_to}")
    if _safe(t.email_cc):
        tpl_lines.append(f"- CC: {t.email_cc}")
    if _safe(t.reply_to):
        tpl_lines.append(f"- Reply-To: {t.reply_to}")
    auto_delete = getattr(t, 'auto_delete', None)
    if auto_delete is not None:
        tpl_lines.append(f"- Auto-delete: {'Yes' if auto_delete else 'No'}")
    body = _safe(t.body_html, '')
    if body:
        tpl_lines.append("- Body:")
        tpl_lines.append(_indent(body))
    tpl_lines.append("")

_write('AI.PRODENV.TEMPLATES.md', '\n'.join(tpl_lines))


# ── AI.PRODENV.ACTIONS.md ─────────────────────────────────────────────────────
# Contains: automated actions (base.automation) + non-standard server actions (ir.actions.server)

automations = env['base.automation'].search([], order='name')
act_lines = [
    "# Production Environment — Automated Actions & Server Actions",
    HEADER_COMMON,
    f"## Automated Actions  ({len(automations)} total)",
    "",
]

for a in automations:
    src = _source('base.automation', a.id)
    act_lines.append(f"### {a.name}  {src}")
    act_lines.append(f"- Model: {_model_name(a)}")
    act_lines.append(f"- Trigger: {_safe(a.trigger, '?')}")
    if _safe(getattr(a, 'filter_domain', None)) not in ('', '[]', None):
        act_lines.append(f"- Filter domain: {_domain(a.filter_domain)}")
    if _safe(getattr(a, 'filter_pre_domain', None)) not in ('', '[]', None):
        act_lines.append(f"- Before-update domain: {_domain(a.filter_pre_domain)}")
    action_recs = (getattr(a, 'action_server_ids', None)
                   or getattr(a, 'child_ids', None)
                   or [])
    for act in action_recs:
        state = _safe(getattr(act, 'state', '?'), '?')
        act_lines.append(f"- Action: [{state}] {act.name}")
        if state == 'code' and _safe(getattr(act, 'code', None)):
            act_lines.append(_indent(act.code))
        elif state == 'mail_post':
            tpl = getattr(act, 'template_id', None)
            if tpl:
                act_lines.append(f"    → template: {tpl.name}")
    act_lines.append(f"- Active: {'Yes' if a.active else 'No'}")
    act_lines.append("")

# Server actions (UI-created and custom only — exclude standard Odoo ones)
all_sa = env['ir.actions.server'].search([('model_id', '!=', False)], order='name')
sa_list = [(sa, _source('ir.actions.server', sa.id)) for sa in all_sa]
sa_list = [(sa, src) for sa, src in sa_list if not src.startswith('[odoo:')]

act_lines.append(f"## Server Actions  ({len(sa_list)} non-standard)")
act_lines.append("")

for sa, src in sa_list:
    act_lines.append(f"### {sa.name}  {src}")
    act_lines.append(f"- Model: {_model_name(sa)}")
    state = _safe(getattr(sa, 'state', '?'), '?')
    act_lines.append(f"- Type: {state}")
    if state == 'code' and _safe(getattr(sa, 'code', None)):
        act_lines.append("- Code:")
        act_lines.append(_indent(sa.code))
    elif state == 'object_write':
        for fl in getattr(sa, 'fields_lines', []):
            col = getattr(fl, 'col1', None)
            fname = col.name if col else '?'
            act_lines.append(f"- Set {fname} = {_safe(getattr(fl, 'value', '?'), '?')}")
    elif state == 'mail_post':
        tpl = getattr(sa, 'template_id', None)
        if tpl:
            act_lines.append(f"- Template: {tpl.name}")
    elif state == 'object_create':
        link = getattr(sa, 'crud_model_id', None)
        if link:
            act_lines.append(f"- Creates: {link.model}")
    act_lines.append("")

_write('AI.PRODENV.ACTIONS.md', '\n'.join(act_lines))


# ── AI.PRODENV.CRONS.md ───────────────────────────────────────────────────────

crons = env['ir.cron'].search([('active', '=', True)], order='name')
cron_lines = [
    "# Production Environment — Scheduled Actions (Cron)",
    HEADER_COMMON,
    f"## Scheduled Actions / Cron  ({len(crons)} active)",
    "",
]

for c in crons:
    src = _source('ir.cron', c.id)
    cron_lines.append(f"### {c.name}  {src}")
    model_name = _model_name(c)
    server_action = getattr(c, 'ir_actions_server_id', None)
    if server_action:
        state = _safe(getattr(server_action, 'state', '?'), '?')
        cron_lines.append(f"- Calls: {model_name} via server action [{state}] {server_action.name}")
        if state == 'code' and _safe(getattr(server_action, 'code', None)):
            cron_lines.append("- Code:")
            cron_lines.append(_indent(server_action.code))
    else:
        fn = (_safe(getattr(c, 'function', None))
              or _safe(getattr(c, 'code', None), '?'))
        cron_lines.append(f"- Calls: {model_name}.{fn}()")
    interval_n = _safe(getattr(c, 'interval_number', None), '?')
    interval_t = _safe(getattr(c, 'interval_type', None), '?')
    cron_lines.append(f"- Interval: every {interval_n} {interval_t}")
    nextcall = getattr(c, 'nextcall', None)
    if nextcall:
        cron_lines.append(f"- Next run: {nextcall.strftime('%Y-%m-%d %H:%M UTC')}")
    cron_lines.append("")

_write('AI.PRODENV.CRONS.md', '\n'.join(cron_lines))


# ── AI.PRODENV.RULES.md ───────────────────────────────────────────────────────

rules = env['ir.rule'].search([('global', '=', False)], order='model_id,name')
rule_lines = [
    "# Production Environment — Record Rules",
    HEADER_COMMON,
    f"## Record Rules  ({len(rules)} non-global)",
    "",
]

for r in rules:
    src = _source('ir.rule', r.id)
    rule_lines.append(f"### {r.name}  {src}")
    rule_lines.append(f"- Model: {_model_name(r, 'model_id')}")
    groups_str = (', '.join(r.groups.mapped('name'))
                  if r.groups else '(global within model)')
    rule_lines.append(f"- Groups: {groups_str}")
    rule_lines.append(f"- Domain: {_domain(r.domain_force)}")
    perms = [p for p, f in [
        ('read', r.perm_read), ('write', r.perm_write),
        ('create', r.perm_create), ('delete', r.perm_unlink),
    ] if f]
    rule_lines.append(f"- Permissions: {', '.join(perms) or '(none)'}")
    rule_lines.append("")

_write('AI.PRODENV.RULES.md', '\n'.join(rule_lines))


# ── AI.PRODENV.REPORTS.md ─────────────────────────────────────────────────────

reports = env['ir.actions.report'].search([], order='name')
rpt_lines = [
    "# Production Environment — Reports",
    HEADER_COMMON,
    f"## Reports  ({len(reports)})",
    "",
]

for rpt in reports:
    src = _source('ir.actions.report', rpt.id)
    rpt_lines.append(f"### {rpt.name}  {src}")
    rpt_lines.append(f"- Model: {rpt.model}")
    rpt_lines.append(f"- Output: {rpt.report_type}")
    pf = getattr(rpt, 'paperformat_id', None)
    if pf:
        rpt_lines.append(f"- Paper: {pf.name}")
    rpt_lines.append(f"- Template: {rpt.report_name}")
    rpt_lines.append("")

_write('AI.PRODENV.REPORTS.md', '\n'.join(rpt_lines))


# ── completion summary ────────────────────────────────────────────────────────

print(f"PRODENV: 6 files written to {AI_PATH}")
print(f"  AI.PRODENV.MODULES.md    ({len(enterprise)+len(community)+len(themes)+len(custom_installed)+len(custom_not)} modules)")
print(f"  AI.PRODENV.TEMPLATES.md  ({len(templates)} mail templates)")
print(f"  AI.PRODENV.ACTIONS.md    ({len(automations)} automations, {len(sa_list)} server actions)")
print(f"  AI.PRODENV.CRONS.md      ({len(crons)} cron jobs)")
print(f"  AI.PRODENV.RULES.md      ({len(rules)} record rules)")
print(f"  AI.PRODENV.REPORTS.md    ({len(reports)} reports)")
print()
print("MODULES.md is transient — AI.canary.py applies it to AI.CUSTOM.md on the next dev run.")
print()
print("Next steps — run these in the OS shell on STAGING:")
print(f'  git add AI/AI.PRODENV.*.md')
print(f'  git commit -m "sync: production environment snapshot {TODAY}"')
print(f'  odoosh-push')
print()
print("Then on DEV (substitute your staging branch name):")
print(f'  git fetch')
print(f"  git checkout origin/<staging-branch> -- 'AI/AI.PRODENV.*.md'")
print(f'  git add AI/AI.PRODENV.*.md')
print(f'  git commit -m "sync: PRODENV from staging"')
print(f'  odoosh-push')
print()
print("On the next `python3 AI/AI.canary.py` run in dev the module list")
print("auto-applies and AI.ENTERPRISE.md + DOC.PRODENV.md are regenerated.")
'''

# ─────────────────────────────────────────────────────────────────────────────

_USAGE = """\
AI/AI.gen_prodenv.py — Production environment context extractor

The extraction body above was printed to stdout for piping to odoo-bin shell.
Run on STAGING (which is a production copy — NEVER on dev):

  python3 AI/AI.gen_prodenv.py | odoo-bin shell --no-http
  git add AI/AI.PRODENV.*.md
  git commit -m "sync: production environment snapshot $(date +%Y-%m-%d)"
  odoosh-push

The script writes 6 files directly to AI/:
  AI.PRODENV.MODULES.md    — installed modules (TRANSIENT: auto-applied+deleted by canary)
  AI.PRODENV.TEMPLATES.md  — mail templates (full bodies)
  AI.PRODENV.ACTIONS.md    — automated actions + non-standard server actions
  AI.PRODENV.CRONS.md      — scheduled actions / cron jobs
  AI.PRODENV.RULES.md      — non-global record rules
  AI.PRODENV.REPORTS.md    — report metadata

Sync the files to dev (substitute your staging branch name):
  git fetch
  git checkout origin/<staging-branch> -- 'AI/AI.PRODENV.*.md'
  git add AI/AI.PRODENV.*.md
  git commit -m "sync: PRODENV from staging"
  odoosh-push

On the next `python3 AI/AI.canary.py` run in dev:
  - AI.PRODENV.MODULES.md is applied to AI.CUSTOM.md (module list updated)
  - AI.PRODENV.MODULES.md is deleted (transient carrier, now consumed)
  - AI.ENTERPRISE.md is regenerated
  - DOC.PRODENV.md (names-only index) is regenerated via AI.gen_prodenv_doc.py

Frequency: run whenever significant DB-resident records are created or changed
(new automations, mail templates, server actions, record rules, cron jobs,
reports) or after any module install/uninstall in production.

See AI.SESSION.md — "Update production environment context" maintenance prompt.
"""

if __name__ == '__main__':
    # Script body → stdout (for piping to odoo-bin shell)
    print(EXTRACT_SCRIPT, end='')
    # Usage → stderr (visible on the terminal, not captured by file redirect)
    print(_USAGE, file=sys.stderr)
