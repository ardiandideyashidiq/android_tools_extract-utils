#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import annotations

import os
import sys
from os import path
from typing import List, Optional, Set, Tuple

from extract_utils.args import parse_args
from extract_utils.console import console, error, rule, table
from extract_utils.extract import ExtractCtx, extract_fns_type
from extract_utils.file import File
from extract_utils.module import (
    ExtractUtilsModule,
    ProprietaryFileType,
)
from extract_utils.postprocess import PostprocessCtx
from extract_utils.source import Source, SourceCtx, create_source
from extract_utils.tools import android_root
from extract_utils.utils import (
    get_module_attr,
    import_module,
)


class ExtractUtils:
    def __init__(
        self,
        device_module: ExtractUtilsModule,
        common_modules: Optional[List[ExtractUtilsModule]] = None,
    ):
        if common_modules is None:
            common_modules = []

        self.__args = parse_args()

        self.__modules: List[ExtractUtilsModule] = []
        if self.__args.only_name:
            all_modules = [device_module] + common_modules
            for module in all_modules:
                if module.device == self.__args.only_name:
                    self.__modules.append(module)
        elif self.__args.only_target:
            self.__modules.append(device_module)
        elif self.__args.only_common:
            self.__modules.extend(common_modules)
        else:
            self.__modules = [device_module]
            self.__modules.extend(common_modules)

    @classmethod
    def device_with_commons(
        cls,
        device_module: ExtractUtilsModule,
        device_vendor_commons: List[Tuple[str] | Tuple[str, str]],
    ):
        common_modules: List[ExtractUtilsModule] = []
        for device_vendor_common in device_vendor_commons:
            device_common = device_vendor_common[0]
            if len(device_vendor_common) == 2:
                vendor_common = device_vendor_common[1]
            else:
                vendor_common = device_module.vendor

            common_module = cls.get_module(device_common, vendor_common)
            common_modules.append(common_module)

        return cls(device_module, common_modules)

    @classmethod
    def device_with_common(
        cls,
        device_module: ExtractUtilsModule,
        device_common: str,
        vendor_common: Optional[str] = None,
    ):
        if vendor_common is None:
            vendor_common = device_module.vendor

        return cls.device_with_commons(
            device_module,
            [
                (device_common, vendor_common),
            ],
        )

    @classmethod
    def device(cls, device_module: ExtractUtilsModule):
        return cls(device_module)

    @classmethod
    def import_module(
        cls,
        device: str,
        vendor: str,
    ) -> Optional[ExtractUtilsModule]:
        module_name = f'{vendor}_{device}'

        module_dir = os.environ.get('EXTRACT_UTILS_DEVICE_PATH')
        if module_dir is None:
            module_dir = path.join(android_root, 'device', vendor, device)
            if not path.isdir(module_dir):
                module_dir = path.join(
                    path.dirname(path.dirname(path.realpath(sys.argv[0]))),
                    f'android_device_{vendor}_{device}',
                )

        module_path = path.join(module_dir, 'extract-files.py')

        module = import_module(module_name, module_path)

        return get_module_attr(module, 'module')

    @classmethod
    def get_module(cls, device: str, vendor: str):
        module = cls.import_module(device, vendor)
        assert module is not None
        return module

    def process_modules(self, source: Source):
        all_copied = True
        for module in self.__modules:
            copied = module.process(
                source,
                self.__args.kang,
                self.__args.no_cleanup,
                self.__args.extract_factory,
                self.__args.section,
                self.__args.allow_prohibited_files,
            )
            if not copied:
                all_copied = False
        return all_copied

    def parse_modules(self):
        for module in self.__modules:
            module.parse(
                self.__args.regenerate,
                self.__args.section,
            )

    def regenerate_modules(self, source: Source):
        for module in self.__modules:
            module.regenerate(
                source,
                self.__args.regenerate,
            )

    def write_updated_proprietary_files(self):
        for module in self.__modules:
            module.write_updated_proprietary_files(
                self.__args.kang,
                self.__args.regenerate,
            )

    def postprocess_modules(self):
        ctx = PostprocessCtx()

        for module in self.__modules:
            for postprocess_fn in module.postprocess_fns:
                postprocess_fn(ctx)

    def write_makefiles(self):
        for module in self.__modules:
            module.write_makefiles(
                self.__args.legacy,
                self.__args.extract_factory,
            )

    def run(self):
        extract_fns: extract_fns_type = []
        extract_partitions: Set[str] = set()
        firmware_files: List[File] = []
        factory_files: List[File] = []

        self.parse_modules()

        for module in self.__modules:
            os.makedirs(module.vendor_path, exist_ok=True)

        if not self.__args.regenerate_makefiles:
            for module in self.__modules:
                extract_fns.extend(module.extract_fns)

                extract_partitions.update(
                    module.get_extract_partitions(self.__args.section),
                )
                firmware_files.extend(
                    module.get_firmware_files(),
                )
                factory_files.extend(
                    module.get_factory_files(),
                )

            extract_ctx = ExtractCtx(
                extract_fns,
                list(extract_partitions),
                firmware_files,
                factory_files,
            )

            source_ctx = SourceCtx(
                self.__args.source,
                self.__args.keep_dump,
                self.__args.download_dir,
                self.__args.download_sha256,
                self.__args.firmware_source_dir,
            )

            with create_source(source_ctx, extract_ctx) as source:
                self.regenerate_modules(source)

                all_copied = self.process_modules(source)
                if not all_copied:
                    error(
                        'Some files failed to process, exiting',
                    )
                    self.print_summary()
                    return

            self.postprocess_modules()

        self.write_updated_proprietary_files()
        self.write_makefiles()
        self.print_summary()

    def print_summary(self):
        rows = []
        for module in self.__modules:
            firmware_names = sorted(
                set(
                    file.root
                    for pf in module.proprietary_files
                    if pf.kind is ProprietaryFileType.FIRMWARE
                    for file in pf.file_list.files
                )
            )
            partitions = sorted(
                set(
                    partition
                    for pf in module.proprietary_files
                    if pf.kind is ProprietaryFileType.BLOBS
                    for partition in pf.file_list.partitions
                )
            )
            total = sum(
                len(list(pf.file_list.files)) for pf in module.proprietary_files
            )
            rows.append(
                [
                    f'{module.vendor}/{module.device}',
                    ', '.join(partitions),
                    str(total),
                    str(module.stats['copied']),
                    str(module.stats['fixed_up']),
                    str(
                        module.stats['pinned_restored']
                        + module.stats['pinned_found']
                    ),
                    str(module.stats['pinned_mismatch']),
                    str(module.stats['firmware']),
                    ', '.join(firmware_names),
                    str(module.stats['failed']),
                ]
            )
        tbl = table(
            'Extraction summary',
            [
                'module',
                'partitions',
                'blobs',
                'copied',
                'fixed up',
                'pinned ok',
                'pinned mismatch',
                'firmware',
                'firmware names',
                'failed',
            ],
            rows,
        )
        rule('Summary')
        console.print(tbl)
