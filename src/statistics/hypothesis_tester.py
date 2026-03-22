"""
假设检验模块
提供各类统计假设检验功能
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class HypothesisTester:
    """
    假设检验类
    
    提供以下检验功能：
    - 均值差异检验 (t检验)
    - 方差分析 (ANOVA)
    - 分布检验 (正态性、独立性)
    - 比例检验
    """
    
    def __init__(self, alpha: float = 0.05):
        """
        初始化假设检验器
        
        Args:
            alpha: 显著性水平
        """
        self.alpha = alpha
        self.test_results = {}
        
    def compare_groups_ttest(self,
                            df: pd.DataFrame,
                            value_col: str,
                            group_col: str,
                            groups: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        使用t检验比较两组之间的均值差异
        
        Args:
            df: 数据框
            value_col: 数值列
            group_col: 分组列
            groups: 要比较的组，默认取前两组
            
        Returns:
            检验结果字典
        """
        if group_col not in df.columns or value_col not in df.columns:
            return {'error': '指定的列不存在'}
        
        unique_groups = df[group_col].unique().tolist()
        
        if groups is None:
            if len(unique_groups) < 2:
                return {'error': '分组数量不足'}
            groups = unique_groups[:2]
        
        group1_data = df[df[group_col] == groups[0]][value_col].dropna()
        group2_data = df[df[group_col] == groups[1]][value_col].dropna()
        
        if len(group1_data) < 2 or len(group2_data) < 2:
            return {'error': '数据量不足'}
        
        statistic, p_value = stats.ttest_ind(group1_data, group2_data)
        
        mean1, mean2 = group1_data.mean(), group2_data.mean()
        std1, std2 = group1_data.std(), group2_data.std()
        
        effect_size = (mean1 - mean2) / np.sqrt((std1**2 + std2**2) / 2)
        
        result = {
            'test_type': '独立样本t检验',
            'groups': groups,
            'group1_stats': {
                'n': len(group1_data),
                'mean': float(mean1),
                'std': float(std1)
            },
            'group2_stats': {
                'n': len(group2_data),
                'mean': float(mean2),
                'std': float(std2)
            },
            'mean_difference': float(mean1 - mean2),
            't_statistic': float(statistic),
            'p_value': float(p_value),
            'effect_size_cohen_d': float(effect_size),
            'significant': p_value < self.alpha,
            'conclusion': self._interpret_ttest(p_value, groups, mean1, mean2)
        }
        
        test_key = f"ttest_{groups[0]}_vs_{groups[1]}_{value_col}"
        self.test_results[test_key] = result
        
        return result
    
    def anova_test(self,
                   df: pd.DataFrame,
                   value_col: str,
                   group_col: str) -> Dict[str, Any]:
        """
        单因素方差分析 (ANOVA)
        
        Args:
            df: 数据框
            value_col: 数值列
            group_col: 分组列
            
        Returns:
            ANOVA结果
        """
        if group_col not in df.columns or value_col not in df.columns:
            return {'error': '指定的列不存在'}
        
        groups = df[group_col].unique()
        
        if len(groups) < 3:
            return {'error': 'ANOVA需要至少3个分组'}
        
        group_data = [df[df[group_col] == g][value_col].dropna() for g in groups]
        group_data = [g for g in group_data if len(g) >= 2]
        
        if len(group_data) < 3:
            return {'error': '有效分组数量不足'}
        
        statistic, p_value = stats.f_oneway(*group_data)
        
        group_stats = {}
        for g in groups:
            g_data = df[df[group_col] == g][value_col].dropna()
            if len(g_data) >= 2:
                group_stats[str(g)] = {
                    'n': len(g_data),
                    'mean': float(g_data.mean()),
                    'std': float(g_data.std())
                }
        
        total_mean = df[value_col].mean()
        ss_between = sum(len(df[df[group_col] == g][value_col].dropna()) * 
                        (df[df[group_col] == g][value_col].mean() - total_mean)**2 
                        for g in groups)
        ss_within = sum(((df[df[group_col] == g][value_col] - 
                         df[df[group_col] == g][value_col].mean())**2).sum() 
                       for g in groups)
        
        eta_squared = ss_between / (ss_between + ss_within) if (ss_between + ss_within) > 0 else 0
        
        result = {
            'test_type': '单因素方差分析 (ANOVA)',
            'value_column': value_col,
            'group_column': group_col,
            'number_of_groups': len(group_stats),
            'group_statistics': group_stats,
            'f_statistic': float(statistic),
            'p_value': float(p_value),
            'eta_squared': float(eta_squared),
            'significant': p_value < self.alpha,
            'conclusion': self._interpret_anova(p_value, group_stats)
        }
        
        test_key = f"anova_{group_col}_{value_col}"
        self.test_results[test_key] = result
        
        return result
    
    def normality_test(self, data: pd.Series, test_type: str = 'shapiro') -> Dict[str, Any]:
        """
        正态性检验
        
        Args:
            data: 数据序列
            test_type: 检验类型 ('shapiro', 'kstest', 'normaltest')
            
        Returns:
            检验结果
        """
        data = data.dropna()
        
        if len(data) < 3:
            return {'error': '数据量不足'}
        
        if test_type == 'shapiro':
            if len(data) > 5000:
                data = data.sample(5000, random_state=42)
            statistic, p_value = stats.shapiro(data)
            test_name = 'Shapiro-Wilk检验'
        elif test_type == 'kstest':
            statistic, p_value = stats.kstest(data, 'norm', args=(data.mean(), data.std()))
            test_name = 'Kolmogorov-Smirnov检验'
        else:
            statistic, p_value = stats.normaltest(data)
            test_name = "D'Agostino-Pearson检验"
        
        result = {
            'test_type': test_name,
            'n': len(data),
            'statistic': float(statistic),
            'p_value': float(p_value),
            'is_normal': p_value >= self.alpha,
            'conclusion': '数据服从正态分布' if p_value >= self.alpha else '数据不服从正态分布'
        }
        
        return result
    
    def compare_irr_by_category(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        比较不同产品类别的IRR差异
        
        Args:
            df: 包含irr和product_category的数据框
            
        Returns:
            分析结果
        """
        if 'irr' not in df.columns or 'product_category' not in df.columns:
            return {'error': '缺少必要的列'}
        
        categories = df['product_category'].unique()
        
        if len(categories) < 2:
            return {'error': '产品类别数量不足'}
        
        results = {
            'descriptive_stats': {},
            'pairwise_comparisons': [],
            'anova_result': None,
            'summary': {}
        }
        
        for cat in categories:
            cat_data = df[df['product_category'] == cat]['irr'].dropna()
            results['descriptive_stats'][cat] = {
                'n': len(cat_data),
                'mean': float(cat_data.mean()),
                'std': float(cat_data.std()),
                'median': float(cat_data.median()),
                'min': float(cat_data.min()),
                'max': float(cat_data.max())
            }
        
        if len(categories) >= 3:
            results['anova_result'] = self.anova_test(df, 'irr', 'product_category')
        elif len(categories) == 2:
            results['pairwise_comparisons'].append(
                self.compare_groups_ttest(df, 'irr', 'product_category', list(categories))
            )
        
        ranked = sorted(results['descriptive_stats'].items(), 
                       key=lambda x: x[1]['mean'], reverse=True)
        results['summary'] = {
            'highest_irr_category': ranked[0][0],
            'highest_irr_mean': ranked[0][1]['mean'],
            'lowest_irr_category': ranked[-1][0],
            'lowest_irr_mean': ranked[-1][1]['mean'],
            'irr_range': ranked[0][1]['mean'] - ranked[-1][1]['mean']
        }
        
        return results
    
    def _interpret_ttest(self, p_value: float, groups: List, mean1: float, mean2: float) -> str:
        """
        解释t检验结果
        """
        if p_value < self.alpha:
            higher = groups[0] if mean1 > mean2 else groups[1]
            return f"在α={self.alpha}水平下，两组均值存在显著差异，{higher}组的均值更高"
        else:
            return f"在α={self.alpha}水平下，两组均值无显著差异"
    
    def _interpret_anova(self, p_value: float, group_stats: Dict) -> str:
        """
        解释ANOVA结果
        """
        if p_value < self.alpha:
            return f"在α={self.alpha}水平下，各组均值存在显著差异，建议进行事后多重比较"
        else:
            return f"在α={self.alpha}水平下，各组均值无显著差异"
    
    def get_all_results(self) -> Dict[str, Any]:
        """
        获取所有检验结果
        """
        return self.test_results
    
    def generate_report(self) -> str:
        """
        生成文本格式的假设检验报告
        """
        if not self.test_results:
            return "尚未执行任何假设检验"
        
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("假设检验报告")
        report_lines.append("=" * 60)
        report_lines.append(f"显著性水平: α = {self.alpha}")
        report_lines.append("")
        
        for test_name, result in self.test_results.items():
            report_lines.append(f"【{result.get('test_type', test_name)}】")
            
            if 'error' in result:
                report_lines.append(f"  错误: {result['error']}")
            else:
                if 'groups' in result:
                    report_lines.append(f"  比较组: {result['groups']}")
                if 'p_value' in result:
                    report_lines.append(f"  P值: {result['p_value']:.4f}")
                if 'significant' in result:
                    sig_text = "显著" if result['significant'] else "不显著"
                    report_lines.append(f"  结果: {sig_text}")
                if 'conclusion' in result:
                    report_lines.append(f"  结论: {result['conclusion']}")
            
            report_lines.append("")
        
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
