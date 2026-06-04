#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ifrit 用例行读写（CSV / JSON）。"""
import csv
import json
from pathlib import Path
from typing import Any, Dict, List

CASE_COLUMNS = [
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


def normalize_row(row: Dict[str, Any]) -> Dict[str, str]:
    normalized: Dict[str, str] = {}
    for column in CASE_COLUMNS:
        value = row.get(column, "")
        if value is None:
            value = ""
        normalized[column] = str(value)
    return normalized


def merge_case_rows(
    original: List[Dict[str, Any]],
    append: List[Dict[str, Any]],
    mark_appended: bool = True,
) -> List[Dict[str, str]]:
    """合并原用例与追加用例，重新编号 id。"""
    merged: List[Dict[str, str]] = []
    for row in original:
        item = normalize_row(row)
        item["_source"] = "original"
        merged.append(item)
    for row in append:
        item = normalize_row(row)
        item["_source"] = "appended" if mark_appended else "original"
        merged.append(item)

    output: List[Dict[str, str]] = []
    for index, row in enumerate(merged, start=1):
        clean = {key: row.get(key, "") for key in CASE_COLUMNS}
        clean["id"] = str(index)
        if mark_appended:
            clean["_source"] = row.get("_source", "original")
        output.append(clean)
    return output


def write_cases(rows: List[Dict[str, Any]], output_path: Path, output_format: str = "csv") -> None:
    """写入 CSV 或 JSON。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [normalize_row(row) for row in rows]
    fmt = (output_format or "csv").lower()

    if fmt == "json":
        payload = [{key: row[key] for key in CASE_COLUMNS} for row in normalized]
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        return

    with open(output_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CASE_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in normalized:
            writer.writerow({key: row.get(key, "") for key in CASE_COLUMNS})


def read_cases(file_path: Path) -> List[Dict[str, str]]:
    """读取 CSV 或 JSON 用例文件。"""
    if not file_path.is_file():
        raise FileNotFoundError(str(file_path))
    suffix = file_path.suffix.lower()
    if suffix == ".json":
        with open(file_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            data = data.get("cases") or data.get("rows") or []
        return [normalize_row(item) for item in data if isinstance(item, dict)]

    with open(file_path, "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [normalize_row(row) for row in reader]
