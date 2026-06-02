#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：从 Swagger 文档理解鉴权方式并重写 auth.ini
创建时间：2026-06-02
"""
import json
import logging
import os
from typing import Any, Dict, List

from agent.actions.base import Action
from config.loader import SETTINGS_DIR

logger = logging.getLogger(__name__)


class DiscoverAuthAction(Action):
    """Agent 鉴权发现：解析 API 文档并重写 auth.ini。"""

    name = "discover_auth"
    description = "从 Swagger 文档推断登录接口与 token 提取规则，更新 auth.ini"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        api_doc = context.get("api_doc") or os.path.join(
            SETTINGS_DIR, "..", "..", "api_docs", "apispec_1.json"
        )
        api_doc = os.path.abspath(api_doc)
        login_hint = context.get("login_path_hint", "/api/login")
        auth_ini_path = context.get(
            "auth_ini_path", os.path.join(SETTINGS_DIR, "auth.ini")
        )

        if not os.path.isfile(api_doc):
            raise FileNotFoundError(f"API 文档不存在: {api_doc}")

        with open(api_doc, "r", encoding="utf-8") as doc_file:
            spec = json.load(doc_file)

        login_info = self._find_login_endpoint(spec, login_hint)
        auth_sections = self._build_auth_sections(login_info)

        self._write_auth_ini(auth_ini_path, auth_sections)
        context["auth_discovered"] = True
        context["auth_ini_path"] = auth_ini_path
        context["login_info"] = login_info
        logger.info("鉴权配置已重写: %s", auth_ini_path)
        return context

    def _find_login_endpoint(
        self, spec: Dict[str, Any], login_hint: str
    ) -> Dict[str, Any]:
        """从 Swagger paths 中定位登录接口。"""
        paths = spec.get("paths", {})
        candidates: List[Dict[str, Any]] = []

        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            for method, detail in methods.items():
                if method.upper() != "POST":
                    continue
                summary = (detail.get("summary") or "").lower()
                operation_id = (detail.get("operationId") or "").lower()
                path_lower = path.lower()
                score = 0
                if login_hint and login_hint.lower() in path_lower:
                    score += 10
                if "login" in path_lower or "login" in summary or "login" in operation_id:
                    score += 5
                if "auth" in path_lower or "token" in summary:
                    score += 2
                if score > 0:
                    candidates.append(
                        {
                            "path": path,
                            "method": "POST",
                            "score": score,
                            "detail": detail,
                        }
                    )

        if not candidates:
            return {
                "path": login_hint or "/api/login",
                "method": "POST",
                "body": {"username": "main", "password": "123456"},
                "token_path": "token",
            }

        best = sorted(candidates, key=lambda item: item["score"], reverse=True)[0]
        body = self._infer_login_body(best["detail"])
        token_path = self._infer_token_path(best["detail"])
        return {
            "path": best["path"],
            "method": "POST",
            "body": body,
            "token_path": token_path,
        }

    @staticmethod
    def _infer_login_body(detail: Dict[str, Any]) -> Dict[str, str]:
        """从 requestBody schema 推断登录字段。"""
        try:
            schema = (
                detail.get("requestBody", {})
                .get("content", {})
                .get("application/json", {})
                .get("schema", {})
            )
            props = schema.get("properties", {})
            body = {}
            for field in props:
                lower = field.lower()
                if "user" in lower or lower == "username":
                    body[field] = "main"
                elif "pass" in lower:
                    body[field] = "123456"
            if body:
                return body
        except (AttributeError, TypeError):
            pass
        return {"username": "main", "password": "123456"}

    @staticmethod
    def _infer_token_path(detail: Dict[str, Any]) -> str:
        """从响应 schema 推断 token 字段路径。"""
        try:
            schema = (
                detail.get("responses", {})
                .get("200", {})
                .get("content", {})
                .get("application/json", {})
                .get("schema", {})
            )
            props = schema.get("properties", {})
            for key in props:
                if "token" in key.lower():
                    return key
        except (AttributeError, TypeError):
            pass
        return "token"

    def _build_auth_sections(self, login_info: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """构建 auth.ini 各 section 内容。"""
        token_path = login_info.get("token_path", "token")
        return {
            "auth": {
                "enabled": "true",
                "auto_login": "false",
            },
            "login": {
                "path": login_info["path"],
                "method": login_info["method"],
                "headers": json.dumps({"Content-Type": "application/json"}, ensure_ascii=False),
                "body": json.dumps(login_info["body"], ensure_ascii=False),
                "expected_status": "200",
            },
            "token": {
                "extract": f"json.{token_path}",
                "variable": "token",
            },
            "header": {
                "name": "Authorization",
                "template": "Bearer {{token}}",
            },
            "body_auth": {
                "username_field": "username",
                "token_field": "token",
                "username_value": login_info["body"].get("username", "main"),
            },
        }

    @staticmethod
    def _write_auth_ini(
        auth_ini_path: str, sections: Dict[str, Dict[str, str]]
    ) -> None:
        """写入 auth.ini（保留 discovery section）。"""
        import configparser

        parser = configparser.ConfigParser()
        if os.path.isfile(auth_ini_path):
            parser.read(auth_ini_path, encoding="utf-8")

        for section_name, options in sections.items():
            if not parser.has_section(section_name):
                parser.add_section(section_name)
            for key, value in options.items():
                parser.set(section_name, key, value)

        if not parser.has_section("discovery"):
            parser.add_section("discovery")
            parser.set("discovery", "api_doc", "api_docs/apispec_1.json")
            parser.set("discovery", "login_path_hint", "/api/login")

        with open(auth_ini_path, "w", encoding="utf-8") as ini_file:
            parser.write(ini_file)

    def run_with_llm(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        可选：用 LLM 辅助推断鉴权（当规则推断失败时）。
        当前默认使用规则推断；LLM 路径供后续扩展。
        """
        return self.run(context)
