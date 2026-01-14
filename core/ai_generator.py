#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI生成器
负责使用AI生成测试用例
"""

import os
import time
import logging
from typing import Any


class AIGenerator:
    """AI测试用例生成器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def run(self, args):
        """
        运行AI测试用例生成
        
        Args:
            args: 命令行参数
            
        Returns:
            退出码
        """
        try:
            self.logger.info("开始AI测试用例生成")
            
            # 检查必要参数
            if not args.input_doc:
                self.logger.error("使用AI生成功能时必须指定 --input-doc 参数")
                return 1
            
            if not os.path.exists(args.input_doc):
                self.logger.error(f"输入文档不存在: {args.input_doc}")
                return 1
            
            # 导入AI相关模块
            from config.ai_config import AIConfig
            from core.document_parser import DocumentParser
            from core.ai_client import AIClient
            from core.case_generator import CaseGenerator
            from core.template_engine import TemplateEngine
            from core.quality_validator import QualityValidator
            
            # 初始化配置
            ai_config = AIConfig()
            if not ai_config.validate_config():
                self.logger.error("AI配置验证失败，请检查配置文件")
                return 1
            
            openai_config = ai_config.get_openai_config()
            generation_config = ai_config.get_generation_config()
            prompt_templates = ai_config.get_prompt_templates()
            output_config = ai_config.get_output_config()
            
            # 初始化组件
            parser = DocumentParser()
            ai_client = AIClient(openai_config)
            generator = CaseGenerator(ai_client, generation_config, prompt_templates)
            template_engine = TemplateEngine()
            validator = QualityValidator()
            
            # 解析文档
            self.logger.info(f"解析输入文档: {args.input_doc}")
            apis = parser.parse_document(args.input_doc, args.swagger_endpoint)
            
            if not apis:
                self.logger.error("未能从文档中解析出任何API接口")
                return 1
            
            self.logger.info(f"成功解析出 {len(apis)} 个API接口")
            
            # 生成测试用例
            all_test_cases = []
            for api in apis:
                self.logger.info(f"为API {api['method']} {api['path']} 生成测试用例")
                cases = generator.generate_all_cases(api)
                all_test_cases.extend(cases)
            
            if not all_test_cases:
                self.logger.error("未能生成任何测试用例")
                return 1
            
            self.logger.info(f"总共生成了 {len(all_test_cases)} 个测试用例")
            
            # 质量验证
            if output_config.get('quality_check', True):
                self.logger.info("进行质量验证")
                validation_result = validator.validate_batch_cases(all_test_cases)
                
                if validation_result['invalid_cases'] > 0:
                    self.logger.warning(f"发现 {validation_result['invalid_cases']} 个无效用例")
                    
                    # 显示错误信息
                    for error in validation_result['errors'][:10]:  # 只显示前10个错误
                        self.logger.warning(f"  - {error}")
                    
                    # 生成修复建议
                    suggestions = validator.generate_fix_suggestions(validation_result['errors'])
                    if suggestions:
                        self.logger.info("修复建议:")
                        for suggestion in suggestions:
                            self.logger.info(f"  - {suggestion}")
                
                # 显示质量评分
                quality_score = validator.get_quality_score(validation_result)
                self.logger.info(f"质量评分: {quality_score['score']} ({quality_score['grade']}) - {quality_score['description']}")
            
            # 确定输出路径
            output_dir = args.output_dir or output_config.get('default_output_dir', 'data/ai_generated')
            
            # 根据格式确定子目录
            format_dirs = {
                'excel': 'excel_data',
                'csv': 'csv_data', 
                'json': 'json_data'
            }
            
            if args.output_format in format_dirs:
                output_dir = os.path.join(output_dir, format_dirs[args.output_format])
            
            # 生成文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S") if output_config.get('add_timestamp', True) else ""
            prefix = output_config.get('file_prefix', 'ai_')
            
            doc_name = os.path.splitext(os.path.basename(args.input_doc))[0]
            
            # 确定正确的文件扩展名
            file_extension = 'xlsx' if args.output_format.lower() == 'excel' else args.output_format
            
            if timestamp:
                filename = f"{prefix}{doc_name}_{timestamp}.{file_extension}"
            else:
                filename = f"{prefix}{doc_name}.{file_extension}"
            
            output_path = os.path.join(output_dir, filename)
            
            # 检查文件冲突
            if os.path.exists(output_path):
                conflict_resolution = output_config.get('conflict_resolution', 'ask')
                
                if conflict_resolution == 'ask':
                    response = input(f"文件 {output_path} 已存在，是否覆盖？(y/n): ")
                    if response.lower() != 'y':
                        self.logger.info("用户取消操作")
                        return 0
                elif conflict_resolution == 'rename':
                    counter = 1
                    base_path = output_path
                    while os.path.exists(output_path):
                        name, ext = os.path.splitext(base_path)
                        output_path = f"{name}_{counter}{ext}"
                        counter += 1
                    self.logger.info(f"文件重命名为: {output_path}")
            
            # 保存文件
            success = template_engine.save_cases_to_file(all_test_cases, output_path, args.output_format)
            
            if success:
                self.logger.info(f"成功保存 {len(all_test_cases)} 个测试用例到: {output_path}")
                
                # 显示统计信息
                stats = generator.get_generation_summary()
                self.logger.info(f"AI调用统计: 调用次数={stats['ai_calls']}, 总耗时={stats['total_response_time']:.2f}秒, 平均耗时={stats['average_response_time']:.2f}秒, 消耗tokens={stats['total_tokens']}")
                
                return 0
            else:
                self.logger.error("保存测试用例失败")
                return 1
                
        except Exception as e:
            self.logger.error(f"AI生成过程中发生异常: {str(e)}")
            import traceback
            self.logger.error(f"详细错误信息:\n{traceback.format_exc()}")
            return 1