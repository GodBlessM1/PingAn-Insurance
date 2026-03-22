"""
数据清洗模块
处理原始数据的缺失值、异常值、格式转换等
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DataCleaner:
    """
    数据清洗类
    
    处理保险数据中的常见问题：
    - 缺失值处理
    - 日期格式统一
    - 金额单位统一
    - 重复数据删除
    - 异常值检测
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化清洗器
        
        Args:
            config: 清洗配置
        """
        self.config = config or {}
        self.cleaning_log = []
        
    def clean_policy_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗保单主表数据
        
        Args:
            df: 原始保单数据
            
        Returns:
            清洗后的数据
        """
        logger.info(f"开始清洗保单数据，原始行数: {len(df)}")
        original_count = len(df)
        
        df = df.copy()
        
        # 1. 删除完全重复的行
        df = df.drop_duplicates()
        self._log_step("删除重复行", original_count - len(df))
        
        # 2. 统一日期格式
        date_columns = ['issue_date', 'effective_date', 'maturity_date', 'termination_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # 3. 统一金额单位为元
        amount_columns = ['sum_assured', 'annual_premium', 'total_premium']
        for col in amount_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 4. 处理保单状态
        if 'policy_status' in df.columns:
            df['policy_status'] = df['policy_status'].str.upper().str.strip()
            # 过滤有效保单
            valid_statuses = ['ACTIVE', 'INFORCE', 'PAID_UP', 'MATURED']
            df = df[df['policy_status'].isin(valid_statuses)]
        
        # 5. 处理缺失值
        df = self._handle_missing_values(df)
        
        # 6. 过滤异常值
        df = self._filter_outliers(df)
        
        logger.info(f"保单数据清洗完成，最终行数: {len(df)}")
        return df
    
    def clean_cash_value_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗现金价值数据
        
        Args:
            df: 原始现金价值数据
            
        Returns:
            清洗后的数据
        """
        logger.info(f"开始清洗现金价值数据，原始行数: {len(df)}")
        
        df = df.copy()
        
        # 1. 删除重复
        df = df.drop_duplicates()
        
        # 2. 统一日期
        if 'valuation_date' in df.columns:
            df['valuation_date'] = pd.to_datetime(df['valuation_date'], errors='coerce')
        
        # 3. 确保现金价值为非负数
        if 'cash_value' in df.columns:
            df['cash_value'] = pd.to_numeric(df['cash_value'], errors='coerce')
            df['cash_value'] = df['cash_value'].fillna(0)
            df['cash_value'] = df['cash_value'].clip(lower=0)
        
        # 4. 按保单ID和日期排序
        if 'policy_id' in df.columns and 'valuation_date' in df.columns:
            df = df.sort_values(['policy_id', 'valuation_date'])
        
        logger.info(f"现金价值数据清洗完成，最终行数: {len(df)}")
        return df
    
    def clean_premium_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗保费流水数据
        
        Args:
            df: 原始保费数据
            
        Returns:
            清洗后的数据
        """
        logger.info(f"开始清洗保费数据，原始行数: {len(df)}")
        
        df = df.copy()
        
        # 1. 删除重复
        df = df.drop_duplicates()
        
        # 2. 统一日期
        if 'payment_date' in df.columns:
            df['payment_date'] = pd.to_datetime(df['payment_date'], errors='coerce')
        
        # 3. 确保保费金额为正数
        if 'premium_amount' in df.columns:
            df['premium_amount'] = pd.to_numeric(df['premium_amount'], errors='coerce')
            df = df[df['premium_amount'] > 0]
        
        # 4. 过滤异常大的保费 (可能是数据错误)
        if 'premium_amount' in df.columns:
            q99 = df['premium_amount'].quantile(0.99)
            df = df[df['premium_amount'] <= q99 * 10]  # 保留小于99分位数10倍的值
        
        logger.info(f"保费数据清洗完成，最终行数: {len(df)}")
        return df
    
    def clean_dividend_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗分红数据
        
        Args:
            df: 原始分红数据
            
        Returns:
            清洗后的数据
        """
        logger.info(f"开始清洗分红数据，原始行数: {len(df)}")
        
        df = df.copy()
        
        # 1. 删除重复
        df = df.drop_duplicates()
        
        # 2. 统一日期
        if 'dividend_date' in df.columns:
            df['dividend_date'] = pd.to_datetime(df['dividend_date'], errors='coerce')
        
        # 3. 确保分红金额非负
        if 'dividend_amount' in df.columns:
            df['dividend_amount'] = pd.to_numeric(df['dividend_amount'], errors='coerce')
            df['dividend_amount'] = df['dividend_amount'].fillna(0)
            df['dividend_amount'] = df['dividend_amount'].clip(lower=0)
        
        logger.info(f"分红数据清洗完成，最终行数: {len(df)}")
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        处理缺失值
        
        Args:
            df: 输入数据
            
        Returns:
            处理后的数据
        """
        # 数值型列：用0或均值填充
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                # 现金价值类用0填充，其他用中位数
                if 'value' in col.lower() or 'amount' in col.lower():
                    df[col] = df[col].fillna(0)
                else:
                    df[col] = df[col].fillna(df[col].median())
                self._log_step(f"填充缺失值 [{col}]", missing_count)
        
        # 类别型列：用众数填充
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                mode_val = df[col].mode()
                if len(mode_val) > 0:
                    df[col] = df[col].fillna(mode_val[0])
                self._log_step(f"填充缺失值 [{col}]", missing_count)
        
        return df
    
    def _filter_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        过滤异常值
        
        Args:
            df: 输入数据
            
        Returns:
            过滤后的数据
        """
        # 基于配置的最小保费阈值
        min_premium = self.config.get('min_premium_threshold', 1000)
        
        if 'annual_premium' in df.columns:
            original_count = len(df)
            df = df[df['annual_premium'] >= min_premium]
            removed = original_count - len(df)
            if removed > 0:
                self._log_step("过滤低保费保单", removed)
        
        # 过滤异常年龄
        if 'insured_age' in df.columns:
            df = df[(df['insured_age'] >= 0) & (df['insured_age'] <= 120)]
        
        return df
    
    def _log_step(self, step_name: str, count: int):
        """记录清洗步骤"""
        self.cleaning_log.append({
            'step': step_name,
            'affected_rows': count,
            'timestamp': datetime.now()
        })
        if count > 0:
            logger.info(f"清洗步骤 [{step_name}]: 影响 {count} 行")
    
    def get_cleaning_report(self) -> pd.DataFrame:
        """
        获取清洗报告
        
        Returns:
            清洗步骤报告
        """
        return pd.DataFrame(self.cleaning_log)
