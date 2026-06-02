#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""临时 LLM 连通性探测脚本（手动运行）。"""
import json
import os
import sys

import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config.ai_config import AIConfig
from core.ai_client import AIClient


def test_raw_request(cfg: dict) -> int:
    """直接 HTTP 请求，打印原始响应。"""
    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg['api_key']}",
    }
    payload = {
        "model": cfg["model"],
        "messages": [{"role": "user", "content": "请只回复两个字：通过"}],
        "temperature": 0.7,
        "max_tokens": 50,
    }
    print("POST", url)
    print("model:", cfg["model"])
    response = requests.post(url, headers=headers, json=payload, timeout=90)
    print("status:", response.status_code)
    try:
        body = response.json()
        print("body:", json.dumps(body, ensure_ascii=False, indent=2)[:3000])
    except Exception:
        print("raw:", response.text[:3000])
    return response.status_code


def test_ai_client(cfg: dict) -> bool:
    """通过 AIClient 调用。"""
    client = AIClient(cfg)
    print("client endpoint:", client.base_url)
    content = client._call_openai_api("请只回复两个字：通过", max_retries=1)
    if content:
        print("AIClient SUCCESS:", content[:200])
        return True
    print("AIClient FAILED")
    return False


def main() -> int:
    ai_config = AIConfig()
    cfg = ai_config.get_openai_config()
    print("validate:", ai_config.validate_config())
    print("base_url:", cfg["base_url"])
    print("model:", cfg["model"])
    print("api_key:", "已设置" if cfg["api_key"] else "未设置")
    print("--- raw ---")
    status = test_raw_request(cfg)
    print("--- client ---")
    ok = test_ai_client(cfg)
    return 0 if status == 200 and ok else 1


if __name__ == "__main__":
    sys.exit(main())
