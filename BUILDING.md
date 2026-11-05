# Building from source

Back to [README.md](README.md). This repository contains no plugin data from other mods, only record IDs and field names.

Tested: macOS (arm64) only. Needs Python 3, the .NET 10 SDK and the `Spriggit.Yaml.Skyrim` 0.41.0 DLL (see the
`SPRIGGIT_DLL` lookup in `build.py`).

Put these in `inputs/`. `inputs.sha256` pins them and `build.py` refuses a mismatch, because `forward.tsv` was derived
from exactly these versions.

| File in `inputs/` | Where it comes from |
|---|---|
| `tpos_ultimate_esm.esp` | [TPOSC](https://www.nexusmods.com/skyrimspecialedition/mods/13196) V11.1.6, BSA version |
| `tposc_Embers XD_patch.esp` | [patch 63308](https://www.nexusmods.com/skyrimspecialedition/mods/63308) V10.6.2 |
| `Embers XD.esp` | [Embers XD](https://www.nexusmods.com/skyrimspecialedition/mods/37085) 3.3.0, default esm + esp install |
| `Unofficial Skyrim Special Edition Patch.esp` | [USSEP](https://www.nexusmods.com/skyrimspecialedition/mods/266), rename from the lower-case name in the archive |

```
python3 build.py            # dry run: prints records and masters
python3 build.py --write    # writes dist/ and round-trip checks it
python3 build.py --fresh    # re-serializes inputs/ first
```
