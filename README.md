# TPOSC - Compatibility Patch 0.2.0

Restores USSEP fixes that The People Of Skyrim Complete overwrites without meaning to, and removes 3 doubled fires in
Hall of the Vigilant when using Embers XD 3.3.0. Plugin only, ESL flagged, adds no new forms.

## Requirements

- [The People Of Skyrim Complete](https://www.nexusmods.com/skyrimspecialedition/mods/13196) V11.1.6
- [XD Embers and The People Of Skyrim Complete Patch](https://www.nexusmods.com/skyrimspecialedition/mods/63308) V10.6.2
- [Embers XD](https://www.nexusmods.com/skyrimspecialedition/mods/37085) 3.3.0
- [Unofficial Skyrim Special Edition Patch](https://www.nexusmods.com/skyrimspecialedition/mods/266)

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
- Keeps the cell location Cutting Room Floor sets, so the copied cell header does not revert it (`headers.tsv`).
- Does not touch navmesh. USSEP's 310 navmesh edits stay overwritten, as they cannot be merged outside the Creation Kit.

## Install

Install as a normal mod and sort with LOOT. No manual placement: the masters keep the patch after TPOSC and its Embers
patch, and it does not depend on TPOSC being at the bottom of the load order. New game recommended, as with TPOSC.

If you add mods later, run `python3 audit.py "<MO2 instance folder>" "<profile>"`. It is read-only and reports anything
that now conflicts with this patch.

## Build from Source

See [BUILDING.md](BUILDING.md). Technical notes: [NOTES.md](NOTES.md).

## Verification Status

Checked: Spriggit round trip, and an independent binary parser (masters, ESL flag, no new forms, every forwarded field
equals USSEP's, every other REFR field equals TPOSC's within float rounding, Hall refs disabled).
Not tested in game.

## Credits and Permissions

Nesbit098 (TPOSC and its Embers patch), mindfIux (Embers XD), the USSEP team. Their permissions have not been reviewed
for publishing, as this is a personal patch for now.

## License

MIT, see [LICENSE](LICENSE). Covers this repository's scripts and documents only.
