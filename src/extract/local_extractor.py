"""
本地文件数据提取器
用于从本地CSV/Parquet文件提取数据 (主要用于测试)
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
from .data_extractor import DataExtractor
import logging

logger = logging.getLogger(__name__)


class LocalExtractor(DataExtractor):
    """
    本地文件数据提取器
    
    支持CSV、Parquet、Excel等格式
    适用于开发和测试环境
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化本地提取器
        
        Args:
            config: 配置字典，包含:
                - raw_data_path: 原始数据目录
                - file_format: 默认文件格式 (csv/parquet/excel)
        """
        super().__init__(config)
        self.raw_data_path = Path(config.get('raw_data_path', 'data/raw'))
        self.default_format = config.get('file_format', 'parquet')
        
    def connect(self) -> bool:
        """
        检查数据目录是否存在
        
        Returns:
            目录是否存在
        """
        if not self.raw_data_path.exists():
            logger.warning(f"数据目录不存在: {self.raw_data_path}")
            self.raw_data_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"已创建数据目录: {self.raw_data_path}")
        
        return True
    
    def disconnect(self):
        """本地提取器无需断开连接"""
        pass
    
    def extract(self, query: str, params: Optional[Dict] = None) -> pd.DataFrame:
        """
        从本地文件提取数据
        
        Args:
            query: 文件名或文件路径
            params: 额外参数
                - file_format: 文件格式 (csv/parquet/excel)
                - columns: 指定列
                - 
        
        Returns:
            数据DataFrame
        """
        file_path = self.raw_data_path / query
        
        # 自动检测文件格式
        if file_path.suffix:
            file_format = file_path.suffix.lstrip('.')
        else:
            file_format = params.get('file_format', self.default_format) if params else self.default_format
            file_path = file_path.with_suffix(f'.{file_format}')
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        logger.info(f"读取本地文件: {file_path}")
        
        # 根据格式读取
        if file_format == 'csv':
            df = pd.read_csv(file_path)
        elif file_format == 'parquet':
            df = pd.read_parquet(file_path)
        elif file_format in ['xlsx', 'xls']:
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {file_format}")
        
        # 筛选指定列
        if params and 'columns' in params:
            df = df[params['columns']]
        
        logger.info(f"读取完成，共 {len(df)} 行")
        return df
    
    def extract_table(self, table_name: str,
                      columns: Optional[list] = None,
                      where_clause: Optional[str] = None,
                      limit: Optional[int] = None) -> pd.DataFrame:
        """
        提取表数据 (从同名文件)
        
        Args:
            table_name: 表名 (对应文件名)
            columns: 指定列
            where_clause: 过滤条件 (使用pandas query)
            limit: 限制行数
            
        Returns:
            数据DataFrame
        """
        params = {'columns': columns} if columns else None
        df = self.extract(table_name, params)
        
        # 应用过滤条件
        if where_clause:
            df = df.query(where_clause)
        
        # 限制行数
        if limit:
            df = df.head(limit)
        
        return df
    
    def list_tables(self) -> list:
        """
        列出所有可用的数据文件
        
        Returns:
            文件名列表
        """
        files = []
        for ext in ['*.csv', '*.parquet', '*.xlsx']:
            files.extend(self.raw_data_path.glob(ext))
        
        return [f.stem for f in files]
