#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

import sys

from extract_utils.cli import convert_dump

if __name__ == '__main__':
    convert_dump(sys.argv[1:])
