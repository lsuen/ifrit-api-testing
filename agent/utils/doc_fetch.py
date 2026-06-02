#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：从 URL 拉取接口文档并缓存到 api_docs/cache
"""
import hashlib
import logging
import os
import re
from typing import Optional
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30
EXT_BY_CONTENT_TYPE = {
    "application/json": ".json",
    "text/yaml": ".yaml",
    "application/yaml": ".yaml",
    "text/markdown": ".md",
    "text/plain": ".md",
}


def _project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_cache_dir() -> str:
    """返回文档缓存目录。"""
    cache_dir = os.path.join(_project_root(), "api_docs", "cache")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def _guess_extension(url: str, content_type: Optional[str], content: bytes) -> str:
    path = urlparse(url).path.lower()
    for ext in (".json", ".yaml", ".yml", ".md", ".markdown"):
        if path.endswith(ext):
            return ext

    if content_type:
        lowered = content_type.split(";")[0].strip().lower()
        if lowered in EXT_BY_CONTENT_TYPE:
            return EXT_BY_CONTENT_TYPE[lowered]

    text_head = content[:200].decode("utf-8", errors="ignore").lstrip()
    if text_head.startswith("{") or text_head.startswith("["):
        return ".json"
    if "openapi:" in text_head or "swagger:" in text_head:
        return ".yaml"
    if text_head.startswith("#"):
        return ".md"
    return ".md"


def _safe_slug(url: str) -> str:
    parsed = urlparse(url)
    name = os.path.basename(parsed.path) or parsed.netloc.replace(".", "_")
    name = re.sub(r"[^\w.\-]", "_", name)
    return name[:80] or "remote_doc"


def fetch_document_to_cache(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """
    下载远程文档到 api_docs/cache，返回本地路径。

    Raises:
        requests.RequestException: 网络或 HTTP 错误
    """
    logger.info("拉取接口文档: %s", url)
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()

    content = response.content
    extension = _guess_extension(url, response.headers.get("Content-Type"), content)
    slug = _safe_slug(url)
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:10]
    filename = f"{slug}_{digest}{extension}"
    cache_path = os.path.join(get_cache_dir(), filename)

    with open(cache_path, "wb") as handle:
        handle.write(content)

    logger.info("文档已缓存: %s", cache_path)
    return cache_path
