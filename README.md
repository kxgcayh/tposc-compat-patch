# TPOSC - Compatibility Patch 0.3.0

Restores USSEP fixes that The People Of Skyrim Complete overwrites without meaning to, and removes 3 doubled fires in
Hall of the Vigilant when using Embers XD 3.3.0. Plugin only, ESL flagged, adds no new forms.

## Requirements

- [The People Of Skyrim Complete](https://www.nexusmods.com/skyrimspecialedition/mods/13196) V11.1.6
- [XD Embers and The People Of Skyrim Complete Patch](https://www.nexusmods.com/skyrimspecialedition/mods/63308) V10.6.2
- [Embers XD](https://www.nexusmods.com/skyrimspecialedition/mods/37085) 3.3.0
- [Unofficial Skyrim Special Edition Patch](https://www.nexusmods.com/skyrimspecialedition/mods/266) 4.3.9c
- [Cutting Room Floor](https://www.nexusmods.com/skyrimspecialedition/mods/276) 3.1.26
- `ccbgssse001-fish.esm` (Creation Club Fishing). USSEP already requires it.

## Target versions

Skyrim SE/AE. Not for VR. Written against the exact plugin hashes in `inputs.sha256`.

## The Problem

TPOSC has no USSEP master and loads after it, so its 45,947 overrides replace USSEP's. Most of that
does not matter: TPOSC disables most of those objects, or deliberately edits the same field. In 107 records it left
a field vanilla that USSEP had fixed, so the fix is lost for no reason. Separately, `tposc_Embers XD_patch.esp` predates
the firepit Embers XD added to Hall of the Vigilant, and re-enables the 3 fires Embers now disables.

## What the Patch Does

- 83 refs and actors and 24 cells: the TPOSC record, with only the USSEP-fixed fields forwarded (`forward.tsv`).
- Hall of the Vigilant: restores Embers XD's disabled state for `0C73C8`, `0C73C9`, `0C73CA`.
- Cutting Room Floor: keeps TPOSC's landscape (13) and navmesh (25) where both edit the same record, so TPOSC's objects stay on their ground without a LOOT rule. Whole records, listed in `world.tsv`.
- Keeps the locations and regions Cutting Room Floor sets on 7 cell headers, so the copied headers do not revert them (`headers.tsv`).
- Does not touch navmesh. USSEP's 310 navmesh edits stay overwritten, as they cannot be merged outside the Creation Kit.

## Install

Install as a normal mod and sort with LOOT. No manual placement: the masters keep the patch after TPOSC and its Embers
patch, and it does not depend on TPOSC being at the bottom of the load order. New game recommended, as with TPOSC.

If you add mods later, run `python3 audit.py "<MO2 instance folder>" "<profile>"`. It is read-only and reports anything
that now conflicts with this patch.

## Build from Source

See [BUILDING.md](BUILDING.md). Technical notes: [NOTES.md](NOTES.md).

## Verification Status

Checked offline: Spriggit round trip, and an independent binary parser (masters, ESL flag, no new forms, every forwarded
field equals USSEP's, every other REFR field equals TPOSC's within float rounding, Hall refs disabled, all 38 landscape
and navmesh records byte-identical to TPOSC).

Tested in game on AE 1.7.104 under CrossOver with a 752-plugin LOOT-sorted list, using DevBench and screenshots:

- All 8 TPOSC inns, The Frozen Hearth and Hall of the Vigilant load, with fire records in each. Hall shows only the Embers firepit.
- 9 patched exteriors load, and the 7 viewed look right. Heljarchen and Frost River keep their Cutting Room Floor locations.
- Helgen Reborn's town loads, outside its quest.

Not tested: the Helgen Reborn quest, NPC pathing on the changed navmesh, Papyrus logs, and a long playthrough. One crash
occurred during rapid `coc` travel, in vanilla effect-shader rendering. It named no record and did not recur at a slower pace.

## Credits and Permissions

Nesbit098 (TPOSC and its Embers patch), mindfIux (Embers XD), Arthmoor (Cutting Room Floor) and the USSEP team.

Permissions, read from each mod's Nexus page:

- USSEP allows use as a master and copying fixes unaltered, which is all this patch does.
- TPOSC does not allow redistributing its files "in whole or part" without express permission. This plugin copies TPOSC cell
  and worldspace headers, placed-record data, and 38 whole landscape and navmesh records. Permission has not been requested.
- Embers XD requires permission to modify its files. This plugin holds no Embers XD forms, but it requires the plugin as a
  master. Permission has not been requested.
- Cutting Room Floor requires permission to modify or upload its files. This plugin references its forms in 6 cell headers and
  requires it as a master. Permission has not been requested.

Do not make this repository or its releases public until those are settled.

## License

MIT, see [LICENSE](LICENSE). Covers this repository's scripts and documents only.
