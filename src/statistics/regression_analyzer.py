"""
回归分析模块
提供线性回归和多元回归分析功能
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class RegressionAnalyzer:
    """
    回归分析类
    
    提供以下分析功能：
    - 简单线性回归
    - 多元线性回归
    - 模型诊断
    - 预测分析
    """
    
    def __init__(self, alpha: float = 0.05):
        """
        初始化回归分析器
        
        Args:
            alpha: 显著性水平
        """
        self.alpha = alpha
        self.models = {}
        
    def simple_linear_regression(self,
                                 df: pd.DataFrame,
                                 x_col: str,
                                 y_col: str) -> Dict[str, Any]:
        """
        简单线性回归分析
        
        Args:
            df: 数据框
            x_col: 自变量列
            y_col: 因变量列
            
        Returns:
            回归分析结果
        """
        if x_col not in df.columns or y_col not in df.columns:
            return {'error': '指定的列不存在'}
        
        data = df[[x_col, y_col]].dropna()
        
        if len(data) < 3:
            return {'error': '数据量不足'}
        
        x = data[x_col].values
        y = data[y_col].values
        
        n = len(x)
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        y_pred = intercept + slope * x
        residuals = y - y_pred
        
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r_squared = 1 - (ss_res / ss_tot)
        
        mse = ss_res / (n - 2)
        rmse = np.sqrt(mse)
        
        t_stat = slope / std_err
        slope_p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
        
        se_intercept = rmse * np.sqrt(1/n + np.mean(x)**2 / np.sum((x - np.mean(x))**2))
        
        result = {
            'model_type': '简单线性回归',
            'dependent_variable': y_col,
            'independent_variable': x_col,
            'n': n,
            'coefficients': {
                'intercept': float(intercept),
                'slope': float(slope)
            },
            'standard_errors': {
                'intercept': float(se_intercept),
                'slope': float(std_err)
            },
            'r_squared': float(r_squared),
            'adjusted_r_squared': float(r_squared),
            'correlation': float(r_value),
            'rmse': float(rmse),
            'p_value': float(p_value),
            'slope_significant': slope_p_value < self.alpha,
            'equation': f"{y_col} = {intercept:.4f} + {slope:.4f} * {x_col}",
            'interpretation': self._interpret_simple_regression(
                slope, r_squared, p_value, x_col, y_col
            ),
            'diagnostics': {
                'residuals_mean': float(np.mean(residuals)),
                'residuals_std': float(np.std(residuals)),
                'durbin_watson': self._durbin_watson(residuals)
            }
        }
        
        model_key = f"simple_{x_col}_{y_col}"
        self.models[model_key] = {
            'type': 'simple',
            'intercept': intercept,
            'slope': slope,
            'x_col': x_col,
            'y_col': y_col
        }
        
        return result
    
    def multiple_linear_regression(self,
                                   df: pd.DataFrame,
                                   y_col: str,
                                   x_cols: List[str]) -> Dict[str, Any]:
        """
        多元线性回归分析
        
        Args:
            df: 数据框
            y_col: 因变量列
            x_cols: 自变量列列表
            
        Returns:
            回归分析结果
        """
        if y_col not in df.columns:
            return {'error': f'因变量 {y_col} 不存在'}
        
        missing_cols = [col for col in x_cols if col not in df.columns]
        if missing_cols:
            return {'error': f'自变量不存在: {missing_cols}'}
        
        all_cols = [y_col] + x_cols
        data = df[all_cols].dropna()
        
        if len(data) < len(x_cols) + 2:
            return {'error': '数据量不足'}
        
        y = data[y_col].values
        X = data[x_cols].values
        
        X = np.column_stack([np.ones(len(X)), X])
        
        try:
            beta = np.linalg.lstsq(X, y, rcond=None)[0]
        except np.linalg.LinAlgError:
            return {'error': '矩阵计算失败，可能存在多重共线性'}
        
        y_pred = X @ beta
        residuals = y - y_pred
        
        n = len(y)
        p = len(x_cols)
        
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        ss_reg = ss_tot - ss_res
        
        r_squared = 1 - (ss_res / ss_tot)
        adjusted_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - p - 1)
        
        mse = ss_res / (n - p - 1)
        rmse = np.sqrt(mse)
        
        try:
            var_beta = mse * np.linalg.inv(X.T @ X)
            se_beta = np.sqrt(np.diag(var_beta))
        except np.linalg.LinAlgError:
            se_beta = np.zeros(len(beta))
        
        t_stats = beta / se_beta
        p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), n - p - 1))
        
        f_stat = (ss_reg / p) / (ss_res / (n - p - 1))
        f_p_value = 1 - stats.f.cdf(f_stat, p, n - p - 1)
        
        coefficients = {
            'intercept': float(beta[0]),
            **{col: float(beta[i+1]) for i, col in enumerate(x_cols)}
        }
        
        standard_errors = {
            'intercept': float(se_beta[0]),
            **{col: float(se_beta[i+1]) for i, col in enumerate(x_cols)}
        }
        
        p_values_dict = {
            'intercept': float(p_values[0]),
            **{col: float(p_values[i+1]) for i, col in enumerate(x_cols)}
        }
        
        significant_vars = [col for i, col in enumerate(x_cols) 
                          if p_values[i+1] < self.alpha]
        
        equation_parts = [f"{coefficients['intercept']:.4f}"]
        for col in x_cols:
            coef = coefficients[col]
            sign = '+' if coef >= 0 else '-'
            equation_parts.append(f"{sign} {abs(coef):.4f} * {col}")
        equation = f"{y_col} = " + " ".join(equation_parts)
        
        result = {
            'model_type': '多元线性回归',
            'dependent_variable': y_col,
            'independent_variables': x_cols,
            'n': n,
            'n_predictors': p,
            'coefficients': coefficients,
            'standard_errors': standard_errors,
            'p_values': p_values_dict,
            'significant_variables': significant_vars,
            'r_squared': float(r_squared),
            'adjusted_r_squared': float(adjusted_r_squared),
            'rmse': float(rmse),
            'f_statistic': float(f_stat),
            'f_p_value': float(f_p_value),
            'model_significant': f_p_value < self.alpha,
            'equation': equation,
            'interpretation': self._interpret_multiple_regression(
                r_squared, adjusted_r_squared, f_p_value, significant_vars, y_col
            ),
            'diagnostics': {
                'residuals_mean': float(np.mean(residuals)),
                'residuals_std': float(np.std(residuals)),
                'durbin_watson': self._durbin_watson(residuals),
                'condition_number': float(np.linalg.cond(X))
            }
        }
        
        model_key = f"multiple_{'_'.join(x_cols)}_{y_col}"
        self.models[model_key] = {
            'type': 'multiple',
            'coefficients': beta,
            'x_cols': x_cols,
            'y_col': y_col
        }
        
        return result
    
    def predict(self, model_key: str, X: pd.DataFrame) -> np.ndarray:
        """
        使用已拟合的模型进行预测
        
        Args:
            model_key: 模型键名
            X: 预测数据
            
        Returns:
            预测值数组
        """
        if model_key not in self.models:
            raise ValueError(f"模型 {model_key} 不存在")
        
        model = self.models[model_key]
        
        if model['type'] == 'simple':
            return model['intercept'] + model['slope'] * X[model['x_col']].values
        else:
            X_values = X[model['x_cols']].values
            X_with_intercept = np.column_stack([np.ones(len(X_values)), X_values])
            return X_with_intercept @ model['coefficients']
    
    def analyze_irr_drivers(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        分析IRR的关键驱动因素
        
        Args:
            df: 包含IRR和相关变量的数据框
            
        Returns:
            分析结果
        """
        if 'irr' not in df.columns:
            return {'error': '缺少IRR列'}
        
        potential_drivers = [
            'annual_premium', 'payment_term', 'sum_assured', 
            'insured_age', 'issue_year', 'cumulative_premium'
        ]
        
        available_drivers = [col for col in potential_drivers if col in df.columns]
        
        if len(available_drivers) < 2:
            return {'error': '可用的驱动因素变量不足'}
        
        results = {
            'simple_regressions': {},
            'multiple_regression': None,
            'summary': {}
        }
        
        for driver in available_drivers:
            result = self.simple_linear_regression(df, driver, 'irr')
            if 'error' not in result:
                results['simple_regressions'][driver] = result
        
        results['multiple_regression'] = self.multiple_linear_regression(
            df, 'irr', available_drivers
        )
        
        sorted_drivers = sorted(
            results['simple_regressions'].items(),
            key=lambda x: x[1].get('r_squared', 0),
            reverse=True
        )
        
        results['summary'] = {
            'top_driver': sorted_drivers[0][0] if sorted_drivers else None,
            'top_driver_r_squared': sorted_drivers[0][1].get('r_squared', 0) if sorted_drivers else 0,
            'model_r_squared': results['multiple_regression'].get('r_squared', 0) if results['multiple_regression'] else 0,
            'significant_drivers': results['multiple_regression'].get('significant_variables', []) if results['multiple_regression'] else []
        }
        
        return results
    
    def _durbin_watson(self, residuals: np.ndarray) -> float:
        """
        计算Durbin-Watson统计量
        """
        diff = np.diff(residuals)
        return np.sum(diff**2) / np.sum(residuals**2)
    
    def _interpret_simple_regression(self, 
                                     slope: float, 
                                     r_squared: float, 
                                     p_value: float,
                                     x_col: str,
                                     y_col: str) -> str:
        """
        解释简单线性回归结果
        """
        if p_value >= self.alpha:
            return f"{x_col}对{y_col}的影响不显著"
        
        direction = "正向" if slope > 0 else "负向"
        
        if r_squared < 0.1:
            explanatory = "解释力较弱"
        elif r_squared < 0.3:
            explanatory = "具有一定的解释力"
        elif r_squared < 0.5:
            explanatory = "具有中等解释力"
        else:
            explanatory = "具有较强的解释力"
        
        return f"{x_col}对{y_col}存在显著的{direction}影响，模型{explanatory}(R²={r_squared:.3f})"
    
    def _interpret_multiple_regression(self,
                                       r_squared: float,
                                       adj_r_squared: float,
                                       f_p_value: float,
                                       significant_vars: List[str],
                                       y_col: str) -> str:
        """
        解释多元线性回归结果
        """
        if f_p_value >= self.alpha:
            return f"整体模型不显著，无法有效解释{y_col}的变化"
        
        n_significant = len(significant_vars)
        
        if r_squared < 0.3:
            fit = "拟合效果一般"
        elif r_squared < 0.5:
            fit = "拟合效果中等"
        elif r_squared < 0.7:
            fit = "拟合效果较好"
        else:
            fit = "拟合效果很好"
        
        if n_significant == 0:
            return f"模型整体显著但无显著变量，可能存在多重共线性"
        
        return f"模型{fit}，{n_significant}个变量显著影响{y_col}，显著变量: {', '.join(significant_vars)}"
    
    def generate_report(self) -> str:
        """
        生成回归分析报告
        """
        if not self.models:
            return "尚未建立任何回归模型"
        
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("回归分析报告")
        report_lines.append("=" * 60)
        
        for model_name, model_info in self.models.items():
            report_lines.append(f"\n【模型: {model_name}】")
            report_lines.append(f"  类型: {model_info['type']}")
            report_lines.append(f"  因变量: {model_info['y_col']}")
            
            if model_info['type'] == 'simple':
                report_lines.append(f"  自变量: {model_info['x_col']}")
                report_lines.append(f"  方程: y = {model_info['intercept']:.4f} + {model_info['slope']:.4f}x")
            else:
                report_lines.append(f"  自变量: {', '.join(model_info['x_cols'])}")
        
        report_lines.append("\n" + "=" * 60)
        
        return "\n".join(report_lines)
