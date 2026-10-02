"""ingestors/fuyao/client.py — 上游 REST API 客户端

本文件是**本项目自行编写**的客户端，调用同花顺 hithink-finance 的公开 REST API。
它不包含上游任何代码 —— 上游的客户端仓库归其所有（见 docs/adr/0002）。

接口依据官方 API 文档：<https://fuyao.aicubes.cn/>
  GET /api/meta/tickers/list                        标的列表
  GET /api/a-share/prices/historical                历史 K 线
  GET /api/a-share/corporate-actions/adjustment-factors  复权因子事件流

鉴权：请求头 ``X-api-key``。响应为统一信封，``code == 0`` 表示成功，
业务数据在 ``data`` 字段。
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import requests

DEFAULT_BASE_URL = "https://fuyao.aicubes.cn"

#: 值得重试的 HTTP 状态码
RETRY_HTTP_STATUS = frozenset({408, 429})
#: 业务错误码：重试无意义，直接抛
NON_RETRY_API_CODES = frozenset({1002, 1003, 400, 401, 403})


class FuyaoError(RuntimeError):
    def __init__(self, code: int, message: str | None = None, request_id: str | None = None):
        self.code = code
        self.message = message
        self.request_id = request_id
        super().__init__(f"fuyao API code={code} message={message} request_id={request_id}")


class MissingCredential(RuntimeError):
    pass


def default_credential_path() -> Path:
    """仓外凭据文件路径。刻意不放在仓库内 —— 见 docs/adr/0001。"""
    return (
        Path.home()
        / "Library"
        / "Application Support"
        / "hithink-finance"
        / "credentials.env"
    )


def load_credential(env_var: str = "HITHINK_FINANCE_API_KEY") -> str:
    """按优先级取 API Key：环境变量 > 仓外 credentials.env。"""
    key = (os.environ.get(env_var) or "").strip()
    if key:
        return key

    path = Path(os.environ.get("HITHINK_FINANCE_CREDENTIALS") or default_credential_path())
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            if name.strip() == env_var:
                key = value.strip().strip('"').strip("'")
                if key:
                    return key

    raise MissingCredential(
        f"{env_var} 未设置。\n"
        f"  1) export {env_var}=<your-key>\n"
        f"  2) 或写入 {path}\n"
        f"     API Key 申请: https://fuyao.aicubes.cn/admin/"
    )


class FuyaoClient:
    """极简 REST 客户端。只做认证、重试、错误分类。"""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        *,
        timeout: float = 15.0,
        retries: int = 3,
    ):
        self.api_key = api_key or load_credential()
        self.base_url = (base_url or os.environ.get("FUYAO_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self._session = requests.Session()
        # 不信任环境里的代理设置，避免把凭据发给意外的代理
        self._session.trust_env = False

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> FuyaoClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict:
        """GET 并返回 ``data`` 对象。

        重试连接错误、HTTP 408/429/5xx，以及非业务性的 API 错误码。
        业务错误（1002/1003/400/401/403）立即抛出。
        """
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        last: Exception = RuntimeError("no attempt made")

        for attempt in range(self.retries):
            try:
                resp = self._session.get(
                    url,
                    params=params,
                    headers={"X-api-key": self.api_key},
                    timeout=self.timeout,
                )
                if resp.status_code in RETRY_HTTP_STATUS or resp.status_code >= 500:
                    last = RuntimeError(f"HTTP {resp.status_code} from {url}")
                    time.sleep(0.5 * (attempt + 1))
                    continue
                resp.raise_for_status()
                body = resp.json()
                code = body.get("code", -1)
                if code != 0:
                    err = FuyaoError(code, body.get("message"), body.get("request_id"))
                    if code in NON_RETRY_API_CODES:
                        raise err
                    last = err
                    time.sleep(0.5 * (attempt + 1))
                    continue
                return body.get("data") or {}
            except (
                requests.exceptions.SSLError,
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
            ) as exc:
                last = exc
                time.sleep(0.5 * (attempt + 1))

        raise last

    # --- 具体接口 -------------------------------------------------------------

    def list_tickers(self, *, limit: int = 10000, asset_type: str | None = None) -> list[dict]:
        """标的列表，自动翻页取尽。"""
        out: list[dict] = []
        offset = 0
        while True:
            params: dict[str, Any] = {"limit": limit, "offset": offset}
            if asset_type:
                params["asset_type"] = asset_type
            data = self.get("/api/meta/tickers/list", params)
            items = data.get("item") or []
            out.extend(items)
            if len(items) < limit:
                return out
            offset += len(items)

    def daily_bars(
        self, thscode: str, start_ms: int, end_ms: int, *, adjust: str = "none"
    ) -> list[dict]:
        """历史日线。

        ``adjust``: ``none``（未复权，默认）/ ``forward`` / ``backward``。
        单次窗口不得超过 10 年，超出返回 code=1003。
        """
        data = self.get(
            "/api/a-share/prices/historical",
            {
                "thscode": thscode,
                "interval": "1d",
                "start": start_ms,
                "end": end_ms,
                "adjust": adjust,
            },
        )
        return data.get("item") or []

    def adjustment_events(self, thscode: str, start: str | None = None, end: str | None = None) -> list[dict]:
        """除权除息事件流。``start`` / ``end`` 为 ``YYYY-MM-DD``。"""
        params: dict[str, Any] = {"thscode": thscode}
        if start:
            params["from"] = start
        if end:
            params["to"] = end
        data = self.get("/api/a-share/corporate-actions/adjustment-factors", params)
        return data.get("item") or []


def _ms(date_str: str) -> int:
    """``YYYY-MM-DD`` -> 毫秒 Unix 时间戳（UTC 零点）。"""
    from datetime import datetime, timezone

    return int(datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)


def _ms_to_date(ms: int) -> str:
    from datetime import datetime, timezone

    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


__all__ = [
    "FuyaoClient",
    "FuyaoError",
    "MissingCredential",
    "load_credential",
    "default_credential_path",
    "DEFAULT_BASE_URL",
    "json",
]
