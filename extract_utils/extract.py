#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import annotations

import os
import shutil
from os import path
from typing import List, Optional

from extract_utils.console import warning
from extract_utils.file import File

ALTERNATE_PARTITION_PATH_MAP = {
    'product': 'system/product',
    'system_ext': 'system/system_ext',
    'vendor': 'system/vendor',
    'odm': 'vendor/odm',
}


class ExtractCtx:
    def __init__(
        self,
        extract_partitions: Optional[List[str]] = None,
        firmware_files: Optional[List[File]] = None,
    ):
        if extract_partitions is None:
            extract_partitions = []
        if firmware_files is None:
            firmware_files = []

        # Files for partitions are extracted if, after removing the
        # extension, their name matches a partition
        self.extract_partitions = extract_partitions
        # Files are extracted if their name matches as-is
        self.firmware_files = firmware_files


def find_partitions(dump_dir: str, ctx: ExtractCtx, missing: bool = False):
    partitions: List[str] = []
    for partition in ctx.extract_partitions:
        dump_partition_dir = path.join(dump_dir, partition)
        exists = (
            path.isdir(dump_partition_dir)
            and len(os.listdir(dump_partition_dir)) != 0
        )

        if exists != missing:
            partitions.append(partition)

    return partitions


def _find_files(dump_dir: str, files: List[File], missing: bool = False):
    found_files: List[File] = []
    for file in files:
        src_file_path = path.join(dump_dir, file.src)
        dst_file_path = path.join(dump_dir, file.dst)
        exists = path.isfile(src_file_path) or path.isfile(dst_file_path)

        if exists != missing:
            found_files.append(file)

    return found_files


def find_firmware_files(dump_dir: str, ctx: ExtractCtx, missing: bool = False):
    return _find_files(dump_dir, ctx.firmware_files, missing)


def extract_dump(dump_dir: str, ctx: ExtractCtx):
    should_extract = filter_already_extracted(dump_dir, ctx)
    if not should_extract:
        move_sar_system_paths(dump_dir)
        return

    move_sar_system_paths(dump_dir)
    move_alternate_partition_paths(dump_dir)

    create_empty_partition_dirs(dump_dir, ctx)


def create_empty_partition_dirs(dump_dir: str, ctx: ExtractCtx):
    missing_partitions = find_partitions(dump_dir, ctx, missing=True)
    for partition in missing_partitions:
        dump_partition_dir = path.join(dump_dir, partition)
        warning(f'Partition {partition} not extracted')
        # Create empty partition dir to prevent re-extraction
        os.makedirs(dump_partition_dir, exist_ok=True)


def move_alternate_partition_paths(dump_dir: str):
    # Make sure that even for devices that don't have separate partitions
    # for vendor, odm, etc., the partition directories are copied into the root
    # dump directory to simplify file copying
    for (
        partition,
        alternate_partition_path,
    ) in ALTERNATE_PARTITION_PATH_MAP.items():
        partition_path = path.join(dump_dir, partition)
        if path.isdir(partition_path):
            continue

        partition_path = path.join(dump_dir, alternate_partition_path)
        if not path.isdir(partition_path):
            continue

        shutil.move(partition_path, dump_dir)


def move_sar_system_paths(dump_dir: str):
    # For System-as-Root, move system/ to system_root/ and system/system/
    # to system/
    system_dir = path.join(dump_dir, 'system')
    system_system_dir = path.join(system_dir, 'system')
    if path.isdir(system_system_dir):
        system_root_dir = path.join(dump_dir, 'system_root')
        system_root_system_dir = path.join(system_root_dir, 'system')

        shutil.move(system_dir, system_root_dir)
        shutil.move(system_root_system_dir, dump_dir)


def filter_already_extracted(dump_dir: str, ctx: ExtractCtx):
    ctx.extract_partitions = find_partitions(dump_dir, ctx, missing=True)
    ctx.firmware_files = find_firmware_files(dump_dir, ctx, missing=True)
    return ctx.extract_partitions or ctx.firmware_files
