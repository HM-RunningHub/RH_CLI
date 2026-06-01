from __future__ import annotations

from pathlib import Path
from typing import Any

from rh_cli.compat import fix_mov_to_mp4
from rh_cli.config import require_api_key
from rh_cli.errors import RhCliError
from rh_cli.http import API_HOST, RhHttpClient
from rh_cli.output import RunResult, resolve_output_path
from rh_cli.poll import poll_task

from .nodes import apply_modifications, parse_webapp_id


APP_LIST_URL = f"{API_HOST}/openapi/v2/aiapp/list"
NODE_INFO_URL = f"{API_HOST}/api/webapp/apiCallDemo"
SUBMIT_URL = f"{API_HOST}/task/openapi/ai-app/run"


def list_apps(
    *,
    api_key_arg: str | None,
    sort: str = "RECOMMEND",
    size: int = 10,
    page: int = 1,
    days: int = 7,
) -> dict[str, Any]:
    resolved = require_api_key(api_key_arg)
    assert resolved.value is not None
    payload: dict[str, Any] = {"current": page, "size": min(size, 50), "sort": sort}
    if sort == "HOTTEST" and days:
        payload["days"] = days

    with RhHttpClient(resolved.value) as client:
        response = client.post_json(APP_LIST_URL, payload)
    if response.get("code") != 0:
        raise RhCliError("LIST_FAILED", str(response.get("msg", "获取 AI 应用列表失败。")), detail=response)
    return response.get("data", {})


def get_node_info(*, api_key_arg: str | None, webapp_id_or_url: str) -> list[dict[str, Any]]:
    resolved = require_api_key(api_key_arg)
    assert resolved.value is not None
    webapp_id = parse_webapp_id(webapp_id_or_url)
    with RhHttpClient(resolved.value) as client:
        response = client.get_json(
            NODE_INFO_URL,
            params={"apiKey": resolved.value, "webappId": webapp_id},
        )
    if response.get("code") != 0:
        raise RhCliError("APP_INFO_FAILED", str(response.get("msg", "获取 AI 应用节点失败。")), detail=response)
    node_list = response.get("data", {}).get("nodeInfoList", [])
    if not node_list:
        raise RhCliError("NO_NODES", "这个 AI 应用没有返回可修改节点，请先在网页端成功运行一次。")
    return node_list


def run_app(
    *,
    api_key_arg: str | None,
    webapp_id_or_url: str,
    node_args: list[str] | None,
    file_args: list[str] | None,
    instance_type: str,
    output: str | None,
    output_dir: Path | None,
) -> RunResult:
    resolved = require_api_key(api_key_arg)
    assert resolved.value is not None
    webapp_id = parse_webapp_id(webapp_id_or_url)

    with RhHttpClient(resolved.value) as client:
        response = client.get_json(
            NODE_INFO_URL,
            params={"apiKey": resolved.value, "webappId": webapp_id},
        )
        if response.get("code") != 0:
            raise RhCliError("APP_INFO_FAILED", str(response.get("msg", "获取 AI 应用节点失败。")), detail=response)
        node_list = response.get("data", {}).get("nodeInfoList", [])
        if not node_list:
            raise RhCliError("NO_NODES", "这个 AI 应用没有返回可修改节点，请先在网页端成功运行一次。")

        modified_nodes = apply_modifications(client, node_list, node_args, file_args)
        payload: dict[str, Any] = {
            "apiKey": resolved.value,
            "webappId": int(webapp_id),
            "nodeInfoList": modified_nodes,
        }
        if instance_type and instance_type != "default":
            payload["instanceType"] = instance_type

        submit_response = client.post_json(SUBMIT_URL, payload, headers={"Content-Type": "application/json"})
        if submit_response.get("code") != 0:
            raise RhCliError("SUBMIT_FAILED", str(submit_response.get("msg", "提交 AI 应用失败。")), detail=submit_response)
        data = submit_response.get("data", {})
        task_id = data.get("taskId")
        if not task_id:
            raise RhCliError("SUBMIT_FAILED", "提交成功但响应中没有 taskId。", detail=submit_response)

        prompt_tips = data.get("promptTips")
        if isinstance(prompt_tips, str) and "node_errors" in prompt_tips:
            raise RhCliError("NODE_ERRORS", "工作流节点校验失败。", detail=prompt_tips)

        final = poll_task(client, str(task_id))
        results = final.get("results") or []
        if not results:
            raise RhCliError("TASK_FAILED", "任务完成但没有返回结果。", detail=final)

        usage = final.get("usage") or {}
        cost = usage.get("consumeMoney") or usage.get("thirdPartyConsumeMoney")
        duration = usage.get("taskCostTime")

        files: list[str] = []
        texts: list[str] = []
        file_urls: list[tuple[str, str]] = []
        for item in results:
            url = item.get("url") or item.get("outputUrl")
            if url:
                file_urls.append((str(url), str(item.get("outputType") or _guess_ext_from_url(str(url)))))
                continue
            text = item.get("text") or item.get("content") or item.get("output")
            if text:
                texts.append(str(text))

        for index, (url, ext) in enumerate(file_urls, start=1):
            path = resolve_output_path(
                output,
                output_dir=output_dir,
                default_name=f"app_result.{ext}",
                ext=ext,
                index=index if len(file_urls) > 1 else None,
            )
            client.download(url, str(path))
            fix_mov_to_mp4(path)
            files.append(str(path.resolve()))

    return RunResult(
        files=files,
        texts=texts,
        cost=str(cost) if cost is not None else None,
        duration=duration,
        task_id=str(task_id),
    )


def _guess_ext_from_url(url: str) -> str:
    path = url.split("?", 1)[0]
    last = path.rsplit("/", 1)[-1]
    if "." in last:
        return last.rsplit(".", 1)[-1].lower()
    return "png"
