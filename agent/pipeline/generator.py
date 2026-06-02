#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：AI 用例生成流水线，基于 ReAct + Skill 编排
创建时间：2026-06-02
"""
import logging
import os
import time
from typing import Any, Optional
from urllib.parse import urlparse

from agent.generator.case_generator import CaseGenerator
from agent.generator.quality_validator import QualityValidator
from agent.generator.template_engine import TemplateEngine
from agent.llm.client import AIClient
from agent.parser.document_parser import DocumentParser
from agent.react.loop import ReActLoop
from agent.skills.registry import get_actions, list_skills
from config.ai_config import AIConfig

logger = logging.getLogger(__name__)

FORMAT_SUBDIRS = {
    "excel": "excel_data",
    "csv": "csv_data",
    "json": "json_data",
}


class AIGenerator:
    """AI 测试用例生成器（ReAct + Skill 驱动）。"""

    def __init__(self, skill_name: Optional[str] = None):
        self.skill_name = skill_name
        self.logger = logger

    def _resolve_skill_name(self, args: Any) -> str:
        if getattr(args, "skill", None):
            return args.skill
        if self.skill_name:
            return self.skill_name
        if getattr(args, "input_url", None):
            return "doc_url_generation"
        return "case_generation"

    def _resolve_doc_source(self, args: Any) -> None:
        """校验并归一化 input_doc / input_url。"""
        input_url = getattr(args, "input_url", None)
        input_doc = getattr(args, "input_doc", None)

        if not input_url and not input_doc:
            raise ValueError("必须指定 --input-doc 或 --input-url")

        if input_doc and not os.path.exists(input_doc):
            raise FileNotFoundError(f"输入文档不存在: {input_doc}")

    def _doc_basename(self, args: Any) -> str:
        if getattr(args, "input_doc", None):
            return os.path.splitext(os.path.basename(args.input_doc))[0]
        if getattr(args, "input_url", None):
            path = urlparse(args.input_url).path
            name = os.path.splitext(os.path.basename(path))[0]
            return name or "remote_doc"
        return "ai_doc"

    def _resolve_output_path(self, args: Any, output_config: dict) -> str:
        """计算输出文件路径。"""
        if args.output_dir:
            output_dir = args.output_dir
        else:
            base_dir = output_config.get("default_output_dir", "fixtures/ai/csv")
            sub_dir = FORMAT_SUBDIRS.get(args.output_format, "")
            normalized = base_dir.replace("\\", "/").rstrip("/")
            if sub_dir and not normalized.endswith(sub_dir):
                output_dir = os.path.join(base_dir, sub_dir)
            else:
                output_dir = base_dir

        os.makedirs(output_dir, exist_ok=True)

        timestamp = (
            time.strftime("%Y%m%d_%H%M%S")
            if output_config.get("add_timestamp", True)
            else ""
        )
        prefix = output_config.get("file_prefix", "ai_")
        doc_name = self._doc_basename(args)
        extension = "xlsx" if args.output_format.lower() == "excel" else args.output_format

        if timestamp:
            filename = f"{prefix}{doc_name}_{timestamp}.{extension}"
        else:
            filename = f"{prefix}{doc_name}.{extension}"

        output_path = os.path.join(output_dir, filename)

        if os.path.exists(output_path):
            resolution = output_config.get("conflict_resolution", "overwrite")
            if resolution == "ask":
                response = input(f"文件 {output_path} 已存在，是否覆盖？(y/n): ")
                if response.lower() != "y":
                    raise RuntimeError("用户取消覆盖")
            elif resolution == "rename":
                counter = 1
                base_path = output_path
                while os.path.exists(output_path):
                    name, ext = os.path.splitext(base_path)
                    output_path = f"{name}_{counter}{ext}"
                    counter += 1

        return output_path

    def _log_validation(self, test_cases: list, output_config: dict) -> None:
        """记录质量验证结果。"""
        if not output_config.get("quality_check", True):
            return

        validator = QualityValidator()
        result = validator.validate_batch_cases(test_cases)
        if result["invalid_cases"] > 0:
            self.logger.warning("发现 %s 个无效用例", result["invalid_cases"])
            for error in result["errors"][:10]:
                self.logger.warning("  - %s", error)

        score = validator.get_quality_score(result)
        self.logger.info(
            "质量评分: %s (%s) - %s",
            score["score"],
            score["grade"],
            score["description"],
        )

    def run(self, args) -> int:
        """运行 AI 用例生成流水线。"""
        try:
            self._resolve_doc_source(args)

            ai_config = AIConfig()
            if not ai_config.validate_config():
                self.logger.error("AI 配置验证失败")
                return 1

            skill_name = self._resolve_skill_name(args)
            if skill_name not in list_skills():
                self.logger.error("未知 skill: %s", skill_name)
                return 1

            openai_config = ai_config.get_openai_config()
            generation_config = ai_config.get_generation_config()
            prompt_templates = ai_config.get_prompt_templates()
            output_config = ai_config.get_output_config()

            ai_client = AIClient(openai_config)
            case_generator = CaseGenerator(
                ai_client, generation_config, prompt_templates
            )
            output_path = self._resolve_output_path(args, output_config)

            context = {
                "input_doc": args.input_doc,
                "input_url": getattr(args, "input_url", None),
                "endpoints": args.swagger_endpoint,
                "parser": DocumentParser(),
                "generator": case_generator,
                "template_engine": TemplateEngine(),
                "output_format": args.output_format,
                "output_path": output_path,
                "quality_check": output_config.get("quality_check", True),
            }

            self.logger.info("启动 Skill: %s", skill_name)
            react_loop = ReActLoop(get_actions(skill_name))
            final_context = react_loop.run(context)

            test_cases = final_context.get("test_cases", [])
            self._log_validation(test_cases, output_config)

            stats = case_generator.get_generation_summary()
            self.logger.info(
                "AI 调用统计: 次数=%s, 总耗时=%.2fs, tokens=%s",
                stats["ai_calls"],
                stats["total_response_time"],
                stats["total_tokens"],
            )
            saved_path = final_context.get("output_path", output_path)
            print(f"[IFRIT] AI用例已保存={saved_path} 条数={len(test_cases)} skill={skill_name}")
            return 0

        except Exception as error:
            self.logger.error("AI 生成失败: %s", error)
            import traceback

            self.logger.error(traceback.format_exc())
            print(f"[IFRIT] AI生成失败: {error}")
            return 1

    @staticmethod
    def get_last_output_path(args, output_config: Optional[dict] = None) -> str:
        """供测试脚本获取预期输出路径。"""
        if output_config is None:
            output_config = AIConfig().get_output_config()
        return AIGenerator()._resolve_output_path(args, output_config)
