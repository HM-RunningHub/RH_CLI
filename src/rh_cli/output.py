from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rich.console import Console

from .config import default_output_dir


@dataclass(slots=True)
class RunResult:
    files: list[str]
    texts: list[str]
    cost: str | None = None
    duration: str | int | float | None = None
    task_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "files": self.files,
            "texts": self.texts,
            "cost": self.cost,
            "duration": self.duration,
            "task_id": self.task_id,
        }


def resolve_output_path(
    output: str | None,
    *,
    output_dir: Path | None,
    default_name: str,
    ext: str,
    index: int | None = None,
) -> Path:
    if output:
        path = Path(output).expanduser()
        if path.exists() and path.is_dir():
            base = path / default_name
        elif output.endswith(("/", "\\")):
            base = path / default_name
        else:
            base = path
    else:
        base_dir = output_dir or default_output_dir()
        base = base_dir / default_name

    if index is not None:
        stem = base.stem
        suffix = base.suffix
        base = base.with_name(f"{stem}_{index}{suffix}")

    if ext and base.suffix.lower() != f".{ext.lower()}":
        base = base.with_suffix(f".{ext}")
    base.parent.mkdir(parents=True, exist_ok=True)
    return base


def print_result(console: Console, result: RunResult, *, json_output: bool = False) -> None:
    if json_output:
        console.print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return
    for text in result.texts:
        console.print(text)
    for path in result.files:
        console.print(f"[green]OUTPUT_FILE:[/green]{path}")
    if result.cost is not None:
        console.print(f"[cyan]花费：¥{result.cost}[/cyan]")
    if result.duration not in (None, "", "0", 0):
        console.print(f"[cyan]耗时：{result.duration}s[/cyan]")
