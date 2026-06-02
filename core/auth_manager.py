#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：全局鉴权管理，与用例内 login 步骤解耦
核心功能：session 登录、Header/Body 注入、401 时触发 Agent 重写 auth.ini
创建时间：2026-06-02
"""
import configparser
import json
import logging
import os
import re
from typing import Any, Dict, Optional

from config.config import Config
from config.loader import SETTINGS_DIR

logger = logging.getLogger(__name__)


class AuthManager:
    """全局鉴权管理器。"""

    def __init__(
        self,
        request_handler,
        data_handler,
        env_names: Optional[list] = None,
    ):
        self.config = Config(env_names=env_names)
        self.request_handler = request_handler
        self.data_handler = data_handler
        self.auth_ini_path = os.path.join(SETTINGS_DIR, "auth.ini")
        self._load_auth_config()
        self._logged_in = False

    def _load_auth_config(self) -> None:
        """从 auth.ini 加载配置。"""
        auth = self.config.auth_config
        self.enabled = auth.getboolean("auth", "enabled", fallback=False)
        self.auto_login = auth.getboolean("auth", "auto_login", fallback=False)

        self.login_path = auth.get("login", "path", fallback="/api/login")
        self.login_method = auth.get("login", "method", fallback="POST").upper()
        login_headers = auth.get("login", "headers", fallback="{}")
        login_body = auth.get("login", "body", fallback="{}")
        self.login_headers = json.loads(login_headers) if login_headers.strip() else {}
        self.login_body = json.loads(login_body) if login_body.strip() else {}
        self.login_expected_status = auth.getint("login", "expected_status", fallback=200)

        self.token_extract = auth.get("token", "extract", fallback="token")
        self.token_variable = auth.get("token", "variable", fallback="token")

        self.header_name = auth.get("header", "name", fallback="Authorization")
        header_template = auth.get("header", "template", fallback="Bearer {{token}}")
        self.header_template = header_template

        self.body_username_field = auth.get("body_auth", "username_field", fallback="username")
        self.body_token_field = auth.get("body_auth", "token_field", fallback="token")
        self.body_username_value = auth.get("body_auth", "username_value", fallback="main")

        self.discovery_api_doc = auth.get(
            "discovery", "api_doc", fallback="api_docs/apispec_1.json"
        )
        self.login_path_hint = auth.get(
            "discovery", "login_path_hint", fallback="/api/login"
        )

    def is_login_endpoint(self, url: str) -> bool:
        """判断当前请求是否为登录接口（跳过重复注入）。"""
        normalized = url.rstrip("/")
        login = self.login_path.rstrip("/")
        return normalized.endswith(login) or login in normalized

    def ensure_logged_in(self) -> bool:
        """执行登录并缓存 token（幂等）。"""
        if not self.enabled:
            return False
        if self._logged_in and self.data_handler.get_variable(self.token_variable):
            return True
        return self.login()

    def login(self) -> bool:
        """调用登录接口，提取 token 并写入 session。"""
        if not self.enabled:
            logger.info("鉴权未启用，跳过登录")
            return False

        logger.info("执行全局登录: %s %s", self.login_method, self.login_path)
        response = self.request_handler.send_request(
            method=self.login_method,
            url=self.login_path,
            headers=self.login_headers,
            json_data=self.login_body,
        )

        if response.status_code != self.login_expected_status:
            logger.error(
                "登录失败: 期望 %s 实际 %s",
                self.login_expected_status,
                response.status_code,
            )
            return False

        try:
            response_json = response.json()
        except ValueError:
            logger.error("登录响应非 JSON，无法提取 token")
            return False

        extract_key = self.token_extract
        if extract_key.startswith("json."):
            extract_key = extract_key[5:]
        token = self.data_handler.extract_value(response_json, extract_key)
        if not token:
            logger.error("未能从登录响应提取 token，路径: %s", self.token_extract)
            return False

        self.data_handler.set_variable(self.token_variable, token)
        self.data_handler.set_variable("username", self.body_username_value)
        auth_header = self._render_template(self.header_template, token)
        self.request_handler.set_default_header(self.header_name, auth_header)
        self._logged_in = True
        logger.info("全局登录成功，token 已注入 session")
        return True

    def _render_template(self, template: str, token: str) -> str:
        """替换模板中的 {{token}}。"""
        result = template.replace("{{token}}", token)
        result = self.data_handler.replace_variables(result)
        return result

    def apply_to_headers(self, headers: Dict[str, Any], url: str) -> Dict[str, Any]:
        """为需要鉴权的请求注入 Authorization 头。"""
        if not self.enabled or self.is_login_endpoint(url):
            return headers

        token = self.data_handler.get_variable(self.token_variable)
        if not token:
            return headers

        merged = dict(headers or {})
        if self.header_name not in merged and self.header_name.lower() not in {
            k.lower() for k in merged
        }:
            merged[self.header_name] = self._render_template(self.header_template, token)
        return merged

    def apply_to_body(self, body: Any, url: str) -> Any:
        """为 body 鉴权接口注入 username/token 字段。"""
        if not self.enabled or self.is_login_endpoint(url):
            return body
        if not isinstance(body, dict):
            return body

        token = self.data_handler.get_variable(self.token_variable)
        if not token:
            return body

        merged = dict(body)
        if self.body_username_field not in merged:
            merged[self.body_username_field] = self.body_username_value
        if self.body_token_field not in merged:
            merged[self.body_token_field] = token
        return merged

    def handle_auth_failure(self, status_code: int) -> bool:
        """
        401/403 时尝试 Agent 重写 auth.ini 并重新登录。

        Returns:
            是否成功恢复鉴权
        """
        if status_code not in (401, 403) or not self.enabled:
            return False

        logger.warning("鉴权失败 (%s)，尝试 Agent 重写 auth.ini", status_code)
        try:
            from agent.actions.discover_auth import DiscoverAuthAction

            context = {
                "api_doc": os.path.join(self.config.base_dir, self.discovery_api_doc),
                "login_path_hint": self.login_path_hint,
                "auth_ini_path": self.auth_ini_path,
            }
            DiscoverAuthAction().run(context)
            self._load_auth_config()
            self._logged_in = False
            return self.login()
        except Exception as error:
            logger.error("Agent 重写鉴权失败: %s", error)
            return False

    def write_auth_ini(self, sections: Dict[str, Dict[str, str]]) -> None:
        """将配置写回 auth.ini（供 Agent 调用）。"""
        parser = configparser.ConfigParser()
        if os.path.isfile(self.auth_ini_path):
            parser.read(self.auth_ini_path, encoding="utf-8")

        for section_name, options in sections.items():
            if not parser.has_section(section_name):
                parser.add_section(section_name)
            for key, value in options.items():
                parser.set(section_name, key, value)

        with open(self.auth_ini_path, "w", encoding="utf-8") as ini_file:
            parser.write(ini_file)
        logger.info("已更新 auth.ini: %s", self.auth_ini_path)
        self._load_auth_config()
