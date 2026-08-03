# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0

# extract-utils

Python rewrite of the LineageOS bash `extract-utils`, for extracting device
proprietary blobs from firmware dumps. It works **standalone** (no Android
source tree needed) and also inside an Android tree. Host tools are vendored
under `extract_utils/prebuilts/` so extraction works out of the box.

## Install

Install as a uv tool (all commands become available on `PATH`):

```sh
uv tool install git+https://github.com/ardiandideyashidiq/android_tools_extract-utils
```

To track repository changes instead of a pinned build, install editable from a
local checkout:

```sh
git clone https://github.com/ardiandideyashidiq/android_tools_extract-utils
uv tool install --editable ./android_tools_extract-utils
```

## Usage

```sh
extract-files --device-tree <device-tree-dir> \
  --firmware-dump <firmware-dump-dir> \
  [--vendor-tree <old-vendor-tree>]
```

- Without `--vendor-tree`, output goes to `android_vendor_<vendor>_<device>`
  next to the device tree.
- With `--vendor-tree`, the existing vendor tree is updated in place and its
  `radio/` firmware is reused for proprietary-firmware missing from the dump
  (hash-checked when pinned).

Other commands: `extract`, `convert-dump`, `sort-blobs-list`.
