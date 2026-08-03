#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from argparse import ArgumentParser
from functools import cmp_to_key
from itertools import groupby
from locale import LC_ALL, setlocale, strcoll
from os import path
from pathlib import Path

from extract_utils.args import DOWNLOAD_DIR_ENV_KEY, FIRMWARE_SOURCE_DIR_ENV_KEY
from extract_utils.console import warning
from extract_utils.extract import (
    ExtractCtx,
    ExtractFn,
    extract_fns_type,
    move_alternate_partition_paths,
)
from extract_utils.extract_misc import ExtractRenameSuperToExtVolumeName
from extract_utils.extract_pixel import (
    copy_pixel_firmware,
    extract_pixel_factory_image,
    extract_pixel_firmware,
    pixel_factory_image_regex,
    pixel_firmware_regex,
)
from extract_utils.extract_star import (
    extract_star_firmware,
    star_firmware_regex,
)
from extract_utils.extract_super_retrofit import ExtractSuperRetrofit
from extract_utils.main import ExtractUtils, create_source
from extract_utils.source import SourceCtx
from extract_utils.utils import get_module_attr, import_module


def extract_files(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description='Extract device blobs from a firmware dump',
    )

    parser.add_argument(
        'device_tree_dir',
        nargs='?',
        help='path to the device tree containing extract-files.py',
    )
    parser.add_argument(
        'firmware_dump_dir',
        nargs='?',
        help='path to the firmware dump directory',
    )
    parser.add_argument(
        'old_vendor_tree',
        nargs='?',
        help=(
            'existing vendor tree to update in place; its radio/ files are '
            'also reused for proprietary-firmware missing from the dump '
            '(hash-checked when pinned)'
        ),
    )
    parser.add_argument(
        '--device-tree',
        dest='device_tree_flag',
        metavar='DEVICE_TREE',
        help='path to the device tree containing extract-files.py',
    )
    parser.add_argument(
        '--firmware-dump',
        dest='firmware_dump_flag',
        metavar='FIRMWARE_DUMP',
        help='path to the firmware dump directory',
    )
    parser.add_argument(
        '--vendor-tree',
        dest='old_vendor_flag',
        metavar='VENDOR_TREE',
        help=(
            'existing vendor tree to update in place; its radio/ files are '
            'also reused for proprietary-firmware missing from the dump '
            '(hash-checked when pinned)'
        ),
    )
    parser.add_argument(
        '-k',
        '--kang',
        action='store_true',
        help='kang and modify hashes',
    )
    parser.add_argument(
        '-s',
        '--section',
        help='only apply to section name matching pattern',
    )
    parser.add_argument(
        '--download-dir',
        help='path to directory into which to store downloads',
    )
    parser.add_argument(
        '--keep-dump',
        action='store_true',
        help='keep the dump directory',
    )

    args = parser.parse_args(argv)

    device_tree_dir = args.device_tree_flag or args.device_tree_dir
    firmware_dump_dir = args.firmware_dump_flag or args.firmware_dump_dir
    old_vendor_tree = args.old_vendor_flag or args.old_vendor_tree

    if device_tree_dir is None or firmware_dump_dir is None:
        parser.print_help()
        return

    os.environ['EXTRACT_UTILS_DEVICE_PATH'] = path.realpath(device_tree_dir)

    if old_vendor_tree is not None:
        os.environ[FIRMWARE_SOURCE_DIR_ENV_KEY] = path.realpath(old_vendor_tree)
        os.environ['EXTRACT_UTILS_VENDOR_PATH'] = path.realpath(old_vendor_tree)

    module_path = path.join(device_tree_dir, 'extract-files.py')
    device_module = import_module('device_module', module_path)
    module = get_module_attr(device_module, 'module')
    if module is None:
        raise ValueError(f'No module in {module_path}')

    sys.argv = [sys.argv[0], firmware_dump_dir]
    if args.kang:
        sys.argv.append('--kang')
    if args.section is not None:
        sys.argv += ['--section', args.section]
    if args.download_dir is not None:
        sys.argv += ['--download-dir', args.download_dir]
    if args.keep_dump:
        sys.argv.append('--keep-dump')

    ExtractUtils.device(module).run()


DEFAULT_EXTRACTED_PARTITIONS = [
    'odm',
    'product',
    'system',
    'system_ext',
    'vendor',
]


def extract(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description='Extract')

    parser.add_argument(
        '--partitions',
        nargs='+',
        type=str,
        help='Partitions to extract',
        default=DEFAULT_EXTRACTED_PARTITIONS,
    )
    parser.add_argument(
        '--extra-partitions',
        nargs='+',
        type=str,
        help='Extra partitions to extract',
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Extract all files from archive',
    )
    parser.add_argument(
        '--pixel-factory',
        nargs='*',
        type=str,
        help='Files to extract as pixel factory image',
    )
    parser.add_argument(
        '--pixel-firmware',
        nargs='*',
        type=str,
        help='Files to extract as pixel firmware',
    )
    parser.add_argument(
        '--star-firmware',
        nargs='*',
        type=str,
        help='Files to extract as star firmware',
    )
    parser.add_argument(
        '--retrofit-super-partitions',
        nargs='*',
        type=str,
        help='Partitions in retrofit super, in order',
    )
    parser.add_argument(
        '--rename-super-to-volume-name',
        action='store_true',
        help='Rename super_*.img images to their volume name',
    )
    parser.add_argument(
        '--download-dir',
        help='path to directory into which to store downloads',
    )
    parser.add_argument(
        '--download-sha256',
        help='SHA256 of the download',
    )

    parser.add_argument(
        'source',
        help='sources from which to extract',
        nargs='?',
    )

    args = parser.parse_args(argv)

    if args.pixel_factory is not None and not args.pixel_factory:
        args.pixel_factory = [pixel_factory_image_regex]

    if args.pixel_firmware is not None and not args.pixel_firmware:
        args.pixel_firmware = [pixel_firmware_regex]

    if args.star_firmware is not None and not args.star_firmware:
        args.star_firmware = [star_firmware_regex]

    extract_fns: extract_fns_type = []

    if args.pixel_factory:
        for extract_pattern in args.pixel_factory:
            extract_fns.append(
                ExtractFn(extract_pattern, extract_pixel_factory_image)
            )

    if args.pixel_firmware:
        for extract_pattern in args.pixel_firmware:
            extract_fns.append(
                ExtractFn(
                    extract_pattern,
                    path_fns=[
                        copy_pixel_firmware,
                        extract_pixel_firmware,
                    ],
                )
            )

    if args.star_firmware:
        for extract_pattern in args.star_firmware:
            extract_fns.append(
                ExtractFn(extract_pattern, extract_star_firmware)
            )

    if args.retrofit_super_partitions:
        extract_fns.append(ExtractSuperRetrofit(args.retrofit_super_partitions))

    if args.rename_super_to_volume_name:
        extract_fns.append(ExtractRenameSuperToExtVolumeName())

    download_dir = args.download_dir

    if download_dir is None and DOWNLOAD_DIR_ENV_KEY in os.environ:
        download_dir = os.environ[DOWNLOAD_DIR_ENV_KEY]

    extract_partitions = args.partitions
    if args.extra_partitions is not None:
        extract_partitions += args.extra_partitions

    extract_ctx = ExtractCtx(
        extract_partitions=extract_partitions,
        extract_fns=extract_fns,
    )

    source_ctx = SourceCtx(
        args.source,
        True,
        download_dir,
        args.download_sha256,
    )

    with create_source(source_ctx, extract_ctx):
        pass


def convert_dump(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description='Convert extract dump from bash extract_utils'
        'to python extract_utils structure',
    )

    parser.add_argument(
        'dump_dir',
        help='dump directory',
        nargs='*',
    )

    args = parser.parse_args(argv)

    for dump_dir in args.dump_dir:
        dump_output_dir = path.join(dump_dir, 'output')

        if path.isdir(dump_output_dir):
            for file in os.scandir(dump_output_dir):
                shutil.move(file.path, dump_dir)

            shutil.rmtree(dump_output_dir)

        move_alternate_partition_paths(dump_dir)


def is_blob(line: str) -> bool:
    line = line.strip()
    return bool(line) and not line.startswith('#')


def get_source_file_name(line: str) -> str:
    # - Remove '-' from strings if there, it is used to indicate a build target
    # - Discard anything after:
    #   - ':' (destination path)
    #   - ';' (additional options)
    #   - '|' (sha1sum hash)
    regex_match = re.match(r'^-?(.+?)(?:[:;\|].*?)?$', line)

    if not regex_match:
        return line

    return regex_match.group(1)


def strcoll_extract_utils(
    string1: str, string2: str, dir_first: bool = False
) -> int:
    # Skip logic if one of the string if empty
    if not string1 or not string2:
        return strcoll(string1, string2)

    # Get the source file name
    string1 = get_source_file_name(string1)
    string2 = get_source_file_name(string2)

    if dir_first:
        # If no directories, compare normally
        if '/' not in string1 and '/' not in string2:
            return strcoll(string1, string2)

        string1_dir = string1.rsplit('/', 1)[0] + '/'
        string2_dir = string2.rsplit('/', 1)[0] + '/'
        if string1_dir == string2_dir:
            # Same directory, compare normally
            return strcoll(string1, string2)

        if string1_dir.startswith(string2_dir):
            # First string dir is a subdirectory of the second one,
            # return string1 > string2
            return -1

        if string2_dir.startswith(string1_dir):
            # Second string dir is a subdirectory of the first one,
            # return string2 > string1
            return 1

    # Compare normally
    return strcoll(string1, string2)


def sort_blobs_list(argv: list[str] | None = None):
    setlocale(LC_ALL, 'C')

    parser = ArgumentParser(description='Sort blobs list')
    parser.add_argument(
        'files',
        nargs='*',
        default=['proprietary-files.txt'],
        help='Files to sort',
    )
    parser.add_argument(
        '--dir-first',
        action='store_true',
        help='Sort directories first',
    )
    args = parser.parse_args(argv)

    sort_key = cmp_to_key(
        lambda x, y: strcoll_extract_utils(x, y, args.dir_first)
    )

    for file in args.files:
        if not Path(file).is_file():
            warning(f'File {file} not found')
            continue

        with open(file, 'r', encoding='utf-8') as f:
            sections = groupby(f.readlines(), is_blob)

        ordered_sections = []
        for sort, section in sections:
            if sort:
                ordered_sections.append(''.join(sorted(section, key=sort_key)))
            else:
                ordered_sections.append(''.join(section))

        with open(file, 'w', encoding='utf-8') as f:
            f.write(''.join(ordered_sections))
