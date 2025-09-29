import logging
import os
from logging.handlers import RotatingFileHandler

# 延迟初始化配置实例
config = None


class Logger:
    """日志处理类"""

    def __init__(self):
        global config
        if config is None:
            from config.config import Config
            config = Config()
        
        self.logger = logging.getLogger('api_automation')
        self.logger.setLevel(getattr(logging, config.get_log_level().upper()))

        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        """设置日志处理器"""
        # 创建日志目录
        os.makedirs(config.logs_dir, exist_ok=True)

        # 文件处理器 - 使用轮转日志
        log_file = os.path.join(config.logs_dir, 'api_automation.log')
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )

        # 控制台处理器
        console_handler = logging.StreamHandler()

        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 添加处理器到logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def get_logger(self):
        """获取logger实例"""
        return self.logger


# 创建全局logger实例
logger_instance = Logger()
logger = logger_instance.get_logger()
