#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import annotations

from typing import Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table

console = Console()
if not console.is_terminal:
    console.width = 140

progress = Progress(
    TextColumn('[bold]{task.description}'),
    BarColumn(),
    TextColumn('{task.completed}/{task.total}'),
    console=console,
)

INFO_STYLE = 'bold'
SUCCESS_STYLE = 'bold green'
WARNING_STYLE = 'bold yellow'
ERROR_STYLE = 'bold red'


def info(*args: Any):
    console.print(*args, style=INFO_STYLE)


def success(*args: Any):
    console.print(*args, style=SUCCESS_STYLE)


def warning(*args: Any):
    console.print(*args, style=WARNING_STYLE)


def error(*args: Any):
    console.print(*args, style=ERROR_STYLE)


def detail(prefix: str, message: str):
    console.print(f'  {prefix} {message}', style='dim')


def rule(title: str = ''):
    console.rule(title)


def track(
    sequence,
    description: str = '',
    total: Optional[int] = None,
    transient: bool = False,
):
    return progress.track(
        sequence,
        description=description,
        total=total,
        transient=transient,
    )


def panel(
    renderable: Any,
    title: Optional[str] = None,
    style: str = 'none',
):
    console.print(Panel(renderable, title=title, style=style))


def table(
    title: str,
    columns: list[str],
    rows: list[list[str]],
    width: Optional[int] = None,
) -> Table:
    tbl = Table(title=title, width=width)
    for column in columns:
        tbl.add_column(column, overflow='fold')
    for row in rows:
        tbl.add_row(*row)
    return tbl
