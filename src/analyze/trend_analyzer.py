"""
趋势分析模块
分析收益指标的时间趋势
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """
    趋势分析类
    
    分析内容：
    - 时间序列趋势
    - 趋势显著性检验
    - 周期性分析
    - 预测
    """
    
    def __init__(self):
        """初始化趋势分析器"""
        pass
    
    def analyze_yearly_trend(self,
                            df: pd.DataFrame,
                            year_col: str = 'issue_year',
                            value_col: str = 'irr_mean') -> Dict:
        """
        分析年度趋势
        
        Args:
            df: 按年份聚合的数据
            year_col: 年份列名
            value_col: 数值列名
            
        Returns:
            趋势分析结果
        """
        if value_col not in df.columns or year_col not in df.columns:
            return {'error': '缺少必要的列'}
        
        df = df.sort_values(year_col).dropna(subset=[value_col])
        
        if len(df) < 3:
            return {'error': '数据点不足，无法分析趋势'}
        
        years = df[year_col].values
        values = df[value_col].values
        
        # 线性回归
        slope, intercept, r_value, p_value, std_err = stats.linregress(years, values)
        
        # 计算年均变化
        total_change = values[-1] - values[0]
        avg_annual_change = total_change / (years[-1] - years[0]) if len(years) > 1 else 0
        
        # 趋势方向
        if slope > 0.001:
            trend_direction = '上升'
        elif slope < -0.001:
            trend_direction = '下降'
        else:
            trend_direction = '平稳'
        
        # 显著性
        is_significant = p_value < 0.05
        
        result = {
            'slope': slope,
            'intercept': intercept,
            'r_squared': r_value ** 2,
            'p_value': p_value,
            'is_significant': is_significant,
            'trend_direction': trend_direction,
            'total_change': total_change,
            'avg_annual_change': avg_annual_change,
            'std_err': std_err
        }
        
        return result
    
    def analyze_category_trends(self,
                               df: pd.DataFrame,
                               category_col: str = 'product_category',
                               year_col: str = 'issue_year',
                               value_col: str = 'irr') -> Dict[str, Dict]:
        """
        分析各产品类别的趋势
        
        Args:
            df: 输入数据
            category_col: 类别列名
            year_col: 年份列名
            value_col: 数值列名
            
        Returns:
            各类别趋势分析结果
        """
        results = {}
        
        for category in df[category_col].unique():
            category_df = df[df[category_col] == category]
            
            # 按年份聚合
            yearly = category_df.groupby(year_col)[value_col].mean().reset_index()
            
            trend = self.analyze_yearly_trend(yearly, year_col, value_col)
            results[category] = trend
        
        return results
    
    def calculate_moving_average(self,
                                 df: pd.DataFrame,
                                 value_col: str,
                                 window: int = 3) -> pd.DataFrame:
        """
        计算移动平均
        
        Args:
            df: 输入数据
            value_col: 数值列名
            window: 移动窗口大小
            
        Returns:
            带移动平均的数据
        """
        df = df.copy()
        df[f'{value_col}_ma{window}'] = df[value_col].rolling(window=window, min_periods=1).mean()
        return df
    
    def detect_volatility(self,
                         df: pd.DataFrame,
                         value_col: str,
                         group_col: Optional[str] = None) -> pd.DataFrame:
        """
        检测波动性
        
        Args:
            df: 输入数据
            value_col: 数值列名
            group_col: 分组列名
            
        Returns:
            波动性统计
        """
        if group_col:
            volatility = df.groupby(group_col)[value_col].agg([
                ('mean', 'mean'),
                ('std', 'std'),
                ('cv', lambda x: x.std() / x.mean() if x.mean() != 0 else np.nan),
                ('min', 'min'),
                ('max', 'max'),
                ('range', lambda x: x.max() - x.min())
            ]).reset_index()
        else:
            volatility = pd.DataFrame({
                'mean': [df[value_col].mean()],
                'std': [df[value_col].std()],
                'cv': [df[value_col].std() / df[value_col].mean() if df[value_col].mean() != 0 else np.nan],
                'min': [df[value_col].min()],
                'max': [df[value_col].max()],
                'range': [df[value_col].max() - df[value_col].min()]
            })
        
        return volatility
    
    def compare_periods(self,
                       df: pd.DataFrame,
                       value_col: str,
                       period_col: str = 'issue_year',
                       period1: tuple = (2020, 2021),
                       period2: tuple = (2023, 2024)) -> Dict:
        """
        对比两个时期的指标
        
        Args:
            df: 输入数据
            value_col: 数值列名
            period_col: 时期列名
            period1: 第一个时期 (start, end)
            period2: 第二个时期 (start, end)
            
        Returns:
            对比结果
        """
        df1 = df[(df[period_col] >= period1[0]) & (df[period_col] <= period1[1])]
        df2 = df[(df[period_col] >= period2[0]) & (df[period_col] <= period2[1])]
        
        mean1 = df1[value_col].mean()
        mean2 = df2[value_col].mean()
        
        # t检验
        if len(df1) > 1 and len(df2) > 1:
            t_stat, p_value = stats.ttest_ind(df1[value_col].dropna(), 
                                              df2[value_col].dropna())
        else:
            t_stat, p_value = np.nan, np.nan
        
        result = {
            'period1': {
                'years': period1,
                'mean': mean1,
                'count': len(df1)
            },
            'period2': {
                'years': period2,
                'mean': mean2,
                'count': len(df2)
            },
            'difference': mean2 - mean1,
            'pct_change': ((mean2 - mean1) / mean1 * 100) if mean1 != 0 else np.nan,
            't_statistic': t_stat,
            'p_value': p_value,
            'is_significant': p_value < 0.05
        }
        
        return result
    
    def generate_trend_summary(self,
                              df: pd.DataFrame,
                              year_col: str = 'issue_year',
                              value_cols: List[str] = None) -> str:
        """
        生成趋势分析文字摘要
        
        Args:
            df: 输入数据
            year_col: 年份列名
            value_cols: 数值列名列表
            
        Returns:
            趋势摘要文本
        """
        if value_cols is None:
            value_cols = ['irr', 'annual_return_rate']
        
        summary_lines = ["=" * 60, "趋势分析报告", "=" * 60, ""]
        
        for value_col in value_cols:
            if value_col not in df.columns:
                continue
            
            # 按年份聚合
            yearly = df.groupby(year_col)[value_col].mean().reset_index()
            trend = self.analyze_yearly_trend(yearly, year_col, value_col)
            
            if 'error' in trend:
                continue
            
            summary_lines.append(f"\n【{value_col}】趋势分析:")
            summary_lines.append(f"  - 趋势方向: {trend['trend_direction']}")
            summary_lines.append(f"  - 年均变化: {trend['avg_annual_change']:.4f}")
            summary_lines.append(f"  - 总变化: {trend['total_change']:.4f}")
            summary_lines.append(f"  - R²: {trend['r_squared']:.4f}")
            summary_lines.append(f"  - 统计显著性: {'是' if trend['is_significant'] else '否'} (p={trend['p_value']:.4f})")
        
        summary_lines.append("\n" + "=" * 60)
        
        return "\n".join(summary_lines)
