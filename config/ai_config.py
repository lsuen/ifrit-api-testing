#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
文件用途：AI / LLM 配置管理
核心功能：OpenAI 兼容接口配置、生成策略、prompt、输出策略
创建时间：2025-09-09
"""
import configparser
import logging
import os
from typing import Any, Dict, Optional

from config.loader import SETTINGS_DIR, get_env_override, get_env_value, load_ini

logger = logging.getLogger(__name__)

LOCAL_LLM_HOST_MARKERS = ("localhost", "127.0.0.1", "0.0.0.0")
INVALID_API_KEY_PLACEHOLDERS = ("", "your_openai_api_key_here")


class AIConfig:
    """AI 配置管理器（供 core 与 agent 模块共用）。"""

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = os.path.join(SETTINGS_DIR, "ai.ini")

        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self._load_config()

    def _load_config(self) -> None:
        """加载 AI 配置文件。"""
        if os.path.exists(self.config_path):
            self.config.read(self.config_path, encoding="utf-8")
            logger.info("成功加载 AI 配置: %s", self.config_path)
            return

        logger.warning("AI 配置文件不存在: %s，使用内存默认配置", self.config_path)
        self._create_default_config()

    def _create_default_config(self) -> None:
        """创建内存默认配置（不写 api_key）。"""
        self.config.clear()
        self.config.add_section("openai")
        self.config.set("openai", "base_url", "http://localhost:8000")
        self.config.set("openai", "model", "gpt-3.5-turbo")
        self.config.set("openai", "temperature", "0.7")
        self.config.set("openai", "max_tokens", "2000")
        self.config.set("openai", "timeout", "30")

        self.config.add_section("generation")
        self.config.set("generation", "positive_cases_count", "3")
        self.config.set("generation", "negative_cases_count", "2")
        self.config.set("generation", "boundary_cases_count", "2")
        self.config.set("generation", "structure_cases_count", "1")
        self.config.set("generation", "path_cases_count", "2")
        self.config.set("generation", "include_auth_cases", "true")

        self.config.add_section("prompts")
        self.config.set(
            "prompts",
            "system_prompt",
            "你是一个专业的API测试工程师，需要根据接口文档生成全面的测试用例。",
        )

        self.config.add_section("output")
        self.config.set("output", "default_output_dir", "data/ai_generated")
        self.config.set("output", "add_timestamp", "true")
        self.config.set("output", "file_prefix", "ai_")
        self.config.set("output", "quality_check", "true")
        self.config.set("output", "conflict_resolution", "ask")

    @staticmethod
    def _is_local_endpoint(base_url: str) -> bool:
        """判断是否为本地 LLM 端点（可无 API Key）。"""
        lowered = base_url.lower()
        return any(marker in lowered for marker in LOCAL_LLM_HOST_MARKERS)

    def get_openai_config(self) -> Dict[str, Any]:
        """获取 OpenAI 兼容接口配置。"""
        default_base_url = self.config.get(
            "openai", "base_url", fallback="http://localhost:8000"
        )
        default_model = self.config.get("openai", "model", fallback="gpt-3.5-turbo")
        return {
            "api_key": get_env_value("OPENAI_API_KEY"),
            "base_url": get_env_override("OPENAI_BASE_URL", default_base_url),
            "model": get_env_override("OPENAI_MODEL", default_model),
            "temperature": self.config.getfloat("openai", "temperature", fallback=0.7),
            "max_tokens": self.config.getint("openai", "max_tokens", fallback=2000),
            "timeout": self.config.getint("openai", "timeout", fallback=30),
        }

    def get_generation_config(self) -> Dict[str, Any]:
        """获取用例生成策略配置。"""
        return {
            "positive_cases_count": self.config.getint(
                "generation", "positive_cases_count", fallback=3
            ),
            "negative_cases_count": self.config.getint(
                "generation", "negative_cases_count", fallback=2
            ),
            "boundary_cases_count": self.config.getint(
                "generation", "boundary_cases_count", fallback=2
            ),
            "structure_cases_count": self.config.getint(
                "generation", "structure_cases_count", fallback=1
            ),
            "path_cases_count": self.config.getint(
                "generation", "path_cases_count", fallback=2
            ),
            "include_auth_cases": self.config.getboolean(
                "generation", "include_auth_cases", fallback=True
            ),
        }

    def get_prompt_templates(self) -> Dict[str, str]:
        """获取 prompt 模板。"""
        return {
            "system_prompt": self.config.get(
                "prompts",
                "system_prompt",
                fallback="你是一个专业的API测试工程师，需要根据接口文档生成全面的测试用例。",
            ),
            "positive_template": self.config.get(
                "prompts",
                "positive_template",
                fallback="为以下接口生成正向测试用例，确保正常场景下的功能验证",
            ),
            "negative_template": self.config.get(
                "prompts",
                "negative_template",
                fallback="为以下接口生成反向测试用例，包括参数错误、权限不足等异常场景",
            ),
            "boundary_template": self.config.get(
                "prompts",
                "boundary_template",
                fallback="为以下接口生成边界测试用例，包括最大值、最小值、空值等边界条件",
            ),
        }

    def get_output_config(self) -> Dict[str, Any]:
        """获取 AI 输出配置。"""
        return {
            "default_output_dir": self.config.get(
                "output", "default_output_dir", fallback="data/ai_generated"
            ),
            "add_timestamp": self.config.getboolean(
                "output", "add_timestamp", fallback=True
            ),
            "file_prefix": self.config.get("output", "file_prefix", fallback="ai_"),
            "quality_check": self.config.getboolean(
                "output", "quality_check", fallback=True
            ),
            "conflict_resolution": self.config.get(
                "output", "conflict_resolution", fallback="ask"
            ),
        }

    def validate_config(self) -> bool:
        """验证配置有效性（本地 LLM 可不配置 API Key）。"""
        try:
            openai_config = self.get_openai_config()
            api_key = openai_config["api_key"]

            if not openai_config["base_url"]:
                logger.error("LLM base_url 未设置")
                return False

            if not openai_config["model"]:
                logger.error("LLM model 未设置")
                return False

            if api_key in INVALID_API_KEY_PLACEHOLDERS:
                if self._is_local_endpoint(openai_config["base_url"]):
                    logger.info("本地 LLM 端点，未配置 OPENAI_API_KEY（允许）")
                else:
                    logger.error("公网 LLM 端点需要设置 OPENAI_API_KEY")
                    return False

            generation_config = self.get_generation_config()
            for key, value in generation_config.items():
                if isinstance(value, int) and value < 0:
                    logger.error("生成策略 %s 不能为负数: %s", key, value)
                    return False

            output_config = self.get_output_config()
            if not output_config["default_output_dir"]:
                logger.error("默认输出目录未设置")
                return False

            valid_resolutions = ["ask", "overwrite", "append", "rename"]
            if output_config["conflict_resolution"] not in valid_resolutions:
                logger.error("无效的冲突解决策略: %s", output_config["conflict_resolution"])
                return False

            logger.info("AI 配置验证通过")
            return True

        except Exception as error:
            logger.error("配置验证失败: %s", error)
            return False

    def get_all_config(self) -> Dict[str, Any]:
        """获取完整 AI 配置。"""
        return {
            "openai": self.get_openai_config(),
            "generation": self.get_generation_config(),
            "prompts": self.get_prompt_templates(),
            "output": self.get_output_config(),
        }

    def save_config(self, config_path: Optional[str] = None) -> bool:
        """保存配置到文件。"""
        try:
            save_path = config_path or self.config_path
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as config_file:
                self.config.write(config_file)
            logger.info("AI 配置已保存: %s", save_path)
            return True
        except Exception as error:
            logger.error("保存 AI 配置失败: %s", error)
            return False
