"""
数据处理管道
整合数据清洗和特征工程流程
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Optional
import logging

from .data_cleaner import DataCleaner
from .feature_engineer import FeatureEngineer

logger = logging.getLogger(__name__)


class DataPipeline:
    """
    数据处理管道
    
    整合完整的数据处理流程：
    1. 数据清洗
    2. 特征工程
    3. 数据输出
    """
    
    def __init__(self, config: Dict, product_categories: Dict):
        """
        初始化处理管道
        
        Args:
            config: 处理配置
            product_categories: 产品分类配置
        """
        self.config = config
        self.cleaner = DataCleaner(config)
        self.engineer = FeatureEngineer(product_categories)
        self.output_path = Path(config.get('processed_data_path', 'data/processed'))
        self.output_path.mkdir(parents=True, exist_ok=True)
        
    def process(self,
                policy_df: pd.DataFrame,
                premium_df: pd.DataFrame,
                cash_value_df: pd.DataFrame,
                dividend_df: Optional[pd.DataFrame] = None,
                claim_df: Optional[pd.DataFrame] = None) -> Dict[str, pd.DataFrame]:
        """
        执行完整的数据处理流程
        
        Args:
            policy_df: 保单主表
            premium_df: 保费流水
            cash_value_df: 现金价值
            dividend_df: 分红数据 (可选)
            claim_df: 赔付数据 (可选)
            
        Returns:
            处理后的数据字典
        """
        logger.info("=" * 50)
        logger.info("开始数据处理管道")
        logger.info("=" * 50)
        
        # Step 1: 数据清洗
        logger.info("\n[Step 1/4] 数据清洗...")
        policy_clean = self.cleaner.clean_policy_data(policy_df)
        premium_clean = self.cleaner.clean_premium_data(premium_df)
        cash_value_clean = self.cleaner.clean_cash_value_data(cash_value_df)
        
        dividend_clean = None
        if dividend_df is not None:
            dividend_clean = self.cleaner.clean_dividend_data(dividend_df)
        
        # Step 2: 特征工程 - 保单特征
        logger.info("\n[Step 2/4] 构建保单特征...")
        policy_features = self.engineer.build_policy_base_features(policy_clean)
        
        # Step 3: 特征工程 - 现金流特征
        logger.info("\n[Step 3/4] 构建现金流特征...")
        cashflow_features = self.engineer.build_cashflow_features(
            policy_features, premium_clean, cash_value_clean, dividend_clean
        )
        
        # Step 4: 创建宽表
        logger.info("\n[Step 4/4] 创建分析宽表...")
        analysis_wide = self.engineer.create_analysis_wide_table(
            policy_features, cashflow_features
        )
        
        # 构建产品汇总
        product_summary = self.engineer.build_product_summary(
            policy_features, cashflow_features
        )
        
        results = {
            'policy_base': policy_features,
            'cashflow_annual': cashflow_features,
            'product_summary': product_summary,
            'analysis_wide': analysis_wide
        }
        
        logger.info("\n" + "=" * 50)
        logger.info("数据处理完成")
        logger.info("=" * 50)
        
        for name, df in results.items():
            logger.info(f"  {name}: {len(df)} 行 x {len(df.columns)} 列")
        
        return results
    
    def save_processed_data(self, data_dict: Dict[str, pd.DataFrame], 
                           format: str = 'parquet') -> Dict[str, Path]:
        """
        保存处理后的数据
        
        Args:
            data_dict: 数据字典
            format: 保存格式 (parquet/csv)
            
        Returns:
            保存路径字典
        """
        saved_paths = {}
        
        # 尝试使用parquet格式，如果失败则回退到CSV
        use_parquet = format == 'parquet'
        if use_parquet:
            try:
                import pyarrow
                logger.info("使用Parquet格式保存数据")
            except ImportError:
                logger.warning("pyarrow未安装，将使用CSV格式保存数据")
                use_parquet = False
        
        for name, df in data_dict.items():
            if use_parquet:
                file_path = self.output_path / f"{name}.parquet"
                df.to_parquet(file_path, index=False)
            else:
                file_path = self.output_path / f"{name}.csv"
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            saved_paths[name] = file_path
            logger.info(f"已保存: {file_path}")
        
        return saved_paths
    
    def load_processed_data(self, names: list, 
                           format: str = 'parquet') -> Dict[str, pd.DataFrame]:
        """
        加载已处理的数据
        
        Args:
            names: 数据表名列表
            format: 文件格式
            
        Returns:
            数据字典
        """
        data_dict = {}
        
        for name in names:
            if format == 'parquet':
                file_path = self.output_path / f"{name}.parquet"
                if file_path.exists():
                    data_dict[name] = pd.read_parquet(file_path)
                else:
                    logger.warning(f"文件不存在: {file_path}")
            elif format == 'csv':
                file_path = self.output_path / f"{name}.csv"
                if file_path.exists():
                    data_dict[name] = pd.read_csv(file_path)
                else:
                    logger.warning(f"文件不存在: {file_path}")
        
        return data_dict
