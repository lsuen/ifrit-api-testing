import json
import shlex
from typing import Optional, Dict, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    import allure

    ALLURE_AVAILABLE = True
except ImportError:
    allure = None
    ALLURE_AVAILABLE = False

import logging

from core.allure_helper import AllureReporter

# 使用增强的日志系统
from utils.logger import get_logger
logger = get_logger(__name__)


class RequestHandler:
    """HTTP请求处理器（根据Content-Type判断发送JSON或表单数据）"""

    def __init__(self, base_url: str = "", timeout: int = 30, retries: int = 3):
        self.base_url = base_url.rstrip('/') if base_url else ""
        self.timeout = timeout

        # 配置会话和重试策略
        self.session = requests.Session()
        retry_strategy = Retry(
            total=retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self._default_headers: Dict[str, str] = {}

    def set_default_header(self, name: str, value: str) -> None:
        """设置 session 级默认请求头（如 Authorization）。"""
        self._default_headers[name] = value
        self.session.headers[name] = value

    def clear_default_headers(self) -> None:
        """清除 session 级默认请求头。"""
        for name in list(self._default_headers):
            self.session.headers.pop(name, None)
        self._default_headers.clear()

    def _generate_curl_command(self, method: str, url: str,
                               headers: Optional[Dict[str, str]] = None,
                               params: Optional[Dict[str, Any]] = None,
                               data: Optional[Dict[str, Any]] = None,
                               json_data: Optional[Dict[str, Any]] = None,
                               plain_text: Optional[str] = None) -> str:
        """生成等效的cURL命令"""
        # 处理URL参数
        if params:
            from urllib.parse import urlencode
            url += ('&' if '?' in url else '?') + urlencode(params)

        curl_cmd = ['curl', '-X', method.upper()]
        final_headers = dict(headers) if headers else {}

        # 根据Content-Type判断处理数据
        content_type = final_headers.get('Content-Type', '').lower()
        
        if json_data is not None:
            if 'application/json' in content_type:
                json_str = json.dumps(json_data, ensure_ascii=False)
                curl_cmd.extend(['--data-raw', json_str])
            else:
                # 如果Content-Type不是application/json，则转换为表单数据
                form_data = '&'.join(f'{k}={v}' for k, v in json_data.items())
                curl_cmd.extend(['--data', form_data])
        elif plain_text is not None:
            # 处理text/plain类型数据
            curl_cmd.extend(['--data', plain_text])
        elif data is not None:
            if isinstance(data, dict):
                form_data = '&'.join(f'{k}={v}' for k, v in data.items())
                curl_cmd.extend(['--data', form_data])
            else:
                curl_cmd.extend(['--data', str(data)])

        # 添加请求头
        for key, value in final_headers.items():
            curl_cmd.extend(['-H', f'{key}: {value}'])

        # 添加URL
        curl_cmd.append(url)

        # 安全拼接命令（兼容Python <3.8）
        try:
            return shlex.join(curl_cmd)
        except AttributeError:
            return ' '.join(shlex.quote(arg) for arg in curl_cmd)

    def send_request(self, method: str, url: str,
                     headers: Optional[Dict[str, str]] = None,
                     params: Optional[Dict[str, Any]] = None,
                     data: Optional[Dict[str, Any]] = None,
                     json_data: Optional[Dict[str, Any]] = None,
                     plain_text: Optional[str] = None,
                     **kwargs) -> Optional[requests.Response]:
        """
        发送HTTP请求（根据Content-Type判断发送JSON或表单数据）

        Args:
            method: HTTP方法（GET/POST/PUT/DELETE等）
            url: 请求路径（自动拼接base_url）
            headers: 请求头
            params: URL参数
            data: 表单数据
            json_data: JSON数据
            plain_text: 纯文本数据
            **kwargs: 其他requests参数（如files、cookies等）
        """
        # 处理URL
        if not url.startswith(('http://', 'https://')):
            base = self.base_url.rstrip('/')
            path = url if url.startswith('/') else '/' + url
            url = base + path if self.base_url else url

        # 处理请求头（合并 session 默认头，显式 headers 优先）
        request_headers = dict(self._default_headers)
        if headers:
            request_headers.update(headers)
        content_type = request_headers.get('Content-Type', '').lower()

        # 根据Content-Type判断发送数据的格式
        request_data = None
        request_json = None

        if json_data is not None:
            if 'application/json' in content_type:
                # 明确指定Content-Type为application/json时发送JSON数据
                request_json = json_data
            else:
                # 否则将JSON数据转换为表单数据发送
                request_data = json_data
                # 如果没有指定Content-Type，则设置为表单类型
                if 'content-type' not in [k.lower() for k in request_headers.keys()]:
                    request_headers['Content-Type'] = 'application/x-www-form-urlencoded'
        elif plain_text is not None:
            # 处理text/plain类型数据
            request_data = plain_text
            # 如果没有指定Content-Type，则设置为text/plain类型
            if 'content-type' not in [k.lower() for k in request_headers.keys()]:
                request_headers['Content-Type'] = 'text/plain'
        elif data is not None:
            # 直接发送表单数据
            request_data = data

        # 生成cURL命令（用于日志和Allure）
        curl_command = self._generate_curl_command(
            method, url, headers=headers, params=params, data=data, json_data=json_data, plain_text=plain_text
        )

        # 记录请求信息（Allure 统一步骤 + 日志）
        request_body = request_json if request_json is not None else (request_data if request_data is not None else None)
        AllureReporter.step_request(
            method=method.upper(),
            url=url,
            headers=request_headers,
            params=params,
            body=request_body,
            curl_command=curl_command,
        )

        logger.debug("=" * 50)
        logger.debug("请求方法: %s", method)
        logger.debug("Curl命令: %s", curl_command)
        logger.debug("请求URL: %s", url)
        logger.debug("请求头: %s", json.dumps(request_headers, ensure_ascii=False, indent=2))
        if params:
            logger.debug("URL参数: %s", json.dumps(params, ensure_ascii=False, indent=2))

        if json_data is not None:
            logger.debug("请求JSON: %s", json.dumps(json_data, ensure_ascii=False, indent=2))
        elif plain_text is not None:
            logger.debug("请求文本: %s", plain_text)
        elif data is not None:
            logger.debug("请求数据: %s", json.dumps(data, ensure_ascii=False, indent=2))

        logger.debug("-" * 30)

        try:
            # 发送请求
            response = self.session.request(
                method=method,
                url=url,
                headers=request_headers,
                params=params,
                json=request_json,  # JSON数据
                data=request_data,  # 表单数据或纯文本数据
                timeout=self.timeout,
                verify=False,
                **kwargs
            )

            AllureReporter.step_response(response)

            logger.debug("收到响应 status=%s elapsed=%ss", response.status_code, response.elapsed.total_seconds())
            logger.debug("响应头: %s", json.dumps(dict(response.headers), ensure_ascii=False, indent=2))
            logger.debug("响应体: %s", response.text)
            logger.debug("=" * 50)

            return response

        except requests.exceptions.Timeout as e:
            logger.error(f"请求超时: {e}")
            AllureReporter.attach_error("请求超时", str(e))
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {e}")
            AllureReporter.attach_error("请求异常", str(e))
        except Exception as e:
            logger.error(f"未知错误: {e}")
            AllureReporter.attach_error("未知错误", str(e))
        return None

    # 快捷方法
    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        return self.send_request('GET', url, **kwargs)

    def post(self, url: str, **kwargs) -> Optional[requests.Response]:
        return self.send_request('POST', url, **kwargs)

    def put(self, url: str, **kwargs) -> Optional[requests.Response]:
        return self.send_request('PUT', url, **kwargs)

    def delete(self, url: str, **kwargs) -> Optional[requests.Response]:
        return self.send_request('DELETE', url, **kwargs)