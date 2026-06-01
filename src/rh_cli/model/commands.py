from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.table import Table

from rh_cli.catalog import find_endpoint, list_endpoints
from rh_cli.errors import RhCliError
from rh_cli.model.client import execute_model
from rh_cli.output import print_result
from rh_cli.state import CliState

from .menus import IMAGE_CHOICES, VIDEO_CHOICES, endpoint_for_choice, find_choice
from .payload import ModelRunInput


model_app = typer.Typer(help="运行 RunningHub 标准模型 API。")


def _state(ctx: typer.Context) -> CliState:
    return ctx.obj if isinstance(ctx.obj, CliState) else CliState()


@model_app.command("list")
def list_models(
    ctx: typer.Context,
    output_type: str | None = typer.Option(None, "--type", help="按输出类型过滤：image/video/audio/3d/string。"),
    task: str | None = typer.Option(None, "--task", help="按任务类型过滤。"),
) -> None:
    state = _state(ctx)
    endpoints = list_endpoints(output_type=output_type, task=task)
    if state.json_output:
        state.out.print(json.dumps({"total": len(endpoints), "endpoints": endpoints}, ensure_ascii=False, indent=2))
        return

    table = Table(title=f"RunningHub Endpoints ({len(endpoints)})")
    table.add_column("Type")
    table.add_column("Task")
    table.add_column("Rank", justify="right")
    table.add_column("Endpoint")
    table.add_column("Name")
    for item in endpoints:
        rank = item.get("popularity", 99)
        table.add_row(
            str(item.get("output_type", "")),
            str(item.get("task", "")),
            "-" if rank == 99 else str(rank),
            str(item.get("endpoint", "")),
            str(item.get("name_cn") or item.get("name_en") or ""),
        )
    state.out.print(table)


@model_app.command("info")
def info(ctx: typer.Context, endpoint: str = typer.Argument(..., help="端点 ID。")) -> None:
    state = _state(ctx)
    endpoint_def = find_endpoint(endpoint)
    if not endpoint_def:
        raise RhCliError("ENDPOINT_NOT_FOUND", f"找不到端点：{endpoint}")
    state.out.print(json.dumps(endpoint_def, ensure_ascii=False, indent=2))


@model_app.command("run")
def run_model(
    ctx: typer.Context,
    endpoint: str | None = typer.Option(None, "--endpoint", "-e", help="指定端点 ID。"),
    task: str | None = typer.Option(None, "--task", "-t", help="按任务自动选择最佳端点。"),
    prompt: str | None = typer.Option(None, "--prompt", "-p", help="文本提示词。"),
    image: list[str] = typer.Option([], "--image", "-i", help="输入图片，可重复。"),
    video: str | None = typer.Option(None, "--video", help="输入视频。"),
    audio: str | None = typer.Option(None, "--audio", help="输入音频。"),
    param: list[str] = typer.Option([], "--param", help="附加参数 key=value，可重复。"),
    output: str | None = typer.Option(None, "--output", "-o", help="输出文件或目录。"),
) -> None:
    state = _state(ctx)
    with state.out.status("提交 RunningHub 任务并等待结果...", spinner="dots"):
        result = execute_model(
            api_key_arg=state.api_key,
            endpoint=endpoint,
            task=task,
            run_input=ModelRunInput(prompt=prompt, images=image, video=video, audio=audio, params=param),
            output=output,
            output_dir=state.output_dir,
            console=state.out if state.verbose else None,
        )
    print_result(state.out, result, json_output=state.json_output)


def _choose_model(ctx: typer.Context, raw_model: str | None, image_mode: bool) -> tuple[str, str]:
    state = _state(ctx)
    choices = IMAGE_CHOICES if image_mode else VIDEO_CHOICES
    if raw_model:
        choice = find_choice(raw_model, choices)
    else:
        table = Table(title="请选择模型")
        table.add_column("#")
        table.add_column("模型")
        table.add_column("特点")
        for item in choices:
            table.add_row(str(item.number), item.name, item.description)
        state.out.print(table)
        selected = typer.prompt("说个数字就行，不填默认 1", default="1")
        choice = find_choice(selected, choices)
    return choice.name, endpoint_for_choice(choice, has_input_image=False)


def run_shortcut(
    ctx: typer.Context,
    *,
    image_mode: bool,
    model: str | None,
    prompt: str,
    images: list[str],
    param: list[str],
    output: str | None,
) -> None:
    state = _state(ctx)
    choices = IMAGE_CHOICES if image_mode else VIDEO_CHOICES
    if model:
        choice = find_choice(model, choices)
    else:
        table = Table(title="图片模型" if image_mode else "视频模型")
        table.add_column("#")
        table.add_column("模型")
        table.add_column("特点")
        for item in choices:
            table.add_row(str(item.number), item.name, item.description)
        state.out.print(table)
        selected = typer.prompt("说个数字就行，不填默认 1", default="1")
        choice = find_choice(selected, choices)

    endpoint = endpoint_for_choice(choice, has_input_image=bool(images))
    if image_mode and choice.number == 3 and images:
        state.out.print("[yellow]悠船模型暂时不支持图生图，我帮你用全能图片PRO来处理。[/yellow]")
    if not image_mode:
        state.out.print(f"开始用 {choice.name} 生成视频，一般需要几分钟，请稍等。")

    with state.out.status("提交 RunningHub 任务并等待结果...", spinner="dots"):
        result = execute_model(
            api_key_arg=state.api_key,
            endpoint=endpoint,
            task=None,
            run_input=ModelRunInput(prompt=prompt, images=images, params=param),
            output=output,
            output_dir=state.output_dir,
        )
    print_result(state.out, result, json_output=state.json_output)


def image_command(
    ctx: typer.Context,
    prompt: str = typer.Option(..., "--prompt", "-p", help="图片提示词。"),
    source: list[str] = typer.Option([], "--image", "-i", help="输入图片，可重复。"),
    model: str | None = typer.Option(None, "--model", "-m", help="模型编号或名称。"),
    param: list[str] = typer.Option([], "--param", help="附加参数 key=value，可重复。"),
    output: str | None = typer.Option(None, "--output", "-o", help="输出文件或目录。"),
) -> None:
    run_shortcut(ctx, image_mode=True, model=model, prompt=prompt, images=source, param=param, output=output)


def video_command(
    ctx: typer.Context,
    prompt: str = typer.Option(..., "--prompt", "-p", help="视频提示词。"),
    image: list[str] = typer.Option([], "--image", "-i", help="首帧/参考图，可重复。"),
    model: str | None = typer.Option(None, "--model", "-m", help="模型编号或名称。"),
    duration: int | None = typer.Option(None, "--duration", help="视频时长，未指定时使用模型默认值。"),
    param: list[str] = typer.Option([], "--param", help="附加参数 key=value，可重复。"),
    output: str | None = typer.Option(None, "--output", "-o", help="输出文件或目录。"),
) -> None:
    params = list(param)
    if duration is not None:
        params.append(f"duration={duration}")
    run_shortcut(ctx, image_mode=False, model=model, prompt=prompt, images=image, param=params, output=output)
