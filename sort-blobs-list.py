#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

import sys

from extract_utils.cli import sort_blobs_list

if __name__ == '__main__':
    sort_blobs_list(sys.argv[1:])
