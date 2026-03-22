"""
数据聚合模块
按不同维度聚合收益数据
"""

import pandas as pd
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class DataAggregator:
    """
    数据聚合类
    
    按以下维度聚合数据：
    - 产品大类/子类
    - 发行年份
    - 观测年份
    - 客户分层 (年龄/保额)
    - 销售渠道
    """
    
    def __init__(self, percentiles: Optional[List[float]] = None):
        """
        初始化聚合器
        
        Args:
            percentiles: 分位数列表，默认 [0.05, 0.25, 0.5, 0.75, 0.95]
        """
        self.percentiles = percentiles or [0.05, 0.25, 0.5, 0.75, 0.95]
        
    def aggregate_by_product(self, 
                            df: pd.DataFrame,
                            value_cols: List[str] = None) -> pd.DataFrame:
        """
        按产品分类聚合
        
        Args:
            df: 输入数据
            value_cols: 需要聚合的数值列
            
        Returns:
            聚合结果
        """
        # 检查是否存在product_category列
        if 'product_category' not in df.columns:
            logger.warning("数据中缺少 product_category 列")
            return pd.DataFrame()
        
        if value_cols is None:
            value_cols = ['irr', 'annual_return_rate', 'total_return_rate']
        
        # 过滤存在的列
        value_cols = [col for col in value_cols if col in df.columns]
        
        if not value_cols:
            logger.warning("没有可用的数值列进行聚合")
            return pd.DataFrame()
        
        agg_dict = {}
        for col in value_cols:
            agg_dict[col] = ['count', 'mean', 'median', 'std', 'min', 'max'] + \
                           [lambda x: x.quantile(p) for p in self.percentiles]
        
        # 重命名lambda函数
        result = df.groupby('product_category').agg(agg_dict)
        
        # 扁平化列名
        new_columns = []
        for col in result.columns:
            if col[1] not in ['<lambda>', '<lambda_0>']:
                new_columns.append(f"{col[0]}_{col[1]}")
            else:
                # 为lambda函数分配分位数名称
                percentile_idx = len([c for c in new_columns if c.startswith(col[0])])
                if percentile_idx < len(self.percentiles):
                    percentile = self.percentiles[percentile_idx]
                    new_columns.append(f"{col[0]}_p{int(percentile*100)}")
                else:
                    new_columns.append(f"{col[0]}_percentile")
        
        result.columns = new_columns
        
        result = result.reset_index()
        
        logger.info(f"按产品聚合完成，共 {len(result)} 个产品类别")
        return result
    
    def aggregate_by_year(self,
                         df: pd.DataFrame,
                         value_cols: List[str] = None) -> pd.DataFrame:
        """
        按发行年份聚合
        
        Args:
            df: 输入数据
            value_cols: 需要聚合的数值列
            
        Returns:
            聚合结果
        """
        if 'issue_year' not in df.columns:
            logger.warning("数据中缺少 issue_year 列")
            return pd.DataFrame()
        
        if value_cols is None:
            value_cols = ['irr', 'annual_return_rate']
        
        value_cols = [col for col in value_cols if col in df.columns]
        
        result = df.groupby('issue_year').agg({
            col: ['count', 'mean', 'median'] for col in value_cols
        }).reset_index()
        
        # 扁平化列名
        result.columns = ['_'.join(col).strip('_') if col[1] else col[0] 
                         for col in result.columns.values]
        
        logger.info(f"按年份聚合完成，共 {len(result)} 个年份")
        return result
    
    def aggregate_by_category_year(self,
                                   df: pd.DataFrame,
                                   value_cols: List[str] = None) -> pd.DataFrame:
        """
        按产品分类和年份交叉聚合
        
        Args:
            df: 输入数据
            value_cols: 需要聚合的数值列
            
        Returns:
            聚合结果
        """
        if value_cols is None:
            value_cols = ['irr', 'annual_return_rate']
        
        value_cols = [col for col in value_cols if col in df.columns]
        
        if 'issue_year' not in df.columns or 'product_category' not in df.columns:
            logger.warning("数据缺少必要的分组列")
            return pd.DataFrame()
        
        result = df.groupby(['product_category', 'issue_year']).agg({
            col: ['count', 'mean', 'median'] for col in value_cols
        }).reset_index()
        
        # 扁平化列名
        result.columns = ['_'.join(col).strip('_') if col[1] else col[0] 
                         for col in result.columns.values]
        
        logger.info(f"交叉聚合完成，共 {len(result)} 个组合")
        return result
    
    def aggregate_by_customer_segment(self,
                                      df: pd.DataFrame,
                                      segment_col: str = 'age_group',
                                      value_cols: List[str] = None) -> pd.DataFrame:
        """
        按客户分层聚合
        
        Args:
            df: 输入数据
            segment_col: 分层列名 (age_group/coverage_group)
            value_cols: 需要聚合的数值列
            
        Returns:
            聚合结果
        """
        if segment_col not in df.columns:
            logger.warning(f"数据中缺少 {segment_col} 列")
            return pd.DataFrame()
        
        if value_cols is None:
            value_cols = ['irr', 'annual_return_rate']
        
        value_cols = [col for col in value_cols if col in df.columns]
        
        result = df.groupby(segment_col).agg({
            col: ['count', 'mean', 'median', 'std'] for col in value_cols
        }).reset_index()
        
        # 扁平化列名
        result.columns = ['_'.join(col).strip('_') if col[1] else col[0] 
                         for col in result.columns.values]
        
        logger.info(f"按客户分层聚合完成，共 {len(result)} 个分层")
        return result
    
    def calculate_yoy_change(self,
                            df: pd.DataFrame,
                            year_col: str = 'issue_year',
                            value_col: str = 'irr_mean') -> pd.DataFrame:
        """
        计算同比变化
        
        Args:
            df: 按年份聚合的数据
            year_col: 年份列名
            value_col: 数值列名
            
        Returns:
            带同比变化的数据
        """
        df = df.sort_values(year_col)
        df[f'{value_col}_yoy'] = df[value_col].pct_change() * 100
        df[f'{value_col}_yoy_abs'] = df[value_col].diff()
        
        return df
    
    def calculate_percentile_distribution(self,
                                         df: pd.DataFrame,
                                         group_col: str = 'product_category',
                                         value_col: str = 'irr') -> pd.DataFrame:
        """
        计算分位数分布
        
        Args:
            df: 输入数据
            group_col: 分组列名
            value_col: 数值列名
            
        Returns:
            分位数分布表
        """
        if value_col not in df.columns:
            logger.warning(f"数据中缺少 {value_col} 列")
            return pd.DataFrame()
        
        percentiles = [0.1, 0.25, 0.5, 0.75, 0.9]
        
        result = df.groupby(group_col)[value_col].quantile(percentiles).unstack()
        result.columns = [f'p{int(p*100)}' for p in percentiles]
        result = result.reset_index()
        
        # 添加IQR
        result['iqr'] = result['p75'] - result['p25']
        
        return result
    
    def get_top_performers(self,
                          df: pd.DataFrame,
                          metric: str = 'irr',
                          n: int = 10,
                          group_by: Optional[str] = 'product_category') -> pd.DataFrame:
        """
        获取表现最佳的产品
        
        Args:
            df: 输入数据
            metric: 排序指标
            n: 返回数量
            group_by: 分组列名
            
        Returns:
            Top N产品
        """
        if metric not in df.columns:
            logger.warning(f"数据中缺少 {metric} 列")
            return pd.DataFrame()
        
        if group_by and group_by in df.columns:
            # 每个类别取Top N
            result = df.groupby(group_by).apply(
                lambda x: x.nlargest(n, metric)
            ).reset_index(drop=True)
        else:
            # 整体Top N
            result = df.nlargest(n, metric)
        
        return result
    
    def generate_summary_statistics(self, df: pd.DataFrame) -> Dict:
        """
        生成汇总统计信息
        
        Args:
            df: 输入数据
            
        Returns:
            统计信息字典
        """
        summary = {
            'total_policies': len(df),
            'date_range': {
                'start': df['issue_year'].min() if 'issue_year' in df.columns else None,
                'end': df['issue_year'].max() if 'issue_year' in df.columns else None
            },
            'product_distribution': df['product_category'].value_counts().to_dict() 
                                   if 'product_category' in df.columns else {},
            'metrics': {}
        }
        
        # 数值指标统计
        numeric_cols = ['irr', 'annual_return_rate', 'total_return_rate']
        for col in numeric_cols:
            if col in df.columns:
                summary['metrics'][col] = {
                    'mean': df[col].mean(),
                    'median': df[col].median(),
                    'std': df[col].std(),
                    'min': df[col].min(),
                    'max': df[col].max()
                }
        
        return summary
