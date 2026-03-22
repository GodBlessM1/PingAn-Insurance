"""
配置模块
加载和管理项目配置
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any


class Config:
    """配置管理类"""
    
    def __init__(self, config_path: str = None):
        """
        初始化配置
        
        Args:
            config_path: 配置文件路径，默认使用 config/config.yaml
        """
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        
        self.config_path = Path(config_path)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 替换环境变量
        config = self._replace_env_vars(config)
        return config
    
    def _replace_env_vars(self, obj: Any) -> Any:
        """递归替换配置中的环境变量"""
        if isinstance(obj, dict):
            return {k: self._replace_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            # 替换 ${VAR_NAME} 格式的环境变量
            import re
            pattern = r'\$\{([^}]+)\}'
            
            def replace_var(match):
                var_name = match.group(1)
                return os.getenv(var_name, match.group(0))
            
            return re.sub(pattern, replace_var, obj)
        return obj
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键，支持点号分隔 (如 "data_source.type")
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    @property
    def all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()
    
    def reload(self):
        """重新加载配置"""
        self._config = self._load_config()


# 全局配置实例
_config_instance = None


def get_config(config_path: str = None) -> Config:
    """
    获取全局配置实例 (单例模式)
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        Config 实例
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance
