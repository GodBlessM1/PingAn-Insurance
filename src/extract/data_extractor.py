"""
数据提取器基类
定义统一的数据提取接口
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class DataExtractor(ABC):
    """
    数据提取器抽象基类
    
    所有具体提取器需要继承此类并实现抽象方法
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化提取器
        
        Args:
            config: 数据源配置字典
        """
        self.config = config
        self.connection = None
        
    @abstractmethod
    def connect(self) -> bool:
        """
        建立数据源连接
        
        Returns:
            连接是否成功
        """
        pass
    
    @abstractmethod
    def disconnect(self):
        """关闭数据源连接"""
        pass
    
    @abstractmethod
    def extract(self, query: str, params: Optional[Dict] = None) -> pd.DataFrame:
        """
        执行查询并提取数据
        
        Args:
            query: 查询语句或表名
            params: 查询参数
            
        Returns:
            提取的数据DataFrame
        """
        pass
    
    def extract_table(self, table_name: str, 
                      columns: Optional[list] = None,
                      where_clause: Optional[str] = None,
                      limit: Optional[int] = None) -> pd.DataFrame:
        """
        提取指定表的数据
        
        Args:
            table_name: 表名
            columns: 需要提取的列，None表示全部
            where_clause: WHERE条件
            limit: 限制返回行数
            
        Returns:
            提取的数据DataFrame
        """
        # 构建查询
        if columns:
            col_str = ', '.join(columns)
        else:
            col_str = '*'
        
        query = f"SELECT {col_str} FROM {table_name}"
        
        if where_clause:
            query += f" WHERE {where_clause}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        logger.info(f"提取表 {table_name}, 查询: {query}")
        
        return self.extract(query)
    
    def extract_by_period(self, table_name: str,
                          date_column: str,
                          start_date: str,
                          end_date: str,
                          columns: Optional[list] = None) -> pd.DataFrame:
        """
        按时间范围提取数据
        
        Args:
            table_name: 表名
            date_column: 日期列名
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            columns: 需要提取的列
            
        Returns:
            提取的数据DataFrame
        """
        where_clause = f"{date_column} BETWEEN '{start_date}' AND '{end_date}'"
        return self.extract_table(table_name, columns, where_clause)
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()
        if exc_type:
            logger.error(f"提取数据时发生错误: {exc_val}")
        return False
