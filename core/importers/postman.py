#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Postman Collection v2.1 → ifrit CSV 转换器。"""
import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qsl, urlparse

CSV_COLUMNS = [
    "id",
    "name",
    "method",
    "url",
    "headers",
    "params",
    "body",
    "expected_status",
    "expected_result",
    "extract",
    "validate",
    "priority",
    "enabled",
]

POSTMAN_SCHEMA_V21 = "v2.1"


class PostmanImportError(ValueError):
    """Postman 导入错误。"""


class PostmanImporter:
    """将 Postman Collection v2.1 转为 ifrit CSV 用例行。"""

    def __init__(self, collection_path: str):
        self.collection_path = Path(collection_path)
        self._case_index = 0

    def load(self) -> Dict[str, Any]:
        if not self.collection_path.is_file():
            raise PostmanImportError(f"文件不存在: {self.collection_path}")
        try:
            with open(self.collection_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except json.JSONDecodeError as error:
            raise PostmanImportError(f"JSON 解析失败: {error}") from error
        if not isinstance(data, dict):
            raise PostmanImportError("Postman Collection 根节点必须是 JSON 对象")
        schema = str(data.get("info", {}).get("schema", ""))
        if "v2.1" not in schema and "v2.0" not in schema:
            raise PostmanImportError(
                f"仅支持 Postman Collection v2.0/v2.1，当前 schema: {schema or '未知'}"
            )
        return data

    def convert(self) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
        data = self.load()
        rows: List[Dict[str, str]] = []
        self._case_index = 0
        self._walk_items(data.get("item") or [], rows, name_prefix="")
        meta = {
            "collection_name": data.get("info", {}).get("name", self.collection_path.stem),
            "source": str(self.collection_path),
            "format": POSTMAN_SCHEMA_V21,
            "case_count": len(rows),
        }
        if not rows:
            raise PostmanImportError("Collection 中未找到可导入的请求")
        return rows, meta

    def _walk_items(
        self,
        items: List[Any],
        rows: List[Dict[str, str]],
        name_prefix: str,
    ) -> None:
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("disabled"):
                continue
            if "request" in item:
                row = self._convert_request(item, name_prefix)
                if row:
                    rows.append(row)
                continue
            folder_name = item.get("name", "Folder")
            child_prefix = f"{name_prefix}{folder_name} - " if name_prefix else f"{folder_name} - "
            self._walk_items(item.get("item") or [], rows, child_prefix)

    def _convert_request(self, item: Dict[str, Any], name_prefix: str) -> Optional[Dict[str, str]]:
        request = item.get("request")
        if not isinstance(request, dict):
            return None
        if request.get("disabled"):
            return None

        method = str(request.get("method") or "GET").upper()
        url_path, query_params = self._parse_url(request.get("url"))
        headers = self._parse_headers(request.get("header"))
        body = self._parse_body(request.get("body"))
        expected_status, expected_result = self._parse_tests(item.get("event"))

        self._case_index += 1
        display_name = f"{name_prefix}{item.get('name', f'Case_{self._case_index}')}".strip(" -")

        return {
            "id": str(self._case_index),
            "name": display_name,
            "method": method,
            "url": url_path,
            "headers": json.dumps(headers, ensure_ascii=False) if headers else "{}",
            "params": json.dumps(query_params, ensure_ascii=False) if query_params else "{}",
            "body": body if body else "{}",
            "expected_status": expected_status,
            "expected_result": expected_result,
            "extract": "",
            "validate": "",
            "priority": "1",
            "enabled": "1",
        }

    @staticmethod
    def _parse_url(url_field: Any) -> Tuple[str, Dict[str, str]]:
        raw = ""
        query_from_url: Dict[str, str] = {}

        if isinstance(url_field, str):
            raw = url_field
        elif isinstance(url_field, dict):
            raw = str(url_field.get("raw") or "")
            query_items = url_field.get("query") or []
            if isinstance(query_items, list):
                for entry in query_items:
                    if not isinstance(entry, dict) or entry.get("disabled"):
                        continue
                    key = entry.get("key")
                    if key:
                        query_from_url[str(key)] = str(entry.get("value", ""))
            if not raw:
                path_parts = [
                    str(part)
                    for part in (url_field.get("path") or [])
                    if part and not str(part).startswith("{{")
                ]
                if path_parts:
                    raw = "/" + "/".join(path_parts)

        raw = raw.strip()
        if raw.startswith("http://") or raw.startswith("https://"):
            parsed = urlparse(raw)
            path = parsed.path or "/"
            for key, value in parse_qsl(parsed.query, keep_blank_values=True):
                query_from_url.setdefault(key, value)
            return path, query_from_url

        raw = re.sub(r"\{\{[^}]+\}\}", "", raw)
        if "?" in raw:
            path_part, query_part = raw.split("?", 1)
            for key, value in parse_qsl(query_part, keep_blank_values=True):
                query_from_url.setdefault(key, value)
            raw = path_part
        if raw and not raw.startswith("/"):
            raw = "/" + raw.lstrip("/")
        return raw or "/", query_from_url

    @staticmethod
    def _parse_headers(header_field: Any) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        if not isinstance(header_field, list):
            return headers
        for entry in header_field:
            if not isinstance(entry, dict) or entry.get("disabled"):
                continue
            key = entry.get("key")
            if key:
                headers[str(key)] = str(entry.get("value", ""))
        return headers

    @staticmethod
    def _parse_body(body_field: Any) -> str:
        if not isinstance(body_field, dict):
            return "{}"
        mode = body_field.get("mode")
        if mode == "raw":
            raw = body_field.get("raw")
            if raw is None:
                return "{}"
            text = str(raw).strip()
            if not text:
                return "{}"
            try:
                json.loads(text)
                return text
            except json.JSONDecodeError:
                return json.dumps(text, ensure_ascii=False)
        if mode == "urlencoded":
            pairs = body_field.get("urlencoded") or []
            data: Dict[str, str] = {}
            if isinstance(pairs, list):
                for entry in pairs:
                    if isinstance(entry, dict) and not entry.get("disabled") and entry.get("key"):
                        data[str(entry["key"])] = str(entry.get("value", ""))
            return json.dumps(data, ensure_ascii=False) if data else "{}"
        if mode == "formdata":
            pairs = body_field.get("formdata") or []
            data = {}
            if isinstance(pairs, list):
                for entry in pairs:
                    if isinstance(entry, dict) and not entry.get("disabled") and entry.get("key"):
                        data[str(entry["key"])] = str(entry.get("value", ""))
            return json.dumps(data, ensure_ascii=False) if data else "{}"
        return "{}"

    @staticmethod
    def _parse_tests(events: Any) -> Tuple[str, str]:
        if not isinstance(events, list):
            return "", ""
        scripts: List[str] = []
        for event in events:
            if not isinstance(event, dict) or event.get("listen") != "test":
                continue
            script = event.get("script") or {}
            exec_lines = script.get("exec") or []
            if isinstance(exec_lines, list):
                scripts.extend(str(line) for line in exec_lines)
        if not scripts:
            return "", ""
        joined = "\n".join(scripts)
        status_match = re.search(
            r"\.(?:to\.)?have\.status\(\s*(\d+)\s*\)|status\s*===?\s*['\"]?(\d+)['\"]?",
            joined,
        )
        expected_status = ""
        if status_match:
            expected_status = status_match.group(1) or status_match.group(2) or ""
        body_match = re.search(r"\.to\.include\(\s*['\"]([^'\"]+)['\"]\s*\)", joined)
        if not body_match:
            body_match = re.search(r"\.to\.eql\(\s*['\"]([^'\"]+)['\"]\s*\)", joined)
        expected_result = body_match.group(1) if body_match else ""
        return expected_status, expected_result

    @staticmethod
    def write_csv(rows: List[Dict[str, str]], output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
