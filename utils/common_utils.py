import json
from typing import Any, Dict


class CommonUtils:
    """通用工具类"""

    @staticmethod
    def parse_json_safely(text: str) -> Dict[str, Any]:
        """
        安全解析JSON字符串
        
        Args:
            text: JSON字符串
            
        Returns:
            解析后的字典
        """
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def is_json(text: str) -> bool:
        """
        判断字符串是否为有效的JSON
        
        Args:
            text: 待检查字符串
            
        Returns:
            是否为有效JSON
        """
        try:
            json.loads(text)
            return True
        except (json.JSONDecodeError, TypeError):
            return False

    @staticmethod
    def convert_str_to_type(value: str) -> Any:
        """
        将字符串转换为相应的数据类型
        
        Args:
            value: 字符串值
            
        Returns:
            转换后的值
        """
        if not isinstance(value, str):
            return value

        # None值
        if value.lower() in ['none', 'null']:
            return None

        # 布尔值
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'

        # 数字
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # JSON对象或数组
        if (value.startswith('{') and value.endswith('}')) or \
                (value.startswith('[') and value.endswith(']')):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass

        # 默认返回原字符串
        return value
