#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模板引擎模块
负责将AI生成的用例转换为框架兼容的格式
"""

import os
import sys
import json
import pandas as pd
from typing import Dict, Any, List
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import Config

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TemplateEngine:
    """模板引擎"""
    
    def __init__(self, config: Config = None):
        """
        初始化模板引擎
        
        Args:
            config: 框架配置实例
        """
        self.config = config or Config()
        self.test_data_config = self.config.test_data_config
        
        # 加载字段映射配置
        self.excel_mapping = self._load_field_mapping('excel')
        self.csv_mapping = self._load_field_mapping('csv')
        self.json_mapping = self._load_field_mapping('json')
        
        logger.info("模板引擎初始化完成")
    
    def _load_field_mapping(self, format_type: str) -> Dict[str, str]:
        """
        加载字段映射配置
        
        Args:
            format_type: 格式类型 (excel/csv/json)
            
        Returns:
            字段映射字典
        """
        mapping = {}
        
        if self.test_data_config.has_section(format_type):
            for key, value in self.test_data_config.items(format_type):
                mapping[key] = value
        
        logger.debug(f"加载 {format_type} 字段映射: {mapping}")
        return mapping
    
    def format_cases_for_output(self, test_cases: List[Dict[str, Any]], output_format: str) -> List[Dict[str, Any]]:
        """
        将测试用例格式化为指定输出格式
        
        Args:
            test_cases: 原始测试用例列表
            output_format: 输出格式 (excel/csv/json)
            
        Returns:
            格式化后的测试用例列表
        """
        logger.info(f"将 {len(test_cases)} 个测试用例格式化为 {output_format} 格式")
        
        formatted_cases = []
        
        for case in test_cases:
            if output_format.lower() == 'excel':
                formatted_case = self.format_case_for_excel(case)
            elif output_format.lower() == 'csv':
                formatted_case = self.format_case_for_csv(case)
            elif output_format.lower() == 'json':
                formatted_case = self.format_case_for_json(case)
            else:
                logger.error(f"不支持的输出格式: {output_format}")
                continue
            
            if formatted_case:
                formatted_cases.append(formatted_case)
        
        logger.info(f"成功格式化 {len(formatted_cases)} 个测试用例")
        return formatted_cases
    
    def format_case_for_excel(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化为Excel格式
        
        Args:
            case_data: 原始用例数据
            
        Returns:
            Excel格式的用例数据
        """
        return self._map_fields(case_data, self.excel_mapping)
    
    def format_case_for_csv(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化为CSV格式
        
        Args:
            case_data: 原始用例数据
            
        Returns:
            CSV格式的用例数据
        """
        return self._map_fields(case_data, self.csv_mapping)
    
    def format_case_for_json(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化为JSON格式
        
        Args:
            case_data: 原始用例数据
            
        Returns:
            JSON格式的用例数据
        """
        return self._map_fields(case_data, self.json_mapping)
    
    def _map_fields(self, case_data: Dict[str, Any], field_mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        字段映射
        
        Args:
            case_data: 原始用例数据
            field_mapping: 字段映射配置
            
        Returns:
            映射后的用例数据
        """
        mapped_case = {}
        
        # 标准字段映射
        field_map = {
            'case_id': ['case_id', 'id'],
            'case_name': ['case_name', 'name'],
            'enabled': ['enabled'],
            'method': ['method'],
            'url': ['url'],
            'headers': ['headers'],
            'params': ['params'],
            'body': ['body', 'data'],
            'expected_status': ['expected_status'],
            'expected_content': ['expected_content', 'expected_result'],
            'json_path': ['json_path'],
            'expected_json_value': ['expected_json_value'],
            'extract_key': ['extract_key', 'extract', 'variable'],
            'save_var_name': ['save_var_name'],
            'validate': ['validate'],
            'priority': ['priority']
        }
        
        # 根据配置映射字段
        for standard_field, possible_fields in field_map.items():
            # 查找配置中的映射
            config_field = field_mapping.get(standard_field)
            if config_field:
                # 使用配置中指定的字段名
                mapped_case[config_field] = case_data.get(standard_field, '')
            else:
                # 尝试可能的字段名
                for field in possible_fields:
                    if field in case_data:
                        mapped_case[field] = case_data[field]
                        break
                else:
                    # 如果都没找到，使用标准字段名和默认值
                    mapped_case[standard_field] = case_data.get(standard_field, '')
        
        # 确保必要字段存在
        self._ensure_required_fields(mapped_case)
        
        return mapped_case
    
    def _ensure_required_fields(self, case_data: Dict[str, Any]) -> None:
        """
        确保必要字段存在
        
        Args:
            case_data: 用例数据
        """
        # 必要字段的默认值
        required_defaults = {
            'enabled': '1',
            'headers': '{"Content-Type": "application/json"}',
            'params': '{}',
            'body': '{}',
            'expected_status': '200',
            'expected_content': '',
            'json_path': '',
            'expected_json_value': '',
            'extract_key': '',
            'save_var_name': '',
            'validate': '',
            'priority': 'medium'
        }
        
        for field, default_value in required_defaults.items():
            # 检查所有可能的字段名
            found = False
            for key in case_data.keys():
                if key.lower() == field.lower() or key == field:
                    found = True
                    break
            
            if not found:
                case_data[field] = default_value
    
    def save_cases_to_file(self, test_cases: List[Dict[str, Any]], file_path: str, output_format: str) -> bool:
        """
        保存测试用例到文件
        
        Args:
            test_cases: 测试用例列表
            file_path: 输出文件路径
            output_format: 输出格式
            
        Returns:
            是否保存成功
        """
        logger.info(f"保存 {len(test_cases)} 个测试用例到文件: {file_path}")
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 格式化用例数据
            formatted_cases = self.format_cases_for_output(test_cases, output_format)
            
            if not formatted_cases:
                logger.error("没有有效的测试用例可保存")
                return False
            
            # 根据格式保存文件
            if output_format.lower() == 'excel':
                return self._save_to_excel(formatted_cases, file_path)
            elif output_format.lower() == 'csv':
                return self._save_to_csv(formatted_cases, file_path)
            elif output_format.lower() == 'json':
                return self._save_to_json(formatted_cases, file_path)
            else:
                logger.error(f"不支持的输出格式: {output_format}")
                return False
                
        except Exception as e:
            logger.error(f"保存测试用例失败: {str(e)}")
            return False
    
    def _save_to_excel(self, test_cases: List[Dict[str, Any]], file_path: str) -> bool:
        """
        保存为Excel文件
        
        Args:
            test_cases: 测试用例列表
            file_path: 文件路径
            
        Returns:
            是否保存成功
        """
        try:
            df = pd.DataFrame(test_cases)
            df.to_excel(file_path, index=False, engine='openpyxl')
            logger.info(f"成功保存Excel文件: {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存Excel文件失败: {str(e)}")
            return False
    
    def _save_to_csv(self, test_cases: List[Dict[str, Any]], file_path: str) -> bool:
        """
        保存为CSV文件
        
        Args:
            test_cases: 测试用例列表
            file_path: 文件路径
            
        Returns:
            是否保存成功
        """
        try:
            df = pd.DataFrame(test_cases)
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            logger.info(f"成功保存CSV文件: {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存CSV文件失败: {str(e)}")
            return False
    
    def _save_to_json(self, test_cases: List[Dict[str, Any]], file_path: str) -> bool:
        """
        保存为JSON文件
        
        Args:
            test_cases: 测试用例列表
            file_path: 文件路径
            
        Returns:
            是否保存成功
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(test_cases, f, ensure_ascii=False, indent=2)
            logger.info(f"成功保存JSON文件: {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存JSON文件失败: {str(e)}")
            return False
    
    def validate_case_compatibility(self, test_cases: List[Dict[str, Any]], output_format: str) -> Dict[str, Any]:
        """
        验证用例与现有框架的兼容性
        
        Args:
            test_cases: 测试用例列表
            output_format: 输出格式
            
        Returns:
            验证结果
        """
        logger.info(f"验证 {len(test_cases)} 个测试用例的兼容性")
        
        validation_result = {
            'total_cases': len(test_cases),
            'valid_cases': 0,
            'invalid_cases': 0,
            'errors': [],
            'warnings': []
        }
        
        # 获取字段映射
        if output_format.lower() == 'excel':
            field_mapping = self.excel_mapping
        elif output_format.lower() == 'csv':
            field_mapping = self.csv_mapping
        elif output_format.lower() == 'json':
            field_mapping = self.json_mapping
        else:
            validation_result['errors'].append(f"不支持的输出格式: {output_format}")
            return validation_result
        
        for i, case in enumerate(test_cases):
            case_errors = []
            case_warnings = []
            
            # 检查必要字段
            required_fields = ['case_name', 'method', 'url']
            for field in required_fields:
                if not case.get(field):
                    case_errors.append(f"用例 {i+1} 缺少必要字段: {field}")
            
            # 检查HTTP方法
            method = case.get('method', '').upper()
            if method not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                case_errors.append(f"用例 {i+1} HTTP方法无效: {method}")
            
            # 检查JSON格式
            json_fields = ['headers', 'params', 'body']
            for field in json_fields:
                value = case.get(field, '{}')
                if value and value != '{}':
                    try:
                        json.loads(value)
                    except json.JSONDecodeError:
                        case_warnings.append(f"用例 {i+1} {field} 字段JSON格式可能有问题")
            
            # 检查状态码
            status_code = case.get('expected_status', '200')
            try:
                status_int = int(status_code)
                if status_int < 100 or status_int > 599:
                    case_warnings.append(f"用例 {i+1} 状态码可能无效: {status_code}")
            except ValueError:
                case_errors.append(f"用例 {i+1} 状态码格式错误: {status_code}")
            
            if case_errors:
                validation_result['invalid_cases'] += 1
                validation_result['errors'].extend(case_errors)
            else:
                validation_result['valid_cases'] += 1
            
            validation_result['warnings'].extend(case_warnings)
        
        logger.info(f"兼容性验证完成: {validation_result['valid_cases']}/{validation_result['total_cases']} 个用例有效")
        return validation_result
    
    def get_supported_formats(self) -> List[str]:
        """
        获取支持的输出格式
        
        Returns:
            支持的格式列表
        """
        return ['excel', 'csv', 'json']


if __name__ == '__main__':
    # 测试模板引擎
    template_engine = TemplateEngine()
    
    # 测试用例数据
    test_cases = [
        {
            'case_id': 'test_001',
            'case_name': '用户登录-正常场景',
            'method': 'POST',
            'url': '/api/user/login',
            'headers': '{"Content-Type": "application/json"}',
            'params': '{}',
            'body': '{"username": "admin", "password": "123456"}',
            'expected_status': '200',
            'expected_content': '成功',
            'json_path': 'code',
            'expected_json_value': '200',
            'validate': '',
            'enabled': '1'
        },
        {
            'case_id': 'test_002',
            'case_name': '用户登录-参数错误',
            'method': 'POST',
            'url': '/api/user/login',
            'headers': '{"Content-Type": "application/json"}',
            'params': '{}',
            'body': '{"username": "", "password": ""}',
            'expected_status': '400',
            'expected_content': '参数错误',
            'json_path': '',
            'expected_json_value': '',
            'validate': '',
            'enabled': '1'
        }
    ]
    
    print("测试模板引擎...")
    
    # 测试格式化
    print("\n测试Excel格式化:")
    excel_cases = template_engine.format_cases_for_output(test_cases, 'excel')
    for case in excel_cases:
        print(f"- {case.get('name', case.get('case_name', 'Unknown'))}")
    
    print("\n测试CSV格式化:")
    csv_cases = template_engine.format_cases_for_output(test_cases, 'csv')
    for case in csv_cases:
        print(f"- {case.get('name', case.get('case_name', 'Unknown'))}")
    
    # 测试兼容性验证
    print("\n测试兼容性验证:")
    validation_result = template_engine.validate_case_compatibility(test_cases, 'excel')
    print(f"验证结果: {validation_result}")
    
    # 测试保存文件
    print("\n测试保存文件:")
    os.makedirs('data/test_output', exist_ok=True)
    
    success = template_engine.save_cases_to_file(test_cases, 'data/test_output/test_cases.csv', 'csv')
    print(f"CSV保存结果: {success}")
    
    success = template_engine.save_cases_to_file(test_cases, 'data/test_output/test_cases.json', 'json')
    print(f"JSON保存结果: {success}")
    
    print(f"\n支持的格式: {template_engine.get_supported_formats()}")