#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/9/18 下午1:48
# @Author  : sunwl
# @Site    : 
# @File    : curltocase_client.py
# @Software: PyCharm

#
# 需要安装的依赖包:
# pip install pandas openpyxl xlrd
#
# 功能说明:
# 1. 解析curl(bash)命令
# 2. 将解析结果追加写入CSV或Excel文件
# 3. 支持GUI界面操作

import json
import logging
import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from urllib.parse import urlparse, parse_qs

import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class CurlToCaseClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Curl转测试用例工具")
        self.root.geometry("800x600")

        # 文件路径变量
        self.file_path_var = tk.StringVar()
        self.file_type_var = tk.StringVar(value="csv")

        # curl内容变量
        self.curl_content_var = tk.StringVar()

        # 状态信息变量
        self.status_var = tk.StringVar()

        self.setup_ui()

    def setup_ui(self):
        # 第一行：文件选择部分
        file_frame = ttk.Frame(self.root)
        file_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(file_frame, text="文件类型:").pack(side=tk.LEFT)
        file_type_combo = ttk.Combobox(file_frame, textvariable=self.file_type_var,
                                       values=["csv", "excel"], state="readonly", width=10)
        file_type_combo.pack(side=tk.LEFT, padx=(5, 10))

        ttk.Label(file_frame, text="文件路径:").pack(side=tk.LEFT)
        ttk.Entry(file_frame, textvariable=self.file_path_var, width=40).pack(side=tk.LEFT, padx=(5, 10))

        ttk.Button(file_frame, text="选择文件", command=self.select_file).pack(side=tk.LEFT)

        # 第二行：curl标签
        curl_label_frame = ttk.Frame(self.root)
        curl_label_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        ttk.Label(curl_label_frame, text="请输入curl（bash）:").pack(anchor=tk.W)

        # 第三行：curl多行文本框
        curl_frame = ttk.Frame(self.root)
        curl_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.curl_text = scrolledtext.ScrolledText(curl_frame, height=8)
        self.curl_text.pack(fill=tk.BOTH, expand=True)

        # 第四行：状态回显部分
        status_label_frame = ttk.Frame(self.root)
        status_label_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        ttk.Label(status_label_frame, text="状态信息:").pack(anchor=tk.W)

        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.status_text = scrolledtext.ScrolledText(status_frame, height=6)
        self.status_text.pack(fill=tk.BOTH, expand=True)

        # 第五行：按钮部分
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="写入文件", command=self.write_to_file).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="调试", command=self.debug_info).pack(side=tk.LEFT)

    def select_file(self):
        file_type = self.file_type_var.get()
        if file_type == "csv":
            file_path = filedialog.askopenfilename(
                title="选择CSV文件",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
        else:
            file_path = filedialog.askopenfilename(
                title="选择Excel文件",
                filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
            )

        if file_path:
            self.file_path_var.set(file_path)
            self.log_status(f"已选择文件: {file_path}")

    def parse_curl(self, curl_command):

        logging.info("=== 开始解析curl命令 ===")
        logging.info(f"原始curl命令: {curl_command}")

        # 清理curl命令
        curl_command = curl_command.strip()
        if curl_command.startswith('curl'):
            curl_command = curl_command[4:].strip()

        logging.info(f"清理后的curl命令: {curl_command}")

        # 初始化测试用例数据
        test_case = {
            'id': '',  # 不设置ID，由文件处理
            'name': '未命名接口测试',
            'method': 'GET',
            'url': '',
            'headers': '{}',
            'params': '{}',
            'body': '{}',
            'expected_status': '200',
            'expected_result': '',
            'extract': '',
            'validate': '',
            'priority': '1',
            'enabled': '1'
        }

        # 提取URL（处理多种格式）
        logging.info("=== 开始解析URL ===")
        # 匹配带引号的URL
        url_match = re.search(r'["\'](https?://[^\s"\']+)["\']', curl_command)
        if not url_match:
            # 匹配不带引号的URL
            url_match = re.search(r'(https?://[^\s"\']+)($|\s)', curl_command)
        if not url_match:
            # 匹配相对路径URL
            url_match = re.search(r'["\'](/[^\s"\']+)["\']', curl_command)
        if not url_match:
            # 匹配不带引号的相对路径URL
            url_match = re.search(r'(/[^\s"\']+)($|\s)', curl_command)

        if url_match:
            url = url_match.group(1)
            logging.info(f"匹配到的URL: {url}")
            parsed_url = urlparse(url)
            test_case['url'] = parsed_url.path  # 只保存路径部分
            test_case['name'] = f"{parsed_url.path}接口测试" if parsed_url.path else "未命名接口测试"
            logging.info(f"解析后的路径: {parsed_url.path}")

            # 处理查询参数
            if parsed_url.query:
                logging.info(f"查询参数: {parsed_url.query}")
                params = parse_qs(parsed_url.query)
                # 转换为简单字典格式
                simple_params = {k: v[0] if v else '' for k, v in params.items()}
                test_case['params'] = json.dumps(simple_params, ensure_ascii=False)
                logging.info(f"解析后的查询参数: {simple_params}")
        else:
            logging.info("未匹配到URL")

        # 提取HTTP方法
        logging.info("=== 开始解析HTTP方法 ===")
        if '-X' in curl_command:
            method_match = re.search(r'-X\s+(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)', curl_command, re.IGNORECASE)
            if method_match:
                test_case['method'] = method_match.group(1).upper()
                logging.info(f"明确指定的HTTP方法: {test_case['method']}")
        else:
            # 如果没有明确指定方法，但有数据，则默认为POST
            if any(param in curl_command for param in ['-d', '--data', '--data-raw', '--data-binary']):
                test_case['method'] = 'POST'
                logging.info("检测到数据参数，设置默认方法为POST")

        # 提取headers
        logging.info("=== 开始解析Headers ===")
        headers = {}
        # 匹配 -H "Key: Value" 格式
        header_matches = re.findall(r'-H\s+["\']([^"\':]+):\s*([^"\']*)["\']', curl_command)
        logging.info(f"匹配到的Header格式1 (-H \"Key: Value\"): {header_matches}")
        for key, value in header_matches:
            headers[key.strip()] = value.strip()

        # 匹配 -H "Key:value" 格式（无空格）
        header_matches2 = re.findall(r'-H\s+["\']([^"\':]+):([^"\']*)["\']', curl_command)
        logging.info(f"匹配到的Header格式2 (-H \"Key:value\"): {header_matches2}")
        for key, value in header_matches2:
            headers[key.strip()] = value.strip()

        if headers:
            test_case['headers'] = json.dumps(headers, ensure_ascii=False)
            logging.info(f"最终Headers: {headers}")
        else:
            logging.info("未匹配到Headers")

        # 提取请求体 - 按优先级处理
        logging.info("=== 开始解析Body ===")
        body_data = None

        # 处理 --data-binary 参数（支持多行格式）
        logging.info("尝试匹配 --data-binary (三重引号格式)")
        data_binary_matches = re.findall(r'--data-binary\s+["\']{3}(.+?)["\']{3}', curl_command, re.DOTALL)
        if data_binary_matches:
            body_data = data_binary_matches[0].strip()
            logging.info(f"匹配到三重引号格式的--data-binary数据: {repr(body_data)}")
        else:
            # 处理单行格式的 --data-binary（支持跨行数据）
            logging.info("尝试匹配 --data-binary (单行格式，支持跨行)")
            # 使用更复杂的正则表达式来匹配跨行的引号内容
            data_binary_match = self._extract_data_between_quotes(curl_command, r'--data-binary\s+')
            if data_binary_match:
                body_data = data_binary_match.strip()
                logging.info(f"匹配到单行格式的--data-binary数据: {repr(body_data)}")

        # 处理 --data-raw 参数（如果data-binary不存在）
        if not body_data:
            logging.info("尝试匹配 --data-raw (三重引号格式)")
            data_raw_matches = re.findall(r'--data-raw\s+["\']{3}(.+?)["\']{3}', curl_command, re.DOTALL)
            if data_raw_matches:
                body_data = data_raw_matches[0].strip()
                logging.info(f"匹配到三重引号格式的--data-raw数据: {repr(body_data)}")
            else:
                logging.info("尝试匹配 --data-raw (单行格式)")
                data_raw_match = self._extract_data_between_quotes(curl_command, r'--data-raw\s+')
                if data_raw_match:
                    body_data = data_raw_match.strip()
                    logging.info(f"匹配到单行格式的--data-raw数据: {repr(body_data)}")

        # 处理 -d 参数（如果data-binary和data-raw都不存在）
        if not body_data:
            logging.info("尝试匹配 -d (三重引号格式)")
            data_matches = re.findall(r'-d\s+["\']{3}(.+?)["\']{3}', curl_command, re.DOTALL)
            if data_matches:
                body_data = data_matches[0].strip()
                logging.info(f"匹配到三重引号格式的-d数据: {repr(body_data)}")
            else:
                logging.info("尝试匹配 -d (单行格式)")
                data_match = self._extract_data_between_quotes(curl_command, r'-d\s+')
                if data_match:
                    body_data = data_match.strip()
                    logging.info(f"匹配到单行格式的-d数据: {repr(body_data)}")

        # 处理 --data 参数（如果其他参数都不存在）
        if not body_data:
            logging.info("尝试匹配 --data (三重引号格式)")
            data_matches2 = re.findall(r'--data\s+["\']{3}(.+?)["\']{3}', curl_command, re.DOTALL)
            if data_matches2:
                body_data = data_matches2[0].strip()
                logging.info(f"匹配到三重引号格式的--data数据: {repr(body_data)}")
            else:
                logging.info("尝试匹配 --data (单行格式)")
                data_match2 = self._extract_data_between_quotes(curl_command, r'--data\s+')
                if data_match2:
                    body_data = data_match2.strip()
                    logging.info(f"匹配到单行格式的--data数据: {repr(body_data)}")

        # 如果找到了body数据，进行处理
        if body_data:
            logging.info(f"原始body数据: {repr(body_data)}")
            # 清理数据（去除首尾空白字符和转义字符）
            body_data = body_data.strip()
            logging.info(f"清理空白后的body数据: {repr(body_data)}")
            # 处理转义的双引号
            body_data = body_data.replace('\\"', '"')
            logging.info(f"处理转义字符后的body数据: {repr(body_data)}")
            try:
                # 尝试解析为JSON
                data_json = json.loads(body_data)
                test_case['body'] = json.dumps(data_json, ensure_ascii=False)
                logging.info(f"成功解析为JSON格式: {data_json}")
            except json.JSONDecodeError as e:
                # 如果不是JSON，保留原始数据
                test_case['body'] = body_data
                logging.info(f"非JSON格式，保留原始数据。JSON解析错误: {e}")
        else:
            logging.info("未匹配到body数据")

        logging.info("=== 解析完成 ===")
        return test_case

    def _extract_data_between_quotes(self, curl_command, prefix_pattern):

        # 查找前缀位置
        prefix_match = re.search(prefix_pattern, curl_command)
        if not prefix_match:
            return None

        start_pos = prefix_match.end()
        if start_pos >= len(curl_command):
            return None

        # 获取第一个字符（引号）
        first_char = curl_command[start_pos]
        if first_char not in ['"', "'"]:
            return None

        # 查找结束引号（考虑转义字符）
        end_pos = start_pos + 1
        while end_pos < len(curl_command):
            if curl_command[end_pos] == first_char:
                # 检查是否是转义字符
                if end_pos > 0 and curl_command[end_pos - 1] != '\\':
                    # 找到结束引号
                    return curl_command[start_pos + 1:end_pos]
            end_pos += 1

        return None

    def log_status(self, message):
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)

    def debug_info(self):
        self.status_text.delete(1.0, tk.END)  # 清空状态文本框

        curl_content = self.curl_text.get(1.0, tk.END).strip()
        if not curl_content:
            self.log_status("错误: 请输入curl命令")
            return

        # 调试时不需要验证文件选择
        try:
            test_case = self.parse_curl(curl_content)
            self.log_status("解析结果（调试信息）:")
            for key, value in test_case.items():
                self.log_status(f"  {key}: {value}")
        except Exception as e:
            self.log_status(f"解析错误: {str(e)}")

    def write_to_file(self):
        self.status_text.delete(1.0, tk.END)  # 清空状态文本框

        curl_content = self.curl_text.get(1.0, tk.END).strip()
        if not curl_content:
            messagebox.showerror("错误", "请输入curl命令")
            return

        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showerror("错误", "请选择要写入的文件")
            return

        if not os.path.exists(file_path):
            messagebox.showerror("错误", f"文件不存在: {file_path}")
            return

        try:
            # 解析curl命令
            test_case = self.parse_curl(curl_content)

            # 读取现有文件
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, dtype=str)
            elif file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path, dtype=str, engine='openpyxl')
            elif file_path.endswith('.xls'):
                df = pd.read_excel(file_path, dtype=str, engine='xlrd')
            else:
                messagebox.showerror("错误", "不支持的文件格式")
                return

            # 过滤掉id列，因为我们不直接写入ID
            columns_to_write = [col for col in df.columns if col != 'id']

            # 创建新行数据
            new_row = {}
            for col in df.columns:
                if col in test_case:
                    new_row[col] = test_case[col]
                else:
                    new_row[col] = ''  # 其他列设为空

            # 添加到DataFrame
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

            # 写入文件
            if file_path.endswith('.csv'):
                df.to_csv(file_path, index=False)
            elif file_path.endswith('.xlsx'):
                df.to_excel(file_path, index=False, engine='openpyxl')
            elif file_path.endswith('.xls'):
                # 对于.xls文件，使用openpyxl引擎保存为.xlsx格式
                # 因为xlrd不支持写入操作
                base_name = os.path.splitext(file_path)[0]
                new_file_path = base_name + '.xlsx'
                df.to_excel(new_file_path, index=False, engine='openpyxl')
                self.log_status(f"注意: .xls文件已转换为.xlsx格式并保存为: {new_file_path}")

            self.log_status("成功写入文件:")
            for key, value in test_case.items():
                self.log_status(f"  {key}: {value}")

            messagebox.showinfo("成功", "测试用例已成功写入文件")

        except Exception as e:
            error_msg = f"写入文件时出错: {str(e)}"
            self.log_status(error_msg)
            messagebox.showerror("错误", error_msg)


def main():
    root = tk.Tk()
    app = CurlToCaseClient(root)
    root.mainloop()


if __name__ == "__main__":
    main()
