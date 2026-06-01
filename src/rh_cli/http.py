from __future__ import annotations

import re
from typing import Any

import httpx

from .errors import RhCliError, classify_api_error


API_HOST = "https://www.runninghub.cn"
BASE_URL = f"{API_HOST}/openapi/v2"
ACCOUNT_STATUS_URL = f"{API_HOST}/uc/openapi/accountStatus"

_SECRET_PATTERNS = (
    re.compile(r"(api[_-]?[kK]ey=)[^&\s]+"),
    re.compile(r"(Bearer\s+)[A-Za-z0-9._-]+"),
)


def mask_secret(text: str) -> str:
    """Redact API keys/tokens that may appear in URLs or error messages."""
    masked = text
    for pattern in _SECRET_PATTERNS:
        masked = pattern.sub(r"\1****", masked)
    return masked


class RhHttpClient:
    def __init__(self, api_key: str, timeout: float = 60.0):
        self.api_key = api_key
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout, follow_redirects=True)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "RhHttpClient":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def bearer_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def post_json(
        self,
        url: str,
        payload: dict[str, Any],
        *,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        try:
            response = self._client.post(
                url,
                json=payload,
                headers=headers or self.bearer_headers(),
                timeout=timeout or self.timeout,
            )
        except httpx.HTTPError as exc:
            raise RhCliError("API_ERROR", f"网络请求失败：{mask_secret(str(exc))}") from exc

        if response.status_code >= 400:
            raise self._error_from_response(response)
        return self._json_response(response)

    def get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        try:
            response = self._client.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout or self.timeout,
            )
        except httpx.HTTPError as exc:
            raise RhCliError("API_ERROR", f"网络请求失败：{mask_secret(str(exc))}") from exc
        if response.status_code >= 400:
            raise self._error_from_response(response)
        return self._json_response(response)

    def upload_form(
        self,
        url: str,
        file_path: str,
        data: dict[str, str],
        *,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        try:
            with open(file_path, "rb") as fh:
                response = self._client.post(
                    url,
                    data=data,
                    files={"file": fh},
                    headers=headers,
                    timeout=120.0,
                )
        except OSError as exc:
            raise RhCliError("FILE_NOT_FOUND", f"文件读取失败：{file_path}") from exc
        except httpx.HTTPError as exc:
            raise RhCliError("UPLOAD_FAILED", f"文件上传失败：{exc}") from exc
        if response.status_code >= 400:
            raise self._error_from_response(response)
        return self._json_response(response)

    def download(self, url: str, output_path: str) -> str:
        try:
            with self._client.stream("GET", url, timeout=300.0) as response:
                response.raise_for_status()
                with open(output_path, "wb") as fh:
                    for chunk in response.iter_bytes():
                        fh.write(chunk)
        except httpx.HTTPError as exc:
            raise RhCliError("DOWNLOAD_FAILED", f"下载失败：{exc}") from exc
        except OSError as exc:
            raise RhCliError("DOWNLOAD_FAILED", f"写入文件失败：{output_path}") from exc
        return output_path

    def _json_response(self, response: httpx.Response) -> dict[str, Any]:
        try:
            return response.json()
        except ValueError as exc:
            raise RhCliError("API_ERROR", f"RunningHub 返回了无效 JSON：{response.text[:500]}") from exc

    def _error_from_response(self, response: httpx.Response) -> RhCliError:
        try:
            data = response.json()
            message = data.get("msg") or data.get("message") or response.text
            code = data.get("code")
        except ValueError:
            message = response.text
            code = response.status_code
        return classify_api_error(str(message), code)
