# AI Toolkit — Getting Started

This folder contains the context, instruction, and tooling files that power
Claude-assisted development in this repository. The AI knows the codebase's
addons, their dependencies, the installed module list, and the production
environment.

## Start a session

Open Claude Code and say:

    read AI/AI.CUSTOM.md

That one line loads everything. The AI reads the repo data file
(AI.CUSTOM.md) and the instruction file (AI.SESSION.md) and is ready for
repo-specific work — it knows the addons, installed modules, conflicts
register, and all available prompts.

## What you can ask the AI to do

All prompts are defined in AI.SESSION.md (MAINTENANCE PROMPTS section).
Common ones:

**Documentation**
- "Analyze and document addon <name>" — build or update an addon's block
- "Build documentation from scratch" — first build for a brand-new addon

## Health check

After any significant change to the repo or AI files:

    python3 AI/AI.canary.py

Checks documentation coverage, derived-file staleness, module inventory
drift, and production-environment sync status. Every finding prints its
own remediation. Clean run = ✅ exit 0.

## Production environment data

The AI.PRODENV.*.md files give the AI visibility into what exists in the
production database — mail templates, automations, cron jobs, record rules,
and reports. These files are generated on STAGING (a production copy) and
synced to dev. If they are absent the AI treats DB-resident records as
unknown.

To refresh (run on STAGING):

    python3 AI/AI.gen_prodenv.py | odoo-bin shell --no-http

The script prints the exact git commands to commit and sync to dev.
On the next `python3 AI/AI.canary.py` run on dev the module list
auto-applies and AI.ENTERPRISE.md is regenerated.

## Where to find more

| File | Purpose |
|---|---|
| AI.SESSION.md | Full session instructions and all maintenance prompts |
| AI.CUSTOM.md | This repo's data file (addons, modules, coverage) |
| AI.ENTERPRISE.md | Enterprise module reference (auto-generated) |
| DOC.PRODENV.md | Names-only index of production DB records (auto-generated) |
