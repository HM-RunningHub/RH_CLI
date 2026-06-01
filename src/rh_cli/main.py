from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from . import __version__
from .account import check_account
from .app.commands import app as app_commands
from .config import config_path, read_config, resolve_api_key, write_config
from .errors import RhCliError
from .model.commands import image_command, model_app, video_command
from .state import CliState


console = Console()
app = typer.Typer(help="RH CLI：RunningHub 标准模型与 AI 应用命令行工具。", no_args_is_help=True)
auth_app = typer.Typer(help="管理 RunningHub API Key 和 CLI 配置。")


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"rh-cli {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    ctx: typer.Context,
    api_key: str | None = typer.Option(None, "--api-key", help="临时指定 RunningHub API Key。"),
    output_dir: Path | None = typer.Option(None, "--output-dir", help="默认输出目录。"),
    json_output: bool = typer.Option(False, "--json", help="输出机器可读 JSON。"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="打印更多调试信息。"),
    version: bool = typer.Option(False, "--version", callback=_version_callback, is_eager=True, help="显示版本。"),
) -> None:
    ctx.obj = CliState(
        api_key=api_key,
        output_dir=output_dir,
        json_output=json_output,
        verbose=verbose,
        console=console,
    )


@app.command("check")
def check(ctx: typer.Context) -> None:
    state = ctx.obj if isinstance(ctx.obj, CliState) else CliState(console=console)
    result = check_account(state.api_key)
    if state.json_output:
        state.out.print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    status = result.get("status")
    if status == "ready":
        state.out.print(f"[green]RunningHub 已就绪[/green]，余额 ¥{result.get('balance')}，Key 来源：{result.get('key_source')}")
    elif status == "no_balance":
        state.out.print(f"[yellow]API Key 可用，但余额为 0。[/yellow]请充值后再运行生成任务。")
    elif status == "no_key":
        state.out.print("[red]还没有配置 API Key。[/red]运行 `rh auth set-key` 或设置 RUNNINGHUB_API_KEY。")
    else:
        state.out.print(f"[red]API Key 校验失败：[/red]{result.get('message')}")


@auth_app.command("set-key")
def set_key(api_key: str = typer.Argument(..., help="RunningHub API Key。")) -> None:
    cfg = read_config()
    cfg["api_key"] = api_key
    path = write_config(cfg)
    console.print(f"[green]已保存 API Key 到[/green] {path}")


@auth_app.command("show")
def show_auth() -> None:
    resolved = resolve_api_key()
    cfg_path = config_path()
    if resolved.value:
        console.print(f"API Key 来源：{resolved.source}，当前 Key：{resolved.value[:4]}****")
    else:
        console.print("尚未配置 API Key。")
    console.print(f"配置文件：{cfg_path}")


@auth_app.command("set-output-dir")
def set_output_dir(output_dir: Path = typer.Argument(..., help="默认输出目录。")) -> None:
    cfg = read_config()
    cfg["output_dir"] = str(output_dir.expanduser())
    path = write_config(cfg)
    console.print(f"[green]已保存默认输出目录到[/green] {path}")


app.add_typer(auth_app, name="auth")
app.add_typer(model_app, name="model")
app.command("image")(image_command)
app.command("video")(video_command)
app.add_typer(app_commands, name="app")


def run() -> None:
    try:
        app()
    except RhCliError as exc:
        console.print(json.dumps(exc.to_dict(), ensure_ascii=False, indent=2))
        raise typer.Exit(exc.exit_code) from exc


if __name__ == "__main__":
    run()
