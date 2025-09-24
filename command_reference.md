# 快速运行指南

本文档提供了所有支持的命令行参数示例，方便开发人员和测试人员快速执行各种测试场景。

## 基础运行命令

<!-- 点击运行: 运行所有测试 -->
```bash
python main.py
```

<!-- 点击运行: 运行测试并生成Allure报告 -->
```bash
python main.py --generate-report
```

<!-- 点击运行: 运行测试并启动Allure报告服务器 -->
```bash
python main.py --serve-report
```

## 指定测试类型

<!-- 点击运行: 只运行Excel测试用例 -->
```bash
python main.py --type excel
```

<!-- 点击运行: 只运行CSV测试用例 -->
```bash
python main.py --type csv
```

<!-- 点击运行: 运行所有测试（默认） -->
```bash
python main.py --type all
```

## 指定测试文件

<!-- 点击运行: 运行指定的Excel文件 -->
```bash
python main.py --file data/excel_data/test_cases.xlsx
```

<!-- 点击运行: 运行指定的CSV文件 -->
```bash
python main.py --file data/csv_data/test_cases.csv
```

## 组合使用参数

<!-- 点击运行: 运行Excel测试并生成报告 -->
```bash
python main.py --type excel --generate-report
```

<!-- 点击运行: 运行指定文件并启动报告服务器 -->
```bash
python main.py --file data/test_cases.xlsx --serve-report
```

<!-- 点击运行: 运行CSV测试并生成HTML报告 -->
```bash
python main.py --type csv --generate-report
```

## 查看测试报告

<!-- 点击运行: 启动Allure报告服务器 -->
```bash
python main.py --serve-report
```

<!-- 点击运行: 生成静态HTML报告 -->
```bash
python main.py --generate-report
```

## 调试相关命令

<!-- 点击运行: 使用pytest直接运行所有测试用例 -->
```bash
pytest testcases/ -v
```

<!-- 点击运行: 使用pytest运行Excel测试用例 -->
```bash
pytest testcases/test_api_excel_driver.py -v
```

<!-- 点击运行: 使用pytest运行CSV测试用例 -->
```bash
pytest testcases/test_api_csv_driver.py -v
```

## 工具命令

<!-- 点击运行: 启动curl转测试用例工具 -->
```bash
python curltocase_client.py
```