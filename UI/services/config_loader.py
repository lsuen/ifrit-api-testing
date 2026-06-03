#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""配置与路径加载。"""
import configparser
import os
from pathlib import Path
from typing import Any, Dict, List

import yaml

UI_DIR = Path(__file__).resolve().parent.parent


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


def load_environments(config: Dict[str, Any]) -> List[str]:
    env_ini = project_path(config, "config") / "env_config.ini"
    if not env_ini.is_file():
        return ["environment"]

    parser = configparser.ConfigParser()
    parser.read(env_ini, encoding="utf-8")
    names = [section for section in parser.sections() if section != "database"]
    return names or ["environment"]


def get_base_url(config: Dict[str, Any], env_name: str) -> str:
    env_ini = project_path(config, "config") / "env_config.ini"
    if not env_ini.is_file():
        return ""
    parser = configparser.ConfigParser()
    parser.read(env_ini, encoding="utf-8")
    if parser.has_option(env_name, "base_url"):
        return parser.get(env_name, "base_url")
    return parser.get("environment", "base_url", fallback="")


def load_auth_summary(config: Dict[str, Any]) -> Dict[str, str]:
    auth_ini = project_path(config, "config") / "auth.ini"
    parser = configparser.ConfigParser()
    parser.read(auth_ini, encoding="utf-8")
    import json

    body = {}
    if parser.has_option("login", "body"):
        try:
            body = json.loads(parser.get("login", "body"))
        except json.JSONDecodeError:
            body = {}
    return {
        "login_path": parser.get("login", "path", fallback="/api/login"),
        "username": body.get("username", "test"),
        "password": "******",
        "enabled": str(parser.getboolean("auth", "enabled", fallback=True)),
    }
