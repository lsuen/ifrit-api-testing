#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""设置读写与连接自检。"""
import configparser
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from services.config_loader import UNAVAILABLE, load_environment_options, load_auth_summary, project_path


def _settings_dir(config: Dict[str, Any]) -> Path:
    return project_path(config, "config")


def _env_file(config: Dict[str, Any]) -> Path:
    return config["ifrit"]["root_path_resolved"] / ".env"


def _ui_prefs_path(config: Dict[str, Any]) -> Path:
    path = config["ifrit"]["root_path_resolved"] / ".ifrit" / "ui_prefs.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def load_ui_prefs(config: Dict[str, Any]) -> Dict[str, Any]:
    path = _ui_prefs_path(config)
    if not path.is_file():
        return {"rag_default_on": True, "auto_ingest_rag": True}
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    data.setdefault("rag_default_on", True)
    data.setdefault("auto_ingest_rag", True)
    return data


def save_ui_prefs(config: Dict[str, Any], prefs: Dict[str, Any]) -> Dict[str, Any]:
    current = load_ui_prefs(config)
    current.update({k: v for k, v in prefs.items() if v is not None})
    path = _ui_prefs_path(config)
    with open(path, "w", encoding="utf-8") as handle:
        yaml.dump(current, handle, allow_unicode=True, default_flow_style=False)
    return current


def _read_env_keys(config: Dict[str, Any]) -> Dict[str, str]:
    root = config["ifrit"]["root_path_resolved"]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from config.loader import get_env_value, ensure_dotenv_loaded

    ensure_dotenv_loaded()
    key = get_env_value("OPENAI_API_KEY", "")
    return {
        "openai_api_key_set": bool(key and key not in ("", "your_openai_api_key_here")),
        "openai_api_key_hint": (key[:4] + "****" + key[-4:]) if len(key) > 8 else ("已设置" if key else ""),
        "openai_base_url_override": get_env_value("OPENAI_BASE_URL", ""),
        "openai_model_override": get_env_value("OPENAI_MODEL", ""),
    }


def _reload_project_env(config: Dict[str, Any]) -> None:
    root = config["ifrit"]["root_path_resolved"]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from config.loader import reload_dotenv

    reload_dotenv(str(root / ".env"))


def get_effective_ai_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """返回实际生效的 LLM 配置（ai.ini + .env 合并）。"""
    _reload_project_env(config)
    from config.ai_config import AIConfig

    ai = AIConfig().get_openai_config()
    ini_path = _settings_dir(config) / "ai.ini"
    ini_base = ""
    ini_model = ""
    if ini_path.is_file():
        parser = configparser.ConfigParser()
        parser.read(ini_path, encoding="utf-8")
        if parser.has_section("openai"):
            ini_base = parser.get("openai", "base_url", fallback="")
            ini_model = parser.get("openai", "model", fallback="")

    env_keys = _read_env_keys(config)
    base_from_env = bool(env_keys.get("openai_base_url_override"))
    model_from_env = bool(env_keys.get("openai_model_override"))

    return {
        "base_url": ai.get("base_url", ""),
        "model": ai.get("model", ""),
        "timeout": ai.get("timeout", 120),
        "api_key_set": env_keys.get("openai_api_key_set", False),
        "api_key_hint": env_keys.get("openai_api_key_hint", ""),
        "ini_base_url": ini_base,
        "ini_model": ini_model,
        "base_url_from_env": base_from_env,
        "model_from_env": model_from_env,
    }


def get_settings_payload(config: Dict[str, Any]) -> Dict[str, Any]:
    settings_dir = _settings_dir(config)
    ai_ini = settings_dir / "ai.ini"
    auth_ini = settings_dir / "auth.ini"

    effective = get_effective_ai_config(config)
    ai_data: Dict[str, str] = {
        "base_url": effective.get("base_url", ""),
        "model": effective.get("model", ""),
        "timeout": str(effective.get("timeout", 120)),
    }
    if ai_ini.is_file():
        parser = configparser.ConfigParser()
        parser.read(ai_ini, encoding="utf-8")
        if parser.has_section("openai"):
            for key in ("temperature", "max_tokens"):
                if parser.has_option("openai", key):
                    ai_data[key] = parser.get("openai", key)

    env_options = load_environment_options(config)
    auth = load_auth_summary(config)
    auth_detail: Dict[str, Any] = dict(auth)
    if auth_ini.is_file():
        ap = configparser.ConfigParser()
        ap.read(auth_ini, encoding="utf-8")
        if ap.has_option("login", "body"):
            auth_detail["login_body"] = ap.get("login", "body")
        if ap.has_option("login", "method"):
            auth_detail["login_method"] = ap.get("login", "method")
    env_keys = _read_env_keys(config)

    return {
        "ai": ai_data,
        "effective_ai": effective,
        "env_options": env_options,
        "auth": auth_detail,
        "env_keys": env_keys,
        "ui_prefs": load_ui_prefs(config),
        "paths": {
            "settings_dir": str(settings_dir.relative_to(config["ifrit"]["root_path_resolved"])).replace("\\", "/"),
            "env_file": ".env",
        },
    }


def save_ai_settings(config: Dict[str, Any], data: Dict[str, Any]) -> None:
    settings_dir = _settings_dir(config)
    ai_ini = settings_dir / "ai.ini"
    parser = configparser.ConfigParser()
    if ai_ini.is_file():
        parser.read(ai_ini, encoding="utf-8")
    if not parser.has_section("openai"):
        parser.add_section("openai")

    for key in ("base_url", "model", "temperature", "max_tokens", "timeout"):
        if key in data and data[key] is not None:
            parser.set("openai", key, str(data[key]).strip())

    with open(ai_ini, "w", encoding="utf-8") as handle:
        parser.write(handle)

    env_path = _env_file(config)
    lines: List[str] = []
    if env_path.is_file():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    def upsert_env_line(key: str, value: str) -> None:
        nonlocal lines
        prefix = key + "="
        found = False
        new_lines = []
        for line in lines:
            if line.strip().startswith(prefix):
                if value:
                    new_lines.append(f"{key}={value}")
                found = True
            else:
                new_lines.append(line)
        if not found and value:
            new_lines.append(f"{key}={value}")
        lines = new_lines

    api_key = data.get("openai_api_key")
    if api_key and api_key.strip() and "****" not in api_key:
        upsert_env_line("OPENAI_API_KEY", api_key.strip())
    if data.get("openai_base_url_override") is not None:
        upsert_env_line("OPENAI_BASE_URL", str(data.get("openai_base_url_override") or "").strip())
    if data.get("openai_model_override") is not None:
        upsert_env_line("OPENAI_MODEL", str(data.get("openai_model_override") or "").strip())

    # 主表单 base_url/model 同步写入 .env，确保与 ai.ini 一致、实际生效
    if data.get("base_url") is not None:
        upsert_env_line("OPENAI_BASE_URL", str(data.get("base_url") or "").strip())
    if data.get("model") is not None:
        upsert_env_line("OPENAI_MODEL", str(data.get("model") or "").strip())

    if lines or api_key or data.get("base_url") is not None:
        env_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    _reload_project_env(config)


def save_env_entry(config: Dict[str, Any], name: str, base_url: str, timeout: str = "30") -> None:
    env_ini = _settings_dir(config) / "env_config.ini"
    parser = configparser.ConfigParser()
    if env_ini.is_file():
        parser.read(env_ini, encoding="utf-8")
    if not parser.has_section(name):
        parser.add_section(name)
    parser.set(name, "base_url", base_url.strip())
    parser.set(name, "timeout", str(timeout).strip() or "30")
    with open(env_ini, "w", encoding="utf-8") as handle:
        parser.write(handle)


def save_auth_settings(config: Dict[str, Any], data: Dict[str, Any]) -> None:
    auth_ini = _settings_dir(config) / "auth.ini"
    parser = configparser.ConfigParser()
    if auth_ini.is_file():
        parser.read(auth_ini, encoding="utf-8")
    if not parser.has_section("auth"):
        parser.add_section("auth")
    if not parser.has_section("login"):
        parser.add_section("login")

    if "enabled" in data:
        parser.set("auth", "enabled", "true" if data["enabled"] else "false")
    if data.get("login_path"):
        parser.set("login", "path", data["login_path"].strip())
    if data.get("login_method"):
        parser.set("login", "method", data["login_method"].strip().upper())
    if data.get("login_body"):
        parser.set("login", "body", data["login_body"].strip())

    with open(auth_ini, "w", encoding="utf-8") as handle:
        parser.write(handle)


def run_health_check(config: Dict[str, Any], ping_llm: bool = False) -> Dict[str, Any]:
    root = config["ifrit"]["root_path_resolved"]
    checks: List[Dict[str, Any]] = []

    def add(name: str, ok: bool, message: str, level: str = "required") -> None:
        checks.append({"name": name, "ok": ok, "message": message, "level": level})

    settings_dir = _settings_dir(config)
    add("配置目录", settings_dir.is_dir(), str(settings_dir.relative_to(root)))

    env_options = load_environment_options(config)
    add("运行环境", len(env_options) > 0, f"共 {len(env_options)} 个环境" if env_options else "env_config.ini 为空")

    auth = load_auth_summary(config)
    add("鉴权配置", auth.get("available"), auth.get("login_path", UNAVAILABLE))

    ai_ini = settings_dir / "ai.ini"
    add("AI 配置", ai_ini.is_file(), "ai.ini 存在" if ai_ini.is_file() else "缺少 ai.ini")

    env_keys = _read_env_keys(config)
    add(
        "API Key",
        True,
        "已配置 OPENAI_API_KEY" if env_keys["openai_api_key_set"] else "未配置（本地 LLM 通常可留空）",
        level="warn" if not env_keys["openai_api_key_set"] else "required",
    )

    smoke = root / config.get("presets", {}).get("smoke_file", "fixtures/smoke/csv/api_test_smoke.csv")
    add("冒烟用例", smoke.is_file(), smoke.name if smoke.is_file() else "冒烟 CSV 缺失", level="warn")

    allure_ok = shutil.which("allure") is not None
    add("Allure CLI", allure_ok, "已安装 allure 命令" if allure_ok else "未检测到 allure（HTML 报告需安装）", level="warn")

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        from core.rag.service import KnowledgeService

        stats = KnowledgeService(str(root)).stats()
        chunks = stats.get("chunks", 0)
        add("知识库 RAG", chunks > 0, f"{chunks} 片段" if chunks else "空库（可在知识库页入库）", level="warn")
    except Exception as error:
        add("知识库 RAG", False, str(error), level="warn")

    if ping_llm and ai_ini.is_file():
        try:
            _reload_project_env(config)
            from config.ai_config import AIConfig
            from agent.llm.client import AIClient

            ai_config = AIConfig()
            openai_cfg = ai_config.get_openai_config()
            endpoint = openai_cfg.get("base_url", "")
            model = openai_cfg.get("model", "")
            if ai_config.validate_config():
                client = AIClient(openai_cfg)
                resp = client.chat_simple(
                    [
                        {"role": "system", "content": "你是助手，请用一句话回复 OK"},
                        {"role": "user", "content": "ping"},
                    ],
                    max_retries=1,
                    max_tokens=32,
                )
                detail = f"{endpoint} · 模型 {model}"
                if resp:
                    add("LLM 连通", True, detail, level="warn")
                else:
                    add(
                        "LLM 连通",
                        False,
                        f"{detail} — {client.last_error or '无响应'}",
                        level="warn",
                    )
            else:
                add("LLM 连通", False, f"配置无效 · {endpoint} · {model}", level="warn")
        except Exception as error:
            add("LLM 连通", False, str(error), level="warn")

    required_ok = all(c["ok"] for c in checks if c["level"] == "required")
    return {
        "ready": required_ok,
        "checks": checks,
        "summary": "可以开始测试" if required_ok else "请先完成必要配置（见设置页）",
    }


def ingest_case_file_to_rag(config: Dict[str, Any], relative_path: str) -> Optional[int]:
    prefs = load_ui_prefs(config)
    if not prefs.get("auto_ingest_rag", True):
        return None
    root = config["ifrit"]["root_path_resolved"]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from core.rag.service import KnowledgeService

    full = (root / relative_path.replace("\\", "/")).resolve()
    if not full.is_file():
        return None
    return KnowledgeService(str(root)).ingest_file(str(full), source_type="fixture")
