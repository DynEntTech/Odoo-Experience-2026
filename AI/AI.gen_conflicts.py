#!/usr/bin/env python3
"""Derive cross-addon INTERACTIONS from the >>ADDON: blocks in AI.CUSTOM.md.

This script DERIVES ONLY. It reports where addons meet — shared models, shared method
names, shared field names, shared view inheritance targets — and says
nothing about whether any of it is a problem.

That restraint is the whole design, not modesty. A script can establish
that four addons touch res.users._compute_is_any_portal_agent; it cannot
establish whether that is a defect. The measured case is almost certainly
BY DESIGN — one addon defines the compute [NEW] and the others extend it
[OVR] — and three addons overriding a standard Odoo method is fine if each
calls super(), which the blocks do not record. So this script never emits
the word "conflict" for a finding, never assigns a severity, and never
guesses intent. Judgment is a separate, recorded act (AI.CONFLICTS.md);
keeping the two apart is what stops a derived file from carrying decisions
it cannot justify.

Usage:
    python3 AI/AI.gen_conflicts.py [path-to-AI.CUSTOM.md]   report to stdout
    python3 AI/AI.gen_conflicts.py --write                  also regenerate
                                                         DOC.CONFLICTS.Addons.md

--write produces the HUMAN-READABLE register: it MERGES the derived facts with
the decisions recorded in AI.CONFLICTS.md, so one file answers "what is the
conflict situation in this repo?" for a developer — what interacts, what was
decided about it, why, and what nobody has decided yet. The file is DERIVED
and disposable: it is regenerated wholesale and carries a SOURCE-HASH stamp,
so it must never be the place a decision is written. Decisions live in
AI.CONFLICTS.md, which is never regenerated.

Exit status: 0 when the derivation ran, 1 only on a usage/parse error.
Finding interactions is a normal result, not a failure — the UNDISPOSED
check that DOES gate belongs to AI.canary.py, against AI.CONFLICTS.md.

TWO PARSING RULES THAT ARE LOAD-BEARING
  1. PRECEDENCE, NOT MERGING. A block may carry BOTH a legacy hand-written
     inventory and a machine-generated INVENTORY:…END_INVENTORY: section —
     7 of 12 addons in the reference repo do. AI.SPECS.ADDONS.md states the
     generated section is "the inventory of record", so when it is present
     the legacy lines are IGNORED. Merging would count every model twice.
  2. GROUP N-WAY, NOT PAIRWISE. Four addons sharing one method is ONE
     interaction, not six pairs. Pairwise emission triples the apparent
     volume and gives the same fact several identities, which would break
     the natural-key matching AI.CONFLICTS.md depends on.
"""
import collections
import datetime
import importlib.util
import os
import re
import sys

# Natural keys — computable from the interaction itself, identical on every
# run, so a disposition in AI.CONFLICTS.md can be matched to its interaction
# by a script rather than by a human. This is why they are not sequential.
KEY_MODEL = "{model}"
KEY_METHOD = "{model}::{name}"
KEY_FIELD = "{model}::field:{name}"
KEY_VIEW = "view::{target}"
# Controllers are their own namespace. Their methods must NOT be filed under
# the last-seen MODEL: a block lists CONTROLLER: after its MODEL sections, and
# treating the line as a mere section terminator attributed every controller
# method to an unrelated model. Found on the Imperial_temp repo, where three
# addons override portal.CustomerPortal._prepare_home_portal_values and it was
# reported as res.users::_prepare_home_portal_values — a real interaction under
# a wrong key, which is worse than missing it, since dispositions are keyed.
# Keyed by METHOD NAME, with the extended base shown as context rather than
# used as the key. Measured on two real repos: the same Odoo class appears as
# "portal.CustomerPortal", "CustomerPortal" and via the subclass
# "project.ProjectCustomerPortal", so keying on the base splits one real
# interaction into three. Name-level grouping produced exactly ONE group on
# each repo — no noise — and recovers the three-way chain that base-keying
# misses. Controllers extend each other, so sharing a method name is the
# reliable signal; which base each addon names is context for the reader.
KEY_CTRL_METHOD = "controller::{name}"

# Lines that end a MODEL's sub-section inside a block.
SECTION = re.compile(
    r"^\s*(MODEL|VIEWS|ASSETS|CRON|CONTROLLER|SECURITY|COMMANDS|DEPENDS"
    r"|EXTERNAL_DEPS|UNEXTRACTED|INVENTORY|END_INVENTORY|README|STATUS"
    r"|UPDATED|CREATED|PURPOSE|IMPACT|TYPE|APP)\b")


def parse_models(body):
    """Return {model: {"kind", "fields", "methods", "views"}} for one block.

    Handles both inventory dialects:
      generated   MODEL: res.users (_inherit, concrete)
                    FIELDS: a, b
                    METHODS:
                      [OVR] def name(self)
                  VIEWS: file
                    - | qweb | id | inherit_id: target
      legacy      MODEL: res.users  _inherit
                    FIELDS:
                      a  (Boolean, compute)
                    METHODS:
                      name()  [OVR]  depends on x
                  VIEWS:
                    file
                      qweb  id   inherit: target  priority=56
    """
    models = {}
    cur = None
    mode = None          # "fields" | "methods" | None
    for line in body.split("\n"):
        m = re.match(r"^\s*MODEL:\s*(\S+)(.*)$", line)
        if m:
            name, rest = m.group(1), m.group(2)
            kind = "_name" if "_name" in rest else (
                "_inherit" if "_inherit" in rest else "?")
            cur = models.setdefault(name, {"kind": kind, "fields": set(),
                                           "methods": {}, "views": set()})
            # a later _name beats an earlier "?" — owning is the stronger fact
            if kind != "?":
                cur["kind"] = kind
            mode = None
            continue

        mc = re.match(r"^\s*CONTROLLER:\s*(\S+)(.*)$", line)
        if mc:
            # prefer the EXTENDED base — that is what two addons actually
            # share; the subclass name is per-addon and would never collide.
            ext = re.search(r"extends\s+([\w.]+)", mc.group(2))
            base = ext.group(1) if ext else mc.group(1)
            cur = models.setdefault("controller:" + base,
                                    {"kind": "extends", "fields": set(),
                                     "methods": {}, "views": set()})
            mode = None
            continue

        # view inheritance targets are block-level, not per-model
        vt = re.search(r"inherit(?:_id)?:\s*([\w.]+)", line)
        if vt:
            models.setdefault("__views__", {"kind": "?", "fields": set(),
                                            "methods": {}, "views": set()})
            models["__views__"]["views"].add(vt.group(1))

        if cur is None:
            continue

        mf = re.match(r"^\s*FIELDS:\s*(.*)$", line)
        if mf:
            inline = mf.group(1).strip()
            if inline:                                    # generated dialect
                cur["fields"] |= {f.strip() for f in inline.split(",")
                                  if f.strip()}
                mode = None
            else:                                          # legacy dialect
                mode = "fields"
            continue
        if re.match(r"^\s*METHODS:\s*$", line):
            mode = "methods"
            continue
        if SECTION.match(line):
            mode = None
            continue

        if mode == "fields" and line.strip():
            cur["fields"].add(line.strip().split()[0].rstrip(","))
        elif mode == "methods" and line.strip():
            tag = ("[OVR]" if "[OVR]" in line else
                   "[NEW]" if "[NEW]" in line else None)
            nm = re.search(r"def\s+(\w+)", line) or re.search(r"(\w+)\s*\(",
                                                              line)
            if nm and tag:
                # [NEW] wins: owning a name is stronger evidence than
                # extending it, and one addon may list both dialects.
                prev = cur["methods"].get(nm.group(1))
                cur["methods"][nm.group(1)] = "[NEW]" if "[NEW]" in (
                    tag, prev or "") else tag
    return models


def parse_addons(text):
    """{addon: models}. Generated INVENTORY section wins over legacy lines."""
    out = {}
    for block in re.split(r"^(?=>>ADDON: )", text, flags=re.M)[1:]:
        name = re.match(r">>ADDON:\s*(\S+)", block).group(1)
        m = re.search(r"^\s*INVENTORY:.*?$(.*?)^\s*END_INVENTORY:", block,
                      re.M | re.S)
        out[name] = parse_models(m.group(1) if m else block)
    return out


def derive(addons):
    """Group every shared name N-way. Returns {(kind, key): {facts}}."""
    seen = collections.defaultdict(lambda: collections.defaultdict(dict))
    for addon, models in addons.items():
        for model, d in models.items():
            if model == "__views__":
                for t in d["views"]:
                    seen["VIEW"][KEY_VIEW.format(target=t)][addon] = "inherits"
                continue
            if model.startswith("controller:"):
                base = model.split(":", 1)[1]
                for meth, tag in d["methods"].items():
                    seen["CONTROLLER"][KEY_CTRL_METHOD.format(name=meth)][
                        addon] = f"{tag} on {base}"
                continue
            seen["MODEL"][KEY_MODEL.format(model=model)][addon] = d["kind"]
            for f in d["fields"]:
                seen["FIELD"][KEY_FIELD.format(model=model, name=f)][addon] = \
                    d["kind"]
            for meth, tag in d["methods"].items():
                seen["METHOD"][KEY_METHOD.format(model=model, name=meth)][
                    addon] = tag
    return {(k, key): parts
            for k, group in seen.items()
            for key, parts in group.items() if len(parts) > 1}


def _canary():
    """Load AI.canary.py — shared hash and disposition-parsing definitions.

    Same pattern AI.gen_summaries.py uses, and for the same reason: the two
    scripts must never disagree on what a SOURCE-HASH is. Loading happens at
    CALL time, not import time, so canary importing this module and this
    module importing canary cannot deadlock.
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "AI.canary.py")
    spec = importlib.util.spec_from_file_location("ai_canary", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Order is deliberate: what needs a decision comes first, what will come back
# next, then what is settled. History last.
GROUPS = (
    ("UNDISPOSED", "\u26a0\ufe0f Undisposed — needs a decision",
     "Nobody has recorded what these mean. They are FACTS, not defects: "
     "addons meeting on a name is often correct architecture."),
    ("Deferred", "\u23f3 Deferred — revisit at a named moment", None),
    ("Accepted", "\u2705 Accepted — no action needed", None),
    ("Fixed", "\u2714\ufe0f Fixed — resolved", None),
    ("Withdrawn", "\u21a9\ufe0f Withdrawn — mis-derived", None),
)


def render(addons, inter, disp, stamp):
    """Merge derived interactions with their dispositions into markdown."""
    undisposed = sum(1 for (_k, key) in inter if key not in disp)
    today = datetime.date.today().isoformat()
    out = ["# Addon \u2194 Addon Conflict Register",
           f"# {len(inter)} interaction{'' if len(inter) == 1 else 's'} "
           f"\u00b7 {undisposed} undisposed \u00b7 {len(addons)} "
           f"addon{'' if len(addons) == 1 else 's'} \u00b7 Updated: {today}",
           f"# SOURCE-HASH: addons={stamp}" if stamp else
           "# SOURCE-HASH: unavailable",
           "",
           "DERIVED FILE — regenerated by AI.gen_conflicts.py --write, never "
           "authoritative and",
           "never the place to write a decision. Decisions live in "
           "AI.CONFLICTS.md.",
           "What INTERACTS is derived from the >>ADDON: blocks; whether it "
           "MATTERS is a",
           "judgment recorded there, and this file only displays the two "
           "together.",
           ""]

    buckets = collections.defaultdict(list)
    for (kind, key), parts in sorted(inter.items()):
        d = disp.get(key)
        buckets["UNDISPOSED" if d is None else (d["status"] or "UNDISPOSED")
                 ].append((kind, key, parts, d))

    for status, title, note in GROUPS:
        rows = buckets.pop(status, [])
        if not rows:
            continue
        out.append(f"## {title} ({len(rows)})")
        if note:
            out.append("")
            out.append(note)
        for kind, key, parts, d in rows:
            out.append("")
            out.append(f"### {key}")
            out.append(f"*{kind}* — {len(parts)} addons: "
                       + ", ".join(f"{a} `{parts[a]}`" for a in sorted(parts)))
            if d:
                if d["reason"]:
                    out.append("")
                    out.append(d["reason"])
                if d["evidence"]:
                    out.append("")
                    out.append(f"**Evidence:** {d['evidence']}")
                if d["decided"]:
                    out.append("")
                    out.append(f"*Decided {d['decided']}.*")
        out.append("")

    # any status the canary would flag as invalid still gets shown, rather
    # than silently vanishing from the human view
    for status, rows in sorted(buckets.items()):
        out.append(f"## \u2049\ufe0f Unrecognized status: {status} ({len(rows)})")
        for kind, key, parts, _d in rows:
            out.append(f"- {key} ({len(parts)} addons)")
        out.append("")

    if not inter:
        out.append("No cross-addon interactions derived.")
        out.append("")
    return "\n".join(out)


def write_register(root, addons, inter):
    canary = _canary()
    disp = canary.parse_conflicts(canary.CONFLICTS_AI)
    try:
        stamp = canary.addons_source_hash(canary.ADDONS_AI)
    except Exception:
        stamp = None
    path = os.path.join(root, "DOC.CONFLICTS.Addons.md")
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(render(addons, inter, disp, stamp))
        os.replace(tmp, path)   # atomic — never a truncated register
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    print(f"\nwrote DOC.CONFLICTS.Addons.md "
          f"({len(inter)} interaction(s), "
          f"{sum(1 for (_k, key) in inter if key not in disp)} undisposed)")


def main(argv):
    write = "--write" in argv
    argv = [a for a in argv if a != "--write"]
    path = argv[1] if len(argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "AI.CUSTOM.md")
    if not os.path.exists(path):
        print(f"⛔ not found: {path}")
        return 1
    with open(path, encoding="utf-8") as fh:
        addons = parse_addons(fh.read())
    if not addons:
        print(f"no >>ADDON: blocks in {os.path.basename(path)}")
        return 0

    inter = derive(addons)
    models = {m for d in addons.values() for m in d if m != "__views__"}
    print(f"addons: {len(addons)}   models touched: {len(models)}   "
          f"interactions: {len(inter)}")

    if not inter:
        print("\nNo cross-addon interactions derived.")
        if write:
            write_register(os.path.dirname(os.path.abspath(__file__)),
                           addons, inter)
        return 0

    # METHOD and FIELD are the specific facts; MODEL is their parent and is
    # reported last so the specific findings are read first.
    for kind in ("METHOD", "CONTROLLER", "FIELD", "VIEW", "MODEL"):
        rows = sorted((k, p) for (t, k), p in inter.items() if t == kind)
        if not rows:
            continue
        print(f"\n── {kind} — shared by more than one addon ({len(rows)})")
        for key, parts in rows:
            print(f"  {key}   [{len(parts)} addons]")
            for addon in sorted(parts):
                print(f"      {parts[addon]:<38} {addon}")
    print("\nFACTS ONLY — no severity is implied and none of the above is "
          "asserted to be a defect.\nDisposition of each interaction belongs "
          "in AI.CONFLICTS.md.")
    if write:
        write_register(os.path.dirname(os.path.abspath(__file__)),
                       addons, inter)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
