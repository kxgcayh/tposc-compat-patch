#!/usr/bin/env python3
"""Build TPOSC - Compatibility Patch.esp (see README.md, BUILDING.md, NOTES.md).

forward.tsv lists records where USSEP changed a field that The People Of Skyrim Complete left vanilla. Each patch record
is the TPOSC record with those fields taken from USSEP. HALL also restores Embers XD's disabled state for 3 fires that
the old TPOSC-Embers patch re-enables. headers.tsv keeps region and location edits that plugins sorted after TPOSC make,
so this patch's copied cell headers do not revert them wherever LOOT places it. world.tsv lists whole landscape and
navmesh records copied from TPOSC where Cutting Room Floor also edits them. No assets, no new forms.
Usage: python3 build.py            (uses or makes build/yaml-*, prints the records, writes no plugin)
       python3 build.py --write    (also writes dist/ and round-trip checks it)
       python3 build.py --fresh    (re-serializes inputs/ first)
Needs: dotnet, python3, the Spriggit.Yaml.Skyrim 0.41.0 DLL (SPRIGGIT_DLL or auto-detected), inputs/ (BUILDING.md).
"""
import collections, hashlib, os, pathlib, re, shutil, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
INPUTS = pathlib.Path(os.environ.get("INPUTS", HERE / "inputs"))
Y = HERE / "build"
NAME = "TPOSC - Compatibility Patch"
TPOSC, EMBERS_PATCH = "tpos_ultimate_esm.esp", "tposc_Embers XD_patch.esp"
USSEP = "Unofficial Skyrim Special Edition Patch.esp"
SOURCES = {TPOSC: "yaml-tposc", USSEP: "yaml-ussep", "Embers XD.esp": "yaml-embers"}
ORDER = ["Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm", "ccbgssse001-fish.esm", USSEP, "Embers XD.esp",
         TPOSC, "Cutting Room Floor.esp", EMBERS_PATCH]
HALL = ["0C73C8:Skyrim.esm", "0C73C9:Skyrim.esm", "0C73CA:Skyrim.esm"]  # HallOfTheVigilant01, Embers disables these
HALL_CELL = "HallOfTheVigilant01 - 0C7348_Skyrim.esm"
DROP = {"Landscape", "NavigationMeshes", "Persistent", "Temporary"}
VARIANTS = {"tposc-ground": True, "crf-ground": False}  # folder -> carry world.tsv; the FOMOD installs one
DESC = "Forwards USSEP fields TPOSC left vanilla; fixes stale Hall of the Vigilant fires."


def find_dll():  # SPRIGGIT_DLL, else Spriggit's own download folder, else the NuGet cache
    if os.environ.get("SPRIGGIT_DLL"):
        return pathlib.Path(os.environ["SPRIGGIT_DLL"])
    for base in [pathlib.Path(d) / "Spriggit/Translations/Spriggit.Yaml.Skyrim/0.41.0"
                 for d in {os.environ.get("TMPDIR", ""), tempfile.gettempdir(), "/tmp"} if d] + [
            pathlib.Path.home() / ".nuget/packages/spriggit.yaml.skyrim/0.41.0"]:
        hits = sorted(base.rglob("Spriggit.Yaml.Skyrim.dll")) if base.is_dir() else []
        if hits:
            return hits[0]
    sys.exit("Spriggit.Yaml.Skyrim.dll 0.41.0 not found. See BUILDING.md, or set SPRIGGIT_DLL.")


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or "ERR" in r.stdout:
        sys.exit(f"failed: {' '.join(map(str, cmd))}\n{r.stdout}\n{r.stderr}")


def serialize(dll, src, out):
    run(["dotnet", dll, "serialize", "-i", src, "-o", out, "-g", "SkyrimSE", "-p", "Spriggit.Yaml.Skyrim", "-v", "0.41.0"])


def check_inputs():  # a different hash stops the build: forward.tsv was derived from exactly these files
    for line in (HERE / "inputs.sha256").read_text().splitlines():
        want, name = line.split(None, 1)
        f = INPUTS / name.strip()
        if not f.is_file():
            sys.exit(f"missing input: {f} (see BUILDING.md)")
        if hashlib.sha256(f.read_bytes()).hexdigest() != want:
            sys.exit(f"{f.name} is not the version this patch was written for (see BUILDING.md)")


def blocks(lines):  # top-level YAML keys -> their lines; list items of a top-level key sit at column 0
    out, key = {}, None
    for l in lines:
        if l and not l[0].isspace() and not l.startswith("- "):
            key = l.split(":")[0]
            out[key] = []
        out[key].append(l)
    return out


def items(lines):  # column-0 list items under a Persistent/Temporary block
    out = []
    for l in lines[1:]:
        if l.startswith("- "):
            out.append([])
        out[-1].append(l)
    return out


def fkey(item):
    return next(l.split("FormKey: ")[1].strip() for l in item if "FormKey: " in l)


def item_blocks(item):  # one list item as top-level blocks
    return blocks(["  " + item[0][2:]] and [item[0][2:]] + [l[2:] for l in item[1:]])


def item_lines(b):
    flat = [l for v in b.values() for l in v]
    return ["- " + flat[0]] + ["  " + l for l in flat[1:]]


def overlay(base, src, take):  # base with the `take` fields replaced by src's (added or dropped as src has them)
    keys = list(base)
    for i, k in enumerate(src):
        if k in take and k not in base:
            prev = [x for x in list(src)[:i] if x in keys]
            keys.insert(keys.index(prev[-1]) + 1 if prev else len(keys), k)
    return {k: (src[k] if k in take else base[k]) for k in keys if not (k in take and k not in src)}


def cell_of(path):  # a cell file, or a worldspace file's TopCell, as (whole file blocks, cell blocks, indent)
    whole = blocks(path.read_text(encoding="utf8").splitlines())
    if "TopCell" in whole:
        return whole, blocks([l[2:] for l in whole["TopCell"][1:]]), 2
    return whole, whole, 0


def index(root):
    """FormKey -> (file, 'cell' or 'ref') for every cell and placed record under Cells/ and Worldspaces/."""
    out = {}
    for sub in ("Cells", "Worldspaces"):
        for p in (root / sub).rglob("RecordData.yaml") if (root / sub).is_dir() else []:
            _, c, _ = cell_of(p)
            if "FormKey" not in c:
                continue
            out[c["FormKey"][0].split(": ")[1]] = (p, "cell")
            for k in ("Persistent", "Temporary"):
                for it in items(c.get(k, [""])):
                    out[fkey(it)] = (p, "ref")
            for it in items(c.get("NavigationMeshes", [""])):
                out[fkey(it)] = (p, "navm")
            if "Landscape" in c:
                out[fkey(c["Landscape"])] = (p, "land")
    return out


def lookup(path, fk):
    _, c, _ = cell_of(path)
    for k in ("Persistent", "Temporary"):
        for it in items(c.get(k, [""])):
            if fkey(it) == fk:
                return k, it
    sys.exit(f"{fk} not in {path}")


def render(path, header_take, src_cell, children):
    """One patch file: the source file's cell header with `header_take` fields from src_cell, plus only `children`."""
    whole, c, ind = cell_of(path)
    head = {k: v for k, v in c.items() if k not in DROP}
    if header_take:
        head = overlay(head, src_cell, header_take)
    body = [l for v in head.values() for l in v]
    for k in ("Persistent", "Temporary", "NavigationMeshes"):
        if children.get(k):
            body.append(f"{k}:")
            for it in children[k]:
                body += it
    body += children.get("Landscape", [])
    if ind:
        whole = dict(whole)
        whole["TopCell"] = ["TopCell:"] + ["  " + l for l in body]
        body = [l for v in whole.values() for l in v]
    return "\n".join(body) + "\n"


def main():
    check_inputs()
    dll = find_dll()
    for f, d in SOURCES.items():
        if "--fresh" in sys.argv or not (Y / d).is_dir():
            shutil.rmtree(Y / d, ignore_errors=True)
            serialize(dll, INPUTS / f, Y / d)
    if "--fresh" in sys.argv or not (Y / "yaml-embers-patch").is_dir():
        serialize(dll, INPUTS / EMBERS_PATCH, Y / "yaml-embers-patch")
    tp, us = index(Y / "yaml-tposc"), index(Y / "yaml-ussep")
    for name, world in VARIANTS.items():
        print(f"\n== {name}")
        build_variant(dll, tp, us, name, world, "--write" in sys.argv)


def build_variant(dll, tp, us, name, with_world, write):
    want = [l.split("\t") for l in (HERE / "forward.tsv").read_text().splitlines() if l and not l.startswith("#")]
    files = collections.defaultdict(lambda: {"take": set(), "src": None, "Persistent": [], "Temporary": [], "NavigationMeshes": [], "Landscape": []})
    stats = collections.Counter()
    for fk, ty, keys in want:
        take = set(keys.split(","))
        assert fk in tp and fk in us, f"{fk} missing from a source"
        p, kind = tp[fk]
        up, ukind = us[fk]
        assert kind == ukind, f"{fk}: cell/ref mismatch"
        e = files[p]
        if kind == "cell":
            e["take"] = take
            e["src"] = cell_of(up)[1]
        else:
            lk, it = lookup(p, fk)
            _, ui = lookup(up, fk)
            a, b = item_blocks(it), item_blocks(ui)
            merged = overlay(a, b, take)
            assert merged != a, f"{fk}: forwarding {take} changes nothing"
            assert {k for k in set(a) | set(merged) if a.get(k) != merged.get(k)} <= take, fk
            e[lk].append(item_lines(merged))
        stats[ty] += 1
    for line in (HERE / "world.tsv").read_text().splitlines() if with_world else []:
        if line and not line.startswith("#"):
            fk, ty = line.split("\t")
            p, kind = tp[fk]
            _, c, _ = cell_of(p)
            if ty == "LAND":
                assert kind == "land", fk
                files[p]["Landscape"] = c["Landscape"]
            else:
                assert kind == "navm", fk
                files[p]["NavigationMeshes"] += [i for i in items(c["NavigationMeshes"]) if fkey(i) == fk]
            stats[ty] += 1
    for line in (HERE / "headers.tsv").read_text().splitlines():
        if line and not line.startswith("#"):
            fk, field, value, _ = line.split("\t")
            assert fk in tp and tp[fk][1] == "cell", f"{fk}: headers.tsv needs a cell"
            if tp[fk][0] not in files:  # the cell is only in the patch for its world.tsv records
                continue
            e = files[tp[fk][0]]
            if e["src"] is None:
                e["src"] = {}
            lines = [f"{field}:"] + [f"- {v}" for v in value.split(",")] if field == "Regions" else [f"{field}: {value}"]
            e["src"] = {**e["src"], field: lines}
            e["take"] = e["take"] | {field}
            stats["CELL fields kept"] += 1
    out = Y / "out" / name
    shutil.rmtree(out, ignore_errors=True)
    yroot = Y / "yaml-tposc"
    recs = {}
    for p, e in files.items():
        recs[p.relative_to(yroot)] = render(p, e["take"], e["src"], e)
    for rel in list(recs):  # Spriggit silently drops an exterior cell whose worldspace has no header file
        if rel.parts[0] == "Worldspaces":
            ws = pathlib.Path(*rel.parts[:2]) / "RecordData.yaml"
            if ws not in recs:
                recs[ws] = render(yroot / ws, set(), None, {})
    # Hall of the Vigilant: Embers XD's own record for each fire, in Embers' cell header
    hp = next((Y / "yaml-embers").rglob(HALL_CELL)) / "RecordData.yaml"
    hall = {"Persistent": [], "Temporary": []}
    for fk in HALL:
        lk, it = lookup(hp, fk)
        text = "\n".join(it)
        assert "InitiallyDisabled" in text and "-30000" in text, f"{fk}: Embers no longer disables this ref"
        hall[lk].append(it)
    recs[hp.relative_to(Y / "yaml-embers")] = render(hp, set(), None, hall)
    stats["REFR (Hall)"] = len(HALL)
    text = "".join(recs.values())
    found = set(re.findall(r"[0-9A-F]{6}:(.+?\.es[pml])\b", text)) | {TPOSC, USSEP, EMBERS_PATCH, "Embers XD.esp"}
    canon = {m.lower(): m for m in ORDER}
    unknown = sorted(m for m in found if m.lower() not in canon)
    assert not unknown, f"masters not in ORDER: {unknown}"
    masters = sorted({canon[m.lower()] for m in found}, key=ORDER.index)
    print(f"records: {dict(stats)}; files: {len(recs)}\nmasters: " + ", ".join(masters))
    for f in sorted(map(str, recs)):
        print("  ", f)
    if not write:
        print("dry run, nothing written (use --write)")
        return
    for rel, t in recs.items():
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        (out / rel).write_text(t, encoding="utf8")
        for up in [Y / "yaml-tposc" / a for a in list(rel.parents)[:-1]] + [Y / "yaml-embers" / a for a in list(rel.parents)[:-1]]:
            g = up / "GroupRecordData.yaml"
            if g.is_file() and not (out / g.relative_to(up.parents[len(up.relative_to(Y).parts) - 2])).is_file():
                dst = out / g.relative_to(up.parents[len(up.relative_to(Y).parts) - 2])
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(g, dst)
    mrefs = "".join(f"  - Master: {m}\n    FileSize: 0\n" for m in masters)
    (out / "RecordData.yaml").write_text(
        "SpriggitSource:\n  PackageName: Spriggit.Yaml.Skyrim\n  Version: 0.41.0\n"
        f"ModKey: {NAME}.esp\nGameRelease: SkyrimSE\nModHeader:\n  Flags:\n  - Small\n"
        "  Stats:\n    Version: 1.7\n    NextFormID: 2048\n  Author: kxgcayh\n"
        f"  Description: {DESC}\n  MasterReferences:\n{mrefs}  INTV: 1\n")
    esp = HERE / "dist" / name / f"{NAME}.esp"
    esp.parent.mkdir(parents=True, exist_ok=True)
    run(["dotnet", dll, "deserialize", "-i", out, "-o", esp])
    rt = Y / "roundtrip" / name
    shutil.rmtree(rt, ignore_errors=True)
    serialize(dll, esp, rt)
    got = sorted(str(p.relative_to(rt)) for p in rt.rglob("RecordData.yaml") if p.parent != rt)
    assert got == sorted(map(str, recs)), "record files changed in round trip"
    for rel, t in recs.items():
        norm = lambda x: sorted(re.sub(r"(?<![\d.])-0(?=,|$)", "0", l) for l in x.splitlines())  # -0 and 0 are the same rotation
        assert norm(t) == norm((rt / rel).read_text(encoding="utf8")), f"round trip differs: {rel}"
    hdr = (rt / "RecordData.yaml").read_text()
    assert "- Small" in hdr and re.findall(r"Master: (.+)", hdr) == masters, "header round trip failed"
    print(f"OK: {esp.name} round-trips to the same {len(recs)} files, {len(masters)} masters")


main()
