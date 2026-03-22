"""
性能监控模块
监控代码执行时间和内存使用
"""

import time
import psutil
import logging
from functools import wraps
from contextlib import contextmanager
from typing import Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    性能监控器
    
    功能：
    - 执行时间监控
    - 内存使用监控
    - 性能报告生成
    """
    
    def __init__(self):
        self.metrics = []
        self.process = psutil.Process()
    
    def get_memory_usage(self) -> dict:
        """
        获取当前内存使用情况
        
        Returns:
            内存使用信息字典
        """
        mem_info = self.process.memory_info()
        return {
            'rss_mb': mem_info.rss / (1024 * 1024),
            'vms_mb': mem_info.vms / (1024 * 1024),
            'percent': self.process.memory_percent()
        }
    
    @contextmanager
    def monitor(self, operation_name: str):
        """
        上下文管理器用于监控代码块性能
        
        使用示例：
            with monitor.monitor('数据处理'):
                process_data()
        
        Args:
            operation_name: 操作名称
        """
        start_time = time.time()
        start_mem = self.get_memory_usage()
        
        try:
            yield self
        finally:
            end_time = time.time()
            end_mem = self.get_memory_usage()
            
            duration = end_time - start_time
            mem_diff = end_mem['rss_mb'] - start_mem['rss_mb']
            
            metric = {
                'operation': operation_name,
                'duration_seconds': round(duration, 3),
                'memory_start_mb': round(start_mem['rss_mb'], 2),
                'memory_end_mb': round(end_mem['rss_mb'], 2),
                'memory_diff_mb': round(mem_diff, 2),
                'timestamp': datetime.now().isoformat()
            }
            
            self.metrics.append(metric)
            
            logger.info(
                f"[性能] {operation_name}: "
                f"耗时 {duration:.3f}s, "
                f"内存变化 {mem_diff:+.2f}MB"
            )
    
    def get_report(self) -> dict:
        """
        生成性能报告
        
        Returns:
            性能报告字典
        """
        if not self.metrics:
            return {'message': '暂无性能数据'}
        
        total_time = sum(m['duration_seconds'] for m in self.metrics)
        total_mem = sum(m['memory_diff_mb'] for m in self.metrics)
        
        # 找出最慢的操作
        slowest = max(self.metrics, key=lambda x: x['duration_seconds'])
        
        return {
            'total_operations': len(self.metrics),
            'total_time_seconds': round(total_time, 3),
            'total_memory_change_mb': round(total_mem, 2),
            'average_time_seconds': round(total_time / len(self.metrics), 3),
            'slowest_operation': slowest['operation'],
            'slowest_time_seconds': slowest['duration_seconds'],
            'operations': self.metrics
        }
    
    def print_report(self):
        """打印性能报告"""
        report = self.get_report()
        
        print("\n" + "=" * 60)
        print("性能监控报告")
        print("=" * 60)
        
        if 'message' in report:
            print(report['message'])
            return
        
        print(f"总操作数: {report['total_operations']}")
        print(f"总耗时: {report['total_time_seconds']:.3f} 秒")
        print(f"平均耗时: {report['average_time_seconds']:.3f} 秒")
        print(f"总内存变化: {report['total_memory_change_mb']:+.2f} MB")
        print(f"最慢操作: {report['slowest_operation']} ({report['slowest_time_seconds']:.3f} 秒)")
        
        print("\n详细操作记录:")
        print("-" * 60)
        for m in self.metrics:
            print(
                f"{m['operation']:<30} "
                f"耗时: {m['duration_seconds']:>8.3f}s  "
                f"内存: {m['memory_diff_mb']:>+7.2f}MB"
            )
        print("=" * 60)
    
    def reset(self):
        """重置监控数据"""
        self.metrics = []
        logger.info("性能监控数据已重置")


def timed(func: Callable) -> Callable:
    """
    计时装饰器
    
    使用示例：
        @timed
        def my_function():
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f"[计时] {func.__name__} 耗时: {duration:.3f} 秒")
        return result
    return wrapper


def profile_memory(func: Callable) -> Callable:
    """
    内存分析装饰器
    
    使用示例：
        @profile_memory
        def my_function():
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        process = psutil.Process()
        mem_before = process.memory_info().rss / (1024 * 1024)
        
        result = func(*args, **kwargs)
        
        mem_after = process.memory_info().rss / (1024 * 1024)
        mem_diff = mem_after - mem_before
        
        logger.info(
            f"[内存] {func.__name__}: "
            f"使用前 {mem_before:.2f}MB, "
            f"使用后 {mem_after:.2f}MB, "
            f"变化 {mem_diff:+.2f}MB"
        )
        
        return result
    return wrapper


# 全局性能监控器实例
monitor = PerformanceMonitor()
