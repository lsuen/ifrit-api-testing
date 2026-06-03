# ifrit-apitest Web UI

ifrit-apitest 框架的可视化 Web 界面，提供测试执行、报告查看、用例管理、AI 生成等功能。

## 特性

- ✅ **零侵入**：不修改原框架任何代码，通过 CLI 调用实现完全解耦
- ✅ **可移植**：通过配置文件指向项目路径，支持相对路径和绝对路径
- ✅ **跨平台**：提供 Windows/Linux/macOS 启动脚本
- ✅ **实时日志**：SSE 技术实现测试执行实时日志推送
- ✅ **轻量级**：Flask + Bootstrap 5 + 原生 JS，无前端工程化
- ✅ **易扩展**：CLI 参数通过 YAML 声明式配置，扩展无需改代码

## 目录结构

```
UI/
├── app.py                  # Flask 核心应用
├── config.yaml             # 配置文件
├── commands_map.yaml       # CLI 命令映射配置
├── requirements-ui.txt     # 依赖清单
├── run.sh / run.bat        # 启动脚本（后台）
├── stop.sh / stop.bat      # 停止脚本
├── debug_start.sh          # 调试启动脚本（前台）
├── templates/              # HTML 模板
│   ├── base.html           # 基础布局
│   ├── index.html          # 仪表盘
│   ├── execute.html        # 执行控制台
│   ├── reports.html        # 报告中心
│   ├── cases.html          # 用例管理
│   └── ai.html             # AI 生成
├── static/                 # 静态资源
│   ├── css/
│   │   └── style.css       # 自定义样式
│   └── js/
│       └── main.js         # 主 JavaScript
└── tests/                  # 单元测试
    └── test_app.py         # 测试用例
```

## 快速开始

### 环境要求

- Python 3.8+
- ifrit-apitest 项目（已安装依赖）

### 安装

1. 进入 UI 目录：
```bash
cd UI
```

2. 运行启动脚本（自动创建虚拟环境并安装依赖）：

**Linux/macOS:**
```bash
chmod +x run.sh
./run.sh
```

**Windows:**
```cmd
run.bat
```

3. 访问 Web 界面：
```
http://localhost:5001
```

### 停止服务

**Linux/macOS:**
```bash
./stop.sh
```

**Windows:**
```cmd
stop.bat
```

### 调试模式

前台运行，方便开发调试：

```bash
./debug_start.sh
```

## 配置说明

### config.yaml

```yaml
ifrit:
  root_path: "../"        # ifrit 项目路径（相对或绝对）
  python_bin: "python"    # Python 可执行文件
  cli_script: "main.py"   # CLI 主脚本

server:
  host: "0.0.0.0"         # 服务监听地址
  port: 5001              # 服务端口
  debug: false            # 调试模式

paths:
  data: "data"            # 测试数据目录
  reports: "reports"      # 报告目录
  logs: "logs"            # 日志目录
  api_docs: "api_docs"    # API 文档目录
```

### commands_map.yaml

声明式配置 CLI 命令参数，示例：

```yaml
test_run:
  cmd: "{python} {script} --type {format} --env {env}"
  params:
    format:
      type: "select"
      options: ["csv", "excel", "json"]
    env:
      type: "select"
      options: ["dev", "staging", "prod"]
```

## 功能模块

### 1. 仪表盘

- 测试用例统计
- 报告数量统计
- 活跃任务监控
- 快捷操作入口

### 2. 执行控制台

- 选择运行环境（dev/staging/prod）
- 选择数据格式（CSV/Excel/JSON）
- 选择测试文件
- 实时日志查看
- 执行状态监控
- 支持取消执行

### 3. 报告中心

- 历史报告列表
- 报告在线查看
- 报告下载
- 生成 HTML 报告
- 启动 Allure 报告服务器

### 4. 用例管理

- CSV/Excel/JSON 文件浏览
- 用例内容在线查看
- 文件下载

### 5. AI 生成

- API 文档上传（Markdown/Swagger）
- 生成参数配置
- 实时生成日志
- 输出格式选择

## 架构设计

### 零侵入原则

UI 与原框架完全隔离：
- 不修改 `core/`、`drivers/`、`main.py` 任何文件
- 通过 `subprocess` 调用原 CLI 执行测试
- 直接读写 `data/` 和 `reports/` 目录
- UI 崩溃不影响原框架 CLI 使用

### 调用链路

```
前端表单 → Flask 路由 → commands_map.yaml → subprocess → SSE 实时日志 → 读取报告
```

### 扩展方式

原框架新增 CLI 参数时：
1. 修改 `commands_map.yaml` 添加新命令配置
2. UI 自动适配，无需修改 Python 代码

## 部署

### 开发环境

```bash
./debug_start.sh
```

### 生产环境（Linux）

```bash
# 后台启动
./run.sh

# 使用 Nginx 反代（可选）
# 配置 Nginx 将请求转发到 localhost:5001
```

### 服务器部署

```bash
# 1. 修改 config.yaml 中的 root_path 为绝对路径
# 2. 运行启动脚本
./run.sh

# 3. 配置开机自启（可选）
# 将 run.sh 添加到系统服务或 crontab
```

## 开发指南

### 运行单元测试

```bash
cd UI
python -m pytest tests/ -v
```

### 添加新功能

1. 在 `app.py` 中添加路由
2. 在 `templates/` 中添加 HTML 模板
3. 在 `static/` 中添加 CSS/JS 资源
4. 在 `tests/` 中添加单元测试

### 修改 CLI 命令

编辑 `commands_map.yaml`，示例：

```yaml
new_command:
  cmd: "{python} {script} --new-flag {param}"
  params:
    param:
      type: "text"
      default: "value"
```

## 常见问题

### Q: 启动失败，提示端口被占用

A: 执行 `./stop.sh` 停止旧进程，或修改 `config.yaml` 中的端口号。

### Q: 无法找到 ifrit 项目

A: 检查 `config.yaml` 中的 `root_path` 配置是否正确。

### Q: 执行测试无日志输出

A: 检查 ifrit 项目 CLI 是否正常工作：`python main.py --help`

### Q: 如何更新依赖

A: 修改 `requirements-ui.txt` 后重新运行 `./run.sh`。

## 技术栈

- **后端**: Flask 3.0+
- **前端**: Bootstrap 5 + 原生 JavaScript + Axios
- **实时通信**: Server-Sent Events (SSE)
- **配置**: YAML
- **测试**: unittest

## 许可证

MIT License

## 作者

孙文龙

## 版本历史

### v1.0.0 (2026-06-02)

- ✨ 初始版本发布
- ✅ 实现测试执行控制台
- ✅ 实现报告中心
- ✅ 实现用例管理
- ✅ 实现 AI 生成功能
- ✅ 跨平台启动脚本
- ✅ 单元测试覆盖
