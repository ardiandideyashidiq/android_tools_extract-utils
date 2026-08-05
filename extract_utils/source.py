#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import annotations

import os
import re
import shutil
from abc import ABC, abstractmethod
from contextlib import contextmanager, suppress
from os import path
from typing import List, Optional

from extract_utils.console import info, warning
from extract_utils.extract import ExtractCtx, extract_dump
from extract_utils.file import File, FileArgs
from extract_utils.utils import file_path_sha1


class SourceCtx:
    def __init__(
        self,
        source: str,
        firmware_source_dir: Optional[str] = None,
    ):
        self.source = source
        self.firmware_source_dir = firmware_source_dir


class Source(ABC):
    @abstractmethod
    def _list_sub_path_file_rel_paths(self, sub_path: str) -> List[str]: ...

    @abstractmethod
    def _copy_file_path(
        self,
        file_path: str,
        target_file_path: str,
    ) -> bool: ...

    @abstractmethod
    def _copy_firmware(
        self,
        file: File,
        target_file_path: str,
    ) -> bool: ...

    def _copy_file_to_path(
        self,
        file: File,
        file_copy_path: str,
    ) -> bool:
        if FileArgs.TRYSRCFIRST in file.args:
            first = file.src
            second = file.dst
        else:
            first = file.dst
            second = file.src

        if self._copy_file_path(first, file_copy_path):
            return True

        if file.has_dst and self._copy_file_path(second, file_copy_path):
            return True

        return False

    def copy_file_to_path(
        self,
        file: File,
        file_path: str,
        is_firmware: bool = False,
    ) -> bool:
        file_dir = path.dirname(file_path)
        os.makedirs(file_dir, exist_ok=True)

        if is_firmware:
            return self._copy_firmware(file, file_path)

        return self._copy_file_to_path(file, file_path)

    def get_file_copy_path(self, file: File, copy_dir: str) -> str:
        return path.join(copy_dir, file.dst)

    def copy_file_to_dir(
        self,
        file: File,
        copy_dir: str,
        is_firmware: bool = False,
    ) -> bool:
        file_copy_path = self.get_file_copy_path(file, copy_dir)
        return self.copy_file_to_path(
            file,
            file_copy_path,
            is_firmware,
        )

    def find_sub_dir_files(
        self,
        sub_path: str,
        regex: Optional[str],
        skipped_file_rel_paths: List[str],
    ) -> List[str]:
        skipped_file_rel_paths_set = set(skipped_file_rel_paths)

        compiled_regex = None
        if regex is not None:
            compiled_regex = re.compile(regex)

        file_srcs: List[str] = []

        file_rel_paths = self._list_sub_path_file_rel_paths(sub_path)
        file_rel_paths.sort()

        for file_rel_path in file_rel_paths:
            if (
                compiled_regex is not None
                and compiled_regex.search(file_rel_path) is None
            ):
                continue

            if file_rel_path in skipped_file_rel_paths_set:
                continue

            file_src = f'{sub_path}/{file_rel_path}'
            file_srcs.append(file_src)

        return file_srcs


class DiskSource(Source):
    def __init__(
        self, dump_dir: str, firmware_source_dir: Optional[str] = None
    ):
        self.dump_dir = dump_dir
        self.firmware_source_dir = firmware_source_dir

    def _copy_firmware(self, file: File, target_file_path: str) -> bool:
        if self._copy_file_to_path(file, target_file_path):
            return True

        if self.firmware_source_dir is None:
            return False

        firmware_path = path.join(
            self.firmware_source_dir,
            'radio',
            file.dst,
        )

        if not path.isfile(firmware_path):
            return False

        if file.hash is not None and file_path_sha1(firmware_path) != file.hash:
            warning(
                f'{file.dst}: firmware source hash mismatch, skipping',
            )
            return False

        with suppress(Exception):
            shutil.copy(firmware_path, target_file_path)
            return True

        return False

    def _copy_file_path(
        self,
        file_path: str,
        target_file_path: str,
    ) -> bool:
        file_path = f'{self.dump_dir}/{file_path}'

        if not path.isfile(file_path):
            return False

        with suppress(Exception):
            shutil.copy(file_path, target_file_path)
            return True

        return False

    def _list_sub_path_file_rel_paths(self, sub_path: str) -> List[str]:
        dump_dir_sub_path = path.join(self.dump_dir, sub_path)

        file_rel_paths: List[str] = []

        for dir_path, _, file_names in os.walk(dump_dir_sub_path):
            dir_rel_path = path.relpath(dir_path, dump_dir_sub_path)
            if dir_rel_path == '.':
                dir_rel_path = ''

            for file_name in file_names:
                if dir_rel_path:
                    file_rel_path = f'{dir_rel_path}/{file_name}'
                else:
                    file_rel_path = file_name

                file_rel_paths.append(file_rel_path)

        return file_rel_paths


def create_disk_source(
    dump_dir: str,
    extract_ctx: ExtractCtx,
    firmware_source_dir: Optional[str] = None,
):
    extract_dump(dump_dir, extract_ctx)
    return DiskSource(dump_dir, firmware_source_dir)


@contextmanager
def create_source(ctx: SourceCtx, extract_ctx: ExtractCtx):
    source = ctx.source

    if not path.isdir(source):
        raise ValueError(f'Unexpected file type at {source}')

    # Source is a directory, try to extract its contents into itself
    info(f'Using source dump dir {source}')
    yield create_disk_source(
        source,
        extract_ctx,
        ctx.firmware_source_dir,
    )
