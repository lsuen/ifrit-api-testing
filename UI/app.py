#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2026/06/02
# @Author  : 孙文龙
# @File    : app.py
# @Software: PyCharm
# @Desc    : ifrit-apitest Web UI 核心应用 - 文件管理器+编辑器模式

import os
import sys
import subprocess
import threading
import time
import json
import mimetypes
from pathlib import Path
from datetime import datetime

import yaml
from flask import Flask, render_template, request, jsonify, Response, stream_with_context

# ============================================================
# 全局配置
# ============================================================

UI_DIR = Path(__file__).parent.absolute()

def load_config():
    """加载配置文件"""
    config_path = UI_DIR / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    root_path_str = config["ifrit"]["root_path"]
    if os.path.isabs(root_path_str):
        root_path = Path(root_path_str)
    else:
        root_path = (UI_DIR / root_path_str).resolve()
    
    if not root_path.exists():
        raise FileNotFoundError(f"项目根目录不存在: {root_path}")
    
    config["ifrit"]["root_path_resolved"] = root_path
    return config

def load_commands_map():
    """加载命令映射"""
    commands_path = UI_DIR / "commands_map.yaml"
    if not commands_path.exists():
        raise FileNotFoundError(f"命令映射文件不存在: {commands_path}")
    
    with open(commands_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

CONFIG = None
COMMANDS_MAP = None

def init_config():
    """初始化配置"""
    global CONFIG, COMMANDS_MAP
    CONFIG = load_config()
    COMMANDS_MAP = load_commands_map()

# ============================================================
# Flask 应用
# ============================================================

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

# ============================================================
# 文件管理器核心功能
# ============================================================

# 支持编辑的文件类型
SUPPORTED_EXTENSIONS = {
    ".txt", ".csv", ".json", ".yaml", ".yml", ".ini", ".cfg",
    ".py", ".js", ".html", ".css", ".md", ".xml", ".sh", ".bat",
    ".log", ".conf", ".properties", ".env", ".toml"
}

# Ace Editor 模式映射
ACE_MODE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".json": "json",
    ".html": "html",
    ".css": "css",
    ".md": "markdown",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".ini": "ini",
    ".sh": "sh",
    ".bat": "batchfile",
    ".csv": "csv",
    ".log": "text",
    ".txt": "text",
    ".conf": "text",
    ".cfg": "text",
    ".properties": "properties",
    ".env": "sh",
    ".toml": "toml",
}

def get_project_path(relative_path):
    """获取项目绝对路径"""
    return CONFIG["ifrit"]["root_path_resolved"] / relative_path

def build_file_tree(directory_path, base_name=""):
    """
    构建文件树
    
    Returns:
        list: 文件树节点列表
    """
    path = Path(directory_path)
    if not path.exists() or not path.is_dir():
        return []
    
    tree = []
    
    try:
        items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
    except PermissionError:
        return []
    
    for item in items:
        # 跳过隐藏文件和缓存目录
        if item.name.startswith(".") or item.name == "__pycache__":
            continue
        
        node = {
            "name": item.name,
            "path": str(item),
            "is_dir": item.is_dir(),
        }
        
        if item.is_dir():
            node["children"] = build_file_tree(item, base_name + item.name + "/")
            node["size"] = None
            node["modified"] = None
        else:
            try:
                stat = item.stat()
                node["size"] = stat.st_size
                node["modified"] = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                node["extension"] = item.suffix.lower()
                node["supported"] = item.suffix.lower() in SUPPORTED_EXTENSIONS
            except Exception:
                node["size"] = 0
                node["modified"] = None
                node["extension"] = item.suffix.lower()
                node["supported"] = False
        
        tree.append(node)
    
    return tree

def read_file_content(file_path):
    """
    读取文件内容
    
    Returns:
        tuple: (success, content_or_error, mime_type)
    """
    path = Path(file_path)
    
    if not path.exists():
        return False, "文件不存在", None
    
    if path.is_dir():
        return False, "这是目录，不是文件", None
    
    # 检查文件大小（限制10MB）
    try:
        if path.stat().st_size > 10 * 1024 * 1024:
            return False, "文件过大（>10MB），不支持在线编辑", None
    except Exception:
        pass
    
    # 检查是否支持
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return False, f"文件格式 {path.suffix} 暂不支持编辑", None
    
    # 尝试读取
    try:
        # 尝试 UTF-8
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return True, content, "utf-8"
    except UnicodeDecodeError:
        pass
    
    try:
        # 尝试 GBK
        with open(path, "r", encoding="gbk") as f:
            content = f.read()
        return True, content, "gbk"
    except Exception as e:
        return False, f"读取失败: {str(e)}", None

def save_file_content(file_path, content, encoding="utf-8"):
    """
    保存文件内容
    
    Returns:
        tuple: (success, message)
    """
    path = Path(file_path)
    
    if not path.exists():
        return False, "文件不存在"
    
    if path.is_dir():
        return False, "无法保存目录"
    
    # 检查是否支持
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return False, f"文件格式 {path.suffix} 暂不支持编辑"
    
    try:
        with open(path, "w", encoding=encoding) as f:
            f.write(content)
        return True, "保存成功"
    except Exception as e:
        return False, f"保存失败: {str(e)}"

# ============================================================
# 路由定义
# ============================================================

@app.route("/")
def index():
    """首页 - 文件管理器"""
    return render_template("index.html")

@app.route("/api/files/tree", methods=["POST"])
def get_file_tree():
    """获取文件树"""
    data = request.json or {}
    dir_key = data.get("dir_key", "fixtures")
    
    dir_path = get_project_path(CONFIG["paths"].get(dir_key, dir_key))
    
    if not dir_path.exists():
        return jsonify({"error": f"目录不存在: {dir_path}"}), 404
    
    tree = build_file_tree(dir_path)
    
    return jsonify({
        "success": True,
        "dir": str(dir_path),
        "tree": tree
    })

@app.route("/api/files/read", methods=["POST"])
def read_file():
    """读取文件内容"""
    data = request.json or {}
    file_path = data.get("path")
    
    if not file_path:
        return jsonify({"error": "请提供文件路径"}), 400
    
    success, content_or_error, encoding = read_file_content(file_path)
    
    if success:
        # 获取Ace模式
        ext = Path(file_path).suffix.lower()
        ace_mode = ACE_MODE_MAP.get(ext, "text")
        
        return jsonify({
            "success": True,
            "content": content_or_error,
            "encoding": encoding,
            "mode": ace_mode,
            "size": len(content_or_error),
            "path": file_path
        })
    else:
        return jsonify({
            "success": False,
            "error": content_or_error,
            "path": file_path
        }), 400

@app.route("/api/files/save", methods=["POST"])
def save_file():
    """保存文件内容"""
    data = request.json or {}
    file_path = data.get("path")
    content = data.get("content")
    encoding = data.get("encoding", "utf-8")
    
    if not file_path:
        return jsonify({"error": "请提供文件路径"}), 400
    
    if content is None:
        return jsonify({"error": "请提供文件内容"}), 400
    
    success, message = save_file_content(file_path, content, encoding)
    
    if success:
        return jsonify({
            "success": True,
            "message": message,
            "path": file_path
        })
    else:
        return jsonify({
            "success": False,
            "error": message,
            "path": file_path
        }), 400

@app.route("/api/files/info", methods=["POST"])
def get_file_info():
    """获取文件信息"""
    data = request.json or {}
    file_path = data.get("path")
    
    if not file_path:
        return jsonify({"error": "请提供文件路径"}), 400
    
    path = Path(file_path)
    
    if not path.exists():
        return jsonify({"error": "文件不存在"}), 404
    
    try:
        stat = path.stat()
        return jsonify({
            "success": True,
            "name": path.name,
            "path": str(path),
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "extension": path.suffix.lower(),
            "supported": path.suffix.lower() in SUPPORTED_EXTENSIONS,
            "mode": ACE_MODE_MAP.get(path.suffix.lower(), "text")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/dirs")
def get_dirs():
    """获取可浏览的目录列表"""
    dirs = []
    
    for key, value in CONFIG["paths"].items():
        dir_path = get_project_path(value)
        if dir_path.exists():
            dirs.append({
                "key": key,
                "name": value,
                "path": str(dir_path),
                "exists": True
            })
    
    return jsonify({"dirs": dirs})

# ============================================================
# 应用入口
# ============================================================

if __name__ == "__main__":
    try:
        init_config()
        
        server_config = CONFIG["server"]
        print(f"\n{'='*60}")
        print(f"ifrit-apitest Web UI 启动中...")
        print(f"项目路径: {CONFIG['ifrit']['root_path_resolved']}")
        print(f"服务地址: http://{server_config['host']}:{server_config['port']}")
        print(f"{'='*60}\n")
        
        app.run(
            host=server_config["host"],
            port=server_config["port"],
            debug=server_config["debug"],
            threaded=True
        )
    
    except Exception as e:
        print(f"\n❌ 启动失败: {str(e)}", file=sys.stderr)
        sys.exit(1)
