# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0

# extract_utils/prebuilts/

Vendored host tools so that `extract-utils` can run **standalone**, without an
Android source tree. This directory lives inside the package so it ships in
wheels and resolves identically from a checkout or an installed wheel.
`extract_utils/tools.py` resolves every tool via:

1. `EXTRACT_UTILS_*` env var override
2. This `prebuilts/` directory (package-local)
3. The Android source tree (`<android_root>/prebuilts/...`, in-tree usage)
4. System `PATH` (only for java/llvm)

## Contents

| Tool | Layout | License |
|---|---|---|
| `brotli` | `build-tools/linux-x86/bin/` | MIT |
| `ota_extractor` | `extract-tools/linux-x86/bin/` | Apache-2.0 |
| `patchelf-0_8`/`0_9`/`0_17_2`/`0_18` | `extract-tools/linux-x86/bin/` | GPL-3.0-or-later |
| `stripzip` | `extract-tools/linux-x86/bin/` | Apache-2.0 |
| `apktool.jar` | `extract-tools/common/apktool/` | Apache-2.0 |
| `unpack_bootimg` | `system/tools/mkbootimg/` | Apache-2.0 |

`java` is **not** vendored (a full JDK is too large) — it falls back to system
`java` via `PATH`. `llvm-strip`/`llvm-objdump`/`fbpacktool.py`/
`carriersettings_extractor.py` are also not vendored; resolve via env var or
system `PATH` when needed.

## Sources

- `brotli`, `ota_extractor`, `unpack_bootimg`: copied from a prebuilt host
  tools directory (e.g. `<android>/prebuilts/...` or `host/linux-x86/bin`).
- `patchelf-*`, `stripzip`, `apktool.jar`: from
  `LineageOS/android_prebuilts_extract-tools` (branch `lineage-23.2`), e.g.:

  ```sh
  curl -L -o extract_utils/prebuilts/extract-tools/linux-x86/bin/patchelf-0_18 \
    https://raw.githubusercontent.com/LineageOS/android_prebuilts_extract-tools/lineage-23.2/linux-x86/bin/patchelf-0_18
  ```

Refresh from upstream by re-downloading; keep the REUSE annotations in
`REUSE.toml` in sync.
