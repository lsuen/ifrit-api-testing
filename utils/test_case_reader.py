import os

import pandas as pd

from config.config import Config
from utils.logger import logger


class DataHandler:
    """
    数据处理工具类，支持Excel和CSV格式
    """

    def __init__(self):
        self.config = Config()

    def read_test_cases(self, file_path):
        """
        读取测试用例，支持Excel和CSV格式

        Args:
            file_path (str): 文件路径

        Returns:
            list: 测试用例列表
        """
        logger.info(f"开始读取测试用例文件: {file_path}")
        logger.info(f"文件是否存在: {os.path.exists(file_path)}")

        if not os.path.exists(file_path):
            logger.error(f"测试文件不存在: {file_path}")
            return []

        try:
            # 根据文件扩展名选择读取方法
            if file_path.endswith('.xlsx'):
                logger.info("检测到.xlsx文件，使用openpyxl引擎读取")
                df = pd.read_excel(file_path, dtype=str, engine='openpyxl')
            elif file_path.endswith('.xls'):
                logger.info("检测到.xls文件，使用xlrd引擎读取")
                df = pd.read_excel(file_path, dtype=str, engine='xlrd')
            elif file_path.endswith('.csv'):
                logger.info("检测到.csv文件，使用CSV方式读取")
                df = pd.read_csv(file_path, dtype=str)
            elif file_path.endswith('.json'):
                logger.info("检测到.json文件，使用JSON方式读取")
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # 如果数据是字典形式，转换为列表
                if isinstance(data, dict):
                    data = [data]
                # 转换为DataFrame
                df = pd.DataFrame(data)
                # 确保所有字段都存在
                required_columns = ['case_id', 'case_name', 'method', 'url', 'headers', 'params', 'body',
                                    'expected_status', 'expected_content', 'json_path', 'expected_json_value',
                                    'extract_key', 'save_var_name', 'validate', 'enabled']
                for col in required_columns:
                    if col not in df.columns:
                        df[col] = ''
            else:
                logger.error(f"不支持的文件格式: {file_path}")
                return []

            logger.info(f"成功读取文件，数据行数: {len(df)}")
            logger.debug(f"数据列名: {list(df.columns)}")

            # 处理空值
            df = df.fillna('')

            # 显示数据预览
            logger.debug(f"数据预览（前3行）: \n{df.head(3)}")

            # 转换为字典列表
            test_cases = []
            for index, row in df.iterrows():
                # 只处理启用的测试用例
                # 检查用例是否启用
                enabled_value = str(row.get('enabled', '1')).strip().lower()
                is_enabled = enabled_value in ['1', 'true', 'yes', 'enabled', 'enable', 'y', 't']
                
                # 提前提取case_id和case_name用于日志记录
                case_id = str(row.get('case_id', row.get('id', '')))
                case_name = str(row.get('case_name', row.get('name', '')))
                
                logger.debug(f"用例行 {index + 1} 是否启用: {is_enabled} (enabled值: {enabled_value})")

                if not is_enabled:
                    logger.debug(f"用例 {case_id} - {case_name} 未启用，跳过")
                    continue

                # 根据实际列名映射到期望的字段名
                case = {
                    'case_id': case_id,
                    'case_name': case_name,
                    'method': str(row.get('method', '')).upper(),
                    'url': str(row.get('url', '')),
                    'headers': str(row.get('headers', '{}')),
                    'params': str(row.get('params', '{}')),
                    'body': str(row.get('body', row.get('data', '{}'))),
                    'expected_status': str(row.get('expected_status', '')),
                    'expected_content': str(row.get('expected_content', row.get('expected_result', ''))),
                    'json_path': str(row.get('json_path', '')),
                    'expected_json_value': str(row.get('expected_json_value', '')),
                    'extract_key': str(row.get('extract_key', row.get('extract', row.get('variable', '')))),
                    'save_var_name': str(row.get('save_var_name', '')),
                    'validate': str(row.get('validate', ''))
                }
                test_cases.append(case)
                logger.debug(f"添加测试用例: {case['case_id']} - {case['case_name']}")

            logger.info(f"从 {file_path} 成功读取 {len(test_cases)} 条测试用例")
            return test_cases

        except Exception as e:
            logger.error(f"读取文件 {file_path} 失败: {str(e)}")
            import traceback
            logger.error(f"详细错误信息:\n{traceback.format_exc()}")
            return []
