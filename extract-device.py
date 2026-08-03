#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

import sys

from extract_utils.cli import extract_files

if __name__ == '__main__':
    extract_files(sys.argv[1:])
