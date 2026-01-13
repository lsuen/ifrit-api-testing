#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
质量验证器模块
负责验证生成用例的质量和完整性
"""

import json
import re
import urllib.parse
from typing import Dict, Any, List, Tuple, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class QualityValidator:
    """质量验证器"""
    
    def __init__(self):
        """初始化质量验证器"""
        # 有效的HTTP方法
        self.valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
        
        # 有效的状态码范围
        self.valid_status_codes = range(100, 600)
        
        # 必填字段
        self.required_fields = ['case_name', 'method', 'url']
        
        # JSON字段
        self.json_fields = ['headers', 'params', 'body']
        
        logger.info("质量验证器初始化完成")
    
    def validate_test_case(self, test_case: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证单个测试用例
        
        Args:
            test_case: 测试用例数据
            
        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []
        
        # 验证必填字段
        field_errors = self._validate_required_fields(test_case)
        errors.extend(field_errors)
        
        # 验证HTTP方法
        method_errors = self._validate_http_method(test_case.get('method', ''))
        errors.extend(method_errors)
        
        # 验证URL格式
        url_errors = self._validate_url_format(test_case.get('url', ''))
        errors.extend(url_errors)
        
        # 验证JSON格式
        json_errors = self._validate_json_fields(test_case)
        errors.extend(json_errors)
        
        # 验证状态码
        status_errors = self._validate_status_code(test_case.get('expected_status', ''))
        errors.extend(status_errors)
        
        # 验证逻辑一致性
        logic_errors = self._validate_logic_consistency(test_case)
        errors.extend(logic_errors)
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.debug(f"测试用例验证通过: {test_case.get('case_name', 'Unknown')}")
        else:
            logger.warning(f"测试用例验证失败: {test_case.get('case_name', 'Unknown')}, 错误: {errors}")
        
        return is_valid, errors
    
    def validate_batch_cases(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量验证测试用例
        
        Args:
            test_cases: 测试用例列表
            
        Returns:
            验证结果统计
        """
        logger.info(f"开始批量验证 {len(test_cases)} 个测试用例")
        
        result = {
            'total_cases': len(test_cases),
            'valid_cases': 0,
            'invalid_cases': 0,
            'errors': [],
            'warnings': [],
            'case_details': []
        }
        
        for i, test_case in enumerate(test_cases):
            is_valid, errors = self.validate_test_case(test_case)
            
            case_detail = {
                'index': i,
                'case_name': test_case.get('case_name', f'Case_{i+1}'),
                'is_valid': is_valid,
                'errors': errors
            }
            
            result['case_details'].append(case_detail)
            
            if is_valid:
                result['valid_cases'] += 1
            else:
                result['invalid_cases'] += 1
                result['errors'].extend([f"用例 {i+1} ({case_detail['case_name']}): {error}" for error in errors])
        
        # 生成警告信息
        warnings = self._generate_batch_warnings(test_cases)
        result['warnings'] = warnings
        
        logger.info(f"批量验证完成: {result['valid_cases']}/{result['total_cases']} 个用例有效")
        return result
    
    def _validate_required_fields(self, test_case: Dict[str, Any]) -> List[str]:
        """验证必填字段"""
        errors = []
        
        for field in self.required_fields:
            value = test_case.get(field, '')
            if not value or str(value).strip() == '':
                errors.append(f"必填字段 '{field}' 缺失或为空")
        
        return errors
    
    def _validate_http_method(self, method: str) -> List[str]:
        """验证HTTP方法"""
        errors = []
        
        if not method:
            errors.append("HTTP方法不能为空")
        elif method.upper() not in self.valid_methods:
            errors.append(f"无效的HTTP方法: {method}，有效方法: {', '.join(self.valid_methods)}")
        
        return errors
    
    def _validate_url_format(self, url: str) -> List[str]:
        """验证URL格式"""
        errors = []
        
        if not url:
            errors.append("URL不能为空")
            return errors
        
        # 检查URL格式
        if not url.startswith('/') and not url.startswith('http'):
            errors.append(f"URL格式错误: {url}，应该以 '/' 或 'http' 开头")
        
        # 检查URL中的特殊字符
        try:
            # 尝试解析URL
            if url.startswith('http'):
                parsed = urllib.parse.urlparse(url)
                if not parsed.scheme or not parsed.netloc:
                    errors.append(f"完整URL格式错误: {url}")
            else:
                # 相对路径URL
                if ' ' in url:
                    errors.append(f"URL包含空格: {url}")
        except Exception as e:
            errors.append(f"URL解析失败: {url}, 错误: {str(e)}")
        
        return errors
    
    def _validate_json_fields(self, test_case: Dict[str, Any]) -> List[str]:
        """验证JSON格式字段"""
        errors = []
        
        for field in self.json_fields:
            value = test_case.get(field, '{}')
            if value and value != '{}':
                try:
                    json.loads(value)
                except json.JSONDecodeError as e:
                    errors.append(f"字段 '{field}' JSON格式错误: {str(e)}")
        
        return errors
    
    def _validate_status_code(self, status_code: str) -> List[str]:
        """验证状态码"""
        errors = []
        
        if not status_code:
            errors.append("期望状态码不能为空")
            return errors
        
        try:
            code = int(status_code)
            if code not in self.valid_status_codes:
                errors.append(f"无效的状态码: {code}，有效范围: 100-599")
        except ValueError:
            errors.append(f"状态码格式错误: {status_code}，应该是数字")
        
        return errors
    
    def _validate_logic_consistency(self, test_case: Dict[str, Any]) -> List[str]:
        """验证逻辑一致性"""
        errors = []
        
        method = test_case.get('method', '').upper()
        status_code = test_case.get('expected_status', '')
        expected_content = test_case.get('expected_content', '')
        body = test_case.get('body', '{}')
        
        try:
            status_int = int(status_code)
            
            # 检查GET请求不应该有请求体
            if method == 'GET' and body and body != '{}':
                try:
                    body_data = json.loads(body)
                    if body_data:  # 非空对象
                        errors.append("GET请求不应该包含请求体")
                except json.JSONDecodeError:
                    pass  # JSON错误会在其他地方检查
            
            # 检查状态码与期望内容的一致性
            if status_int >= 400:
                # 错误状态码应该有错误相关的期望内容
                if expected_content and '成功' in expected_content:
                    errors.append(f"状态码 {status_code} 表示错误，但期望内容包含'成功'")
            elif status_int >= 200 and status_int < 300:
                # 成功状态码应该有成功相关的期望内容
                if expected_content and ('错误' in expected_content or '失败' in expected_content):
                    errors.append(f"状态码 {status_code} 表示成功，但期望内容包含'错误'或'失败'")
            
            # 检查POST/PUT请求通常需要请求体
            if method in ['POST', 'PUT'] and (not body or body == '{}'):
                # 这是警告而不是错误，因为有些POST请求可能不需要请求体
                pass
            
        except ValueError:
            # 状态码格式错误会在其他地方检查
            pass
        
        return errors
    
    def _generate_batch_warnings(self, test_cases: List[Dict[str, Any]]) -> List[str]:
        """生成批量验证的警告信息"""
        warnings = []
        
        # 检查用例名称重复
        case_names = [case.get('case_name', '') for case in test_cases]
        duplicates = []
        for name in set(case_names):
            if case_names.count(name) > 1 and name:
                duplicates.append(name)
        
        if duplicates:
            warnings.append(f"发现重复的用例名称: {', '.join(duplicates)}")
        
        # 检查用例覆盖度
        methods = [case.get('method', '').upper() for case in test_cases]
        unique_methods = set(methods)
        if len(unique_methods) == 1:
            warnings.append(f"所有用例都使用相同的HTTP方法: {list(unique_methods)[0]}")
        
        # 检查状态码覆盖度
        status_codes = [case.get('expected_status', '') for case in test_cases]
        unique_status = set(status_codes)
        if len(unique_status) == 1:
            warnings.append(f"所有用例都期望相同的状态码: {list(unique_status)[0]}")
        
        return warnings
    
    def generate_fix_suggestions(self, errors: List[str]) -> List[str]:
        """
        生成修复建议
        
        Args:
            errors: 错误信息列表
            
        Returns:
            修复建议列表
        """
        suggestions = []
        
        for error in errors:
            if "必填字段" in error and "缺失" in error:
                suggestions.append("请确保所有必填字段都有有效值，特别是 case_name、method 和 url")
            
            elif "HTTP方法" in error:
                suggestions.append(f"请使用有效的HTTP方法: {', '.join(self.valid_methods)}")
            
            elif "URL格式错误" in error:
                suggestions.append("URL应该以 '/' 开头（相对路径）或以 'http' 开头（完整URL）")
            
            elif "JSON格式错误" in error:
                suggestions.append("请检查 headers、params、body 字段的JSON格式是否正确")
            
            elif "状态码" in error:
                suggestions.append("状态码应该是100-599之间的数字")
            
            elif "GET请求不应该包含请求体" in error:
                suggestions.append("GET请求的 body 字段应该为空或 '{}'")
            
            elif "状态码" in error and "期望内容" in error:
                suggestions.append("请确保状态码与期望内容的逻辑一致性，成功状态码配成功内容，错误状态码配错误内容")
        
        # 去重
        suggestions = list(set(suggestions))
        
        return suggestions
    
    def get_quality_score(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算质量评分
        
        Args:
            validation_result: 验证结果
            
        Returns:
            质量评分信息
        """
        total_cases = validation_result['total_cases']
        valid_cases = validation_result['valid_cases']
        warnings_count = len(validation_result['warnings'])
        
        if total_cases == 0:
            return {'score': 0, 'grade': 'N/A', 'description': '没有测试用例'}
        
        # 基础分数：有效用例比例
        base_score = (valid_cases / total_cases) * 100
        
        # 扣除警告分数
        warning_penalty = min(warnings_count * 5, 20)  # 每个警告扣5分，最多扣20分
        
        final_score = max(0, base_score - warning_penalty)
        
        # 评级
        if final_score >= 90:
            grade = 'A'
            description = '优秀'
        elif final_score >= 80:
            grade = 'B'
            description = '良好'
        elif final_score >= 70:
            grade = 'C'
            description = '一般'
        elif final_score >= 60:
            grade = 'D'
            description = '需要改进'
        else:
            grade = 'F'
            description = '质量较差'
        
        return {
            'score': round(final_score, 1),
            'grade': grade,
            'description': description,
            'valid_ratio': f"{valid_cases}/{total_cases}",
            'warnings_count': warnings_count
        }


if __name__ == '__main__':
    # 测试质量验证器
    validator = QualityValidator()
    
    # 测试用例数据
    test_cases = [
        {
            'case_name': '用户登录-正常场景',
            'method': 'POST',
            'url': '/api/user/login',
            'headers': '{"Content-Type": "application/json"}',
            'params': '{}',
            'body': '{"username": "admin", "password": "123456"}',
            'expected_status': '200',
            'expected_content': '登录成功'
        },
        {
            'case_name': '用户登录-参数错误',
            'method': 'POST',
            'url': '/api/user/login',
            'headers': '{"Content-Type": "application/json"}',
            'params': '{}',
            'body': '{"username": "", "password": ""}',
            'expected_status': '400',
            'expected_content': '参数错误'
        },
        {
            'case_name': '',  # 缺少用例名称
            'method': 'INVALID',  # 无效HTTP方法
            'url': 'invalid-url',  # 无效URL
            'headers': '{"invalid": json}',  # 无效JSON
            'params': '{}',
            'body': '{}',
            'expected_status': '999',  # 无效状态码
            'expected_content': ''
        }
    ]
    
    print("测试质量验证器...")
    
    # 测试单个用例验证
    print("\n测试单个用例验证:")
    for i, case in enumerate(test_cases):
        is_valid, errors = validator.validate_test_case(case)
        print(f"用例 {i+1}: {'有效' if is_valid else '无效'}")
        if errors:
            for error in errors:
                print(f"  - {error}")
    
    # 测试批量验证
    print("\n测试批量验证:")
    validation_result = validator.validate_batch_cases(test_cases)
    print(f"验证结果: {validation_result['valid_cases']}/{validation_result['total_cases']} 个用例有效")
    
    if validation_result['errors']:
        print("错误信息:")
        for error in validation_result['errors'][:5]:  # 只显示前5个错误
            print(f"  - {error}")
    
    if validation_result['warnings']:
        print("警告信息:")
        for warning in validation_result['warnings']:
            print(f"  - {warning}")
    
    # 测试修复建议
    print("\n修复建议:")
    suggestions = validator.generate_fix_suggestions(validation_result['errors'])
    for suggestion in suggestions:
        print(f"  - {suggestion}")
    
    # 测试质量评分
    print("\n质量评分:")
    quality_score = validator.get_quality_score(validation_result)
    print(f"评分: {quality_score['score']} ({quality_score['grade']}) - {quality_score['description']}")
    print(f"有效比例: {quality_score['valid_ratio']}, 警告数量: {quality_score['warnings_count']}")