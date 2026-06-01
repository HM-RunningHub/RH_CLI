from __future__ import annotations

import json

import typer
from rich.table import Table

from rh_cli.app.client import get_node_info, list_apps, run_app
from rh_cli.app.nodes import extract_webapp_id_from_invoke, parse_webapp_id
from rh_cli.output import print_result
from rh_cli.state import CliState


app = typer.Typer(help="浏览和运行 RunningHub AI 应用。")


def _state(ctx: typer.Context) -> CliState:
    return ctx.obj if isinstance(ctx.obj, CliState) else CliState()


@app.command("list")
def list_command(
    ctx: typer.Context,
    sort: str = typer.Option("RECOMMEND", "--sort", help="RECOMMEND/HOTTEST/NEWEST。"),
    size: int = typer.Option(10, "--size", help="每页数量，最大 50。"),
    page: int = typer.Option(1, "--page", help="页码。"),
    days: int = typer.Option(7, "--days", help="HOTTEST 热度窗口天数。"),
) -> None:
    state = _state(ctx)
    data = list_apps(api_key_arg=state.api_key, sort=sort, size=size, page=page, days=days)
    records = data.get("records", [])
    apps = []
    for record in records:
        apps.append(
            {
                "webappId": extract_webapp_id_from_invoke(record.get("invokeExample", "")),
                "title": record.get("title", ""),
                "description": record.get("description", ""),
                "cover": record.get("cover", ""),
            }
        )

    output = {
        "sort": sort,
        "page": int(data.get("current", page)),
        "size": int(data.get("size", size)),
        "total": int(data.get("total", 0)),
        "pages": int(data.get("pages", 0)),
        "hasNext": data.get("hasNext", False),
        "apps": apps,
    }
    if state.json_output:
        state.out.print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    table = Table(title=f"AI Apps ({output['total']})")
    table.add_column("WebApp ID")
    table.add_column("Title")
    table.add_column("Description")
    for item in apps:
        table.add_row(str(item.get("webappId") or ""), str(item["title"]), str(item["description"])[:80])
    state.out.print(table)


@app.command("info")
def info_command(ctx: typer.Context, webapp: str = typer.Argument(..., help="webappId 或 AI 应用 URL。")) -> None:
    state = _state(ctx)
    webapp_id = parse_webapp_id(webapp)
    nodes = get_node_info(api_key_arg=state.api_key, webapp_id_or_url=webapp_id)
    if state.json_output:
        state.out.print(json.dumps({"webappId": webapp_id, "nodeCount": len(nodes), "nodes": nodes}, ensure_ascii=False, indent=2))
        return

    table = Table(title=f"AI App Nodes ({webapp_id})")
    table.add_column("Node ID")
    table.add_column("Field")
    table.add_column("Type")
    table.add_column("Value")
    for node in nodes:
        table.add_row(
            str(node.get("nodeId", "")),
            str(node.get("fieldName", "")),
            str(node.get("fieldType", "")),
            str(node.get("fieldValue", ""))[:80],
        )
    state.out.print(table)


@app.command("run")
def run_command(
    ctx: typer.Context,
    webapp: str = typer.Argument(..., help="webappId 或 AI 应用 URL。"),
    node: list[str] = typer.Option([], "--node", help="设置节点：nodeId:fieldName=value，可重复。"),
    file: list[str] = typer.Option([], "--file", help="上传文件并设置节点：nodeId:fieldName=/path，可重复。"),
    instance_type: str = typer.Option("default", "--instance-type", help="default 或 plus。"),
    output: str | None = typer.Option(None, "--output", "-o", help="输出文件或目录。"),
) -> None:
    state = _state(ctx)
    state.out.print("开始运行 AI 应用，复杂工作流可能需要几分钟。")
    with state.out.status("提交 RunningHub AI 应用任务并等待结果...", spinner="dots"):
        result = run_app(
            api_key_arg=state.api_key,
            webapp_id_or_url=webapp,
            node_args=node,
            file_args=file,
            instance_type=instance_type,
            output=output,
            output_dir=state.output_dir,
        )
    print_result(state.out, result, json_output=state.json_output)
