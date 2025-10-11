import re

from utils.logger import logger


class DataHandler:
    """
    数据处理工具类
    """

    def __init__(self):
        self.variables = {}

    def set_variable(self, key, value):
        """
        设置变量

        Args:
            key (str): 变量名
            value (str): 变量值
        """
        self.variables[key] = value
        logger.info(f"设置变量: {key} = {value}")
        logger.debug(f"当前所有变量: {self.variables}")

    def get_variable(self, key):
        """
        获取变量值

        Args:
            key (str): 变量名

        Returns:
            str: 变量值
        """
        value = self.variables.get(key, '')
        logger.debug(f"获取变量: {key} = {value}")
        return value

    def replace_variables(self, text):
        """
        替换文本中的变量占位符，支持${variable_name}和{{variable_name}}两种格式，兼容全角字符

        Args:
            text (str): 包含变量占位符的文本

        Returns:
            str: 替换变量后的文本
        """
        if not isinstance(text, str):
            return text

        logger.debug(f"替换变量前的文本: {text}")

        # 处理全角字符转换为半角字符
        text = text.replace('｛', '{').replace('｝', '}')

        # 匹配 ${variable_name} 格式的变量占位符
        pattern1 = r'\$\{([^}]+)\}'
        matches1 = re.findall(pattern1, text)

        # 匹配 {{variable_name}} 格式的变量占位符
        pattern2 = r'\{\{([^}]+)\}\}'
        matches2 = re.findall(pattern2, text)

        result = text
        # 处理 ${variable_name} 格式
        for match in matches1:
            variable_value = self.get_variable(match)
            if variable_value:
                result = result.replace('${' + match + '}', variable_value)
                logger.debug(f"替换变量 {match} 为 {variable_value}")
            else:
                logger.warning(f"变量 {match} 未找到")

        # 处理 {{variable_name}} 格式
        for match in matches2:
            variable_value = self.get_variable(match)
            if variable_value:
                result = result.replace('{{' + match + '}}', variable_value)
                logger.debug(f"替换变量 {match} 为 {variable_value}")
            else:
                logger.warning(f"变量 {match} 未找到")

        logger.debug(f"替换变量后的文本: {result}")
        return result

    def extract_value(self, response_data, extract_key):
        """
        从响应数据中提取值，支持多值提取（用分号分隔）
        支持语法: "var1=key1; var2=key2" 或 "var1=path[0].field; var2=path2.field"
        """
        # 支持多值提取
        if ';' in extract_key:
            results = {}
            keys = [k.strip() for k in extract_key.split(';')]
            for key in keys:
                if '=' in key:
                    # 处理别名赋值，如 "message=debug[0].path1"
                    alias, actual_key = key.split('=', 1)
                    alias = alias.strip()
                    actual_key = actual_key.strip()
                    results[alias] = self._extract_single_value(response_data, actual_key)
                else:
                    # 直接使用键名作为变量名
                    results[key] = self._extract_single_value(response_data, key)
            return results
        else:
            # 单值提取保持原有逻辑
            return self._extract_single_value(response_data, extract_key)

    def _extract_single_value(self, response_data, extract_key):
        """
        从响应数据中提取值

        Args:
            response_data (dict): 响应数据
            extract_key (str): 提取键

        Returns:
            str: 提取到的值
        """
        if not extract_key:
            logger.debug("提取键为空，返回空字符串")
            return ''

        logger.debug(f"开始提取值，提取键: {extract_key}")
        logger.debug(f"响应数据: {response_data}")

        try:
            # 处理正则表达式提取
            if extract_key.startswith('regex:'):
                pattern = extract_key[6:]  # 去掉 'regex:' 前缀
                logger.debug(f"使用正则表达式提取: {pattern}")
                match = re.search(pattern, str(response_data))
                if match:
                    extracted_value = match.group(1) if match.groups() else match.group(0)
                    logger.info(f"正则表达式提取成功: {extract_key} -> {extracted_value}")
                    return extracted_value
                else:
                    logger.warning(f"正则表达式 {pattern} 未匹配到内容")
                    return ''

            # 处理JSON路径提取
            else:
                logger.debug(f"使用JSON路径提取: {extract_key}")
                # keys = extract_key.split('.')
                # value = response_data
                # for key in keys:
                #     if isinstance(value, dict) and key in value:
                #         value = value[key]
                #         logger.debug(f"获取键 {key} 的值: {value}")
                #     else:
                #         logger.warning(f"JSON路径 {extract_key} 未找到")
                #         return ''
                # 解析带索引的路径

                # 将 extract_key 按照数组索引和对象属性分离
                parts = re.findall(r'[^.\[\]]+|\[\d+\]', extract_key)
                value = response_data

                for part in parts:
                    if part.startswith('[') and part.endswith(']'):
                        # 处理数组索引 [index]
                        index = int(part[1:-1])
                        if isinstance(value, list) and 0 <= index < len(value):
                            value = value[index]
                        else:
                            return ''  # 索引越界或不是数组
                    else:
                        # 处理普通键访问
                        if isinstance(value, dict) and part in value:
                            value = value[part]
                        else:
                            return ''  # 键不存在或不是字典
                extracted_value = str(value)
                logger.info(f"JSON路径提取成功: {extract_key} -> {extracted_value}")
                return extracted_value

        except Exception as e:
            logger.error(f"提取值失败: {str(e)}")
            return ''

    def clear_global_vars(self):
        """
        清空全局变量
        """
        self.variables.clear()
        logger.debug("清空全局变量")

    def get_all_variables(self):
        """
        获取所有变量

        Returns:
            dict: 所有变量
        """
        logger.debug(f"获取所有变量: {self.variables}")
        return self.variables
