"""
风险分析模块
计算各类风险指标：波动率、VaR、夏普比率等
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class RiskAnalyzer:
    """
    风险分析器
    
    提供以下风险指标计算：
    - 波动率 (Volatility)
    - 风险价值 (VaR)
    - 条件风险价值 (CVaR)
    - 夏普比率 (Sharpe Ratio)
    - 索提诺比率 (Sortino Ratio)
    - 最大回撤 (Max Drawdown)
    - 贝塔系数 (Beta)
    """
    
    def __init__(self, risk_free_rate: float = 0.025, confidence_level: float = 0.95):
        """
        初始化风险分析器
        
        Args:
            risk_free_rate: 无风险利率（年化）
            confidence_level: 置信水平（默认95%）
        """
        self.risk_free_rate = risk_free_rate
        self.confidence_level = confidence_level
    
    def calculate_volatility(self, returns: pd.Series, annualize: bool = True) -> float:
        """
        计算波动率
        
        Args:
            returns: 收益率序列
            annualize: 是否年化
            
        Returns:
            波动率
        """
        if len(returns) < 2:
            return 0.0
        
        vol = returns.std()
        
        if annualize:
            # 假设月度数据，年化乘以sqrt(12)
            vol = vol * np.sqrt(12)
        
        return vol
    
    def calculate_var(self, returns: pd.Series, method: str = 'historical') -> float:
        """
        计算风险价值 (VaR)
        
        Args:
            returns: 收益率序列
            method: 计算方法 ('historical', 'parametric', 'monte_carlo')
            
        Returns:
            VaR值（负数表示损失）
        """
        if len(returns) < 10:
            return 0.0
        
        alpha = 1 - self.confidence_level
        
        if method == 'historical':
            # 历史模拟法
            var = np.percentile(returns, alpha * 100)
        
        elif method == 'parametric':
            # 参数法（假设正态分布）
            mean = returns.mean()
            std = returns.std()
            var = stats.norm.ppf(alpha, mean, std)
        
        elif method == 'monte_carlo':
            # 蒙特卡洛模拟
            mean = returns.mean()
            std = returns.std()
            simulations = np.random.normal(mean, std, 10000)
            var = np.percentile(simulations, alpha * 100)
        
        else:
            raise ValueError(f"未知的VaR计算方法: {method}")
        
        return var
    
    def calculate_cvar(self, returns: pd.Series) -> float:
        """
        计算条件风险价值 (CVaR/Expected Shortfall)
        
        Args:
            returns: 收益率序列
            
        Returns:
            CVaR值
        """
        if len(returns) < 10:
            return 0.0
        
        var = self.calculate_var(returns)
        cvar = returns[returns <= var].mean()
        
        return cvar if not np.isnan(cvar) else var
    
    def calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """
        计算夏普比率
        
        Args:
            returns: 收益率序列
            
        Returns:
            夏普比率
        """
        if len(returns) < 2:
            return 0.0
        
        excess_returns = returns - (self.risk_free_rate / 12)  # 月度无风险收益
        
        if excess_returns.std() == 0:
            return 0.0
        
        sharpe = excess_returns.mean() / excess_returns.std()
        
        # 年化
        sharpe = sharpe * np.sqrt(12)
        
        return sharpe
    
    def calculate_sortino_ratio(self, returns: pd.Series) -> float:
        """
        计算索提诺比率（只考虑下行波动）
        
        Args:
            returns: 收益率序列
            
        Returns:
            索提诺比率
        """
        if len(returns) < 2:
            return 0.0
        
        excess_returns = returns - (self.risk_free_rate / 12)
        
        # 下行标准差
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return float('inf') if excess_returns.mean() > 0 else 0.0
        
        downside_std = downside_returns.std()
        
        if downside_std == 0:
            return 0.0
        
        sortino = excess_returns.mean() / downside_std
        sortino = sortino * np.sqrt(12)  # 年化
        
        return sortino
    
    def calculate_max_drawdown(self, returns: pd.Series) -> Dict:
        """
        计算最大回撤
        
        Args:
            returns: 收益率序列
            
        Returns:
            包含最大回撤信息的字典
        """
        if len(returns) < 2:
            return {'max_drawdown': 0.0, 'peak_date': None, 'trough_date': None}
        
        # 计算累计收益
        cumulative = (1 + returns).cumprod()
        
        # 计算回撤
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        
        # 最大回撤
        max_dd = drawdown.min()
        
        # 找到最大回撤的峰值和谷值日期
        trough_idx = drawdown.idxmin()
        peak_idx = cumulative.loc[:trough_idx].idxmax()
        
        return {
            'max_drawdown': max_dd,
            'peak_date': peak_idx,
            'trough_date': trough_idx,
            'drawdown_duration': (trough_idx - peak_idx).days if hasattr(trough_idx, 'days') else None
        }
    
    def calculate_beta(self, returns: pd.Series, market_returns: pd.Series) -> float:
        """
        计算贝塔系数
        
        Args:
            returns: 资产收益率
            market_returns: 市场收益率
            
        Returns:
            贝塔系数
        """
        if len(returns) < 2 or len(market_returns) < 2:
            return 1.0
        
        # 对齐数据
        aligned_data = pd.DataFrame({
            'asset': returns,
            'market': market_returns
        }).dropna()
        
        if len(aligned_data) < 2:
            return 1.0
        
        # 计算协方差和方差
        covariance = aligned_data['asset'].cov(aligned_data['market'])
        market_variance = aligned_data['market'].var()
        
        if market_variance == 0:
            return 1.0
        
        beta = covariance / market_variance
        
        return beta
    
    def calculate_calmar_ratio(self, returns: pd.Series) -> float:
        """
        计算卡尔马比率（收益/最大回撤）
        
        Args:
            returns: 收益率序列
            
        Returns:
            卡尔马比率
        """
        if len(returns) < 2:
            return 0.0
        
        annual_return = returns.mean() * 12
        max_dd = self.calculate_max_drawdown(returns)['max_drawdown']
        
        if max_dd == 0:
            return float('inf') if annual_return > 0 else 0.0
        
        calmar = annual_return / abs(max_dd)
        
        return calmar
    
    def analyze_policy_risk(self, policy_returns: pd.Series) -> Dict:
        """
        综合分析保单风险
        
        Args:
            policy_returns: 保单收益率序列
            
        Returns:
            风险指标字典
        """
        logger.info("分析保单风险指标...")
        
        risk_metrics = {
            'volatility': self.calculate_volatility(policy_returns),
            'volatility_annual': self.calculate_volatility(policy_returns, annualize=True),
            'var_95': self.calculate_var(policy_returns, method='historical'),
            'cvar_95': self.calculate_cvar(policy_returns),
            'sharpe_ratio': self.calculate_sharpe_ratio(policy_returns),
            'sortino_ratio': self.calculate_sortino_ratio(policy_returns),
            'max_drawdown': self.calculate_max_drawdown(policy_returns)['max_drawdown'],
            'calmar_ratio': self.calculate_calmar_ratio(policy_returns)
        }
        
        return risk_metrics
    
    def compare_risk_by_category(self, df: pd.DataFrame, 
                                  return_col: str = 'irr',
                                  category_col: str = 'product_category') -> pd.DataFrame:
        """
        按产品类别比较风险指标
        
        Args:
            df: 数据DataFrame
            return_col: 收益率列名
            category_col: 类别列名
            
        Returns:
            风险比较表
        """
        logger.info("按产品类别比较风险...")
        
        results = []
        
        for category in df[category_col].unique():
            category_data = df[df[category_col] == category]
            returns = category_data[return_col]
            
            if len(returns) < 5:
                continue
            
            risk_metrics = self.analyze_policy_risk(returns)
            risk_metrics['product_category'] = category
            risk_metrics['sample_size'] = len(returns)
            
            results.append(risk_metrics)
        
        result_df = pd.DataFrame(results)
        
        if not result_df.empty:
            result_df = result_df.set_index('product_category')
        
        return result_df
    
    def generate_risk_report(self, returns: pd.Series, 
                            benchmark_returns: Optional[pd.Series] = None) -> Dict:
        """
        生成完整的风险分析报告
        
        Args:
            returns: 收益率序列
            benchmark_returns: 基准收益率（可选）
            
        Returns:
            风险报告字典
        """
        report = {
            'basic_metrics': {
                'mean_return': returns.mean(),
                'median_return': returns.median(),
                'std_return': returns.std(),
                'skewness': returns.skew(),
                'kurtosis': returns.kurtosis()
            },
            'risk_metrics': self.analyze_policy_risk(returns),
            'distribution_analysis': {
                'percentiles': {
                    '5%': returns.quantile(0.05),
                    '25%': returns.quantile(0.25),
                    '50%': returns.quantile(0.50),
                    '75%': returns.quantile(0.75),
                    '95%': returns.quantile(0.95)
                }
            }
        }
        
        # 如果有基准数据，计算相对指标
        if benchmark_returns is not None:
            report['relative_metrics'] = {
                'beta': self.calculate_beta(returns, benchmark_returns),
                'alpha': self._calculate_alpha(returns, benchmark_returns),
                'tracking_error': self._calculate_tracking_error(returns, benchmark_returns),
                'information_ratio': self._calculate_information_ratio(returns, benchmark_returns)
            }
        
        return report
    
    def _calculate_alpha(self, returns: pd.Series, market_returns: pd.Series) -> float:
        """计算阿尔法系数"""
        beta = self.calculate_beta(returns, market_returns)
        alpha = returns.mean() - (self.risk_free_rate / 12 + beta * (market_returns.mean() - self.risk_free_rate / 12))
        return alpha * 12  # 年化
    
    def _calculate_tracking_error(self, returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """计算跟踪误差"""
        aligned_data = pd.DataFrame({
            'asset': returns,
            'benchmark': benchmark_returns
        }).dropna()
        
        return (aligned_data['asset'] - aligned_data['benchmark']).std() * np.sqrt(12)
    
    def _calculate_information_ratio(self, returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """计算信息比率"""
        tracking_error = self._calculate_tracking_error(returns, benchmark_returns)
        
        if tracking_error == 0:
            return 0.0
        
        aligned_data = pd.DataFrame({
            'asset': returns,
            'benchmark': benchmark_returns
        }).dropna()
        
        active_return = (aligned_data['asset'] - aligned_data['benchmark']).mean() * 12
        
        return active_return / tracking_error
