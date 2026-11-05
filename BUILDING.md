# Building from source

Back to [README.md](README.md). This repository contains no plugin data from other mods, only record IDs and field names.

Tested: macOS (arm64) only. Needs Python 3, the .NET 10 SDK and the `Spriggit.Yaml.Skyrim` 0.41.0 DLL (see the
`SPRIGGIT_DLL` lookup in `build.py`).

Put these in `inputs/`. `inputs.sha256` pins them and `build.py` refuses a mismatch, because `forward.tsv` was derived
from exactly these versions. `headers.tsv` holds the cell fields kept from other plugins.

| File in `inputs/` | Where it comes from |
|---|---|
| `tpos_ultimate_esm.esp` | [TPOSC](https://www.nexusmods.com/skyrimspecialedition/mods/13196?tab=files&file_id=382604) V11.1.6, main file "The People Of Skyrim Complete BSA File Version" (file ID 382604) |
| `tposc_Embers XD_patch.esp` | [Patch 63308](https://www.nexusmods.com/skyrimspecialedition/mods/63308?tab=files&file_id=262896) V10.6.2 (file ID 262896) |
| `Embers XD.esp` | [Embers XD](https://www.nexusmods.com/skyrimspecialedition/mods/37085?tab=files&file_id=821728) 3.3.0, main file "Embers XD 1K" (file ID 821728), the installer's default esm + esp output |
| `Unofficial Skyrim Special Edition Patch.esp` | [USSEP](https://www.nexusmods.com/skyrimspecialedition/mods/266?tab=files&file_id=800977) 4.3.9c (file ID 800977), named in lower case in the archive: rename it to this |

`Cutting Room Floor.esp` (3.1.26, file ID 796288) is a master of the `tposc-ground` plugin but not a build input: `headers.tsv` already holds the values.

```
python3 build.py            # dry run: prints records and masters
python3 build.py --write    # writes dist/tposc-ground and dist/crf-ground, round-trip checks both
python3 build.py --fresh    # re-serializes inputs/ first
```
