#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：用 curl/requests 探测端点是否可达，供 AI 生成前校验
创建时间：2026-06-02
"""
import json
import logging
import subprocess
from typing import Any, Dict, List

import requests

from agent.actions.base import Action

logger = logging.getLogger(__name__)


class ProbeEndpointAction(Action):
    """探测 API 端点连通性。"""

    name = "probe_endpoint"
    description = "用 HTTP 请求验证端点是否可达，结果写入 context['probe_results']"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        base_url = context.get("base_url", "").rstrip("/")
        endpoints: List[str] = context.get("endpoints") or ["/api/test"]
        timeout = context.get("probe_timeout", 10)
        use_curl = context.get("use_curl", False)

        results = []
        for endpoint in endpoints:
            path = endpoint if endpoint.startswith("/") else f"/{endpoint}"
            url = f"{base_url}{path}"
            result = (
                self._probe_with_curl(url, timeout)
                if use_curl
                else self._probe_with_requests(url, timeout)
            )
            result["endpoint"] = path
            results.append(result)
            status = "OK" if result["ok"] else "FAIL"
            logger.info(
                "探测 %s -> %s (status=%s, body=%s)",
                path,
                status,
                result.get("status_code"),
                (result.get("body_preview") or "")[:80],
            )

        context["probe_results"] = results
        context["probe_ok"] = all(item["ok"] for item in results)
        return context

    @staticmethod
    def _probe_with_requests(url: str, timeout: int) -> Dict[str, Any]:
        try:
            response = requests.get(url, timeout=timeout, verify=False)
            body = response.text[:200]
            return {
                "ok": response.status_code < 500,
                "status_code": response.status_code,
                "body_preview": body,
                "method": "requests",
            }
        except requests.RequestException as error:
            return {
                "ok": False,
                "status_code": 0,
                "body_preview": str(error),
                "method": "requests",
            }

    @staticmethod
    def _probe_with_curl(url: str, timeout: int) -> Dict[str, Any]:
        try:
            completed = subprocess.run(
                [
                    "curl",
                    "-sS",
                    "-m",
                    str(timeout),
                    "-w",
                    "\n%{http_code}",
                    url,
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            output = completed.stdout.strip()
            if "\n" in output:
                body, status_line = output.rsplit("\n", 1)
            else:
                body, status_line = output, "0"
            status_code = int(status_line) if status_line.isdigit() else 0
            return {
                "ok": completed.returncode == 0 and status_code < 500,
                "status_code": status_code,
                "body_preview": body[:200],
                "method": "curl",
            }
        except FileNotFoundError:
            logger.warning("curl 不可用，回退 requests")
            return ProbeEndpointAction._probe_with_requests(url, timeout)
        except Exception as error:
            return {
                "ok": False,
                "status_code": 0,
                "body_preview": str(error),
                "method": "curl",
            }
