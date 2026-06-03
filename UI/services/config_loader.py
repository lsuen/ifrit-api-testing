#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""配置与路径加载。"""
import configparser
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

UI_DIR = Path(__file__).resolve().parent.parent
UNAVAILABLE = "获取不到"


def load_config() -> Dict[str, Any]:
    config_path = UI_DIR / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    root_str = config["ifrit"]["root_path"]
    root_path = Path(root_str) if os.path.isabs(root_str) else (UI_DIR / root_str).resolve()
    if not root_path.exists():
        raise FileNotFoundError(f"项目根目录不存在: {root_path}")

    config["ifrit"]["root_path_resolved"] = root_path
    return config


def project_path(config: Dict[str, Any], key: str) -> Path:
    rel = config["paths"].get(key, key)
    return config["ifrit"]["root_path_resolved"] / rel


def load_environment_options(config: Dict[str, Any]) -> List[Dict[str, str]]:
    """从 env_config.ini 读取环境列表及 base_url，文件不存在则返回空列表。"""
    env_ini = project_path(config, "config") / "env_config.ini"
    if not env_ini.is_file():
        return []

    parser = configparser.ConfigParser()
    parser.read(env_ini, encoding="utf-8")
    options: List[Dict[str, str]] = []
    for section in parser.sections():
        if section == "database":
            continue
        base_url = ""
        if parser.has_option(section, "base_url"):
            base_url = parser.get(section, "base_url").strip()
        options.append(
            {
                "name": section,
                "base_url": base_url or UNAVAILABLE,
            }
        )
    return options


def load_environments(config: Dict[str, Any]) -> List[str]:
    return [item["name"] for item in load_environment_options(config)]


def get_base_url(config: Dict[str, Any], env_name: str) -> str:
    for item in load_environment_options(config):
        if item["name"] == env_name:
            return item["base_url"]
    return UNAVAILABLE


def load_auth_summary(config: Dict[str, Any]) -> Dict[str, Any]:
    auth_ini = project_path(config, "config") / "auth.ini"
    if not auth_ini.is_file():
        return {
            "available": False,
            "login_path": UNAVAILABLE,
            "username": UNAVAILABLE,
            "password": UNAVAILABLE,
            "enabled": UNAVAILABLE,
        }

    parser = configparser.ConfigParser()
    parser.read(auth_ini, encoding="utf-8")

    body: Dict[str, Any] = {}
    if parser.has_option("login", "body"):
        try:
            body = json.loads(parser.get("login", "body"))
        except json.JSONDecodeError:
            body = {}

    login_path = UNAVAILABLE
    if parser.has_option("login", "path"):
        login_path = parser.get("login", "path").strip() or UNAVAILABLE

    username = body.get("username") or UNAVAILABLE

    enabled = UNAVAILABLE
    if parser.has_option("auth", "enabled"):
        enabled = "true" if parser.getboolean("auth", "enabled") else "false"

    return {
        "available": True,
        "login_path": login_path,
        "username": username,
        "password": "******" if username != UNAVAILABLE else UNAVAILABLE,
        "enabled": enabled,
    }


def get_remote_swagger_url(config: Dict[str, Any]) -> Optional[str]:
    """根据 env base_url 与 auth.ini [discovery] api_doc 文件名推导远程 Swagger URL。"""
    env_options = load_environment_options(config)
    if not env_options:
        return None

    base_url = env_options[0].get("base_url", "")
    if not base_url or base_url == UNAVAILABLE:
        return None

    auth_ini = project_path(config, "config") / "auth.ini"
    if not auth_ini.is_file():
        return None

    parser = configparser.ConfigParser()
    parser.read(auth_ini, encoding="utf-8")
    if not parser.has_option("discovery", "api_doc"):
        return None

    api_doc = parser.get("discovery", "api_doc").strip()
    if not api_doc:
        return None

    filename = Path(api_doc).name
    return f"{base_url.rstrip('/')}/{filename}"


def get_preset_status(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """检查 config.yaml 中预设用例文件是否真实存在。"""
    root = config["ifrit"]["root_path_resolved"]
    presets = config.get("presets", {})
    status: Dict[str, Dict[str, Any]] = {}
    for key, rel_path in presets.items():
        if not isinstance(rel_path, str):
            continue
        file_path = root / rel_path.replace("/", os.sep)
        status[key] = {
            "path": rel_path.replace("\\", "/"),
            "exists": file_path.is_file(),
        }
    return status
