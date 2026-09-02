#!/usr/bin/env python3
"""
AI.gen_inventory.py — mechanical inventory extractor + drift checker

An >>ADDON: block in AI.CUSTOM.md splits into judgment fields (PURPOSE,
IMPACT, TYPE, APP, STATUS, UPDATED — AI/human work) and INVENTORY fields
(DEPENDS, DEPENDS_CUSTOM, EXTERNAL_DEPS, MODEL/FIELDS/METHODS/CONSTRAINT,
VIEWS, ASSETS, CRON — facts already present in the addon's code). This
script extracts the inventory mechanically from each addon's code
(__manifest__.py, Python ast, XML records) and, with --check, DIFFS it
against the hand-written block — hand-copied inventory drifts; extracted
inventory cannot.

CANARY CHECK 18: AI.canary.py runs this script as a subprocess (--check) and
adopts its indented ⚠️ findings VERBATIM as the INVENTORY DRIFT finding
(each prefixed with its addon name, replacing the "== addon" group
headers), so the two can never disagree; findings are now under the canary covenant
that every finding is actionable. The ◻︎ honesty notes remain advisory in
both modes and are never adopted as findings. The script stays fully
usable standalone — same output, same exit codes.

Usage:
  python3 AI/AI.gen_inventory.py [addon ...]           print extracted inventory
                                                    (all documented-or-on-disk
                                                    addons, or just the named)
  python3 AI/AI.gen_inventory.py --check [addon ...]   diff each >>ADDON: block's
                                                    inventory against the code
  python3 AI/AI.gen_inventory.py --write [addon ...]   Stage 2: write the
                                                    inventory portion into each
                                                    block — header DEPENDS/
                                                    DEPENDS_CUSTOM/EXTERNAL_DEPS
                                                    lines rewritten in place
                                                    (js: tails preserved,
                                                    hand-owned), everything else
                                                    in a marker-delimited
                                                    'INVENTORY:'…'END_INVENTORY:'
                                                    section (machine-owned — do
                                                    not hand-edit; UPDATED dates
                                                    are judgment and never
                                                    touched). Idempotent;
                                                    verify with --check after.
  --root PATH   repo root to operate on. Default: this script's own folder
                (self-locating, like AI.canary.py).
  --no-tags     skip the [NEW]/[OVR] heuristic (it greps /home/odoo/src/odoo
                and /home/odoo/src/enterprise for standard "def <name>("
                definitions — slow, heuristic, on-platform only)

Exit status:
  --check: 1 when at least one drift finding was printed, else 0.
  extract mode and --write: always 0.
  2 (any mode): unusable invocation or setup — nothing was checked or
    written: --check combined with --write, no AI.CUSTOM.md under --root,
    or a block-splitter disagreement with AI.canary.parse_addons.
    AI.canary.py's check 18 surfaces any exit other than 0/1 as
    INVENTORY CHECKER UNAVAILABLE.

Honesty rules (load-bearing — an extraction blind spot must be visible):
  · What cannot be extracted is REPORTED as unchecked, never silently
    skipped: dynamically built field declarations, SECURITY/COMMANDS
    sections, js EXTERNAL_DEPS, prose descriptors on ASSETS lines.
  · The [NEW]/[OVR] verdicts are a grep heuristic ("does a standard class
    define a method of this name anywhere") — mixins and monkey-patches are
    known false-positive sources; TAG findings say so.

Delegation: the documented-addon set comes from AI.canary.py's
parse_addons (imported from this script's own folder) so the two scripts
can never disagree on what counts as a block; the addon-folder rule
mirrors AI.canary.py's find_addon_folders (one-level glob,
studio_customization excluded) with a --root parameter added.
"""

import argparse
import ast
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent   # AI/ subfolder
REPO_ROOT  = SCRIPT_DIR.parent                 # actual repo root

# Standard source trees for the [NEW]/[OVR] heuristic (on-platform paths;
# both optional — absent trees just disable the heuristic, reported once).
STD_TREES = (Path("/home/odoo/src/odoo"), Path("/home/odoo/src/enterprise"))

# Block sections that exist in (older) hand-written blocks but are OUTSIDE
# the Stage 1 inventory field list — parsed only far enough to skip them,
# and named in the honesty note.
IGNORED_SECTIONS = ("SECURITY", "COMMANDS")


# ─── shared helpers ──────────────────────────────────────────────────────────

def find_addon_folders(root):
    """Names of TOP-LEVEL subdirectories containing __manifest__.py —
    mirrors AI.canary.py's find_addon_folders (one-level glob, nested
    layouts invisible, studio_customization excluded by name) with the
    root as a parameter. Change the two together."""
    return sorted(
        p.parent.name
        for p in root.glob("*/__manifest__.py")
        if p.parent.name != "studio_customization"
    )


def load_canary():
    """AI.canary.py as a module, from THIS SCRIPT's folder (not --root:
    the canary ships with the template scripts, the root under test may
    predate it). None if absent/unloadable — reported, then the local
    block splitter's name set is used alone."""
    path = SCRIPT_DIR / "AI.canary.py"
    if not path.exists():
        return None
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("ai_canary", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        return None


# ─── extraction: manifest ────────────────────────────────────────────────────

def parse_manifest(root, addon):
    """The addon's __manifest__.py as a dict (literal_eval), or None."""
    try:
        return ast.literal_eval((root / addon / "__manifest__.py")
                                .read_text(encoding="utf-8"))
    except Exception:
        return None


def split_depends(root, manifest):
    """(standard_depends, custom_depends) — custom = a same-named addon
    folder exists at the root (the DEPENDS_CUSTOM definition)."""
    on_disk = set(find_addon_folders(root))
    depends = [d for d in manifest.get("depends", []) if isinstance(d, str)]
    return ([d for d in depends if d not in on_disk],
            [d for d in depends if d in on_disk])


def manifest_assets(root, addon, manifest, notes):
    """Sorted repo-relative asset file paths from the manifest 'assets' dict,
    glob entries expanded against the filesystem. Non-string directives
    (('remove', …) etc.) and entries matching no file are reported in notes,
    not guessed at."""
    files = set()
    for bundle, entries in (manifest.get("assets") or {}).items():
        if not isinstance(entries, (list, tuple)):
            notes.append(f"assets bundle {bundle!r} is not a list — not extracted")
            continue
        for entry in entries:
            if not isinstance(entry, str):
                notes.append(f"assets: non-string directive {entry!r} in "
                             f"{bundle} — not extracted")
                continue
            try:
                # standard manifests sometimes write '/module/static/…' —
                # same meaning, addons-path-relative; normalize the slash
                matched = [p for p in root.glob(entry.lstrip("/"))
                           if p.is_file()]
            except (NotImplementedError, ValueError) as e:
                notes.append(f"assets: entry {entry!r} in {bundle} is not "
                             f"globbable ({e}) — not extracted")
                continue
            if not matched:
                notes.append(f"assets: entry {entry!r} in {bundle} matched no "
                             f"file under the repo root — not extracted "
                             f"(a reference into another addon, or dead)")
            files.update(str(p.relative_to(root)) for p in matched)
    return sorted(files)


# ─── extraction: Python (models + controllers) ──────────────────────────────

def _base_names(cls):
    """Dotted names of a ClassDef's bases, e.g. 'models.Model',
    'portal.CustomerPortal'."""
    names = []
    for base in cls.bases:
        try:
            names.append(ast.unparse(base))
        except Exception:
            pass
    return names


def _const_str(node):
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _signature(fn):
    """'name(a, b, *args, **kw)' from a FunctionDef — names only, defaults
    elided (the blocks document signatures, not default values)."""
    a = fn.args
    parts = [arg.arg for arg in a.posonlyargs + a.args]
    if a.vararg:
        parts.append("*" + a.vararg.arg)
    parts += [arg.arg for arg in a.kwonlyargs]
    if a.kwarg:
        parts.append("**" + a.kwarg.arg)
    return f"{fn.name}({', '.join(parts)})"


def _route_of(fn):
    """Route info from an @http.route decorator: (paths, kwargs_text) or
    None. paths = list of str route paths."""
    for dec in fn.decorator_list:
        call = dec if isinstance(dec, ast.Call) else None
        target = call.func if call else dec
        name = (target.attr if isinstance(target, ast.Attribute)
                else target.id if isinstance(target, ast.Name) else None)
        if name != "route":
            continue
        paths, extras = [], []
        if call:
            if call.args:
                first = call.args[0]
                if _const_str(first):
                    paths = [first.value]
                elif isinstance(first, (ast.List, ast.Tuple)):
                    paths = [e.value for e in first.elts if _const_str(e)]
            for kw in call.keywords:
                if kw.arg in ("type", "auth", "methods"):
                    try:
                        extras.append(f"{kw.arg}={ast.unparse(kw.value)}")
                    except Exception:
                        pass
        return (paths, ", ".join(extras))
    return None


def _constraint_type(definition):
    d = (definition or "").strip().lower()
    for prefix, ctype in (("unique", "UNIQUE"), ("check", "CHECK"),
                          ("exclude", "EXCLUDE")):
        if d.startswith(prefix):
            return ctype
    return "SQL"


def extract_python(root, addon, notes):
    """(models, controllers) from every non-test .py file.
    models: {model_name: {kind, flavor, fields{name}, methods{name: {sig,
    route}}, constraints{name: type}}}
    controllers: {ClassName: {extends, methods{name: {sig, route}}}}
    Test files (any path segment 'tests') are excluded — blocks do not
    inventory test classes."""
    models, controllers = {}, {}
    for py in sorted((root / addon).rglob("*.py")):
        rel = py.relative_to(root / addon)
        if "tests" in rel.parts:
            continue
        try:
            src = py.read_text(encoding="utf-8")
            tree = ast.parse(src)
        except Exception as e:
            notes.append(f"{rel}: unparsable Python ({e.__class__.__name__}) "
                         f"— not extracted")
            continue
        for cls in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
            _extract_class(cls, src, rel, models, controllers, notes)
    return models, controllers


def _extract_class(cls, src, rel, models, controllers, notes):
    bases = _base_names(cls)
    name_attr, inherit_attrs = None, []
    fields, methods, constraints = {}, {}, {}
    dynamic = False
    for stmt in cls.body:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 \
                and isinstance(stmt.targets[0], ast.Name):
            tgt, val = stmt.targets[0].id, stmt.value
            if tgt == "_name" and _const_str(val):
                name_attr = val.value
            elif tgt == "_inherit":
                if _const_str(val):
                    inherit_attrs = [val.value]
                elif isinstance(val, ast.List):
                    inherit_attrs = [e.value for e in val.elts if _const_str(e)]
            elif tgt == "_sql_constraints" and isinstance(val, (ast.List, ast.Tuple)):
                for elt in val.elts:
                    if isinstance(elt, (ast.List, ast.Tuple)) and len(elt.elts) >= 2:
                        cname, cdef = _const_str(elt.elts[0]), _const_str(elt.elts[1])
                        if cname:
                            constraints[cname] = _constraint_type(cdef)
            elif isinstance(val, ast.Call) and isinstance(val.func, ast.Attribute):
                func = val.func
                if isinstance(func.value, ast.Name) and func.value.id == "fields":
                    fields[tgt] = func.attr  # e.g. Many2one, Boolean
                elif func.attr == "Constraint":  # Odoo 19 models.Constraint
                    cdef = _const_str(val.args[0]) if val.args else None
                    constraints[tgt] = _constraint_type(cdef)
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # async defs included: rare in Odoo addons but legal — without
            # this they were invisible both ways (an undocumented async
            # method never flagged; a documented one flagged as missing)
            methods[stmt.name] = {"sig": _signature(stmt), "route": _route_of(stmt)}
        elif isinstance(stmt, (ast.For, ast.While, ast.If, ast.With)):
            try:
                if "fields." in ast.unparse(stmt):
                    dynamic = True
            except Exception:
                dynamic = True

    is_model = bool(name_attr or inherit_attrs) and any(
        b.split(".")[-1] in ("Model", "TransientModel", "AbstractModel")
        for b in bases)
    has_routes = any(m["route"] for m in methods.values())

    if is_model:
        flavor = "concrete"
        if any(b.endswith("TransientModel") for b in bases):
            flavor = "transient"
        elif any(b.endswith("AbstractModel") for b in bases):
            flavor = "abstract"
        kind = "_name" if name_attr else "_inherit"
        model_names = [name_attr] if name_attr else inherit_attrs
        for mname in model_names:
            entry = models.setdefault(mname, {
                "kind": kind, "flavor": flavor, "fields": {},
                "methods": {}, "constraints": {}})
            entry["fields"].update(fields)
            entry["methods"].update(methods)
            entry["constraints"].update(constraints)
        if dynamic:
            notes.append(f"{rel}: class {cls.name} builds fields inside a "
                         f"loop/branch — those declarations are NOT extracted")
        if len(model_names) > 1:
            notes.append(f"{rel}: class {cls.name} inherits multiple models "
                         f"({', '.join(model_names)}) — members attributed "
                         f"to each")
    elif has_routes or any(re.search(r"(Controller|Portal|Home)\b", b) for b in bases):
        controllers[cls.name] = {
            "extends": ", ".join(bases) or "(no base)",
            "methods": methods,
        }
    elif fields or (name_attr or inherit_attrs):
        notes.append(f"{rel}: class {cls.name} looks model-ish but its bases "
                     f"({', '.join(bases) or 'none'}) were not recognized — "
                     f"not extracted")


# ─── extraction: XML (views + crons) ─────────────────────────────────────────

# Recognized view-arch root tags ("list" is the 18.0+ name of the former
# tree view — both kept, old data files still say tree).
VIEW_ROOT_TAGS = {"list", "tree", "form", "search", "kanban", "calendar",
                  "pivot", "graph", "gantt", "grid", "map", "activity",
                  "cohort", "hierarchy", "qweb"}

def extract_xml(root, addon, manifest, notes):
    """(views, crons) from the manifest's data files.
    views: {relpath: [ {model, vtype, xml_id, inherit} ]} — ir.ui.view
    records and <template> elements only.
    crons: {xml_id: schedule_text}."""
    views, crons = {}, {}
    for entry in manifest.get("data", []) or []:
        if not isinstance(entry, str) or not entry.endswith(".xml"):
            continue
        path = root / addon / entry
        if not path.exists():
            notes.append(f"manifest data file {entry!r} not found on disk")
            continue
        try:
            xml_root = ET.parse(path).getroot()
        except ET.ParseError as e:
            notes.append(f"{entry}: unparsable XML ({e}) — not extracted")
            continue
        recs = []
        for rec in xml_root.iter("record"):
            model = rec.get("model", "")
            fields = {f.get("name"): f for f in rec.findall("field")}
            if model == "ir.ui.view":
                vtype = None
                if "type" in fields and (fields["type"].text or "").strip():
                    vtype = fields["type"].text.strip()
                elif "arch" in fields:
                    arch_children = list(fields["arch"])
                    # an INHERITED view's arch starts with positioning
                    # elements (xpath/field/button/…), not a view root —
                    # only a recognized root tag names the type; otherwise
                    # the type lives on the parent view and is not
                    # locally extractable
                    if arch_children and arch_children[0].tag in VIEW_ROOT_TAGS:
                        vtype = arch_children[0].tag
                inherit = fields.get("inherit_id")
                recs.append({
                    "model": (fields.get("model").text or "").strip()
                             if fields.get("model") is not None else "",
                    "vtype": vtype or "?",
                    "xml_id": rec.get("id", "?"),
                    "inherit": inherit.get("ref") if inherit is not None else None,
                })
            elif model == "ir.cron":
                num = fields.get("interval_number")
                unit = fields.get("interval_type")
                sched = "schedule not extracted"
                if num is not None and unit is not None:
                    sched = (f"every {(num.text or '?').strip()} "
                             f"{(unit.text or '?').strip()}")
                crons[rec.get("id", "?")] = sched
        for tmpl in xml_root.iter("template"):
            recs.append({
                "model": "", "vtype": "qweb", "xml_id": tmpl.get("id", "?"),
                "inherit": tmpl.get("inherit_id"),
            })
        if recs:
            views[entry] = recs
    return views, crons


def extract_addon(root, addon):
    """Full extracted inventory for one addon, or None without a manifest."""
    manifest = parse_manifest(root, addon)
    if manifest is None:
        return None
    notes = []
    std_dep, custom_dep = split_depends(root, manifest)
    ext = manifest.get("external_dependencies") or {}
    models, controllers = extract_python(root, addon, notes)
    assets = manifest_assets(root, addon, manifest, notes)
    views, crons = extract_xml(root, addon, manifest, notes)
    return {
        "depends": std_dep,
        "depends_custom": custom_dep,
        "external_python": [d for d in ext.get("python", []) if isinstance(d, str)],
        "models": models,
        "controllers": controllers,
        "views": views,
        "assets": assets,
        "crons": crons,
        "notes": notes,
    }


# ─── block parsing (tolerant: current template format AND older spellings) ──

BLOCK_START = re.compile(r'^>>ADDON:\s+(\S+)')  # mirrors AI.canary.parse_addons
# A section/field line: optional indent, ALL-CAPS keyword, optional
# parenthetical (e.g. "STATIC (web.assets_backend — …):"), colon.
KEYWORD_LINE = re.compile(r'^(\s*)([A-Z_]+)(?:\s*\([^)]*\))?\s*:\s*(.*?)\s*$')
JUDGMENT_FIELDS = ("README", "STATUS", "UPDATED", "PURPOSE", "IMPACT",
                   "TYPE", "APP")

# ── block completeness ───────────────────────────────────────────────────
# A generated INVENTORY section always emits the four core sections below,
# using EMPTY_MARKER when the addon has nothing for it. Emitting them always
# makes ABSENCE MEANINGFUL — a block that genuinely has no models is
# distinguishable from a stale block written before the section existed:
#   "MODEL: (none)"  -> current-format block, addon genuinely has none
#   no MODEL line    -> STALE-FORMAT block. AI.canary.py reports it; regenerate.
EMPTY_MARKER = "(none)"
REQUIRED_INVENTORY_FIELDS = (
    "MODEL", "CONTROLLER", "VIEWS", "ASSETS",
)


def split_blocks(md_path):
    """{addon_name: raw_block_text} from AI.CUSTOM.md — same block-start
    line definition as AI.canary.parse_addons (cross-checked in main())."""
    blocks, current, buf = {}, None, []
    for line in md_path.read_text(encoding="utf-8").splitlines():
        m = BLOCK_START.match(line)
        if m:
            if current:
                blocks[current] = "\n".join(buf)
            current, buf = m.group(1), []
            continue
        if current is not None:
            buf.append(line)
    if current:
        blocks[current] = "\n".join(buf)
    return blocks


def _method_claim(line):
    """(name, tag) from a METHODS content line — the def-name when a 'def'
    is present (current template), else the first identifier followed by
    '(' (older spelling). tag: 'NEW' | 'OVR' | None."""
    m = re.search(r'\bdef\s+([A-Za-z_]\w*)\s*\(', line)
    if not m:
        m = re.search(r'([A-Za-z_]\w*)\s*\(', line)
    if not m:
        return None, None
    tag = "NEW" if "[NEW]" in line else "OVR" if "[OVR]" in line else None
    return m.group(1), tag


def parse_block_inventory(text):
    """Inventory CLAIMS from one block's raw text. Tolerant of both the
    current template format and older hand-written spellings (STATIC for
    ASSETS, indented FIELDS lists, CONTROLLER sections). Whatever a claim
    line's tail says beyond the identifying token is prose — never parsed."""
    claims = {
        "depends": None, "depends_custom": None, "external_python": None,
        "models": {},        # name → {kindtext, fields[], methods{n: tag}, constraints{n}}
        "controllers": {},   # name → {methods{n: tag}}
        "view_files": [],
        "asset_files": [],
        "crons": [],
        "ignored_sections": set(),
    }
    section = None   # None | dict (model/controller entry) | 'VIEWS' | 'ASSETS' | 'IGNORED' | 'CRON'
    sub = None       # None | 'FIELDS' | 'METHODS' within a model/controller

    def xml_tokens(s):
        return re.findall(r'[\w./-]+\.xml\b', s)

    def asset_tokens(s):
        return re.findall(r'[\w./-]+\.(?:js|xml|css|scss)\b', s)

    for line in text.splitlines():
        km = KEYWORD_LINE.match(line)
        kw = km.group(2) if km else None
        rest = km.group(3) if km else ""

        # A field declared empty ("<FIELD>: (none)") is skipped so no
        # downstream branch parses "(none)" as a value (MODEL would otherwise
        # register a model literally named "(none)"). The completeness check
        # distinguishes "declared empty" from "field missing" by the field
        # NAME being present in the block text, so nothing is recorded here.
        if kw and rest.strip() == EMPTY_MARKER:
            section, sub = None, None
            continue

        if kw in JUDGMENT_FIELDS:
            section, sub = None, None
        elif kw == "DEPENDS":
            claims["depends"] = [d.strip() for d in rest.split(",") if d.strip()]
            section, sub = None, None
        elif kw == "DEPENDS_CUSTOM":
            claims["depends_custom"] = [d.strip() for d in rest.split(",") if d.strip()]
            section, sub = None, None
        elif kw == "EXTERNAL_DEPS":
            m = re.search(r'python:\s*\[([^\]]*)\]', rest)
            claims["external_python"] = ([d.strip() for d in m.group(1).split(",")
                                          if d.strip()] if m else [])
            section, sub = None, None
        elif kw == "MODEL":
            name = rest.split()[0].rstrip(",") if rest.split() else "?"
            section = claims["models"].setdefault(name, {
                "kindtext": rest, "fields": [], "methods": {}, "constraints": []})
            sub = None
        elif kw == "CONTROLLER":
            name = rest.split()[0].rstrip(",") if rest.split() else "?"
            section = claims["controllers"].setdefault(name, {"methods": {}})
            sub = "METHODS"  # older blocks sometimes omit the METHODS: subheader
        elif kw == "FIELDS" and isinstance(section, dict):
            if rest:
                section["fields"] += [f.strip() for f in rest.split(",") if f.strip()]
                sub = None
            else:
                sub = "FIELDS"
        elif kw == "METHODS" and isinstance(section, dict):
            sub = "METHODS"
        elif kw == "CONSTRAINT" and isinstance(section, dict):
            m = re.match(r'([\w.]+)', rest)
            if m:
                section["constraints"].append(m.group(1))
        elif kw == "VIEWS":
            section, sub = "VIEWS", None
            if rest:
                claims["view_files"] += xml_tokens(rest)
        # STATIC and TESTS are older hand-written spellings of ASSETS
        # (older blocks used them for asset files) — treated identically
        elif kw in ("ASSETS", "STATIC", "TESTS"):
            section, sub = "ASSETS", None
            if rest:
                claims["asset_files"] += asset_tokens(rest)
        elif kw == "CRON":
            section, sub = "CRON", None
            m = re.match(r'([\w.]+)', rest)
            if m:
                claims["crons"].append(m.group(1))
        elif kw in ("INVENTORY", "END_INVENTORY", "UNEXTRACTED"):
            # --write's section markers and honesty notes: transparent to
            # the parser — the lines between the markers are ordinary
            # inventory keywords, parsed exactly like hand-written ones
            section, sub = None, None
        elif kw in IGNORED_SECTIONS:
            claims["ignored_sections"].add(kw)
            section, sub = "IGNORED", None
        else:
            # content line — dispatch on the open section
            stripped = line.strip()
            if not stripped:
                continue
            if isinstance(section, dict):
                if sub == "FIELDS":
                    m = re.match(r'([A-Za-z_]\w*)\b', stripped)
                    if m:
                        section["fields"].append(m.group(1))
                elif sub == "METHODS":
                    name, tag = _method_claim(stripped)
                    if name:
                        section["methods"][name] = tag
            elif section == "VIEWS":
                claims["view_files"] += xml_tokens(stripped)
            elif section == "ASSETS":
                claims["asset_files"] += asset_tokens(stripped)
    return claims


# ─── [NEW]/[OVR] heuristic ───────────────────────────────────────────────────

def _grep_defs(names, dirs):
    """Subset of names defined as 'def <name>(' anywhere under dirs —
    ONE grep, patterns fed one per line via stdin (-f -) so the name
    count can never overflow a single argv element (ARG_MAX). None on
    grep failure."""
    if not names:
        return set()
    patterns = "\n".join(rf"def {re.escape(n)}\(" for n in sorted(names))
    try:
        # 600s worst-case budget per grep (called up to twice per run —
        # std + core). AI.canary.py's check-18 subprocess timeout must
        # exceed the sum plus extraction — change the two budgets together.
        out = subprocess.run(
            ["grep", "-rhoE", "--include=*.py", "--exclude-dir=.git",
             "-f", "-"] + [str(d) for d in dirs],
            input=patterns, capture_output=True, text=True,
            timeout=600).stdout
    except Exception:
        return None
    return set(re.findall(r"def (\w+)\(", out))


def build_tag_oracle(names, root, all_extracted):
    """The [NEW]/[OVR] heuristic's knowledge, or None when it cannot be
    built — either no standard tree is available or the def-grep failed
    (the caller's warning distinguishes the two causes):
      std:  names defined anywhere in /home/odoo/src/odoo + /enterprise —
            the oracle for methods on _inherit models and controllers
      core: names defined in the ORM framework itself (odoo/odoo — the
            odoo package, not addons) — the only names that can be [OVR]
            on a _name (brand-new) model; an addon-land name collision
            (some other module's action_confirm) is NOT an override there
      custom: {(model, method) → {addons defining it}} across ALL root
            addons — a method overriding a DEPENDS_CUSTOM base addon's
            method is [OVR] too, invisible to the standard-source grep.
            DIRECTION-AWARE: only defs in addons the current addon
            (transitively) depends on count — the base addon that others
            override is itself still [NEW]
      deps: {addon → transitive custom-dependency set}"""
    trees = [t for t in STD_TREES if t.is_dir()]
    if not trees:
        return None
    std = _grep_defs(names, trees)
    core_dir = STD_TREES[0] / "odoo"
    core = _grep_defs(names, [core_dir]) if core_dir.is_dir() else set()
    if std is None or core is None:
        return None
    custom = {}
    for addon, ext in all_extracted.items():
        for mname, m in ext["models"].items():
            for meth in m["methods"]:
                custom.setdefault((mname, meth), set()).add(addon)
    deps = {}
    for addon in all_extracted:
        closure, stack = set(), list(all_extracted[addon]["depends_custom"])
        while stack:
            d = stack.pop()
            if d in closure or d not in all_extracted:
                continue
            closure.add(d)
            stack += all_extracted[d]["depends_custom"]
        deps[addon] = closure
    return {"std": std, "core": core, "custom": custom, "deps": deps}


def expected_tag(oracle, addon, model_name, model_kind, name):
    """Heuristic verdict for one method. model_name/model_kind None for
    controller methods (full standard-tree scope applies)."""
    if model_kind == "_name":
        std_hit = name in oracle["core"]
    else:
        std_hit = name in oracle["std"]
    custom_hit = model_name is not None and bool(
        oracle["custom"].get((model_name, name), set())
        & oracle["deps"].get(addon, set()))
    return "OVR" if std_hit or custom_hit else "NEW"


# ─── check mode ──────────────────────────────────────────────────────────────

def compare_addon(addon, ext, claims, block_text, oracle):
    """Drift findings for one addon: list of one-line strings.
    Directions: 'block omits X' (code has it) / 'block lists X — not found
    in code' (claim gone stale)."""
    F = []

    # ── block completeness: every REQUIRED_INVENTORY_FIELDS section must be
    # PRESENT, even when empty (as "(none)"). A section that is simply absent
    # means the block was generated before that section existed, which is
    # indistinguishable from "this addon genuinely has no such surface" — so
    # a stale-format block silently reads as complete. Reported as drift on
    # purpose so it gets regenerated. Gated on the block actually having a
    # generated section: a purely hand-written legacy block is a different
    # concern and is not spammed with findings here.
    inv = re.search(r'^\s*INVENTORY:.*?(?=^\s*END_INVENTORY:|\Z)',
                    block_text, re.S | re.M)
    if inv:
        span = inv.group(0)
        missing = [f for f in REQUIRED_INVENTORY_FIELDS
                   if not re.search(rf'^\s*{f}\s*:', span, re.M)]
        if missing:
            F.append(f"INVENTORY: generated section is missing "
                     f"{', '.join(missing)} — the block predates "
                     f"{'these sections' if len(missing) > 1 else 'this section'}. "
                     f"An absent section is NOT the same as an empty one, so a "
                     f"stale-format block silently reads as complete. "
                     f"Fix: python3 AI/AI.gen_inventory.py --write {addon}")

    # DEPENDS / DEPENDS_CUSTOM — set compare, bucket-aware. A block with
    # no DEPENDS line at all (pre-template-format blocks) gets ONE
    # collapsed finding, not one per dependency.
    blk_dep = claims["depends"]
    blk_cust = claims["depends_custom"]
    if blk_dep is None and ext["depends"]:
        F.append(f"DEPENDS: block has no DEPENDS line — manifest standard "
                 f"depends: {', '.join(sorted(ext['depends']))}")
    if blk_cust is None and ext["depends_custom"]:
        F.append(f"DEPENDS: block has no DEPENDS_CUSTOM line — manifest "
                 f"depends on custom addon(s): "
                 f"{', '.join(sorted(ext['depends_custom']))}")
    blk_all = set(blk_dep or []) | set(blk_cust or [])
    code_all = set(ext["depends"]) | set(ext["depends_custom"])
    for d in sorted(code_all - blk_all):
        bucket = "DEPENDS_CUSTOM" if d in ext["depends_custom"] else "DEPENDS"
        if (blk_dep if bucket == "DEPENDS" else blk_cust) is None:
            continue  # covered by the collapsed finding above
        F.append(f"DEPENDS: manifest depends on '{d}' — missing from the "
                 f"block (belongs under {bucket})")
    for d in sorted(blk_all - code_all):
        F.append(f"DEPENDS: block lists '{d}' — not in the manifest depends")
    for d in sorted(set(blk_dep or []) & set(ext["depends_custom"])):
        F.append(f"DEPENDS: '{d}' is a custom addon (folder at the repo "
                 f"root) but listed under DEPENDS — move to DEPENDS_CUSTOM")
    for d in sorted(set(blk_cust or []) & set(ext["depends"])):
        F.append(f"DEPENDS: '{d}' listed under DEPENDS_CUSTOM but no such "
                 f"addon folder exists at the repo root")

    # EXTERNAL_DEPS (python only — js claims are unverifiable from the manifest)
    code_ext = set(ext["external_python"])
    blk_ext = set(claims["external_python"] or [])
    if claims["external_python"] is None and code_ext:
        F.append(f"EXTERNAL_DEPS: manifest declares python deps "
                 f"({', '.join(sorted(code_ext))}) — block has no "
                 f"EXTERNAL_DEPS line")
    else:
        for d in sorted(code_ext - blk_ext):
            F.append(f"EXTERNAL_DEPS: manifest declares python '{d}' — "
                     f"missing from the block")
        for d in sorted(blk_ext - code_ext):
            F.append(f"EXTERNAL_DEPS: block lists python '{d}' — not in "
                     f"the manifest")

    # MODELS + their members
    for mname in sorted(set(ext["models"]) - set(claims["models"])):
        F.append(f"MODEL: code defines {mname} "
                 f"({ext['models'][mname]['kind']}) — no MODEL entry in "
                 f"the block")
    for mname in sorted(set(claims["models"]) - set(ext["models"])):
        F.append(f"MODEL: block lists {mname} — not defined in the "
                 f"addon's Python")
    for mname in sorted(set(ext["models"]) & set(claims["models"])):
        cm, bm = ext["models"][mname], claims["models"][mname]
        if cm["kind"] not in bm["kindtext"] and \
                ("_name" in bm["kindtext"] or "_inherit" in bm["kindtext"]):
            F.append(f"MODEL {mname}: block says "
                     f"'{bm['kindtext'].strip()}', code uses {cm['kind']}")
        for f in sorted(set(cm["fields"]) - set(bm["fields"])):
            F.append(f"FIELDS {mname}: code defines '{f}' "
                     f"({cm['fields'][f]}) — missing from the block")
        for f in sorted(set(bm["fields"]) - set(cm["fields"])):
            F.append(f"FIELDS {mname}: block lists '{f}' — no such "
                     f"static field declaration in code")
        F += _method_drift(f"METHODS {mname}", cm["methods"],
                           bm["methods"], block_text)
        # Odoo 19 models.Constraint attributes are named '_foo' in Python but
        # the SQL constraint Odoo creates is named 'foo' (leading underscore
        # stripped) — a block may legitimately use either form, so compare
        # with underscores stripped on both sides (gate evidence run 2).
        code_c = {c.lstrip("_"): c for c in cm["constraints"]}
        block_c = {c.lstrip("_"): c for c in bm["constraints"]}
        for k in sorted(set(code_c) - set(block_c)):
            c = code_c[k]
            F.append(f"CONSTRAINT {mname}: code defines '{c}' "
                     f"({cm['constraints'][c]}) — missing from the block")
        for k in sorted(set(block_c) - set(code_c)):
            F.append(f"CONSTRAINT {mname}: block lists '{block_c[k]}' — "
                     f"not found in code")

    # CONTROLLERS
    for cname in sorted(set(ext["controllers"]) - set(claims["controllers"])):
        F.append(f"CONTROLLER: code defines class {cname} (extends "
                 f"{ext['controllers'][cname]['extends']}) — no CONTROLLER "
                 f"entry in the block")
    for cname in sorted(set(claims["controllers"]) - set(ext["controllers"])):
        F.append(f"CONTROLLER: block lists {cname} — no such class in code")
    for cname in sorted(set(ext["controllers"]) & set(claims["controllers"])):
        F += _method_drift(f"METHODS {cname}",
                           ext["controllers"][cname]["methods"],
                           claims["controllers"][cname]["methods"],
                           block_text)

    # VIEWS — file level both ways; record level code→block (mention check)
    code_files = set(ext["views"])
    blk_files = set(claims["view_files"])
    for f in sorted(code_files - blk_files):
        F.append(f"VIEWS: {f} contains view records — file not listed in "
                 f"the block")
    for f in sorted(blk_files - code_files):
        F.append(f"VIEWS: block lists {f} — not a view file of this addon "
                 f"(absent from the manifest data, or no view records in it)")
    for f in sorted(code_files & blk_files):
        for rec in ext["views"][f]:
            xml_id = rec["xml_id"]
            if xml_id != "?" and xml_id not in block_text:
                F.append(f"VIEWS {f}: record {xml_id} "
                         f"({rec['model'] or rec['vtype']}) — not mentioned "
                         f"in the block")

    # ASSETS — full-path mention both ways; bare basename accepted only
    # while unique among the addon's assets (two same-named files in
    # different folders must never compare as one). A block may spell a
    # path repo-relative (addon prefix included — the --write form) or
    # addon-relative (the hand-written form) — both accepted.
    code_paths = set(ext["assets"])
    base_counts = {}
    for a in code_paths:
        base_counts[Path(a).name] = base_counts.get(Path(a).name, 0) + 1
    for a in sorted(code_paths):
        variants = {a, a.split("/", 1)[1] if "/" in a else a}
        if any(v in block_text for v in variants):
            continue
        base = Path(a).name
        if base_counts[base] == 1 and base in block_text:
            continue  # legacy bare-filename mention — unambiguous here
        F.append(f"ASSETS: {a} is in a manifest asset bundle — not "
                 f"mentioned in the block")
    for claim in sorted(set(claims["asset_files"])):
        if "/" in claim:
            ok = any(p == claim or p.endswith("/" + claim)
                     for p in code_paths)
        else:
            ok = claim in base_counts
        if not ok:
            F.append(f"ASSETS: block mentions {claim} — not in any "
                     f"manifest asset bundle")

    # CRON
    for c in sorted(ext["crons"]):
        if c not in block_text and c.split(".")[-1] not in block_text:
            F.append(f"CRON: code defines ir.cron {c} ({ext['crons'][c]}) — "
                     f"missing from the block")
    for c in claims["crons"]:
        short = c.split(".")[-1]
        if short not in {k.split(".")[-1] for k in ext["crons"]}:
            F.append(f"CRON: block lists {c} — no such ir.cron record in "
                     f"the addon's data files")

    # TAGS — heuristic, clearly labeled
    if oracle is not None:
        for scope, mname, kind, cmethods, bmethods in _tagged_scopes(ext, claims):
            for name, tag in sorted(bmethods.items()):
                if not tag or name not in cmethods:
                    continue
                want = expected_tag(oracle, addon, mname, kind, name)
                if tag != want:
                    F.append(f"TAG {scope}: block tags {name}() [{tag}] — "
                             f"heuristic expects [{want}] (name-only def "
                             f"search over standard source + the other "
                             f"custom addons; mixins/monkey-patches can "
                             f"mislead it)")
    return F


def _tagged_scopes(ext, claims):
    for mname in set(ext["models"]) & set(claims["models"]):
        cm = ext["models"][mname]
        yield (mname, mname, cm["kind"], cm["methods"],
               claims["models"][mname]["methods"])
    for cname in set(ext["controllers"]) & set(claims["controllers"]):
        yield (cname, None, None, ext["controllers"][cname]["methods"],
               claims["controllers"][cname]["methods"])


def _method_drift(scope, code_methods, blk_methods, block_text):
    F = []
    for name in sorted(set(code_methods) - set(blk_methods)):
        F.append(f"{scope}: code defines {name}() — missing from the block")
    for name in sorted(set(blk_methods) - set(code_methods)):
        F.append(f"{scope}: block lists {name}() — no such method in code")
    # route drift: methods in both — at least ONE of the method's route
    # paths must appear in the block (a multi-path route is documented by
    # its primary path). Converter prefixes are normalized away on both
    # sides ('/x/<int:ticket_id>' matches a documented '/x/<ticket_id>').
    norm = lambda s: re.sub(r'<\w+(?:\([^)]*\))?:', '<', s)
    norm_block = norm(block_text)
    for name in sorted(set(code_methods) & set(blk_methods)):
        route = code_methods[name]["route"]
        if route and route[0]:
            if not any(norm(p) in norm_block for p in route[0]):
                F.append(f"{scope}: {name}() serves route {route[0][0]} — "
                         f"route not mentioned in the block")
    return F


# ─── extract-mode rendering ──────────────────────────────────────────────────

def render_extracted(addon, ext, oracle):
    out = [f">>ADDON: {addon}   (mechanically extracted inventory — "
           f"judgment fields NOT included)"]
    if ext["depends"]:
        out.append(f"  DEPENDS: {', '.join(ext['depends'])}")
    if ext["depends_custom"]:
        out.append(f"  DEPENDS_CUSTOM: {', '.join(ext['depends_custom'])}")
    if ext["external_python"]:
        out.append(f"  EXTERNAL_DEPS: python: [{', '.join(ext['external_python'])}]")
    out += _render_body(addon, ext, oracle)
    return "\n".join(out)


def _render_body(addon, ext, oracle):
    """The non-header inventory lines (MODEL/CONTROLLER/VIEWS/ASSETS/CRON
    plus UNEXTRACTED honesty notes) — shared by extract mode and --write."""
    out = []
    if not ext["models"]:
        out.append(f"  MODEL: {EMPTY_MARKER}")
    for mname, m in sorted(ext["models"].items()):
        out.append(f"  MODEL: {mname} ({m['kind']}, {m['flavor']})")
        if m["fields"]:
            out.append(f"    FIELDS: {', '.join(sorted(m['fields']))}")
        for cname, ctype in sorted(m["constraints"].items()):
            out.append(f"    CONSTRAINT: {cname} ({ctype})")
        if m["methods"]:
            out.append("    METHODS:")
            out += _render_methods(m["methods"], oracle, addon,
                                   mname, m["kind"])
    if not ext["controllers"]:
        out.append(f"  CONTROLLER: {EMPTY_MARKER}")
    for cname, c in sorted(ext["controllers"].items()):
        out.append(f"  CONTROLLER: {cname} (extends {c['extends']})")
        if c["methods"]:
            out.append("    METHODS:")
            out += _render_methods(c["methods"], oracle, addon, None, None)
    if not ext["views"]:
        out.append(f"  VIEWS: {EMPTY_MARKER}")
    for f, recs in sorted(ext["views"].items()):
        out.append(f"  VIEWS: {f}")
        for r in recs:
            parts = [r["model"] or "-", r["vtype"], r["xml_id"]]
            line = "    " + " | ".join(parts)
            if r["inherit"]:
                line += f" | inherit_id: {r['inherit']}"
            out.append(line)
    if not ext["assets"]:
        out.append(f"  ASSETS: {EMPTY_MARKER}")
    for a in ext["assets"]:
        out.append(f"  ASSETS: {a}")
    for c, sched in sorted(ext["crons"].items()):
        out.append(f"  CRON: {c} — {sched}")
    for n in ext["notes"]:
        out.append(f"  UNEXTRACTED: {n}")
    return out


def _render_methods(methods, oracle, addon, model_name, kind):
    lines = []
    for name, m in sorted(methods.items()):
        # no oracle → no tag at all: an untagged claim is skipped by the
        # TAG comparison, so --write stays a --check fixpoint off-platform
        tag = (f"[{expected_tag(oracle, addon, model_name, kind, name)}] "
               if oracle is not None else "")
        line = f"      {tag}def {m['sig']}"
        if m["route"] and m["route"][0]:
            line += f"  route={', '.join(m['route'][0])}"
            if m["route"][1]:
                line += f" ({m['route'][1]})"
        lines.append(line)
    return lines


# ─── --write mode (Stage 2): the script owns the inventory portion ──────────

INV_START_RE = re.compile(r'^\s*INVENTORY\s*(?:\([^)]*\))?\s*:')
INV_END_RE = re.compile(r'^\s*END_INVENTORY\s*:')


def render_inventory_section(addon, ext, oracle):
    """The marker-delimited, machine-owned section --write maintains inside
    a block. Everything between the markers is regenerated wholesale; hand
    content outside them is never touched."""
    lines = ["  INVENTORY: (machine-generated by AI.gen_inventory.py --write "
             "— do not hand-edit between this line and END_INVENTORY; "
             "regenerate after any code change)"]
    lines += _render_body(addon, ext, oracle)
    lines.append("  END_INVENTORY:")
    return lines


def _set_header_field(lines, field, value):
    """Rewrite the block's first '<FIELD>:' line to the code-truth value —
    in place (never a second line: the canary's duplicate-line check treats
    these as single-value fields). value None removes the line; a missing
    line is inserted at the canonical spot (after the field's template
    predecessor — APP for DEPENDS — falling back up the header)."""
    pat = re.compile(rf'^(\s*){field}\s*:\s*(.*)$')
    for i, ln in enumerate(lines):
        m = pat.match(ln)
        if m:
            if value is None:
                del lines[i]
            elif m.group(2) != value:
                lines[i] = f"{m.group(1)}{field}: {value}"
            return
    if value is None:
        return
    anchors = {"DEPENDS": ("APP", "TYPE", "IMPACT", "UPDATED", "STATUS"),
               "DEPENDS_CUSTOM": ("DEPENDS", "APP", "TYPE", "IMPACT"),
               "EXTERNAL_DEPS": ("DEPENDS_CUSTOM", "DEPENDS", "APP", "TYPE",
                                 "IMPACT")}[field]
    pos, indent = 0, ""
    for a in anchors:
        apat = re.compile(rf'^(\s*){a}\s*:')
        hit = next((i for i, ln in enumerate(lines) if apat.match(ln)), None)
        if hit is not None:
            pos, indent = hit + 1, apat.match(lines[hit]).group(1)
            break
    lines.insert(pos, f"{indent}{field}: {value}")


def _external_deps_value(existing_rest, python_list):
    """python part = code truth; a hand-written 'js: [...]' tail is
    unextractable (honesty rules) and therefore hand-owned — preserved
    verbatim. None when neither part remains (line is then removed)."""
    js = re.search(r'js:\s*\[[^\]]*\]', existing_rest or "")
    parts = []
    if python_list:
        parts.append(f"python: [{', '.join(python_list)}]")
    if js:
        parts.append(js.group(0))
    return "  ".join(parts) if parts else None


def apply_inventory(block_lines, addon, ext, oracle):
    """Transform one block's lines in place: header inventory fields to
    code truth, then replace (or first-run append) the marker-delimited
    INVENTORY section. Idempotent; judgment lines and hand prose are
    never modified."""
    _set_header_field(block_lines, "DEPENDS",
                      ", ".join(ext["depends"]) if ext["depends"] else None)
    _set_header_field(block_lines, "DEPENDS_CUSTOM",
                      ", ".join(ext["depends_custom"])
                      if ext["depends_custom"] else None)
    ext_pat = re.compile(r'^\s*EXTERNAL_DEPS\s*:\s*(.*)$')
    existing_rest = next((m.group(1) for ln in block_lines
                          if (m := ext_pat.match(ln))), None)
    _set_header_field(block_lines, "EXTERNAL_DEPS",
                      _external_deps_value(existing_rest,
                                           ext["external_python"]))

    section = render_inventory_section(addon, ext, oracle)
    start = next((i for i, ln in enumerate(block_lines)
                  if INV_START_RE.match(ln)), None)
    if start is not None:
        end = next((i for i in range(start + 1, len(block_lines))
                    if INV_END_RE.match(block_lines[i])), None)
        if end is not None:
            block_lines[start:end + 1] = section
        else:   # damaged pair (END marker lost): reclaim to end of block —
                # destructive to any hand content below the orphaned marker,
                # so never silent (mirrors the honesty rules above)
            print(f"⚠️  {addon}: INVENTORY: marker found without "
                  f"END_INVENTORY: — reclaimed to end of block; any hand "
                  f"content below the marker was replaced (review the "
                  f"block; recover it from git history if needed)")
            block_lines[start:] = section + [""]
    else:
        while block_lines and not block_lines[-1].strip():
            block_lines.pop()
        block_lines += [""] + section + [""]


# ─── main ────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("addons", nargs="*", help="limit to these addons")
    ap.add_argument("--check", action="store_true",
                    help="diff blocks vs code instead of printing inventory")
    ap.add_argument("--write", action="store_true",
                    help="write the inventory portion into each block: "
                         "header DEPENDS/DEPENDS_CUSTOM/EXTERNAL_DEPS lines "
                         "rewritten in place + a marker-delimited INVENTORY "
                         "section (machine-owned) replaced or appended")
    ap.add_argument("--root", type=Path, default=REPO_ROOT,
                    help="repo root to operate on (default: parent of AI/ subfolder)")
    ap.add_argument("--no-tags", action="store_true",
                    help="skip the [NEW]/[OVR] standard-source heuristic")
    args = ap.parse_args()

    if args.check and args.write:
        print("❌ --check and --write are mutually exclusive — run --write, "
              "then verify with --check")
        return 2

    root = args.root.resolve()
    md = root / "AI" / "AI.CUSTOM.md"   # lives in AI/ subfolder after v13
    if not md.exists():
        if args.check or args.write:
            print(f"❌ no AI.CUSTOM.md under {root}/AI/ — nothing to "
                  f"{'check against' if args.check else 'write into'} "
                  f"(wrong --root?)")
            return 2
        blocks = {}  # extract mode works without a master file
        # (calibrating against a bare addons tree, or bootstrapping)
    else:
        blocks = split_blocks(md)

    on_disk = find_addon_folders(root)

    # Delegation cross-check: the canary's parse_addons is the definition
    # of record for "what is a documented addon" — disagreement between it
    # and the local splitter is a bug in THIS script.
    if md.exists():
        canary = load_canary()
        if canary is None:
            print("⚠️  AI.canary.py not loadable from the script folder — "
                  "documented-addon set NOT cross-checked")
        else:
            canary_names = set(canary.parse_addons(md))
            if canary_names != set(blocks):
                print(f"❌ block-splitter disagreement with "
                      f"AI.canary.parse_addons "
                      f"(only here: {sorted(set(blocks) - canary_names)}; only "
                      f"canary: {sorted(canary_names - set(blocks))}) — fix "
                      f"AI.gen_inventory.py before trusting any finding")
                return 2

    selected = args.addons or sorted(set(on_disk) | set(blocks))
    skipped_msgs = []
    work = []
    for addon in selected:
        has_folder, has_block = addon in on_disk, addon in blocks
        if not has_folder and not has_block:
            skipped_msgs.append(f"{addon}: neither folder nor block — skipped")
        elif not has_folder:
            skipped_msgs.append(f"{addon}: block without folder — skipped "
                                f"(AI.canary.py's FOLDER MISSING owns this)")
        elif (args.check or args.write) and not has_block:
            skipped_msgs.append(f"{addon}: folder without block — skipped "
                                f"(AI.canary.py's UNDOCUMENTED owns this)")
        else:
            work.append(addon)

    # With the tag heuristic on, extract EVERY on-disk addon, not only the
    # selected ones — the oracle's custom-defs corpus must see all root
    # addons (a method may override a DEPENDS_CUSTOM base addon outside
    # the selection). With --no-tags only the selection is extracted.
    all_extracted = {}
    for addon in (on_disk if not args.no_tags else work):
        ext = extract_addon(root, addon)
        if ext is not None:
            all_extracted[addon] = ext
    extracted = {a: all_extracted[a] for a in work if a in all_extracted}
    for addon in work:
        if addon not in all_extracted:
            skipped_msgs.append(f"{addon}: __manifest__.py unreadable — skipped")

    # one grep pass for all method names across the run
    oracle = None
    if not args.no_tags:
        names = set()
        for ext in all_extracted.values():
            for m in ext["models"].values():
                names |= set(m["methods"])
            for c in ext["controllers"].values():
                names |= set(c["methods"])
        oracle = build_tag_oracle(names, root, all_extracted)
        if oracle is None:
            cause = ("standard source trees not found under /home/odoo/src"
                     if not any(t.is_dir() for t in STD_TREES)
                     else "def-grep over the standard source trees failed")
            # AI.canary.py's check 18 matches the failure variant of this
            # line ("def-grep" in a column-0 ⚠️ line) and reports it as
            # INVENTORY CHECKER UNAVAILABLE — a silently disabled TAG
            # dimension would break the never-silent principle. The
            # trees-absent variant stays advisory: off-platform the
            # disablement is by design. Change the two places together.
            print(f"⚠️  {cause} — [NEW]/[OVR] heuristic disabled for this run")

    if args.write:
        original = md.read_text(encoding="utf-8")

        # ── one-time header pointer upgrade (expires 2026-10-31) ──────────
        # Replaces the old ⚠️ READ NOW pointer with the stronger 🛑 STOP
        # wording. Runs only while the cutoff date has not passed and only
        # when the old text is still present — a no-op on already-upgraded
        # repos and after the cutoff.
        _OLD_POINTER = "# ⚠️  AI: READ NOW: AI.SESSION.md"
        _NEW_POINTER = (
            "# 🛑 AI INSTRUCTION — STOP: read AI/AI.SESSION.md BEFORE processing\n"
            "#    anything in this file. The session-start sequence, all field\n"
            "#    semantics, and every convention live in AI.SESSION.md. This file\n"
            "#    contains ONLY this repo's data. Reading this file without first\n"
            "#    reading AI.SESSION.md is an error — stop and read it now.\n"
            '#   Bump the "# UPDATED:" line below on every edit to this file.'
        )
        if date.today() <= date(2026, 10, 31) and _OLD_POINTER in original:
            # Replace the old multi-line pointer block. The old block spans
            # from the _OLD_POINTER line through the next 4 continuation
            # lines (the indented "#   ..." lines that follow it), ending
            # just before the '#   "# UPDATED:"' line which is the last of
            # the old block. Replace the whole run in one substitution so
            # partial matches never leave a mangled header.
            _OLD_BLOCK = (
                "# ⚠️  AI: READ NOW: AI.SESSION.md — the session-start sequence and every\n"
                "#   convention live there (template-owned; overwritten by template\n"
                "#   upgrades). This file carries ONLY this repo's data — formats and\n"
                "#   field semantics: AI.SESSION.md and the AI.SPECS.* files. Bump the\n"
                '#   "# UPDATED:" line below on every edit to this file, for any reason.'
            )
            if _OLD_BLOCK in original:
                original = original.replace(_OLD_BLOCK, _NEW_POINTER, 1)
                print("✍️  AI.CUSTOM.md header pointer upgraded "
                      "(⚠️ READ NOW → 🛑 STOP)")
        # ──────────────────────────────────────────────────────────────────

        lines = original.splitlines()
        regions, cur, cur_start = [], None, None
        for i, ln in enumerate(lines):
            if BLOCK_START.match(ln):
                if cur is not None:
                    regions.append((cur, cur_start, i))
                cur, cur_start = BLOCK_START.match(ln).group(1), i
        if cur is not None:
            regions.append((cur, cur_start, len(lines)))
        out, pos, written = [], 0, []
        for name, s, e in regions:
            out += lines[pos:s + 1]        # up to and incl. the >>ADDON: line
            body = lines[s + 1:e]
            if name in extracted:
                apply_inventory(body, name, extracted[name], oracle)
                written.append(name)
            out += body
            pos = e
        out += lines[pos:]
        new_text = "\n".join(out)
        if original.endswith("\n") and not new_text.endswith("\n"):
            new_text += "\n"
        if new_text != original:
            tmp = md.with_name(md.name + ".tmp")
            try:
                tmp.write_text(new_text, encoding="utf-8")
                tmp.replace(md)   # atomic — never a truncated master file
            except BaseException:
                tmp.unlink(missing_ok=True)  # no stray .tmp after a failed run
                raise
            print(f"✍️  inventory written for {len(written)} addon(s): "
                  f"{', '.join(written)}")
        else:
            print(f"✍️  no changes — inventory already current for "
                  f"{len(written)} addon(s)")
        for msg in skipped_msgs:
            print(f"   ◻︎  {msg}")
        print("   verify now: python3 AI/AI.gen_inventory.py --check   "
              "(then python3 AI/AI.canary.py)")
        return 0

    drift_found = False
    for addon in sorted(extracted):
        ext = extracted[addon]
        if not args.check:
            print(render_extracted(addon, ext, oracle))
            print()
            continue
        block_text = blocks[addon]
        claims = parse_block_inventory(block_text)
        findings = compare_addon(addon, ext, claims, block_text, oracle)
        unchecked = sorted(claims["ignored_sections"])
        if findings or ext["notes"] or unchecked:
            print(f"== {addon}")
            for f in findings:
                drift_found = True
                print(f"   ⚠️  {f}")
            for n in ext["notes"]:
                print(f"   ◻︎  unextracted: {n}")
            if unchecked:
                print(f"   ◻︎  block sections not checked (outside the "
                      f"inventory field list): {', '.join(unchecked)}")

    for msg in skipped_msgs:
        print(f"   ◻︎  {msg}")

    if args.check:
        checked = len(extracted)
        if drift_found:
            print(f"\n⚠️  INVENTORY DRIFT — findings above "
                  f"({checked} addon(s) checked). Classify each as doc rot "
                  f"(fix the block) or extractor bug (fix this script).")
            return 1
        print(f"\n✅ no inventory drift across {checked} addon(s) checked "
              f"(js EXTERNAL_DEPS, SECURITY/COMMANDS sections, and prose "
              f"descriptors are outside this tool's scope)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
