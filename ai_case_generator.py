#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI测试用例生成器独立脚本
提供独立的AI测试用例生成功能，支持批量处理和交互式操作
"""

import argparse
import os
import sys
import time
import glob
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.ai_config import AIConfig
from agent.parser.document_parser import DocumentParser
from agent.llm.client import AIClient
from agent.generator.case_generator import CaseGenerator
from agent.generator.template_engine import TemplateEngine
from agent.generator.quality_validator import QualityValidator
from utils.logger import logger


class AITestCaseGenerator:
    """AI测试用例生成器"""
    
    def __init__(self):
        """初始化生成器"""
        # 初始化配置
        self.ai_config = AIConfig()
        if not self.ai_config.validate_config():
            logger.error("AI配置验证失败，请检查配置文件")
            sys.exit(1)
        
        self.openai_config = self.ai_config.get_openai_config()
        self.generation_config = self.ai_config.get_generation_config()
        self.prompt_templates = self.ai_config.get_prompt_templates()
        self.output_config = self.ai_config.get_output_config()
        
        # 初始化组件
        self.parser = DocumentParser()
        self.ai_client = AIClient(self.openai_config)
        self.generator = CaseGenerator(self.ai_client, self.generation_config, self.prompt_templates)
        self.template_engine = TemplateEngine()
        self.validator = QualityValidator()
        
        logger.info("AI测试用例生成器初始化完成")
    
    def generate_from_single_doc(self, doc_path: str, endpoints: List[str] = None, 
                                output_format: str = 'csv', output_dir: str = None,
                                preview: bool = False) -> bool:
        """
        从单个文档生成测试用例
        
        Args:
            doc_path: 文档路径
            endpoints: 指定端点列表
            output_format: 输出格式
            output_dir: 输出目录
            preview: 是否预览模式
            
        Returns:
            是否成功
        """
        logger.info(f"开始处理文档: {doc_path}")
        
        if not os.path.exists(doc_path):
            logger.error(f"文档不存在: {doc_path}")
            return False
        
        try:
            # 解析文档
            apis = self.parser.parse_document(doc_path, endpoints)
            if not apis:
                logger.error(f"未能从文档 {doc_path} 中解析出任何API接口")
                return False
            
            logger.info(f"从 {doc_path} 解析出 {len(apis)} 个API接口")
            
            # 生成测试用例
            all_test_cases = []
            for api in apis:
                logger.info(f"为API {api['method']} {api['path']} 生成测试用例")
                cases = self.generator.generate_all_cases(api)
                all_test_cases.extend(cases)
            
            if not all_test_cases:
                logger.error("未能生成任何测试用例")
                return False
            
            logger.info(f"总共生成了 {len(all_test_cases)} 个测试用例")
            
            # 质量验证
            validation_result = self.validator.validate_batch_cases(all_test_cases)
            self._show_validation_result(validation_result)
            
            # 预览模式
            if preview:
                self._show_preview(all_test_cases, output_format)
                response = input("是否保存这些测试用例？(y/n): ")
                if response.lower() != 'y':
                    logger.info("用户取消保存")
                    return True
            
            # 保存文件
            output_path = self._generate_output_path(doc_path, output_format, output_dir)
            success = self.template_engine.save_cases_to_file(all_test_cases, output_path, output_format)
            
            if success:
                logger.info(f"成功保存 {len(all_test_cases)} 个测试用例到: {output_path}")
                self._show_statistics()
                return True
            else:
                logger.error("保存测试用例失败")
                return False
                
        except Exception as e:
            logger.error(f"处理文档 {doc_path} 时发生异常: {str(e)}")
            return False
    
    def generate_from_multiple_docs(self, doc_paths: List[str], endpoints: List[str] = None,
                                   output_format: str = 'csv', output_dir: str = None,
                                   merge_output: bool = False) -> bool:
        """
        从多个文档批量生成测试用例
        
        Args:
            doc_paths: 文档路径列表
            endpoints: 指定端点列表
            output_format: 输出格式
            output_dir: 输出目录
            merge_output: 是否合并输出到单个文件
            
        Returns:
            是否成功
        """
        logger.info(f"开始批量处理 {len(doc_paths)} 个文档")
        
        if merge_output:
            return self._generate_merged_output(doc_paths, endpoints, output_format, output_dir)
        else:
            return self._generate_separate_outputs(doc_paths, endpoints, output_format, output_dir)
    
    def _generate_merged_output(self, doc_paths: List[str], endpoints: List[str],
                               output_format: str, output_dir: str) -> bool:
        """生成合并输出"""
        all_test_cases = []
        processed_docs = []
        
        for doc_path in doc_paths:
            if not os.path.exists(doc_path):
                logger.warning(f"文档不存在，跳过: {doc_path}")
                continue
            
            try:
                # 解析文档
                apis = self.parser.parse_document(doc_path, endpoints)
                if not apis:
                    logger.warning(f"未能从文档 {doc_path} 中解析出API接口，跳过")
                    continue
                
                # 生成测试用例
                for api in apis:
                    cases = self.generator.generate_all_cases(api)
                    all_test_cases.extend(cases)
                
                processed_docs.append(os.path.basename(doc_path))
                logger.info(f"已处理文档: {doc_path}")
                
            except Exception as e:
                logger.error(f"处理文档 {doc_path} 时发生异常: {str(e)}")
                continue
        
        if not all_test_cases:
            logger.error("未能生成任何测试用例")
            return False
        
        logger.info(f"总共生成了 {len(all_test_cases)} 个测试用例")
        
        # 质量验证
        validation_result = self.validator.validate_batch_cases(all_test_cases)
        self._show_validation_result(validation_result)
        
        # 生成合并文件名
        merged_name = "_".join([os.path.splitext(doc)[0] for doc in processed_docs[:3]])
        if len(processed_docs) > 3:
            merged_name += f"_and_{len(processed_docs)-3}_more"
        
        output_path = self._generate_output_path(merged_name, output_format, output_dir)
        success = self.template_engine.save_cases_to_file(all_test_cases, output_path, output_format)
        
        if success:
            logger.info(f"成功保存合并的 {len(all_test_cases)} 个测试用例到: {output_path}")
            self._show_statistics()
            return True
        else:
            logger.error("保存合并测试用例失败")
            return False
    
    def _generate_separate_outputs(self, doc_paths: List[str], endpoints: List[str],
                                  output_format: str, output_dir: str) -> bool:
        """生成分离输出"""
        success_count = 0
        
        for doc_path in doc_paths:
            if self.generate_from_single_doc(doc_path, endpoints, output_format, output_dir):
                success_count += 1
        
        logger.info(f"批量处理完成: {success_count}/{len(doc_paths)} 个文档处理成功")
        return success_count > 0
    
    def _show_validation_result(self, validation_result: Dict[str, Any]) -> None:
        """显示验证结果"""
        if validation_result['invalid_cases'] > 0:
            logger.warning(f"发现 {validation_result['invalid_cases']} 个无效用例")
            
            # 显示部分错误信息
            for error in validation_result['errors'][:5]:
                logger.warning(f"  - {error}")
            
            if len(validation_result['errors']) > 5:
                logger.warning(f"  ... 还有 {len(validation_result['errors']) - 5} 个错误")
            
            # 生成修复建议
            suggestions = self.validator.generate_fix_suggestions(validation_result['errors'])
            if suggestions:
                logger.info("修复建议:")
                for suggestion in suggestions:
                    logger.info(f"  - {suggestion}")
        
        # 显示质量评分
        quality_score = self.validator.get_quality_score(validation_result)
        logger.info(f"质量评分: {quality_score['score']} ({quality_score['grade']}) - {quality_score['description']}")
    
    def _show_preview(self, test_cases: List[Dict[str, Any]], output_format: str) -> None:
        """显示预览"""
        print("\n" + "="*60)
        print("测试用例预览")
        print("="*60)
        
        # 按类型分组显示
        case_types = {}
        for case in test_cases:
            case_id = case.get('case_id', '')
            case_type = case_id.split('_')[0] if '_' in case_id else 'unknown'
            if case_type not in case_types:
                case_types[case_type] = []
            case_types[case_type].append(case)
        
        for case_type, cases in case_types.items():
            print(f"\n{case_type.upper()} 测试用例 ({len(cases)}个):")
            for i, case in enumerate(cases[:3]):  # 只显示前3个
                print(f"  {i+1}. {case.get('case_name', 'Unknown')}")
                print(f"     {case.get('method', 'GET')} {case.get('url', '/')}")
                print(f"     期望状态码: {case.get('expected_status', '200')}")
            
            if len(cases) > 3:
                print(f"  ... 还有 {len(cases) - 3} 个用例")
        
        print(f"\n总计: {len(test_cases)} 个测试用例")
        print(f"输出格式: {output_format.upper()}")
        print("="*60)
    
    def _show_statistics(self) -> None:
        """显示统计信息"""
        stats = self.generator.get_generation_summary()
        print("\n" + "="*50)
        print("生成统计信息")
        print("="*50)
        print(f"AI调用次数: {stats['ai_calls']}")
        print(f"总耗时: {stats['total_response_time']:.2f} 秒")
        print(f"平均耗时: {stats['average_response_time']:.2f} 秒")
        print(f"消耗tokens: {stats['total_tokens']}")
        print("="*50)
    
    def _generate_output_path(self, doc_path_or_name: str, output_format: str, output_dir: str = None) -> str:
        """生成输出路径"""
        # 确定输出目录
        if output_dir is None:
            output_dir = self.output_config.get('default_output_dir', 'data/ai_generated')
        
        # 根据格式确定子目录
        format_dirs = {
            'excel': 'excel_data',
            'csv': 'csv_data',
            'json': 'json_data'
        }
        
        if output_format in format_dirs:
            output_dir = os.path.join(output_dir, format_dirs[output_format])
        
        # 生成文件名
        if os.path.exists(doc_path_or_name):
            doc_name = os.path.splitext(os.path.basename(doc_path_or_name))[0]
        else:
            doc_name = doc_path_or_name
        
        timestamp = time.strftime("%Y%m%d_%H%M%S") if self.output_config.get('add_timestamp', True) else ""
        prefix = self.output_config.get('file_prefix', 'ai_')
        
        # 确定正确的文件扩展名
        file_extension = 'xlsx' if output_format.lower() == 'excel' else output_format
        
        if timestamp:
            filename = f"{prefix}{doc_name}_{timestamp}.{file_extension}"
        else:
            filename = f"{prefix}{doc_name}.{file_extension}"
        
        return os.path.join(output_dir, filename)
    
    def interactive_mode(self) -> None:
        """交互式模式"""
        print("\n" + "="*60)
        print("AI测试用例生成器 - 交互式模式")
        print("="*60)
        
        while True:
            print("\n请选择操作:")
            print("1. 从单个文档生成测试用例")
            print("2. 从多个文档批量生成测试用例")
            print("3. 查看配置信息")
            print("4. 退出")
            
            choice = input("\n请输入选择 (1-4): ").strip()
            
            if choice == '1':
                self._interactive_single_doc()
            elif choice == '2':
                self._interactive_multiple_docs()
            elif choice == '3':
                self._show_config_info()
            elif choice == '4':
                print("退出程序")
                break
            else:
                print("无效选择，请重新输入")
    
    def _interactive_single_doc(self) -> None:
        """交互式单文档处理"""
        print("\n--- 单文档处理 ---")
        
        # 输入文档路径
        doc_path = input("请输入文档路径: ").strip()
        if not doc_path:
            print("文档路径不能为空")
            return
        
        # 输入端点过滤
        endpoints_input = input("请输入要处理的端点（多个用逗号分隔，留空处理所有）: ").strip()
        endpoints = [e.strip() for e in endpoints_input.split(',')] if endpoints_input else None
        
        # 选择输出格式
        print("请选择输出格式:")
        print("1. CSV")
        print("2. Excel")
        print("3. JSON")
        format_choice = input("请输入选择 (1-3): ").strip()
        
        format_map = {'1': 'csv', '2': 'excel', '3': 'json'}
        output_format = format_map.get(format_choice, 'csv')
        
        # 输出目录
        output_dir = input("请输入输出目录（留空使用默认）: ").strip() or None
        
        # 是否预览
        preview = input("是否预览生成结果？(y/n): ").strip().lower() == 'y'
        
        # 执行生成
        print("\n开始生成...")
        success = self.generate_from_single_doc(doc_path, endpoints, output_format, output_dir, preview)
        
        if success:
            print("✓ 生成完成")
        else:
            print("✗ 生成失败")
    
    def _interactive_multiple_docs(self) -> None:
        """交互式多文档处理"""
        print("\n--- 批量文档处理 ---")
        
        # 输入文档路径
        print("请输入文档路径（支持通配符，如 __docs/*.md）:")
        paths_input = input("文档路径: ").strip()
        if not paths_input:
            print("文档路径不能为空")
            return
        
        # 展开通配符
        doc_paths = glob.glob(paths_input)
        if not doc_paths:
            print(f"未找到匹配的文档: {paths_input}")
            return
        
        print(f"找到 {len(doc_paths)} 个文档:")
        for i, path in enumerate(doc_paths[:10]):  # 只显示前10个
            print(f"  {i+1}. {path}")
        if len(doc_paths) > 10:
            print(f"  ... 还有 {len(doc_paths) - 10} 个文档")
        
        # 确认处理
        if input("是否继续处理这些文档？(y/n): ").strip().lower() != 'y':
            return
        
        # 输入端点过滤
        endpoints_input = input("请输入要处理的端点（多个用逗号分隔，留空处理所有）: ").strip()
        endpoints = [e.strip() for e in endpoints_input.split(',')] if endpoints_input else None
        
        # 选择输出格式
        print("请选择输出格式:")
        print("1. CSV")
        print("2. Excel")
        print("3. JSON")
        format_choice = input("请输入选择 (1-3): ").strip()
        
        format_map = {'1': 'csv', '2': 'excel', '3': 'json'}
        output_format = format_map.get(format_choice, 'csv')
        
        # 输出目录
        output_dir = input("请输入输出目录（留空使用默认）: ").strip() or None
        
        # 是否合并输出
        merge_output = input("是否合并所有文档的输出到单个文件？(y/n): ").strip().lower() == 'y'
        
        # 执行生成
        print("\n开始批量生成...")
        success = self.generate_from_multiple_docs(doc_paths, endpoints, output_format, output_dir, merge_output)
        
        if success:
            print("✓ 批量生成完成")
        else:
            print("✗ 批量生成失败")
    
    def _show_config_info(self) -> None:
        """显示配置信息"""
        print("\n--- 配置信息 ---")
        
        openai_config = self.ai_config.get_openai_config()
        generation_config = self.ai_config.get_generation_config()
        output_config = self.ai_config.get_output_config()
        
        print(f"OpenAI端点: {openai_config['base_url']}")
        print(f"模型: {openai_config['model']}")
        print(f"温度: {openai_config['temperature']}")
        print(f"最大tokens: {openai_config['max_tokens']}")
        
        print(f"\n生成策略:")
        print(f"  正向用例: {generation_config['positive_cases_count']} 个")
        print(f"  反向用例: {generation_config['negative_cases_count']} 个")
        print(f"  边界用例: {generation_config['boundary_cases_count']} 个")
        print(f"  结构用例: {generation_config['structure_cases_count']} 个")
        print(f"  路径用例: {generation_config['path_cases_count']} 个")
        print(f"  包含认证用例: {'是' if generation_config['include_auth_cases'] else '否'}")
        
        print(f"\n输出配置:")
        print(f"  默认输出目录: {output_config['default_output_dir']}")
        print(f"  文件前缀: {output_config['file_prefix']}")
        print(f"  添加时间戳: {'是' if output_config['add_timestamp'] else '否'}")
        print(f"  质量检查: {'是' if output_config['quality_check'] else '否'}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AI测试用例生成器")
    parser.add_argument(
        "input_docs",
        nargs="*",
        help="输入文档路径（支持多个文档和通配符）"
    )
    parser.add_argument(
        "--endpoints",
        action="append",
        help="指定要处理的端点，可以多次使用"
    )
    parser.add_argument(
        "--format",
        choices=["excel", "csv", "json"],
        default="csv",
        help="输出格式（默认：csv）"
    )
    parser.add_argument(
        "--output-dir",
        help="输出目录"
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="合并多个文档的输出到单个文件"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="预览生成结果后再保存"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="启动交互式模式"
    )
    
    args = parser.parse_args()
    
    try:
        # 初始化生成器
        generator = AITestCaseGenerator()
        
        # 交互式模式
        if args.interactive:
            generator.interactive_mode()
            return
        
        # 检查输入文档
        if not args.input_docs:
            print("错误: 请指定输入文档路径或使用 --interactive 启动交互式模式")
            print("使用 --help 查看帮助信息")
            return
        
        # 展开通配符
        all_docs = []
        for pattern in args.input_docs:
            matched = glob.glob(pattern)
            if matched:
                all_docs.extend(matched)
            else:
                if os.path.exists(pattern):
                    all_docs.append(pattern)
                else:
                    logger.warning(f"文档不存在: {pattern}")
        
        if not all_docs:
            logger.error("未找到任何有效的输入文档")
            return
        
        # 处理文档
        if len(all_docs) == 1:
            # 单文档处理
            success = generator.generate_from_single_doc(
                all_docs[0], 
                args.endpoints, 
                args.format, 
                args.output_dir,
                args.preview
            )
        else:
            # 多文档处理
            success = generator.generate_from_multiple_docs(
                all_docs,
                args.endpoints,
                args.format,
                args.output_dir,
                args.merge
            )
        
        if success:
            logger.info("AI测试用例生成完成")
        else:
            logger.error("AI测试用例生成失败")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"程序执行异常: {str(e)}")
        import traceback
        logger.error(f"详细错误信息:\n{traceback.format_exc()}")
        sys.exit(1)


if __name__ == '__main__':
    main()