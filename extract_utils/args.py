#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import annotations

import argparse
import os
from typing import Optional

parser = argparse.ArgumentParser(description='Extract utils')

parser.add_argument(
    '-n',
    '--no-cleanup',
    action='store_true',
    help='do not cleanup vendor',
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
    '-m',
    '--regenerate_makefiles',
    action='store_true',
    help='regenerate makefiles',
)
parser.add_argument(
    '-r',
    '--regenerate',
    action='store_true',
    help='regenerate proprietary files',
)
parser.add_argument(
    '-l',
    '--legacy',
    action='store_true',
    help='generate legacy makefiles',
)
parser.add_argument(
    '--allow-prohibited-files',
    action='store_true',
    help='Allow extraction of normally-prohibited files',
)
parser.add_argument(
    '--firmware-source-dir',
    help=(
        'directory of a previous vendor tree from which to reuse '
        'proprietary-firmware files missing from the source'
    ),
)

parser.add_argument(
    'source',
    help='firmware dump directory from which to extract',
)

FIRMWARE_SOURCE_DIR_ENV_KEY = 'EXTRACT_UTILS_FIRMWARE_SOURCE_DIR'


class Args:
    def __init__(self, args: argparse.Namespace):
        # Wrap to provide type hints
        self.regenerate_makefiles: bool = args.regenerate_makefiles
        self.regenerate: bool = args.regenerate
        self.legacy: bool = args.legacy
        self.no_cleanup: bool = args.no_cleanup
        self.kang: bool = args.kang
        self.section: Optional[str] = args.section
        self.allow_prohibited_files: bool = args.allow_prohibited_files
        self.firmware_source_dir: Optional[str] = args.firmware_source_dir

        if (
            self.firmware_source_dir is None
            and FIRMWARE_SOURCE_DIR_ENV_KEY in os.environ
        ):
            self.firmware_source_dir = os.environ[FIRMWARE_SOURCE_DIR_ENV_KEY]

        self.source: str = args.source

        if self.section is not None:
            self.regenerate = False

        if self.regenerate_makefiles:
            self.regenerate = False


def parse_args():
    parser_args = parser.parse_args()
    return Args(parser_args)
