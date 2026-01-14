#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/9/10 上午10:07
# @Author  : sunwl
# @Site    :
# @File    : main.py
# @Software: PyCharm

from core.cli_manager import CLIManager


def main():
    """
    主函数 - 应用程序入口点
    """
    cli_manager = CLIManager()
    cli_manager.run()


if __name__ == "__main__":
    main()
