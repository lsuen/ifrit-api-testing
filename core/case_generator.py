#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试用例生成器模块
负责协调不同类型测试用例的生成逻辑
"""

import os
import sys
from typing import Dict, Any, List
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ai_client import AIClient

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CaseGenerator:
    """测试用例生成器"""
    
    def __init__(self, ai_client: AIClient, generation_config: Dict[str, Any], prompt_templates: Dict[str, str]):
        """
        初始化用例生成器
        
        Args:
            ai_client: AI客户端实例
            generation_config: 生成策略配置
            prompt_templates: 提示词模板
        """
        self.ai_client = ai_client
        self.generation_config = generation_config
        self.prompt_templates = prompt_templates
        
        logger.info("测试用例生成器初始化完成")
    
    def generate_all_cases(self, api_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成所有类型的测试用例
        
        Args:
            api_info: API信息
            
        Returns:
            所有生成的测试用例列表
        """
        logger.info(f"开始为API {api_info['method']} {api_info['path']} 生成所有类型的测试用例")
        
        all_cases = []
        
        # 生成正向测试用例
        positive_count = self.generation_config.get('positive_cases_count', 3)
        if positive_count > 0:
            positive_cases = self.generate_positive_cases(api_info, positive_count)
            all_cases.extend(positive_cases)
        
        # 生成反向测试用例
        negative_count = self.generation_config.get('negative_cases_count', 2)
        if negative_count > 0:
            negative_cases = self.generate_negative_cases(api_info, negative_count)
            all_cases.extend(negative_cases)
        
        # 生成边界测试用例
        boundary_count = self.generation_config.get('boundary_cases_count', 2)
        if boundary_count > 0:
            boundary_cases = self.generate_boundary_cases(api_info, boundary_count)
            all_cases.extend(boundary_cases)
        
        # 生成结构验证用例
        structure_count = self.generation_config.get('structure_cases_count', 1)
        if structure_count > 0:
            structure_cases = self.generate_structure_cases(api_info, structure_count)
            all_cases.extend(structure_cases)
        
        # 生成路径覆盖用例
        path_count = self.generation_config.get('path_cases_count', 2)
        if path_count > 0:
            path_cases = self.generate_path_cases(api_info, path_count)
            all_cases.extend(path_cases)
        
        # 生成权限验证用例
        include_auth = self.generation_config.get('include_auth_cases', True)
        if include_auth and api_info.get('auth_required', False):
            auth_cases = self.generate_auth_cases(api_info)
            all_cases.extend(auth_cases)
        
        logger.info(f"总共生成了 {len(all_cases)} 个测试用例")
        return all_cases
    
    def generate_positive_cases(self, api_info: Dict[str, Any], count: int = 3) -> List[Dict[str, Any]]:
        """
        生成正向测试用例
        
        Args:
            api_info: API信息
            count: 生成数量
            
        Returns:
            正向测试用例列表
        """
        logger.info(f"生成 {count} 个正向测试用例")
        
        # 构建增强的提示词模板
        enhanced_template = f"""{self.prompt_templates.get('positive_template', '')}

请生成 {count} 个正向测试用例，包括：
1. 基本正常场景 - 使用有效的必填参数
2. 完整参数场景 - 包含所有可选参数
3. 最小参数场景 - 只包含必填参数

每个用例都应该：
- 使用合理的测试数据
- 验证成功响应的状态码和关键内容
- 包含必要的请求头
- 设置合适的断言条件"""
        
        # 临时替换模板
        original_template = self.prompt_templates.get('positive_template', '')
        self.prompt_templates['positive_template'] = enhanced_template
        
        try:
            cases = self.ai_client.generate_test_cases(api_info, 'positive', self.prompt_templates)
            return cases
        finally:
            # 恢复原始模板
            self.prompt_templates['positive_template'] = original_template
    
    def generate_negative_cases(self, api_info: Dict[str, Any], count: int = 2) -> List[Dict[str, Any]]:
        """
        生成反向测试用例
        
        Args:
            api_info: API信息
            count: 生成数量
            
        Returns:
            反向测试用例列表
        """
        logger.info(f"生成 {count} 个反向测试用例")
        
        # 构建增强的提示词模板
        enhanced_template = f"""{self.prompt_templates.get('negative_template', '')}

请生成 {count} 个反向测试用例，包括：
1. 缺少必填参数
2. 参数类型错误（如字符串传数字字段）
3. 参数值无效（如负数、空字符串、过长字符串）
4. 无效的HTTP方法
5. 错误的Content-Type

每个用例都应该：
- 验证错误响应的状态码（400、422、500等）
- 检查错误信息的关键字
- 设置合适的断言条件"""
        
        # 临时替换模板
        original_template = self.prompt_templates.get('negative_template', '')
        self.prompt_templates['negative_template'] = enhanced_template
        
        try:
            cases = self.ai_client.generate_test_cases(api_info, 'negative', self.prompt_templates)
            return cases
        finally:
            # 恢复原始模板
            self.prompt_templates['negative_template'] = original_template
    
    def generate_boundary_cases(self, api_info: Dict[str, Any], count: int = 2) -> List[Dict[str, Any]]:
        """
        生成边界测试用例
        
        Args:
            api_info: API信息
            count: 生成数量
            
        Returns:
            边界测试用例列表
        """
        logger.info(f"生成 {count} 个边界测试用例")
        
        # 构建增强的提示词模板
        enhanced_template = f"""{self.prompt_templates.get('boundary_template', '')}

请生成 {count} 个边界测试用例，包括：
1. 字符串长度边界：
   - 空字符串 ""
   - 单字符字符串
   - 最大长度字符串（如255字符）
2. 数值边界：
   - 零值 0
   - 负数 -1
   - 最大整数值
   - 浮点数边界
3. 数组边界：
   - 空数组 []
   - 单元素数组
   - 大量元素数组
4. 特殊字符：
   - SQL注入字符
   - XSS字符
   - Unicode字符

每个用例都应该测试系统对边界值的处理能力"""
        
        # 临时替换模板
        original_template = self.prompt_templates.get('boundary_template', '')
        self.prompt_templates['boundary_template'] = enhanced_template
        
        try:
            cases = self.ai_client.generate_test_cases(api_info, 'boundary', self.prompt_templates)
            return cases
        finally:
            # 恢复原始模板
            self.prompt_templates['boundary_template'] = original_template
    
    def generate_structure_cases(self, api_info: Dict[str, Any], count: int = 1) -> List[Dict[str, Any]]:
        """
        生成数据结构验证用例
        
        Args:
            api_info: API信息
            count: 生成数量
            
        Returns:
            结构验证用例列表
        """
        logger.info(f"生成 {count} 个结构验证测试用例")
        
        # 构建结构验证模板
        structure_template = f"""为以下接口生成数据结构验证测试用例：

请生成 {count} 个结构验证测试用例，包括：
1. JSON格式验证：
   - 发送无效JSON格式
   - 发送不完整的JSON
   - 发送嵌套JSON结构错误
2. 字段类型验证：
   - 字符串字段传入数字
   - 数字字段传入字符串
   - 布尔字段传入其他类型
3. 必填字段验证：
   - 缺少必填字段
   - 必填字段为null
   - 必填字段为空值
4. 响应结构验证：
   - 验证响应JSON结构
   - 验证必要字段存在
   - 验证字段类型正确

每个用例都应该验证数据结构的完整性和正确性"""
        
        # 临时添加结构模板
        self.prompt_templates['structure_template'] = structure_template
        
        try:
            cases = self.ai_client.generate_test_cases(api_info, 'structure', self.prompt_templates)
            return cases
        finally:
            # 清理临时模板
            if 'structure_template' in self.prompt_templates:
                del self.prompt_templates['structure_template']
    
    def generate_path_cases(self, api_info: Dict[str, Any], count: int = 2) -> List[Dict[str, Any]]:
        """
        生成路径覆盖用例
        
        Args:
            api_info: API信息
            count: 生成数量
            
        Returns:
            路径覆盖用例列表
        """
        logger.info(f"生成 {count} 个路径覆盖测试用例")
        
        # 构建路径覆盖模板
        path_template = f"""为以下接口生成路径覆盖测试用例：

请生成 {count} 个路径覆盖测试用例，包括：
1. URL路径参数变化：
   - 不同的路径参数值
   - 路径参数包含特殊字符
   - 路径参数为空或无效
2. 查询参数组合：
   - 不同的查询参数组合
   - 可选参数的不同组合
   - 参数顺序变化
3. 请求方法验证：
   - 使用错误的HTTP方法访问
   - 验证方法不被支持的情况
4. 路径访问权限：
   - 访问不存在的路径
   - 访问受限的路径

每个用例都应该覆盖不同的代码执行路径"""
        
        # 临时添加路径模板
        self.prompt_templates['path_template'] = path_template
        
        try:
            cases = self.ai_client.generate_test_cases(api_info, 'path', self.prompt_templates)
            return cases
        finally:
            # 清理临时模板
            if 'path_template' in self.prompt_templates:
                del self.prompt_templates['path_template']
    
    def generate_auth_cases(self, api_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成权限验证用例
        
        Args:
            api_info: API信息
            
        Returns:
            权限验证用例列表
        """
        logger.info("生成权限验证测试用例")
        
        # 构建权限验证模板
        auth_template = """为以下需要认证的接口生成权限验证测试用例：

请生成权限验证测试用例，包括：
1. 未认证访问：
   - 不提供认证信息
   - 提供空的认证头
2. 认证信息错误：
   - 无效的token
   - 过期的token
   - 格式错误的token
3. 权限不足：
   - 使用低权限用户的token
   - 访问超出权限范围的资源
4. 认证头格式：
   - 错误的认证头格式
   - 缺少Bearer前缀
   - 多余的认证信息

每个用例都应该验证认证和授权机制的正确性，期望状态码通常为401或403"""
        
        # 临时添加认证模板
        self.prompt_templates['auth_template'] = auth_template
        
        try:
            cases = self.ai_client.generate_test_cases(api_info, 'auth', self.prompt_templates)
            return cases
        finally:
            # 清理临时模板
            if 'auth_template' in self.prompt_templates:
                del self.prompt_templates['auth_template']
    
    def get_generation_summary(self) -> Dict[str, Any]:
        """
        获取生成统计摘要
        
        Returns:
            生成统计信息
        """
        ai_stats = self.ai_client.get_statistics()
        
        return {
            'ai_calls': ai_stats['call_count'],
            'total_response_time': ai_stats['total_response_time'],
            'average_response_time': ai_stats['average_response_time'],
            'total_tokens': ai_stats['total_tokens'],
            'generation_config': self.generation_config
        }


if __name__ == '__main__':
    # 测试用例生成器
    from config.ai_config import AIConfig
    
    # 初始化配置
    ai_config = AIConfig()
    openai_config = ai_config.get_openai_config()
    generation_config = ai_config.get_generation_config()
    prompt_templates = ai_config.get_prompt_templates()
    
    # 创建AI客户端
    ai_client = AIClient(openai_config)
    
    # 创建用例生成器
    generator = CaseGenerator(ai_client, generation_config, prompt_templates)
    
    # 测试API信息
    api_info = {
        'name': '用户登录',
        'method': 'POST',
        'path': '/api/user/login',
        'description': '用户登录接口',
        'parameters': {
            'body': {
                'username': {'type': 'string', 'required': True, 'description': '用户名'},
                'password': {'type': 'string', 'required': True, 'description': '密码'}
            }
        },
        'responses': {
            '200': {'description': '登录成功'},
            '400': {'description': '参数错误'},
            '401': {'description': '认证失败'}
        },
        'auth_required': False
    }
    
    print("测试用例生成器...")
    
    # 生成正向测试用例
    print("\n生成正向测试用例:")
    positive_cases = generator.generate_positive_cases(api_info, 2)
    for case in positive_cases:
        print(f"- {case['case_name']}")
    
    # 生成反向测试用例
    print("\n生成反向测试用例:")
    negative_cases = generator.generate_negative_cases(api_info, 2)
    for case in negative_cases:
        print(f"- {case['case_name']}")
    
    # 获取统计信息
    print(f"\n生成统计: {generator.get_generation_summary()}")