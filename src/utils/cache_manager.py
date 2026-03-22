"""
缓存管理模块
提供数据缓存功能以提升性能
"""

import pickle
import hashlib
import json
from pathlib import Path
from functools import wraps
from datetime import datetime, timedelta
from typing import Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """
    缓存管理器
    
    功能：
    - 文件缓存（pickle格式）
    - 内存缓存
    - 缓存过期管理
    - 缓存键生成
    """
    
    def __init__(self, cache_dir: str = '.cache', default_ttl: int = 3600):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录
            default_ttl: 默认缓存时间（秒）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.default_ttl = default_ttl
        self._memory_cache = {}
        
    def _generate_cache_key(self, data: Any) -> str:
        """
        生成缓存键
        
        Args:
            data: 输入数据
            
        Returns:
            缓存键（MD5哈希）
        """
        if isinstance(data, pd.DataFrame):
            # DataFrame使用列名和数据摘要
            key_data = f"{list(data.columns)}_{data.shape}_{data.head(1).to_json()}"
        elif isinstance(data, dict):
            key_data = json.dumps(data, sort_keys=True, default=str)
        else:
            key_data = str(data)
        
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cache_path(self, key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{key}.pkl"
    
    def _get_meta_path(self, key: str) -> Path:
        """获取缓存元数据路径"""
        return self.cache_dir / f"{key}.meta"
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存数据
        
        Args:
            key: 缓存键
            
        Returns:
            缓存数据或None
        """
        # 先检查内存缓存
        if key in self._memory_cache:
            data, expiry = self._memory_cache[key]
            if datetime.now() < expiry:
                logger.debug(f"内存缓存命中: {key[:8]}...")
                return data
            else:
                del self._memory_cache[key]
        
        # 检查文件缓存
        cache_path = self._get_cache_path(key)
        meta_path = self._get_meta_path(key)
        
        if not cache_path.exists() or not meta_path.exists():
            return None
        
        # 检查是否过期
        try:
            with open(meta_path, 'r') as f:
                meta = json.load(f)
            
            expiry = datetime.fromisoformat(meta['expiry'])
            if datetime.now() > expiry:
                logger.debug(f"缓存过期: {key[:8]}...")
                cache_path.unlink(missing_ok=True)
                meta_path.unlink(missing_ok=True)
                return None
            
            # 加载缓存数据
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
            
            logger.debug(f"文件缓存命中: {key[:8]}...")
            return data
            
        except Exception as e:
            logger.warning(f"读取缓存失败: {e}")
            return None
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None):
        """
        设置缓存数据
        
        Args:
            key: 缓存键
            data: 缓存数据
            ttl: 缓存时间（秒），默认使用初始化值
        """
        ttl = ttl or self.default_ttl
        expiry = datetime.now() + timedelta(seconds=ttl)
        
        # 保存到内存缓存
        self._memory_cache[key] = (data, expiry)
        
        # 保存到文件缓存
        try:
            cache_path = self._get_cache_path(key)
            meta_path = self._get_meta_path(key)
            
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
            
            with open(meta_path, 'w') as f:
                json.dump({
                    'expiry': expiry.isoformat(),
                    'created': datetime.now().isoformat(),
                    'size': cache_path.stat().st_size if cache_path.exists() else 0
                }, f)
            
            logger.debug(f"缓存已保存: {key[:8]}...")
            
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")
    
    def clear(self, expired_only: bool = True):
        """
        清理缓存
        
        Args:
            expired_only: 只清理过期缓存
        """
        if not expired_only:
            # 清理所有缓存
            for f in self.cache_dir.glob('*.pkl'):
                f.unlink()
            for f in self.cache_dir.glob('*.meta'):
                f.unlink()
            self._memory_cache.clear()
            logger.info("所有缓存已清理")
        else:
            # 只清理过期缓存
            count = 0
            for meta_file in self.cache_dir.glob('*.meta'):
                try:
                    with open(meta_file, 'r') as f:
                        meta = json.load(f)
                    
                    expiry = datetime.fromisoformat(meta['expiry'])
                    if datetime.now() > expiry:
                        key = meta_file.stem
                        self._get_cache_path(key).unlink(missing_ok=True)
                        meta_file.unlink()
                        if key in self._memory_cache:
                            del self._memory_cache[key]
                        count += 1
                except:
                    pass
            
            logger.info(f"已清理 {count} 个过期缓存")
    
    def get_cache_stats(self) -> dict:
        """
        获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        total_size = 0
        file_count = 0
        
        for cache_file in self.cache_dir.glob('*.pkl'):
            total_size += cache_file.stat().st_size
            file_count += 1
        
        return {
            'file_count': file_count,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'memory_cache_count': len(self._memory_cache),
            'cache_dir': str(self.cache_dir)
        }


def cached(ttl: Optional[int] = None, cache_dir: str = '.cache'):
    """
    缓存装饰器
    
    使用示例：
        @cached(ttl=3600)
        def expensive_function(data):
            return process(data)
    
    Args:
        ttl: 缓存时间（秒）
        cache_dir: 缓存目录
    """
    def decorator(func: Callable) -> Callable:
        cache_manager = CacheManager(cache_dir=cache_dir, default_ttl=ttl or 3600)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key_data = {
                'func': func.__name__,
                'args': args,
                'kwargs': kwargs
            }
            key = cache_manager._generate_cache_key(cache_key_data)
            
            # 尝试获取缓存
            cached_result = cache_manager.get(key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 保存缓存
            cache_manager.set(key, result)
            
            return result
        
        return wrapper
    return decorator


# 导入pandas用于类型检查
try:
    import pandas as pd
except ImportError:
    pd = None
