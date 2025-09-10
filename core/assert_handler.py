#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9 上午10:07
# @Author  : sunwl
# @Site    :
# @File    : test_api_csv_driver.py
# @Software: PyCharm
import json
import re
from typing import Any, Dict
from utils.logger import logger


class AssertHandler:
    """断言处理类"""

    @staticmethod
    def assert_equal(actual: Any, expected: Any, message: str = "") -> bool:
        """断言相等"""
        logger.debug(f"执行相等断言: 实际值={actual}, 期望值={expected}")
        try:
            assert actual == expected, f"期望值: {expected}, 实际值: {actual}. {message}"
            logger.info(f"断言成功: {actual} == {expected}")
            return True
        except AssertionError as e:
            logger.error(f"断言失败: {str(e)}")
            raise e

    @staticmethod
    def assert_contains(actual: str, expected: str, message: str = "") -> bool:
        """断言包含"""
        logger.debug(f"执行包含断言: 实际值='{actual}', 期望包含='{expected}'")
        try:
            assert expected in actual, f"期望包含: {expected}, 实际值: {actual}. {message}"
            logger.info(f"断言成功: '{actual}' 包含 '{expected}'")
            return True
        except AssertionError as e:
            logger.error(f"断言失败: {str(e)}")
            raise e

    @staticmethod
    def assert_status_code(response, expected_status: int, message: str = "") -> bool:
        """断言响应状态码"""
        logger.debug(f"执行状态码断言: 期望状态码={expected_status}")
        try:
            if response is None:
                raise ValueError("响应对象为空")

            actual_status = response.status_code if hasattr(response, 'status_code') else int(response)
            logger.debug(f"实际状态码: {actual_status}")

            assert actual_status == expected_status, f"期望状态码: {expected_status}, 实际状态码: {actual_status}. {message}"
            logger.info(f"断言成功: 状态码 {actual_status} == {expected_status}")
            return True
        except AssertionError as e:
            logger.error(f"状态码断言失败: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"状态码断言异常: {str(e)}")
            raise e

    @staticmethod
    def assert_json_value(response, json_path: str, expected_value: Any, message: str = "") -> bool:
        """断言JSON响应中指定路径的值"""
        logger.debug(f"执行JSON值断言: 路径={json_path}, 期望值={expected_value}")
        try:
            if response is None:
                raise ValueError("响应对象为空")

            try:
                response_json = response.json() if hasattr(response, 'json') else json.loads(response)
                logger.debug(f"响应JSON: {response_json}")
                
                # 使用jsonpath提取值
                matches = jsonpath.jsonpath(response_json, json_path)
                if not matches:
                    raise ValueError(f"JSON路径 '{json_path}' 未找到匹配项")
                
                actual_value = matches[0]
                logger.debug(f"实际值: {actual_value}")
                
                assert actual_value == expected_value, f"期望值: {expected_value}, 实际值: {actual_value}. {message}"
                logger.info(f"断言成功: JSON路径 '{json_path}' 的值 {actual_value} == {expected_value}")
                return True
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {str(e)}")
                raise ValueError(f"响应不是有效的JSON格式: {str(e)}")
        except AssertionError as e:
            logger.error(f"JSON值断言失败: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"JSON值断言异常: {str(e)}")
            raise e

    @staticmethod
    def assert_content_contains(response, expected_content: str, message: str = "") -> bool:
        """断言响应内容包含指定文本，增强对JSON格式内容的处理"""
        logger.debug(f"执行内容包含断言: 期望内容='{expected_content}'")
        try:
            if response is None:
                raise ValueError("响应对象为空")

            actual_content = response.text if hasattr(response, 'text') else str(response)
            logger.debug(f"实际内容: {actual_content}")

            # 如果期望内容和实际内容都是JSON格式，进行标准化比较
            if AssertHandler._is_json_string(expected_content) and AssertHandler._is_json_string(actual_content):
                logger.debug("检测到JSON格式内容，进行标准化比较")
                expected_normalized = AssertHandler._normalize_json_string(expected_content)
                actual_normalized = AssertHandler._normalize_json_string(actual_content)
                
                assert expected_normalized in actual_normalized, f"标准化后的期望内容 '{expected_normalized}' 未找到. {message}"
                logger.info(f"断言成功: 响应内容包含标准化后的 '{expected_normalized}'")
            else:
                # 普通文本比较
                assert expected_content in actual_content, f"期望内容 '{expected_content}' 未找到. {message}"
                logger.info(f"断言成功: 响应内容包含 '{expected_content}'")
            
            return True

        except AssertionError as e:
            logger.error(f"内容包含断言失败: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"内容包含断言异常: {str(e)}")
            raise e

    @staticmethod
    def _is_json_string(text: str) -> bool:
        """判断字符串是否为JSON格式"""
        try:
            json.loads(text)
            return True
        except (json.JSONDecodeError, TypeError):
            return False

    @staticmethod
    def _normalize_json_string(json_str: str) -> str:
        """标准化JSON字符串，移除多余空格和换行符"""
        try:
            # 解析JSON字符串
            parsed_json = json.loads(json_str)
            # 重新序列化为紧凑格式
            normalized = json.dumps(parsed_json, separators=(',', ':'), ensure_ascii=False)
            logger.debug(f"标准化JSON字符串: {normalized}")
            return normalized
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"JSON标准化失败: {e}, 返回原始字符串")
            # 如果标准化失败，移除多余空格和换行符
            return re.sub(r'\s+', ' ', json_str.strip())

    @staticmethod
    def assert_regex(response, expected_pattern: str, message: str = "") -> bool:
        """断言响应内容匹配正则表达式"""
        logger.debug(f"执行正则表达式断言: 期望模式='{expected_pattern}'")
        try:
            if not response:
                raise ValueError("响应对象为空")

            actual_content = response.text if hasattr(response, 'text') else str(response)
            logger.debug(f"实际内容: {actual_content}")

            assert re.search(expected_pattern, actual_content), f"正则表达式 '{expected_pattern}' 未匹配. {message}"
            logger.info(f"断言成功: 响应内容匹配正则表达式 '{expected_pattern}'")
            return True

        except AssertionError as e:
            logger.error(f"正则表达式断言失败: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"正则表达式断言异常: {str(e)}")
            raise e

    @staticmethod
    def assert_json_structure(response, expected_structure: Dict, message: str = "") -> bool:
        """断言JSON结构符合预期"""
        logger.debug(f"执行JSON结构断言: 期望结构={expected_structure}")
        try:
            if not response:
                raise ValueError("响应对象为空")

            try:
                response_json = response.json() if hasattr(response, 'json') else json.loads(response)
                logger.debug(f"响应JSON: {response_json}")
            except json.JSONDecodeError:
                raise ValueError("响应不是有效的JSON格式")

            def check_structure(actual, expected):
                if isinstance(expected, dict):
                    if not isinstance(actual, dict):
                        return False
                    for key, value in expected.items():
                        if key not in actual:
                            return False
                        if not check_structure(actual[key], value):
                            return False
                    return True
                elif isinstance(expected, list):
                    if not isinstance(actual, list):
                        return False
                    if len(expected) > 0 and len(actual) > 0:
                        return check_structure(actual[0], expected[0])
                    return True
                else:
                    return isinstance(actual, type(expected))

            assert check_structure(response_json,
                                   expected_structure), f"实际结构: {response_json}, 期望结构: {expected_structure}. {message}"
            logger.info("断言成功: JSON结构符合预期")
            return True

        except AssertionError as e:
            logger.error(f"JSON结构断言失败: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"JSON结构断言异常: {str(e)}")
            raise e

    @staticmethod
    def assert_response_time(response, max_response_time: float, message: str = "") -> bool:
        """断言响应时间小于指定值"""
        logger.debug(f"执行响应时间断言: 最大允许时间={max_response_time}秒")
        try:
            if not response:
                raise ValueError("响应对象为空")

            actual_response_time = response.elapsed.total_seconds() if hasattr(response, 'elapsed') else float(response)
            logger.debug(f"实际响应时间: {actual_response_time}秒")

            assert actual_response_time <= max_response_time, f"实际响应时间: {actual_response_time}, 最大允许时间: {max_response_time}. {message}"
            logger.info(f"断言成功: 响应时间 {actual_response_time} <= {max_response_time}")
            return True

        except AssertionError as e:
            logger.error(f"响应时间断言失败: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"响应时间断言异常: {str(e)}")
            raise e