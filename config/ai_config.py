#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI配置管理模块
负责加载和管理AI功能相关的所有配置参数
"""

import configparser
import os
import sys
import logging
from typing import Dict, Any, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AIConfig:
    """AI配置管理器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化AI配置
        
        Args:
            config_path: 配置文件路径，默认为config/ai_config.ini
        """
        if config_path is None:
            # 获取项目根目录
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, 'config', 'ai_config.ini')
        
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self._load_config()
    
    def _load_config(self) -> None:
        """加载AI配置文件"""
        try:
            if os.path.exists(self.config_path):
                self.config.read(self.config_path, encoding='utf-8')
                logger.info(f"成功加载AI配置文件: {self.config_path}")
            else:
                logger.warning(f"AI配置文件不存在: {self.config_path}，将使用默认配置")
                self._create_default_config()
        except Exception as e:
            logger.error(f"加载AI配置文件失败: {str(e)}，将使用默认配置")
            self._create_default_config()
    
    def _create_default_config(self) -> None:
        """创建默认配置"""
        self.config.clear()
        
        # OpenAI配置
        self.config.add_section('openai')
        self.config.set('openai', 'api_key', 'your_openai_api_key_here')
        self.config.set('openai', 'base_url', 'https://api.openai.com/v1')
        self.config.set('openai', 'model', 'gpt-3.5-turbo')
        self.config.set('openai', 'temperature', '0.7')
        self.config.set('openai', 'max_tokens', '2000')
        self.config.set('openai', 'timeout', '30')
        
        # 生成策略配置
        self.config.add_section('generation')
        self.config.set('generation', 'positive_cases_count', '3')
        self.config.set('generation', 'negative_cases_count', '2')
        self.config.set('generation', 'boundary_cases_count', '2')
        self.config.set('generation', 'structure_cases_count', '1')
        self.config.set('generation', 'path_cases_count', '2')
        self.config.set('generation', 'include_auth_cases', 'true')
        
        # 提示词模板配置
        self.config.add_section('prompts')
        self.config.set('prompts', 'system_prompt', '你是一个专业的API测试工程师，需要根据接口文档生成全面的测试用例。')
        self.config.set('prompts', 'positive_template', '为以下接口生成正向测试用例，确保正常场景下的功能验证')
        self.config.set('prompts', 'negative_template', '为以下接口生成反向测试用例，包括参数错误、权限不足等异常场景')
        self.config.set('prompts', 'boundary_template', '为以下接口生成边界测试用例，包括最大值、最小值、空值等边界条件')
        
        # 输出配置
        self.config.add_section('output')
        self.config.set('output', 'default_output_dir', 'data/ai_generated')
        self.config.set('output', 'add_timestamp', 'true')
        self.config.set('output', 'file_prefix', 'ai_')
        self.config.set('output', 'quality_check', 'true')
        self.config.set('output', 'conflict_resolution', 'ask')
        
        logger.info("已创建默认AI配置")
    
    def get_openai_config(self) -> Dict[str, Any]:
        """
        获取OpenAI接口配置
        
        Returns:
            OpenAI配置字典
        """
        # 优先从环境变量读取API密钥
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            api_key = self.config.get('openai', 'api_key', fallback='your_openai_api_key_here')
            if api_key == 'your_openai_api_key_here':
                logger.warning("未设置有效的OpenAI API密钥，请设置环境变量OPENAI_API_KEY或修改配置文件")
        
        config = {
            'api_key': api_key,
            'base_url': self.config.get('openai', 'base_url', fallback='http://localhost:8000'),
            'model': self.config.get('openai', 'model', fallback='gpt-3.5-turbo'),
            'temperature': self.config.getfloat('openai', 'temperature', fallback=0.7),
            'max_tokens': self.config.getint('openai', 'max_tokens', fallback=2000),
            'timeout': self.config.getint('openai', 'timeout', fallback=30)
        }
        
        logger.debug(f"OpenAI配置: {config}")
        return config
    
    def get_generation_config(self) -> Dict[str, Any]:
        """
        获取生成策略配置
        
        Returns:
            生成策略配置字典
        """
        config = {
            'positive_cases_count': self.config.getint('generation', 'positive_cases_count', fallback=3),
            'negative_cases_count': self.config.getint('generation', 'negative_cases_count', fallback=2),
            'boundary_cases_count': self.config.getint('generation', 'boundary_cases_count', fallback=2),
            'structure_cases_count': self.config.getint('generation', 'structure_cases_count', fallback=1),
            'path_cases_count': self.config.getint('generation', 'path_cases_count', fallback=2),
            'include_auth_cases': self.config.getboolean('generation', 'include_auth_cases', fallback=True)
        }
        
        logger.debug(f"生成策略配置: {config}")
        return config
    
    def get_prompt_templates(self) -> Dict[str, str]:
        """
        获取提示词模板
        
        Returns:
            提示词模板字典
        """
        templates = {
            'system_prompt': self.config.get('prompts', 'system_prompt', 
                fallback='你是一个专业的API测试工程师，需要根据接口文档生成全面的测试用例。'),
            'positive_template': self.config.get('prompts', 'positive_template',
                fallback='为以下接口生成正向测试用例，确保正常场景下的功能验证'),
            'negative_template': self.config.get('prompts', 'negative_template',
                fallback='为以下接口生成反向测试用例，包括参数错误、权限不足等异常场景'),
            'boundary_template': self.config.get('prompts', 'boundary_template',
                fallback='为以下接口生成边界测试用例，包括最大值、最小值、空值等边界条件')
        }
        
        logger.debug(f"提示词模板配置: {templates}")
        return templates
    
    def get_output_config(self) -> Dict[str, Any]:
        """
        获取输出配置
        
        Returns:
            输出配置字典
        """
        config = {
            'default_output_dir': self.config.get('output', 'default_output_dir', fallback='data/ai_generated'),
            'add_timestamp': self.config.getboolean('output', 'add_timestamp', fallback=True),
            'file_prefix': self.config.get('output', 'file_prefix', fallback='ai_'),
            'quality_check': self.config.getboolean('output', 'quality_check', fallback=True),
            'conflict_resolution': self.config.get('output', 'conflict_resolution', fallback='ask')
        }
        
        logger.debug(f"输出配置: {config}")
        return config
    
    def validate_config(self) -> bool:
        """
        验证配置有效性
        
        Returns:
            配置是否有效
        """
        try:
            # 验证OpenAI配置
            openai_config = self.get_openai_config()
            if not openai_config['api_key'] or openai_config['api_key'] == 'your_openai_api_key_here':
                logger.error("OpenAI API密钥未设置或无效")
                return False
            
            if not openai_config['base_url']:
                logger.error("OpenAI base_url未设置")
                return False
            
            if not openai_config['model']:
                logger.error("OpenAI model未设置")
                return False
            
            # 验证生成策略配置
            gen_config = self.get_generation_config()
            for key, value in gen_config.items():
                if isinstance(value, int) and value < 0:
                    logger.error(f"生成策略配置 {key} 不能为负数: {value}")
                    return False
            
            # 验证输出配置
            output_config = self.get_output_config()
            if not output_config['default_output_dir']:
                logger.error("默认输出目录未设置")
                return False
            
            valid_resolutions = ['ask', 'overwrite', 'append', 'rename']
            if output_config['conflict_resolution'] not in valid_resolutions:
                logger.error(f"无效的冲突解决策略: {output_config['conflict_resolution']}")
                return False
            
            logger.info("AI配置验证通过")
            return True
            
        except Exception as e:
            logger.error(f"配置验证失败: {str(e)}")
            return False
    
    def get_all_config(self) -> Dict[str, Any]:
        """
        获取所有配置
        
        Returns:
            完整配置字典
        """
        return {
            'openai': self.get_openai_config(),
            'generation': self.get_generation_config(),
            'prompts': self.get_prompt_templates(),
            'output': self.get_output_config()
        }
    
    def save_config(self, config_path: str = None) -> bool:
        """
        保存配置到文件
        
        Args:
            config_path: 配置文件路径，默认使用初始化时的路径
            
        Returns:
            是否保存成功
        """
        try:
            save_path = config_path or self.config_path
            
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            
            logger.info(f"AI配置已保存到: {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存AI配置失败: {str(e)}")
            return False


if __name__ == '__main__':
    # 测试AI配置管理器
    ai_config = AIConfig()
    
    print("OpenAI配置:")
    print(ai_config.get_openai_config())
    
    print("\n生成策略配置:")
    print(ai_config.get_generation_config())
    
    print("\n提示词模板:")
    print(ai_config.get_prompt_templates())
    
    print("\n输出配置:")
    print(ai_config.get_output_config())
    
    print(f"\n配置验证结果: {ai_config.validate_config()}")