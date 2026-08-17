#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：LLM 客户端，负责与 OpenAI 兼容接口交互、API 调用与错误重试
创建时间：2026-06-02
"""

import json
import time
import requests
from typing import Dict, Any, List, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AIClient:
    """AI客户端"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化AI客户端
        
        Args:
            config: AI配置字典
        """
        self.config = config
        self.api_key = config.get('api_key', '')
        self.base_url = config.get('base_url', 'http://localhost:8000')
        self.model = config.get('model', 'gpt-3.5-turbo')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 2000)
        self.timeout = config.get('timeout', 30)
        
        # 统计信息
        self.call_count = 0
        self.total_response_time = 0
        self.total_tokens = 0
        self.last_error: Optional[str] = None
        
        # 确保base_url格式正确
        if not self.base_url.endswith('/chat/completions'):
            if self.base_url.endswith('/'):
                self.base_url = self.base_url + 'chat/completions'
            else:
                self.base_url = self.base_url + '/chat/completions'
        
        logger.info(f"AI客户端初始化完成，使用端点: {self.base_url}")
    
    def generate_test_cases(self, api_info: Dict[str, Any], case_type: str, prompt_templates: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        生成测试用例
        
        Args:
            api_info: API信息
            case_type: 用例类型 (positive/negative/boundary/structure/path/auth)
            prompt_templates: 提示词模板
            
        Returns:
            生成的测试用例列表
        """
        logger.info(f"开始生成 {case_type} 类型的测试用例，API: {api_info['method']} {api_info['path']}")
        
        try:
            # 构建提示词
            prompt = self._build_prompt(api_info, case_type, prompt_templates)
            
            # 调用AI接口
            response_text = self._call_openai_api(prompt)
            
            if not response_text:
                logger.error("AI接口返回空响应")
                return []
            
            # 解析响应
            test_cases = self._parse_ai_response(response_text, api_info, case_type)
            
            logger.info(f"成功生成 {len(test_cases)} 个 {case_type} 测试用例")
            return test_cases
            
        except Exception as e:
            logger.error(f"生成测试用例失败: {str(e)}")
            return []
    
    def _build_prompt(self, api_info: Dict[str, Any], case_type: str, prompt_templates: Dict[str, str]) -> str:
        """
        构建提示词
        
        Args:
            api_info: API信息
            case_type: 用例类型
            prompt_templates: 提示词模板
            
        Returns:
            完整的提示词
        """
        # 获取系统提示词
        system_prompt = prompt_templates.get('system_prompt', '你是一个专业的API测试工程师。')
        
        # 获取对应类型的模板
        template_key = f"{case_type}_template"
        case_template = prompt_templates.get(template_key, f"为以下接口生成{case_type}测试用例")
        
        # 构建API信息描述
        api_description = self._format_api_info(api_info)

        rag_block = prompt_templates.get("rag_context", "").strip()
        rag_section = f"\n\n{rag_block}\n" if rag_block else ""

        # 构建完整提示词
        prompt = f"""{system_prompt}

{case_template}
{rag_section}
API信息:
{api_description}

请生成JSON格式的测试用例，每个测试用例包含以下字段：
- case_name: 测试用例名称
- method: HTTP方法
- url: 请求路径
- headers: 请求头(JSON字符串)
- params: URL参数(JSON字符串)
- body: 请求体(JSON字符串)
- expected_status: 期望状态码
- expected_content: 期望响应内容关键字
- json_path: JSON路径断言(可选)
- expected_json_value: 期望JSON值(可选)
- validate: 断言表达式(可选)

请返回JSON数组格式，例如：
[
  {{
    "case_name": "用户登录-正常场景",
    "method": "POST",
    "url": "/api/user/login",
    "headers": "{{\\"Content-Type\\": \\"application/json\\"}}", 
    "params": "{{}}",
    "body": "{{\\"username\\": \\"admin\\", \\"password\\": \\"123456\\"}}",
    "expected_status": "200",
    "expected_content": "成功",
    "json_path": "code",
    "expected_json_value": "200",
    "validate": ""
  }}
]"""
        
        logger.debug(f"构建的提示词: {prompt}")
        return prompt
    
    def _format_api_info(self, api_info: Dict[str, Any]) -> str:
        """
        格式化API信息为文本描述
        
        Args:
            api_info: API信息字典
            
        Returns:
            格式化的API描述
        """
        description = f"""
接口名称: {api_info['name']}
HTTP方法: {api_info['method']}
请求路径: {api_info['path']}
接口描述: {api_info['description']}
是否需要认证: {'是' if api_info['auth_required'] else '否'}
"""
        
        # 添加参数信息
        parameters = api_info.get('parameters', {})
        if parameters:
            description += "\n参数信息:\n"
            
            # 请求体参数
            if parameters.get('body'):
                description += "  请求体参数:\n"
                for param_name, param_info in parameters['body'].items():
                    required = "必填" if param_info.get('required', False) else "可选"
                    description += f"    - {param_name} ({param_info.get('type', 'string')}, {required}): {param_info.get('description', '')}\n"
            
            # 查询参数
            if parameters.get('query'):
                description += "  查询参数:\n"
                for param_name, param_info in parameters['query'].items():
                    required = "必填" if param_info.get('required', False) else "可选"
                    description += f"    - {param_name} ({param_info.get('type', 'string')}, {required}): {param_info.get('description', '')}\n"
            
            # 路径参数
            if parameters.get('path'):
                description += "  路径参数:\n"
                for param_name, param_info in parameters['path'].items():
                    description += f"    - {param_name} ({param_info.get('type', 'string')}): {param_info.get('description', '')}\n"
        
        # 添加响应信息
        responses = api_info.get('responses', {})
        if responses:
            description += "\n响应信息:\n"
            for status_code, response_info in responses.items():
                description += f"  - {status_code}: {response_info.get('description', '')}\n"
        
        return description

    def _format_api_error(self, response: requests.Response) -> str:
        """将 HTTP 错误响应转为用户可读说明。"""
        try:
            body = response.json()
            err = body.get("error") or {}
            if isinstance(err, dict):
                message = str(err.get("message") or err.get("code") or err)
                code = str(err.get("code") or "")
                if code == "model_not_found" or "no available channel for model" in message.lower():
                    return (
                        f"模型「{self.model}」在当前网关不可用: {message}。"
                        f"请检查 .env 中 OPENAI_MODEL 或 config/settings/ai.ini 的 model"
                    )
                return f"LLM 请求失败(HTTP {response.status_code}): {message}"
        except Exception:
            pass
        text = (response.text or "")[:300]
        return f"LLM 请求失败(HTTP {response.status_code}): {text}"
    
    def _call_openai_api(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """
        调用OpenAI API
        
        Args:
            prompt: 提示词
            max_retries: 最大重试次数
            
        Returns:
            AI响应文本
        """
        self.last_error = None
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                
                # 构建请求数据
                data = {
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                }
                
                # 构建请求头
                headers = {
                    "Content-Type": "application/json"
                }
                
                # 如果有API密钥，添加到请求头
                if self.api_key and self.api_key != 'your_openai_api_key_here':
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                logger.debug(f"调用AI接口，尝试 {attempt + 1}/{max_retries}")
                
                # 发送请求
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                )
                
                # 计算响应时间
                response_time = time.time() - start_time
                self.total_response_time += response_time
                self.call_count += 1
                
                logger.debug(f"AI接口响应时间: {response_time:.2f}秒")
                
                if response.status_code == 200:
                    result = response.json()
                    logger.debug(f"AI接口原始响应: {result}")
                    
                    # 提取响应内容 - 支持多种响应格式
                    content = None
                    
                    # 标准OpenAI格式（兼容 choices 为 null/空列表/message 缺失）
                    choices = result.get('choices')
                    if choices is None or (isinstance(choices, list) and len(choices) == 0):
                        logger.error("AI接口响应 choices 为空 (尝试 %d/%d)", attempt + 1, max_retries)
                        continue
                    if choices and len(choices) > 0:
                        first = choices[0] if isinstance(choices[0], dict) else {}
                        message = first.get('message') if isinstance(first, dict) else None
                        if isinstance(message, dict):
                            content = message.get('content')
                    # 简化格式 - 直接返回内容
                    elif 'content' in result:
                        content = result['content']
                    # 其他可能的格式
                    elif 'response' in result:
                        content = result['response']
                    elif 'text' in result:
                        content = result['text']
                    # 如果响应本身就是字符串
                    elif isinstance(result, str):
                        content = result
                    else:
                        logger.error(f"未知的AI接口响应格式: {result}")
                        continue
                    
                    if content:
                        # 统计token使用量
                        if 'usage' in result:
                            tokens = result['usage'].get('total_tokens', 0)
                            self.total_tokens += tokens
                            logger.debug(f"本次调用消耗tokens: {tokens}")
                        
                        logger.info(f"AI接口调用成功，响应时间: {response_time:.2f}秒")
                        return content
                    else:
                        logger.error("AI接口响应内容为空")
                        
                else:
                    self.last_error = self._format_api_error(response)
                    logger.error(f"AI接口调用失败，状态码: {response.status_code}, 响应: {response.text}")
                    
                    # 如果是429错误（请求过于频繁），等待后重试
                    if response.status_code == 429:
                        wait_time = 2 ** attempt  # 指数退避
                        logger.info(f"请求频率限制，等待 {wait_time} 秒后重试")
                        time.sleep(wait_time)
                        continue
                
            except requests.exceptions.Timeout:
                self.last_error = f"LLM 请求超时（>{self.timeout}s），请检查网络或增大 ai.ini 的 timeout"
                logger.error(f"AI接口调用超时 (尝试 {attempt + 1}/{max_retries})")
            except requests.exceptions.ConnectionError:
                self.last_error = f"无法连接 LLM 网关: {self.base_url}"
                logger.error(f"AI接口连接失败 (尝试 {attempt + 1}/{max_retries})")
            except Exception as e:
                self.last_error = f"LLM 调用异常: {e}"
                logger.error(f"AI接口调用异常: {str(e)} (尝试 {attempt + 1}/{max_retries})")
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < max_retries - 1:
                wait_time = 1 + attempt  # 线性退避
                logger.info(f"等待 {wait_time} 秒后重试")
                time.sleep(wait_time)
        
        if not self.last_error:
            self.last_error = f"LLM 调用失败，已重试 {max_retries} 次（模型: {self.model}）"
        logger.error(f"AI接口调用失败，已重试 {max_retries} 次")
        print(f"[IFRIT] {self.last_error}")
        return None

    def _post_chat(self, data: Dict[str, Any], max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """发送 chat/completions 请求并解析 message（含 tool_calls）。"""
        self.last_error = None
        headers = {"Content-Type": "application/json"}
        if self.api_key and self.api_key != "your_openai_api_key_here":
            headers["Authorization"] = f"Bearer {self.api_key}"

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=data,
                    timeout=self.timeout,
                )
                if response.status_code != 200:
                    self.last_error = self._format_api_error(response)
                    if response.status_code == 429 and attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    raise RuntimeError(self.last_error)

                result = response.json()
                choices = result.get("choices") or []
                if not choices:
                    raise RuntimeError("LLM choices 为空")
                message = choices[0].get("message") or {}
                tool_calls_raw = message.get("tool_calls") or []
                tool_calls = []
                for item in tool_calls_raw:
                    fn = item.get("function") or {}
                    tool_calls.append(
                        {
                            "id": item.get("id"),
                            "name": fn.get("name"),
                            "arguments": fn.get("arguments") or "{}",
                        }
                    )
                self.call_count += 1
                if "usage" in result:
                    self.total_tokens += result["usage"].get("total_tokens", 0)
                return {
                    "content": message.get("content"),
                    "tool_calls": tool_calls,
                    "raw": result,
                }
            except Exception as error:
                self.last_error = str(error)
                if attempt >= max_retries - 1:
                    raise
                time.sleep(1 + attempt)
        return None

    def chat_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = "auto",
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """OpenAI 兼容 Function Calling。"""
        data: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if tools:
            data["tools"] = tools
            data["tool_choice"] = tool_choice or "auto"
        parsed = self._post_chat(data, max_retries=max_retries)
        if not parsed:
            raise RuntimeError(self.last_error or "LLM 无响应")
        return parsed

    def chat_simple(
        self,
        messages: List[Dict[str, str]],
        max_retries: int = 2,
        max_tokens: Optional[int] = None,
    ) -> Optional[str]:
        """多轮对话（system/user），用于 Agent 闲聊与用法引导。"""
        data: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": min(float(self.temperature), 0.85),
            "max_tokens": max_tokens or min(int(self.max_tokens), 1200),
        }
        parsed = self._post_chat(data, max_retries=max_retries)
        if not parsed:
            return None
        content = (parsed.get("content") or "").strip()
        return content or None

    def complete(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """通用单轮 LLM 补全（供导入诊断等场景）。"""
        return self._call_openai_api(prompt, max_retries=max_retries)
    
    def _parse_ai_response(self, response_text: str, api_info: Dict[str, Any], case_type: str) -> List[Dict[str, Any]]:
        """
        解析AI响应
        
        Args:
            response_text: AI响应文本
            api_info: API信息
            case_type: 用例类型
            
        Returns:
            解析后的测试用例列表
        """
        try:
            # 尝试提取JSON内容
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                test_cases = json.loads(json_text)
                
                # 验证和补充测试用例数据
                validated_cases = []
                for i, case in enumerate(test_cases):
                    if isinstance(case, dict):
                        # 补充必要字段
                        validated_case = self._validate_and_complete_case(case, api_info, case_type, i)
                        if validated_case:
                            validated_cases.append(validated_case)
                
                return validated_cases
            else:
                logger.error("AI响应中未找到有效的JSON数组")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"解析AI响应JSON失败: {str(e)}")
            logger.debug(f"原始响应: {response_text}")
            return []
        except Exception as e:
            logger.error(f"解析AI响应失败: {str(e)}")
            return []
    
    def _validate_and_complete_case(self, case: Dict[str, Any], api_info: Dict[str, Any], case_type: str, index: int) -> Optional[Dict[str, Any]]:
        """
        验证和补充测试用例数据
        
        Args:
            case: 原始测试用例
            api_info: API信息
            case_type: 用例类型
            index: 用例索引
            
        Returns:
            验证后的测试用例
        """
        try:
            # 生成用例ID
            case_id = f"{case_type}_{api_info['method'].lower()}_{api_info['path'].replace('/', '_').replace('{', '').replace('}', '')}_{index + 1}"
            
            # 补充必要字段
            validated_case = {
                'case_id': case_id,
                'case_name': case.get('case_name', f"{api_info['name']}-{case_type}-{index + 1}"),
                'method': case.get('method', api_info['method']),
                'url': case.get('url', api_info['path']),
                'headers': case.get('headers', '{"Content-Type": "application/json"}'),
                'params': case.get('params', '{}'),
                'body': case.get('body', '{}'),
                'expected_status': str(case.get('expected_status', '200')),
                'expected_content': case.get('expected_content', ''),
                'json_path': case.get('json_path', ''),
                'expected_json_value': case.get('expected_json_value', ''),
                'extract_key': case.get('extract_key', ''),
                'save_var_name': case.get('save_var_name', ''),
                'validate': case.get('validate', ''),
                'enabled': '1'
            }
            
            # 验证必要字段
            if not validated_case['case_name'] or not validated_case['method'] or not validated_case['url']:
                logger.warning(f"测试用例缺少必要字段，跳过: {case}")
                return None
            
            # 验证JSON格式
            for json_field in ['headers', 'params', 'body']:
                try:
                    json.loads(validated_case[json_field])
                except json.JSONDecodeError:
                    logger.warning(f"测试用例 {json_field} 字段JSON格式错误，使用默认值")
                    validated_case[json_field] = '{}'
            
            return validated_case
            
        except Exception as e:
            logger.error(f"验证测试用例失败: {str(e)}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取使用统计信息
        
        Returns:
            统计信息字典
        """
        avg_response_time = self.total_response_time / self.call_count if self.call_count > 0 else 0
        
        return {
            'call_count': self.call_count,
            'total_response_time': self.total_response_time,
            'average_response_time': avg_response_time,
            'total_tokens': self.total_tokens
        }
    
    def reset_statistics(self):
        """重置统计信息"""
        self.call_count = 0
        self.total_response_time = 0
        self.total_tokens = 0
        logger.info("AI客户端统计信息已重置")


if __name__ == '__main__':
    # 测试AI客户端
    config = {
        'api_key': 'test_key',
        'base_url': 'http://localhost:8000',
        'model': 'gpt-3.5-turbo',
        'temperature': 0.7,
        'max_tokens': 2000,
        'timeout': 30
    }
    
    prompt_templates = {
        'system_prompt': '你是一个专业的API测试工程师，需要根据接口文档生成全面的测试用例。',
        'positive_template': '为以下接口生成正向测试用例，确保正常场景下的功能验证'
    }
    
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
    
    client = AIClient(config)
    
    print("测试AI客户端...")
    test_cases = client.generate_test_cases(api_info, 'positive', prompt_templates)
    
    print(f"生成了 {len(test_cases)} 个测试用例:")
    for case in test_cases:
        print(f"- {case['case_name']}")
    
    print(f"\n统计信息: {client.get_statistics()}")