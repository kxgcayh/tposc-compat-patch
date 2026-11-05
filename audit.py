#!/usr/bin/env python3
"""Rerun after adding mods or a LOOT sort. Read-only. Reports what this patch or TPOSC now conflicts with.

Usage: python3 audit.py "<MO2 instance folder>" "<profile name>" [--game-data "<Skyrim Data folder>"]
"""
import os, struct, sys, zlib

TPOSC, PATCH = "tpos_ultimate_esm.esp", "tposc - compatibility patch.esp"
BASE = {"skyrim.esm", "update.esm", "dawnguard.esm", "hearthfires.esm", "dragonborn.esm"}


def subs(b):
    i, big, out = 0, None, {}
    while i + 6 <= len(b):
        t, n = b[i:i + 4].decode("latin1"), struct.unpack_from("<H", b, i + 4)[0]
        i += 6
        if t == "XXXX":
            big = struct.unpack_from("<I", b, i)[0]
            i += n
            continue
        n, big = (big, None) if big is not None else (n, None)
        out.setdefault(t, []).append(b[i:i + n])
        i += n
    return out


def scan(path, bodies=False):
    """{(owner plugin, object id): (type, flags, subrecords or None, resolve)} for one plugin."""
    b = open(path, "rb").read()
    hs = struct.unpack_from("<I", b, 4)[0]
    masters = [m.rstrip(b"\0").decode("latin1").lower() for m in subs(b[24:24 + hs]).get("MAST", [])]
    names = masters + [os.path.basename(path).lower()]
    out = {}

    def walk(off, end):
        while off < end:
            t, sz = b[off:off + 4], struct.unpack_from("<I", b, off + 4)[0]
            if t == b"GRUP":
                walk(off + 24, off + sz)
                off += sz
                continue
            fl, fid = struct.unpack_from("<II", b, off + 8)
            key = (names[min(fid >> 24, len(names) - 1)], fid & 0xffffff)
            s = None
            if bodies:
                body = b[off + 24:off + 24 + sz]
                s = subs(zlib.decompress(body[4:]) if fl & 0x40000 else body)
            out[key] = (t.decode("latin1"), fl, s)
            off += 24 + sz

    walk(24 + hs, len(b))
    return out, names


def forms(values, names):  # raw FormIDs as (plugin, id), so the same form at another master index compares equal
    return {(names[min(v >> 24, len(names) - 1)], v & 0xffffff) for raw in values for v in struct.unpack(f"<{len(raw) // 4}I", raw)}


def plugin_paths(root, profile, game_data):
    enabled = [l.strip()[1:] for l in open(os.path.join(root, "profiles", profile, "modlist.txt"), encoding="utf8", errors="replace") if l.startswith("+")]
    loc = {}
    for m in reversed(enabled):  # first line of modlist.txt has the highest priority
        d = os.path.join(root, "mods", m)
        if os.path.isdir(d):
            loc.update({f.lower(): os.path.join(d, f) for f in os.listdir(d) if f.lower().endswith((".esp", ".esm", ".esl"))})
    if game_data and os.path.isdir(game_data):
        for f in os.listdir(game_data):
            if f.lower().endswith((".esp", ".esm", ".esl")):
                loc.setdefault(f.lower(), os.path.join(game_data, f))
    order = [l.strip()[1:].lower() for l in open(os.path.join(root, "profiles", profile, "plugins.txt"), encoding="utf8", errors="replace") if l.startswith("*")]
    return order, loc


def selftest():
    assert forms([b"\x01\x00\x00\x01"], ["a", "b"]) == forms([b"\x01\x00\x00\x00"], ["b"])  # same form, other master index
    s = subs(b"EDID\x02\x00a\0XXXX\x04\x00\x03\x00\x00\x00DATA\x00\x00abc")
    assert s == {"EDID": [b"a\0"], "DATA": [b"abc"]}, s


def main():
    selftest()
    args = sys.argv[1:]
    data = args[args.index("--game-data") + 1] if "--game-data" in args else None
    order, loc = plugin_paths(args[0], args[1], data)
    for need in (TPOSC, PATCH):
        if need not in order:
            sys.exit(f"{need} is not active in this profile")
    t, p = order.index(TPOSC), order.index(PATCH)
    print(f"{len(order)} active. TPOSC at {t}, this patch at {p}.")
    (tp, _), (pr, pnames) = scan(loc[TPOSC]), scan(loc[PATCH], True)
    heads = {k: v for k, v in pr.items() if v[0] in ("CELL", "WRLD")}
    world, after, last = 0, [], {}
    for i, f in enumerate(order):
        if i <= t or i == p or f not in loc or f in BASE:
            continue
        r, names = scan(loc[f], bodies=True)
        nav = sum(1 for k, v in r.items() if k in tp and v[0] in ("NAVM", "LAND") and not (k in pr and i < p))
        if nav:
            after.append((f, nav))
        if i < p:  # only the last editor before this patch matters: it is what the patch replaces
            last.update({k: (f, r[k][2], names) for k in heads if k in r})
    for k, (f, b, names) in last.items():
        a = heads[k][2]
        for field, name in (("XLCN", "location"), ("XOWN", "owner"), ("XCLR", "regions")):
            if b.get(field) and forms(a.get(field, []), pnames) != forms(b[field], names):
                print(f"HEADER: {f} sets the {name} of {k[1]:06X}; this patch overrides it; check whether headers.tsv needs it")
                world += 1
    for f, n in sorted(after, key=lambda x: -x[1]):
        print(f"WORLD: {f} loads after TPOSC and wins {n} navmesh or landscape records")
    print(f"{world} header issue(s), {len(after)} plugin(s) beating TPOSC on navmesh or landscape.")  # Helgen Reborn is expected here


main()
