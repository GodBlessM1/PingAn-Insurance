"""
特征工程模块
构建分析所需的特征和宽表
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    特征工程类
    
    构建以下核心特征：
    - 保单基础特征
    - 现金流特征
    - 时间序列特征
    - 产品分类特征
    """
    
    def __init__(self, product_categories: Dict):
        """
        初始化特征工程器
        
        Args:
            product_categories: 产品分类配置
        """
        self.product_categories = product_categories
        
    def build_policy_base_features(self, policy_df: pd.DataFrame) -> pd.DataFrame:
        """
        构建保单基础特征
        
        Args:
            policy_df: 保单主表数据
            
        Returns:
            带特征的保单数据
        """
        logger.info("构建保单基础特征...")
        df = policy_df.copy()
        
        # 1. 产品分类映射
        df['product_category'] = df['product_code'].apply(self._map_product_category)
        df['product_sub_type'] = df['product_code'].apply(self._map_product_sub_type)
        
        # 2. 时间特征
        if 'issue_date' in df.columns:
            df['issue_year'] = df['issue_date'].dt.year
            df['issue_month'] = df['issue_date'].dt.month
            df['issue_quarter'] = df['issue_date'].dt.quarter
            
            # 保单存续期（年）
            current_year = datetime.now().year
            df['policy_duration_years'] = current_year - df['issue_year']
        
        # 3. 保费特征
        if 'annual_premium' in df.columns and 'payment_term' in df.columns:
            df['expected_total_premium'] = df['annual_premium'] * df['payment_term']
        
        # 4. 保额保费比
        if 'sum_assured' in df.columns and 'annual_premium' in df.columns:
            df['coverage_premium_ratio'] = df['sum_assured'] / df['annual_premium'].replace(0, np.nan)
        
        # 5. 客户分层
        if 'insured_age' in df.columns:
            df['age_group'] = pd.cut(
                df['insured_age'],
                bins=[0, 30, 40, 50, 60, 100],
                labels=['18-30', '31-40', '41-50', '51-60', '60+']
            )
        
        if 'sum_assured' in df.columns:
            df['coverage_group'] = pd.cut(
                df['sum_assured'],
                bins=[0, 100000, 500000, 1000000, 5000000, float('inf')],
                labels=['<10万', '10-50万', '50-100万', '100-500万', '500万+']
            )
        
        logger.info(f"保单特征构建完成，共 {len(df.columns)} 列")
        return df
    
    def build_cashflow_features(self, 
                                policy_df: pd.DataFrame,
                                premium_df: pd.DataFrame,
                                cash_value_df: pd.DataFrame,
                                dividend_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        构建现金流特征表
        
        Args:
            policy_df: 保单数据
            premium_df: 保费数据
            cash_value_df: 现金价值数据
            dividend_df: 分红数据 (可选)
            
        Returns:
            年度现金流宽表
        """
        logger.info("构建现金流特征...")
        
        # 1. 聚合保费数据 - 按保单和年度
        premium_annual = premium_df.copy()
        premium_annual['year'] = pd.to_datetime(premium_annual['payment_date']).dt.year
        premium_agg = premium_annual.groupby(['policy_id', 'year'])['premium_amount'].sum().reset_index()
        premium_agg.columns = ['policy_id', 'year', 'premium_outflow']
        
        # 2. 聚合现金价值数据 - 取年末值
        cv_annual = cash_value_df.copy()
        cv_annual['year'] = pd.to_datetime(cv_annual['valuation_date']).dt.year
        # 取每年最后一个值
        cv_agg = cv_annual.sort_values('valuation_date').groupby(['policy_id', 'year']).tail(1)
        cv_agg = cv_agg[['policy_id', 'year', 'cash_value']].copy()
        cv_agg.columns = ['policy_id', 'year', 'cash_value_eoy']
        
        # 3. 合并数据
        cashflow = premium_agg.merge(cv_agg, on=['policy_id', 'year'], how='outer')
        
        # 4. 添加分红数据 (如果有)
        if dividend_df is not None and not dividend_df.empty:
            div_annual = dividend_df.copy()
            div_annual['year'] = pd.to_datetime(div_annual['dividend_date']).dt.year
            div_agg = div_annual.groupby(['policy_id', 'year'])['dividend_amount'].sum().reset_index()
            cashflow = cashflow.merge(div_agg, on=['policy_id', 'year'], how='left')
            cashflow['dividend_amount'] = cashflow['dividend_amount'].fillna(0)
        else:
            cashflow['dividend_amount'] = 0
        
        # 5. 填充缺失值
        cashflow['premium_outflow'] = cashflow['premium_outflow'].fillna(0)
        cashflow['cash_value_eoy'] = cashflow['cash_value_eoy'].ffill()
        cashflow['cash_value_eoy'] = cashflow['cash_value_eoy'].fillna(0)
        
        # 6. 计算累计保费
        cashflow = cashflow.sort_values(['policy_id', 'year'])
        cashflow['cumulative_premium'] = cashflow.groupby('policy_id')['premium_outflow'].cumsum()
        
        # 7. 计算累计分红
        cashflow['cumulative_dividend'] = cashflow.groupby('policy_id')['dividend_amount'].cumsum()
        
        # 8. 净现金流 (负表示流出，正表示流入)
        cashflow['net_cashflow'] = cashflow['dividend_amount'] - cashflow['premium_outflow']
        
        logger.info(f"现金流特征构建完成，共 {len(cashflow)} 条记录")
        return cashflow
    
    def build_product_summary(self, 
                              policy_df: pd.DataFrame,
                              cashflow_df: pd.DataFrame) -> pd.DataFrame:
        """
        构建产品汇总特征
        
        Args:
            policy_df: 保单数据 (带特征)
            cashflow_df: 现金流数据
            
        Returns:
            产品汇总表
        """
        logger.info("构建产品汇总特征...")
        
        # 合并保单信息和最新现金流
        latest_cashflow = cashflow_df.sort_values('year').groupby('policy_id').tail(1)
        
        summary = policy_df.merge(
            latest_cashflow[['policy_id', 'cumulative_premium', 'cash_value_eoy', 
                           'cumulative_dividend', 'year']],
            on='policy_id',
            how='left'
        )
        
        # 计算汇总指标
        summary['total_value'] = summary['cash_value_eoy'] + summary['cumulative_dividend']
        summary['absolute_return'] = summary['total_value'] - summary['cumulative_premium']
        
        logger.info(f"产品汇总构建完成，共 {len(summary)} 条记录")
        return summary
    
    def _map_product_category(self, product_code: str) -> str:
        """映射产品代码到产品大类"""
        for category, info in self.product_categories.items():
            codes = info.get('codes', [])
            if any(product_code.startswith(code) for code in codes):
                return info.get('name', category)
        return '其他'
    
    def _map_product_sub_type(self, product_code: str) -> str:
        """映射产品代码到子类型"""
        # 简化处理，实际可根据更详细的映射表
        category = self._map_product_category(product_code)
        return category
    
    def create_analysis_wide_table(self,
                                   policy_df: pd.DataFrame,
                                   cashflow_df: pd.DataFrame) -> pd.DataFrame:
        """
        创建分析用宽表
        
        Args:
            policy_df: 保单数据
            cashflow_df: 现金流数据
            
        Returns:
            分析宽表
        """
        logger.info("创建分析宽表...")
        
        # 聚合现金流到保单级别
        cashflow_agg = cashflow_df.groupby('policy_id').agg({
            'premium_outflow': 'sum',
            'cumulative_premium': 'max',
            'dividend_amount': 'sum',
            'cumulative_dividend': 'max',
            'cash_value_eoy': 'last',
            'year': ['min', 'max', 'count']
        }).reset_index()
        
        # 扁平化列名
        cashflow_agg.columns = [
            'policy_id', 'total_premium_paid', 'cumulative_premium',
            'total_dividend', 'cumulative_dividend', 'latest_cash_value',
            'first_year', 'latest_year', 'observation_years'
        ]
        
        # 合并到保单表
        wide_table = policy_df.merge(cashflow_agg, on='policy_id', how='left')
        
        # 计算派生指标
        wide_table['total_account_value'] = (
            wide_table['latest_cash_value'].fillna(0) + 
            wide_table['cumulative_dividend'].fillna(0)
        )
        
        logger.info(f"分析宽表创建完成，共 {len(wide_table)} 条记录，{len(wide_table.columns)} 列")
        return wide_table
