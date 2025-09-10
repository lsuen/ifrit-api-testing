import json
import requests
from typing import Optional, Dict, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 尝试导入allure，如果失败则设置为None
try:
    import allure
    ALLURE_AVAILABLE = True
except ImportError:
    allure = None
    ALLURE_AVAILABLE = False

from utils.logger import logger


class RequestHandler:
    """HTTP请求处理器"""
    
    def __init__(self, base_url: str = "", timeout: int = 30, retries: int = 3):
        """
        初始化请求处理器
        
        Args:
            base_url (str): 基础URL
            timeout (int): 超时时间（秒）
            retries (int): 重试次数
        """
        self.base_url = base_url.rstrip('/') if base_url else ""
        self.timeout = timeout
        
        # 创建会话并配置重试策略
        self.session = requests.Session()
        retry_strategy = Retry(
            total=retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
    def send_request(self, method: str, url: str, 
                    headers: Optional[Dict[str, str]] = None,
                    params: Optional[Dict[str, Any]] = None,
                    data: Optional[Dict[str, Any]] = None,
                    json_data: Optional[Dict[str, Any]] = None,
                    **kwargs) -> Optional[requests.Response]:
        """
        发送HTTP请求
        
        Args:
            method (str): HTTP方法
            url (str): 请求URL
            headers (dict, optional): 请求头
            params (dict, optional): URL参数
            data (dict, optional): 表单数据
            json_data (dict, optional): JSON数据
            **kwargs: 其他参数
            
        Returns:
            requests.Response: 响应对象，如果请求失败则返回None
        """
        # 处理URL
        if not url.startswith(('http://', 'https://')):
            # 确保base_url不以/结尾，url以/开头
            base = self.base_url.rstrip('/')
            path = url if url.startswith('/') else '/' + url
            url = base + path if self.base_url else url
            
        # 记录请求信息到allure报告（如果可用）
        if ALLURE_AVAILABLE and allure:
            allure.attach(url, "请求URL", allure.attachment_type.TEXT)
            if headers:
                allure.attach(json.dumps(headers, ensure_ascii=False, indent=2), "请求头", allure.attachment_type.JSON)
            if params:
                allure.attach(json.dumps(params, ensure_ascii=False, indent=2), "URL参数", allure.attachment_type.JSON)
            if data:
                allure.attach(json.dumps(data, ensure_ascii=False, indent=2), "表单数据", allure.attachment_type.JSON)
            if json_data:
                allure.attach(json.dumps(json_data, ensure_ascii=False, indent=2), "JSON数据", allure.attachment_type.JSON)
        
        # 记录详细的请求日志
        logger.info("=" * 50)
        logger.info("开始发送HTTP请求")
        logger.info(f"请求方法: {method}")
        logger.info(f"请求URL: {url}")
        logger.info(f"请求头: {json.dumps(headers, ensure_ascii=False, indent=2) if headers else {}}")
        if params:
            logger.info(f"URL参数: {json.dumps(params, ensure_ascii=False, indent=2)}")
        if data:
            logger.info(f"表单数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
        if json_data:
            logger.info(f"JSON数据: {json.dumps(json_data, ensure_ascii=False, indent=2)}")
        logger.info(f"超时时间: {self.timeout}秒")
        logger.info("-" * 30)
        
        try:
            # 发送请求
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=data,
                json=json_data,
                timeout=self.timeout
            )
            
            # 记录响应信息到allure报告（如果可用）
            if ALLURE_AVAILABLE and allure:
                allure.attach(str(response.status_code), "响应状态码", allure.attachment_type.TEXT)
                allure.attach(json.dumps(dict(response.headers), ensure_ascii=False, indent=2), "响应头", allure.attachment_type.JSON)
                allure.attach(response.text, "响应体", allure.attachment_type.TEXT)
            
            # 记录详细的响应日志
            logger.info("收到HTTP响应")
            logger.info(f"响应状态码: {response.status_code}")
            logger.info(f"响应头: {json.dumps(dict(response.headers), ensure_ascii=False, indent=2)}")
            logger.info(f"响应体: {response.text}")
            logger.info(f"响应时间: {response.elapsed.total_seconds()}秒")
            logger.info("=" * 50)
            
            return response
            
        except requests.exceptions.Timeout as e:
            logger.error(f"请求超时: {str(e)}")
            logger.info(f"超时时间: {self.timeout}秒")
            if ALLURE_AVAILABLE and allure:
                allure.attach(str(e), "请求超时", allure.attachment_type.TEXT)
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"连接错误: {str(e)}")
            if ALLURE_AVAILABLE and allure:
                allure.attach(str(e), "连接错误", allure.attachment_type.TEXT)
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"请求发送失败: {str(e)}")
            if ALLURE_AVAILABLE and allure:
                allure.attach(str(e), "请求异常", allure.attachment_type.TEXT)
            return None
        except Exception as e:
            logger.error(f"未知错误: {str(e)}")
            if ALLURE_AVAILABLE and allure:
                allure.attach(str(e), "未知错误", allure.attachment_type.TEXT)
            return None
            
    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """发送GET请求"""
        return self.send_request('GET', url, **kwargs)
        
    def post(self, url: str, **kwargs) -> Optional[requests.Response]:
        """发送POST请求"""
        return self.send_request('POST', url, **kwargs)
        
    def put(self, url: str, **kwargs) -> Optional[requests.Response]:
        """发送PUT请求"""
        return self.send_request('PUT', url, **kwargs)
        
    def delete(self, url: str, **kwargs) -> Optional[requests.Response]:
        """发送DELETE请求"""
        return self.send_request('DELETE', url, **kwargs)