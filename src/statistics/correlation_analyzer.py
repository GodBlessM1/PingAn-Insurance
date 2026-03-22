"""
相关性分析模块
分析变量之间的相关关系
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class CorrelationAnalyzer:
    """
    相关性分析类
    
    提供以下分析功能：
    - Pearson相关系数
    - Spearman相关系数
    - 相关矩阵
    - 偏相关分析
    """
    
    def __init__(self, alpha: float = 0.05):
        """
        初始化相关性分析器
        
        Args:
            alpha: 显著性水平
        """
        self.alpha = alpha
        self.correlation_results = {}
        
    def pearson_correlation(self,
                           df: pd.DataFrame,
                           col1: str,
                           col2: str) -> Dict[str, Any]:
        """
        计算Pearson相关系数
        
        Args:
            df: 数据框
            col1: 第一列
            col2: 第二列
            
        Returns:
            相关系数结果
        """
        if col1 not in df.columns or col2 not in df.columns:
            return {'error': '指定的列不存在'}
        
        data1 = df[col1].dropna()
        data2 = df[col2].dropna()
        
        common_idx = data1.index.intersection(data2.index)
        data1 = data1.loc[common_idx]
        data2 = data2.loc[common_idx]
        
        if len(data1) < 3:
            return {'error': '数据量不足'}
        
        corr, p_value = stats.pearsonr(data1, data2)
        
        r_squared = corr ** 2
        
        if abs(corr) < 0.3:
            strength = '弱相关'
        elif abs(corr) < 0.5:
            strength = '中等相关'
        elif abs(corr) < 0.7:
            strength = '较强相关'
        else:
            strength = '强相关'
        
        direction = '正相关' if corr > 0 else '负相关'
        
        result = {
            'method': 'Pearson',
            'variable1': col1,
            'variable2': col2,
            'n': len(data1),
            'correlation': float(corr),
            'p_value': float(p_value),
            'r_squared': float(r_squared),
            'significant': p_value < self.alpha,
            'strength': strength,
            'direction': direction,
            'interpretation': f"{col1}与{col2}之间存在{strength}的{direction}关系 (r={corr:.3f}, p={p_value:.4f})"
        }
        
        return result
    
    def spearman_correlation(self,
                            df: pd.DataFrame,
                            col1: str,
                            col2: str) -> Dict[str, Any]:
        """
        计算Spearman秩相关系数
        
        Args:
            df: 数据框
            col1: 第一列
            col2: 第二列
            
        Returns:
            相关系数结果
        """
        if col1 not in df.columns or col2 not in df.columns:
            return {'error': '指定的列不存在'}
        
        data1 = df[col1].dropna()
        data2 = df[col2].dropna()
        
        common_idx = data1.index.intersection(data2.index)
        data1 = data1.loc[common_idx]
        data2 = data2.loc[common_idx]
        
        if len(data1) < 3:
            return {'error': '数据量不足'}
        
        corr, p_value = stats.spearmanr(data1, data2)
        
        if abs(corr) < 0.3:
            strength = '弱相关'
        elif abs(corr) < 0.5:
            strength = '中等相关'
        elif abs(corr) < 0.7:
            strength = '较强相关'
        else:
            strength = '强相关'
        
        direction = '正相关' if corr > 0 else '负相关'
        
        result = {
            'method': 'Spearman',
            'variable1': col1,
            'variable2': col2,
            'n': len(data1),
            'correlation': float(corr),
            'p_value': float(p_value),
            'significant': p_value < self.alpha,
            'strength': strength,
            'direction': direction,
            'interpretation': f"{col1}与{col2}之间存在{strength}的{direction}关系 (ρ={corr:.3f}, p={p_value:.4f})"
        }
        
        return result
    
    def correlation_matrix(self,
                          df: pd.DataFrame,
                          columns: Optional[List[str]] = None,
                          method: str = 'pearson') -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        计算相关矩阵
        
        Args:
            df: 数据框
            columns: 要分析的列，默认所有数值列
            method: 相关系数方法 ('pearson', 'spearman')
            
        Returns:
            相关矩阵和显著性信息
        """
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(columns) < 2:
            return pd.DataFrame(), {'error': '需要至少2个数值列'}
        
        data = df[columns].dropna()
        
        if method == 'pearson':
            corr_matrix = data.corr(method='pearson')
        else:
            corr_matrix = data.corr(method='spearman')
        
        p_matrix = pd.DataFrame(np.zeros((len(columns), len(columns))), 
                               index=columns, columns=columns)
        
        for i, col1 in enumerate(columns):
            for j, col2 in enumerate(columns):
                if i != j:
                    if method == 'pearson':
                        _, p = stats.pearsonr(data[col1], data[col2])
                    else:
                        _, p = stats.spearmanr(data[col1], data[col2])
                    p_matrix.loc[col1, col2] = p
                else:
                    p_matrix.loc[col1, col2] = 1.0
        
        significant_pairs = []
        for i, col1 in enumerate(columns):
            for j, col2 in enumerate(columns):
                if i < j:
                    corr = corr_matrix.loc[col1, col2]
                    p_val = p_matrix.loc[col1, col2]
                    if p_val < self.alpha and abs(corr) > 0.3:
                        significant_pairs.append({
                            'var1': col1,
                            'var2': col2,
                            'correlation': float(corr),
                            'p_value': float(p_val)
                        })
        
        metadata = {
            'method': method,
            'n': len(data),
            'significant_correlations': significant_pairs,
            'strong_correlations': [p for p in significant_pairs if abs(p['correlation']) > 0.5]
        }
        
        return corr_matrix, metadata
    
    def analyze_premium_irr_relationship(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        分析保费与IRR的关系
        
        Args:
            df: 包含保费和IRR数据的数据框
            
        Returns:
            分析结果
        """
        results = {}
        
        premium_cols = [col for col in df.columns if 'premium' in col.lower()]
        irr_cols = [col for col in df.columns if 'irr' in col.lower()]
        
        if not premium_cols or not irr_cols:
            return {'error': '缺少保费或IRR相关列'}
        
        premium_col = premium_cols[0]
        irr_col = irr_cols[0]
        
        results['pearson'] = self.pearson_correlation(df, premium_col, irr_col)
        results['spearman'] = self.spearman_correlation(df, premium_col, irr_col)
        
        df_copy = df.copy()
        df_copy['premium_quartile'] = pd.qcut(df_copy[premium_col], q=4, 
                                              labels=['低', '中低', '中高', '高'], 
                                              duplicates='drop')
        
        quartile_stats = df_copy.groupby('premium_quartile')[irr_col].agg(['mean', 'std', 'count'])
        results['by_premium_quartile'] = quartile_stats.to_dict()
        
        results['interpretation'] = self._interpret_premium_irr(results)
        
        return results
    
    def find_key_drivers(self,
                        df: pd.DataFrame,
                        target_col: str,
                        feature_cols: Optional[List[str]] = None,
                        top_n: int = 5) -> Dict[str, Any]:
        """
        找出影响目标变量的关键驱动因素
        
        Args:
            df: 数据框
            target_col: 目标变量
            feature_cols: 特征列，默认所有数值列
            top_n: 返回前N个最重要的因素
            
        Returns:
            关键驱动因素分析结果
        """
        if target_col not in df.columns:
            return {'error': f'目标列 {target_col} 不存在'}
        
        if feature_cols is None:
            feature_cols = [col for col in df.select_dtypes(include=[np.number]).columns 
                          if col != target_col]
        
        correlations = []
        for col in feature_cols:
            result = self.pearson_correlation(df, col, target_col)
            if 'error' not in result:
                correlations.append({
                    'feature': col,
                    'correlation': result['correlation'],
                    'abs_correlation': abs(result['correlation']),
                    'p_value': result['p_value'],
                    'significant': result['significant']
                })
        
        correlations.sort(key=lambda x: x['abs_correlation'], reverse=True)
        top_drivers = correlations[:top_n]
        
        results = {
            'target': target_col,
            'top_drivers': top_drivers,
            'all_correlations': correlations,
            'summary': {
                'total_features_analyzed': len(correlations),
                'significant_features': sum(1 for c in correlations if c['significant']),
                'strong_correlations': sum(1 for c in correlations if c['abs_correlation'] > 0.5)
            }
        }
        
        return results
    
    def _interpret_premium_irr(self, results: Dict) -> str:
        """
        解释保费与IRR的关系
        """
        pearson = results.get('pearson', {})
        spearman = results.get('spearman', {})
        
        if 'error' in pearson:
            return "无法分析保费与IRR的关系"
        
        p_corr = pearson.get('correlation', 0)
        p_significant = pearson.get('significant', False)
        
        if not p_significant:
            return "保费与IRR之间不存在显著的相关关系"
        
        direction = "正相关" if p_corr > 0 else "负相关"
        strength = pearson.get('strength', '弱')
        
        return f"保费与IRR之间存在显著的{direction}关系（{strength}），相关系数为{p_corr:.3f}"
    
    def generate_report(self) -> str:
        """
        生成相关性分析报告
        """
        if not self.correlation_results:
            return "尚未执行相关性分析"
        
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("相关性分析报告")
        report_lines.append("=" * 60)
        
        for name, result in self.correlation_results.items():
            report_lines.append(f"\n【{name}】")
            if 'interpretation' in result:
                report_lines.append(f"  {result['interpretation']}")
            elif 'correlation' in result:
                report_lines.append(f"  相关系数: {result['correlation']:.3f}")
                report_lines.append(f"  P值: {result['p_value']:.4f}")
                report_lines.append(f"  显著性: {'显著' if result.get('significant') else '不显著'}")
        
        report_lines.append("\n" + "=" * 60)
        
        return "\n".join(report_lines)
