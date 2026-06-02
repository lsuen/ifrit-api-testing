#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：接口文档解析器，支持 Markdown / Swagger JSON / YAML
创建时间：2026-06-02
"""

import json
import os
import re
import yaml
from typing import Dict, Any, List, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DocumentParser:
    """文档解析器"""
    
    def __init__(self):
        """初始化文档解析器"""
        self.supported_formats = ['md', 'markdown', 'json', 'yaml', 'yml']
    
    def parse_document(self, file_path: str, endpoints: List[str] = None) -> List[Dict[str, Any]]:
        """
        解析文档文件
        
        Args:
            file_path: 文档文件路径
            endpoints: 指定要解析的端点列表，None表示解析所有端点
            
        Returns:
            API信息列表
        """
        if not os.path.exists(file_path):
            logger.error(f"文档文件不存在: {file_path}")
            return []
        
        file_ext = os.path.splitext(file_path)[1].lower().lstrip('.')
        
        if file_ext not in self.supported_formats:
            logger.error(f"不支持的文件格式: {file_ext}，支持的格式: {self.supported_formats}")
            return []
        
        try:
            if file_ext in ['md', 'markdown']:
                return self.parse_markdown(file_path, endpoints)
            elif file_ext == 'json':
                return self.parse_swagger_json(file_path, endpoints)
            elif file_ext in ['yaml', 'yml']:
                return self.parse_swagger_yaml(file_path, endpoints)
        except Exception as e:
            logger.error(f"解析文档失败: {str(e)}")
            return []
    
    def parse_markdown(self, file_path: str, endpoints: List[str] = None) -> List[Dict[str, Any]]:
        """
        解析Markdown接口文档
        
        Args:
            file_path: Markdown文件路径
            endpoints: 指定要解析的端点列表
            
        Returns:
            API信息列表
        """
        logger.info(f"开始解析Markdown文档: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        apis = []
        
        # 使用正则表达式匹配API接口信息
        # 匹配格式如: ## POST /api/user/login
        api_pattern = r'#{1,3}\s*(GET|POST|PUT|DELETE|PATCH)\s+([^\s\n]+)([^\n]*)'
        matches = re.finditer(api_pattern, content, re.IGNORECASE)
        
        for match in matches:
            method = match.group(1).upper()
            path = match.group(2).strip()
            title = match.group(3).strip()
            
            # 如果指定了端点过滤，检查是否匹配
            if endpoints and not any(endpoint in path for endpoint in endpoints):
                continue
            
            # 提取该API的详细信息
            api_info = self._extract_api_from_markdown_section(content, match.start(), method, path, title)
            if api_info:
                apis.append(api_info)
        
        logger.info(f"从Markdown文档解析出 {len(apis)} 个API接口")
        return apis
    
    def _extract_api_from_markdown_section(self, content: str, start_pos: int, method: str, path: str, title: str) -> Dict[str, Any]:
        """
        从Markdown内容中提取单个API的详细信息
        
        Args:
            content: 完整的Markdown内容
            start_pos: API标题在内容中的起始位置
            method: HTTP方法
            path: API路径
            title: API标题
            
        Returns:
            API信息字典
        """
        # 找到下一个API标题的位置，确定当前API的内容范围
        next_api_pattern = r'#{1,3}\s*(GET|POST|PUT|DELETE|PATCH)\s+'
        next_match = re.search(next_api_pattern, content[start_pos + 1:], re.IGNORECASE)
        
        if next_match:
            end_pos = start_pos + 1 + next_match.start()
            section_content = content[start_pos:end_pos]
        else:
            section_content = content[start_pos:]
        
        # 提取描述
        description = title if title else f"{method} {path}"
        
        # 提取参数信息
        parameters = self._extract_parameters_from_markdown(section_content)
        
        # 提取响应信息
        responses = self._extract_responses_from_markdown(section_content)
        
        # 检查是否需要认证
        auth_required = self._check_auth_required(section_content)
        
        api_info = {
            "name": description,
            "method": method,
            "path": path,
            "description": description,
            "parameters": parameters,
            "responses": responses,
            "auth_required": auth_required,
            "tags": []
        }
        
        logger.debug(f"解析API: {method} {path}")
        return api_info
    
    def _extract_parameters_from_markdown(self, content: str) -> Dict[str, Any]:
        """从Markdown内容中提取参数信息"""
        parameters = {
            "body": {},
            "query": {},
            "path": {},
            "headers": {}
        }
        
        # 查找参数表格或列表
        # 匹配表格格式的参数
        table_pattern = r'\|[^|]*参数[^|]*\|[^|]*类型[^|]*\|[^|]*必填[^|]*\|[^|]*说明[^|]*\|'
        if re.search(table_pattern, content, re.IGNORECASE):
            # 解析表格格式的参数
            lines = content.split('\n')
            in_table = False
            for line in lines:
                if '参数' in line and '类型' in line and '|' in line:
                    in_table = True
                    continue
                if in_table and '|' in line and '---' not in line:
                    parts = [p.strip() for p in line.split('|') if p.strip()]
                    if len(parts) >= 4:
                        param_name = parts[0]
                        param_type = parts[1]
                        required = '必填' in parts[2] or 'required' in parts[2].lower()
                        description = parts[3]
                        
                        parameters["body"][param_name] = {
                            "type": param_type,
                            "required": required,
                            "description": description
                        }
                elif in_table and '|' not in line:
                    break
        
        # 查找JSON示例
        json_pattern = r'```json\s*\n(.*?)\n```'
        json_matches = re.findall(json_pattern, content, re.DOTALL)
        for json_str in json_matches:
            try:
                json_data = json.loads(json_str)
                if isinstance(json_data, dict):
                    for key, value in json_data.items():
                        if key not in parameters["body"]:
                            parameters["body"][key] = {
                                "type": type(value).__name__,
                                "required": True,
                                "description": f"示例值: {value}"
                            }
            except json.JSONDecodeError:
                continue
        
        return parameters
    
    def _extract_responses_from_markdown(self, content: str) -> Dict[str, Any]:
        """从Markdown内容中提取响应信息"""
        responses = {}
        
        # 查找响应状态码
        status_pattern = r'(\d{3})[:\s]*([^\n]*)'
        matches = re.findall(status_pattern, content)
        
        for status_code, description in matches:
            responses[status_code] = {
                "description": description.strip() or f"HTTP {status_code}",
                "schema": {}
            }
        
        # 如果没有找到状态码，添加默认响应
        if not responses:
            responses["200"] = {"description": "成功", "schema": {}}
            responses["400"] = {"description": "请求错误", "schema": {}}
        
        return responses
    
    def _check_auth_required(self, content: str) -> bool:
        """检查是否需要认证"""
        auth_keywords = ['认证', '授权', 'auth', 'token', 'login', '登录', 'bearer', 'jwt']
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in auth_keywords)
    
    def parse_swagger_json(self, file_path: str, endpoints: List[str] = None) -> List[Dict[str, Any]]:
        """
        解析Swagger JSON文档
        
        Args:
            file_path: Swagger JSON文件路径
            endpoints: 指定要解析的端点列表
            
        Returns:
            API信息列表
        """
        logger.info(f"开始解析Swagger JSON文档: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            swagger_data = json.load(f)
        
        return self._parse_swagger_data(swagger_data, endpoints)
    
    def parse_swagger_yaml(self, file_path: str, endpoints: List[str] = None) -> List[Dict[str, Any]]:
        """
        解析Swagger YAML文档
        
        Args:
            file_path: Swagger YAML文件路径
            endpoints: 指定要解析的端点列表
            
        Returns:
            API信息列表
        """
        logger.info(f"开始解析Swagger YAML文档: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            swagger_data = yaml.safe_load(f)
        
        return self._parse_swagger_data(swagger_data, endpoints)
    
    def _parse_swagger_data(self, swagger_data: Dict[str, Any], endpoints: List[str] = None) -> List[Dict[str, Any]]:
        """
        解析Swagger数据
        
        Args:
            swagger_data: Swagger数据字典
            endpoints: 指定要解析的端点列表
            
        Returns:
            API信息列表
        """
        apis = []
        paths = swagger_data.get('paths', {})
        
        for path, path_data in paths.items():
            # 如果指定了端点过滤，检查是否匹配
            if endpoints and not any(endpoint in path for endpoint in endpoints):
                continue
            
            for method, method_data in path_data.items():
                if method.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    continue
                
                api_info = {
                    "name": method_data.get('summary', f"{method.upper()} {path}"),
                    "method": method.upper(),
                    "path": path,
                    "description": method_data.get('description', method_data.get('summary', '')),
                    "parameters": self._extract_swagger_parameters(method_data),
                    "responses": self._extract_swagger_responses(method_data),
                    "auth_required": self._check_swagger_auth_required(method_data, swagger_data),
                    "tags": method_data.get('tags', [])
                }
                
                apis.append(api_info)
                logger.debug(f"解析API: {method.upper()} {path}")
        
        logger.info(f"从Swagger文档解析出 {len(apis)} 个API接口")
        return apis
    
    def _extract_swagger_parameters(self, method_data: Dict[str, Any]) -> Dict[str, Any]:
        """从Swagger方法数据中提取参数信息"""
        parameters = {
            "body": {},
            "query": {},
            "path": {},
            "headers": {}
        }
        
        # 处理parameters字段
        for param in method_data.get('parameters', []):
            param_in = param.get('in', 'query')
            param_name = param.get('name', '')
            param_type = param.get('type', param.get('schema', {}).get('type', 'string'))
            required = param.get('required', False)
            description = param.get('description', '')
            
            if param_in == 'body':
                # 处理请求体参数
                schema = param.get('schema', {})
                if 'properties' in schema:
                    for prop_name, prop_data in schema['properties'].items():
                        parameters["body"][prop_name] = {
                            "type": prop_data.get('type', 'string'),
                            "required": prop_name in schema.get('required', []),
                            "description": prop_data.get('description', '')
                        }
            else:
                param_location = param_in if param_in in parameters else 'query'
                parameters[param_location][param_name] = {
                    "type": param_type,
                    "required": required,
                    "description": description
                }
        
        # 处理requestBody字段 (OpenAPI 3.0)
        request_body = method_data.get('requestBody', {})
        if request_body:
            content = request_body.get('content', {})
            for content_type, content_data in content.items():
                schema = content_data.get('schema', {})
                if 'properties' in schema:
                    for prop_name, prop_data in schema['properties'].items():
                        parameters["body"][prop_name] = {
                            "type": prop_data.get('type', 'string'),
                            "required": prop_name in schema.get('required', []),
                            "description": prop_data.get('description', '')
                        }
        
        return parameters
    
    def _extract_swagger_responses(self, method_data: Dict[str, Any]) -> Dict[str, Any]:
        """从Swagger方法数据中提取响应信息"""
        responses = {}
        
        for status_code, response_data in method_data.get('responses', {}).items():
            responses[str(status_code)] = {
                "description": response_data.get('description', f"HTTP {status_code}"),
                "schema": response_data.get('schema', {})
            }
        
        return responses
    
    def _check_swagger_auth_required(self, method_data: Dict[str, Any], swagger_data: Dict[str, Any]) -> bool:
        """检查Swagger接口是否需要认证"""
        # 检查方法级别的安全要求
        if 'security' in method_data:
            return len(method_data['security']) > 0
        
        # 检查全局安全要求
        if 'security' in swagger_data:
            return len(swagger_data['security']) > 0
        
        # 检查安全定义
        if 'securityDefinitions' in swagger_data or 'components' in swagger_data:
            return True
        
        return False


def create_sample_markdown_doc():
    """创建示例Markdown文档"""
    sample_content = """# API接口文档

## POST /api/user/login 用户登录

用户登录接口，验证用户名和密码。

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

### 请求示例

```json
{
    "username": "admin",
    "password": "123456"
}
```

### 响应

- 200: 登录成功
- 400: 参数错误
- 401: 认证失败

### 响应示例

```json
{
    "code": 200,
    "message": "登录成功",
    "data": {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "user_id": 1
    }
}
```

## GET /api/user/profile 获取用户信息

获取当前登录用户的详细信息，需要认证。

### 请求头

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 是 | Bearer token |

### 响应

- 200: 获取成功
- 401: 未认证
- 403: 权限不足
"""
    
    os.makedirs('data/examples', exist_ok=True)
    with open('data/examples/sample_api.md', 'w', encoding='utf-8') as f:
        f.write(sample_content)
    
    logger.info("已创建示例Markdown文档: data/examples/sample_api.md")


def create_sample_swagger_doc():
    """创建示例Swagger文档"""
    swagger_data = {
        "swagger": "2.0",
        "info": {
            "title": "示例API",
            "version": "1.0.0",
            "description": "示例API接口文档"
        },
        "host": "api.example.com",
        "basePath": "/v1",
        "schemes": ["https"],
        "paths": {
            "/user/login": {
                "post": {
                    "summary": "用户登录",
                    "description": "用户登录接口",
                    "parameters": [
                        {
                            "name": "body",
                            "in": "body",
                            "required": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "username": {
                                        "type": "string",
                                        "description": "用户名"
                                    },
                                    "password": {
                                        "type": "string",
                                        "description": "密码"
                                    }
                                },
                                "required": ["username", "password"]
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "登录成功",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "token": {"type": "string"},
                                    "user_id": {"type": "integer"}
                                }
                            }
                        },
                        "400": {"description": "参数错误"},
                        "401": {"description": "认证失败"}
                    }
                }
            },
            "/user/profile": {
                "get": {
                    "summary": "获取用户信息",
                    "description": "获取当前用户信息",
                    "security": [{"Bearer": []}],
                    "responses": {
                        "200": {
                            "description": "获取成功",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "username": {"type": "string"},
                                    "email": {"type": "string"}
                                }
                            }
                        },
                        "401": {"description": "未认证"}
                    }
                }
            }
        },
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header"
            }
        }
    }
    
    os.makedirs('data/examples', exist_ok=True)
    with open('data/examples/sample_api.json', 'w', encoding='utf-8') as f:
        json.dump(swagger_data, f, ensure_ascii=False, indent=2)
    
    logger.info("已创建示例Swagger文档: data/examples/sample_api.json")


if __name__ == '__main__':
    # 创建示例文档
    create_sample_markdown_doc()
    create_sample_swagger_doc()
    
    # 测试文档解析器
    parser = DocumentParser()
    
    print("测试Markdown解析:")
    md_apis = parser.parse_document('data/examples/sample_api.md')
    for api in md_apis:
        print(f"- {api['method']} {api['path']}: {api['name']}")
    
    print("\n测试Swagger解析:")
    swagger_apis = parser.parse_document('data/examples/sample_api.json')
    for api in swagger_apis:
        print(f"- {api['method']} {api['path']}: {api['name']}")
    
    print("\n测试端点过滤:")
    filtered_apis = parser.parse_document('data/examples/sample_api.json', endpoints=['/user/login'])
    for api in filtered_apis:
        print(f"- {api['method']} {api['path']}: {api['name']}")