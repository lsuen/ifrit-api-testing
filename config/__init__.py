"""
作者：孙文龙
配置模块入口：统一导出 Config / AIConfig 与 loader 工具。
"""
from config.ai_config import AIConfig
from config.config import Config
from config.loader import (
    get_dingtalk_config,
    get_env_value,
    get_project_root,
    load_dotenv,
    load_ini,
)

__all__ = [
    "AIConfig",
    "Config",
    "get_dingtalk_config",
    "get_env_value",
    "get_project_root",
    "load_dotenv",
    "load_ini",
]
