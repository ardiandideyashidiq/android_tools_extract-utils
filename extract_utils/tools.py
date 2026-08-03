#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import annotations

import os
import shutil
from os import path
from typing import Dict, Optional

patchelf_versions = ['0_8', '0_9', '0_17_2', '0_18']
DEFAULT_PATCHELF_VERSION = '0_18'

script_dir = path.dirname(path.realpath(__file__))
# Android source root. Only meaningful when this repo is checked out at
# <android_root>/tools/extract-utils/; resolved as a fallback for in-tree
# usage and still needed by extract_utils/module.py and main.py.
android_root = path.realpath(path.join(script_dir, '..', '..', '..'))

sdat2img_path = path.join(script_dir, 'sdat2img.py')

# Lives inside the package so it ships in wheels and resolves identically
# from a checkout and an installed wheel.
prebuilts_dir = path.join(script_dir, 'prebuilts')


def resolve_tool(
    env_key: str,
    repo_rel_path: str,
    android_rel_path: str,
    sys_fallback: Optional[str] = None,
) -> str:
    """Resolve a tool path, in order of priority:

    1. ``EXTRACT_UTILS_*`` environment variable override
    2. A prebuilt vendored inside this repo (``prebuilts/``)
    3. The same tool in the Android source tree (in-tree usage)
    4. A system executable found on ``PATH`` (optional)
    """
    env_path = os.environ.get(env_key)
    if env_path:
        return env_path

    repo_path = path.join(prebuilts_dir, repo_rel_path)
    if path.isfile(repo_path):
        return repo_path

    android_path = path.join(android_root, android_rel_path)
    if path.isfile(android_path):
        return android_path

    if sys_fallback is not None:
        sys_path = shutil.which(sys_fallback)
        if sys_path:
            return sys_path

    return android_path


binaries_dir_rel_path = 'prebuilts/extract-tools/linux-x86/bin'
binaries_dir = path.join(android_root, binaries_dir_rel_path)
ota_extractor_path = resolve_tool(
    'EXTRACT_UTILS_OTA_EXTRACTOR',
    'extract-tools/linux-x86/bin/ota_extractor',
    binaries_dir_rel_path + '/ota_extractor',
)
stripzip_path = resolve_tool(
    'EXTRACT_UTILS_STRIPZIP',
    'extract-tools/linux-x86/bin/stripzip',
    binaries_dir_rel_path + '/stripzip',
)

patchelf_version_path_map: Dict[str, str] = {}
for version in patchelf_versions:
    patchelf_version_path_map[version] = resolve_tool(
        f'EXTRACT_UTILS_PATCHELF_{version}',
        f'extract-tools/linux-x86/bin/patchelf-{version}',
        f'{binaries_dir_rel_path}/patchelf-{version}',
    )

build_tools_dir_rel_path = 'prebuilts/build-tools/linux-x86/bin'
build_tools_dir = path.join(android_root, build_tools_dir_rel_path)
brotli_path = resolve_tool(
    'EXTRACT_UTILS_BROTLI',
    'build-tools/linux-x86/bin/brotli',
    build_tools_dir_rel_path + '/brotli',
)

common_binaries_dir_rel_path = 'prebuilts/extract-tools/common'
common_binaries_dir = path.join(android_root, common_binaries_dir_rel_path)
apktool_path = resolve_tool(
    'EXTRACT_UTILS_APKTOOL',
    'extract-tools/common/apktool/apktool.jar',
    common_binaries_dir_rel_path + '/apktool/apktool.jar',
)

jdk_binaries_dir_rel_path = 'prebuilts/jdk/jdk21/linux-x86/bin'
jdk_binaries_dir = path.join(android_root, jdk_binaries_dir_rel_path)
java_path = resolve_tool(
    'EXTRACT_UTILS_JAVA',
    'jdk/jdk21/linux-x86/bin/java',
    jdk_binaries_dir_rel_path + '/java',
    sys_fallback='java',
)

llvm_binaries_dir_rel_path = (
    'prebuilts/clang/host/linux-x86/llvm-binutils-stable'
)
llvm_binaries_dir = path.join(android_root, llvm_binaries_dir_rel_path)
llvm_objdump_path = resolve_tool(
    'EXTRACT_UTILS_LLVM_OBJDUMP',
    'clang/host/linux-x86/llvm-binutils-stable/llvm-objdump',
    llvm_binaries_dir_rel_path + '/llvm-objdump',
    sys_fallback='llvm-objdump',
)
llvm_strip_path = resolve_tool(
    'EXTRACT_UTILS_LLVM_STRIP',
    'clang/host/linux-x86/llvm-binutils-stable/llvm-strip',
    llvm_binaries_dir_rel_path + '/llvm-strip',
    sys_fallback='llvm-strip',
)

lineage_scripts_dir_rel_path = 'prebuilts/lineage/scripts'
lineage_scripts_dir = path.join(android_root, lineage_scripts_dir_rel_path)
carriersettings_extractor_path = resolve_tool(
    'EXTRACT_UTILS_CARRIERSETTINGS_EXTRACTOR',
    'lineage/scripts/carriersettings-extractor/carriersettings_extractor.py',
    lineage_scripts_dir_rel_path
    + '/carriersettings-extractor/carriersettings_extractor.py',
)
fbpacktool_path = resolve_tool(
    'EXTRACT_UTILS_FBPACKTOOL',
    'lineage/scripts/fbpacktool/fbpacktool.py',
    lineage_scripts_dir_rel_path + '/fbpacktool/fbpacktool.py',
)

system_tools_dir_rel_path = 'prebuilts/system/tools'
system_tools_dir = path.join(android_root, system_tools_dir_rel_path)
mkbootimg_dir_rel_path = 'prebuilts/system/tools/mkbootimg'
mkbootimg_dir = path.join(android_root, mkbootimg_dir_rel_path)
unpack_bootimg_path = resolve_tool(
    'EXTRACT_UTILS_UNPACK_BOOTIMG',
    'system/tools/mkbootimg/unpack_bootimg',
    mkbootimg_dir_rel_path + '/unpack_bootimg.py',
)
