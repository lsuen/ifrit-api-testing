#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9 上午10:07
# @Author  : sunwl
# @Site    :
# @File    : assert_handler.py
# @Software: PyCharm
import json
import re
from typing import Any, Dict

from jsonpath_ng import parse

import logging

logger = logging.getLogger(__name__)


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

                # 改用 jsonpath-ng 的调用方式
                jsonpath_expr = parse(json_path)
                matches = [match.value for match in jsonpath_expr.find(response_json)]

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
                    # 修复：严谨校验数组元素结构
                    if len(expected) > 0:
                        # 期望有结构时，所有实际数组元素都要匹配
                        for item in actual:
                            if not check_structure(item, expected[0]):
                                return False
                    return True
                else:
                    # 修复：通过类型示例判断实际类型是否匹配
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

            # 修复：增加非响应对象的异常处理
            if hasattr(response, 'elapsed'):
                actual_response_time = response.elapsed.total_seconds()
            else:
                try:
                    actual_response_time = float(response)
                except (ValueError, TypeError):
                    raise ValueError(f"响应时间必须是数字类型，实际传入: {type(response)}")

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


if __name__ == "__main__":
    from unittest.mock import Mock


    # 创建一个模拟的响应对象用于测试
    class MockResponse:
        def __init__(self, json_data=None, status_code=200, text="", elapsed_seconds=0.1):
            # 修复：默认值改为空字典，避免json()返回None
            self.json_data = json_data if json_data is not None else {}
            self.status_code = status_code
            self.text = text
            self.elapsed = Mock()
            self.elapsed.total_seconds.return_value = elapsed_seconds

        def json(self):
            return self.json_data


    # 测试用例
    handler = AssertHandler()

    # 测试 assert_equal
    print("测试 assert_equal:")
    try:
        handler.assert_equal(5, 5, "数值相等")
        print("✓ assert_equal 成功")
    except AssertionError:
        print("✗ assert_equal 失败")

    # 测试 assert_contains
    print("\n测试 assert_contains:")
    try:
        handler.assert_contains("hello world", "world", "包含子串")
        print("✓ assert_contains 成功")
    except AssertionError:
        print("✗ assert_contains 失败")

    # 测试 assert_status_code
    print("\n测试 assert_status_code:")
    mock_resp = MockResponse(status_code=200)
    try:
        handler.assert_status_code(mock_resp, 200, "状态码正确")
        print("✓ assert_status_code 成功")
    except AssertionError:
        print("✗ assert_status_code 失败")

    # 测试 assert_json_value
    print("\n测试 assert_json_value:")
    json_resp = MockResponse(json_data={"user": {"name": "test", "age": 25}})
    try:
        handler.assert_json_value(json_resp, "user.name", "test", "JSON值正确")
        print("✓ assert_json_value 成功")
    except AssertionError:
        print("✗ assert_json_value 失败")

    # 测试 assert_content_contains
    print("\n测试 assert_content_contains:")
    content_resp = MockResponse(text="Welcome to our website")
    try:
        handler.assert_content_contains(content_resp, "website", "内容包含")
        print("✓ assert_content_contains 成功")
    except AssertionError:
        print("✗ assert_content_contains 失败")

    # 测试 assert_regex
    print("\n测试 assert_regex:")
    regex_resp = MockResponse(text="My email is test@example.com")
    try:
        handler.assert_regex(regex_resp, r"\w+@\w+\.\w+", "正则匹配")
        print("✓ assert_regex 成功")
    except AssertionError:
        print("✗ assert_regex 失败")

    # 测试 assert_json_structure
    print("\n测试 assert_json_structure:")
    struct_resp = MockResponse(json_data={"user": {"name": "test", "settings": {}}})
    expected_struct = {"user": {"name": "", "settings": {}}}
    try:
        handler.assert_json_structure(struct_resp, expected_struct, "JSON结构正确")
        print("✓ assert_json_structure 成功")
    except AssertionError:
        print("✗ assert_json_structure 失败")

    # 测试 assert_response_time
    print("\n测试 assert_response_time:")
    time_resp = MockResponse(elapsed_seconds=0.5)
    try:
        handler.assert_response_time(time_resp, 1.0, "响应时间正确")
        print("✓ assert_response_time 成功")
    except AssertionError:
        print("✗ assert_response_time 失败")

    print("\n所有测试完成！")