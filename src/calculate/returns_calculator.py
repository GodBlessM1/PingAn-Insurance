"""
收益率计算模块
实现各类收益指标的计算
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class ReturnsCalculator:
    """
    收益率计算器
    
    计算各类收益指标：
    - 年化现金价值回报率
    - 分红收益率
    - 累计收益率
    - 简单收益率
    """
    
    def __init__(self, annualization_method: str = 'compound'):
        """
        初始化收益率计算器
        
        Args:
            annualization_method: 年化方法 ('compound' 或 'simple')
        """
        self.annualization_method = annualization_method
        
    def calculate_annual_return(self,
                                initial_value: float,
                                final_value: float,
                                years: float) -> Optional[float]:
        """
        计算年化收益率
        
        Args:
            initial_value: 初始值
            final_value: 最终值
            years: 投资年限
            
        Returns:
            年化收益率
        """
        if initial_value <= 0 or years <= 0:
            return None
        
        total_return = (final_value - initial_value) / initial_value
        
        if self.annualization_method == 'compound':
            # 复利年化: (终值/初值)^(1/年数) - 1
            annual_return = (final_value / initial_value) ** (1 / years) - 1
        else:
            # 单利年化: 总收益 / 年数
            annual_return = total_return / years
        
        return annual_return
    
    def calculate_cash_value_return(self,
                                    cumulative_premium: float,
                                    cash_value: float,
                                    years: float) -> Dict[str, float]:
        """
        计算现金价值回报率
        
        Args:
            cumulative_premium: 累计已交保费
            cash_value: 当前现金价值
            years: 保单存续年数
            
        Returns:
            收益指标字典
        """
        if cumulative_premium <= 0 or years <= 0:
            return {
                'absolute_return': None,
                'total_return_rate': None,
                'annual_return_rate': None
            }
        
        # 绝对收益
        absolute_return = cash_value - cumulative_premium
        
        # 总收益率
        total_return_rate = absolute_return / cumulative_premium
        
        # 年化收益率
        annual_return_rate = self.calculate_annual_return(
            cumulative_premium, cash_value, years
        )
        
        return {
            'absolute_return': absolute_return,
            'total_return_rate': total_return_rate,
            'annual_return_rate': annual_return_rate
        }
    
    def calculate_dividend_return(self,
                                  cumulative_premium: float,
                                  cumulative_dividend: float,
                                  years: float) -> Dict[str, float]:
        """
        计算分红收益率 (仅适用于分红险)
        
        Args:
            cumulative_premium: 累计已交保费
            cumulative_dividend: 累计分红金额
            years: 保单存续年数
            
        Returns:
            分红收益指标字典
        """
        if cumulative_premium <= 0:
            return {
                'dividend_yield_total': None,
                'dividend_yield_annual': None
            }
        
        # 累计分红收益率
        dividend_yield_total = cumulative_dividend / cumulative_premium
        
        # 年化分红收益率
        if years > 0:
            dividend_yield_annual = dividend_yield_total / years
        else:
            dividend_yield_annual = None
        
        return {
            'dividend_yield_total': dividend_yield_total,
            'dividend_yield_annual': dividend_yield_annual
        }
    
    def calculate_universal_life_return(self,
                                        initial_account_value: float,
                                        final_account_value: float,
                                        settlement_rates: list,
                                        years: float) -> Dict[str, float]:
        """
        计算万能险收益率
        
        Args:
            initial_account_value: 期初账户价值
            final_account_value: 期末账户价值
            settlement_rates: 历年结算利率列表
            years: 存续年数
            
        Returns:
            万能险收益指标字典
        """
        if initial_account_value <= 0 or years <= 0:
            return {
                'account_growth_rate': None,
                'avg_settlement_rate': None,
                'annual_account_return': None
            }
        
        # 账户价值增长率
        account_growth_rate = (final_account_value - initial_account_value) / initial_account_value
        
        # 年化账户增长率
        annual_account_return = self.calculate_annual_return(
            initial_account_value, final_account_value, years
        )
        
        # 平均结算利率
        avg_settlement_rate = np.mean(settlement_rates) if settlement_rates else None
        
        return {
            'account_growth_rate': account_growth_rate,
            'avg_settlement_rate': avg_settlement_rate,
            'annual_account_return': annual_account_return
        }
    
    def calculate_investment_linked_return(self,
                                           initial_units: float,
                                           initial_nav: float,
                                           final_units: float,
                                           final_nav: float,
                                           years: float) -> Dict[str, float]:
        """
        计算投连险收益率
        
        Args:
            initial_units: 期初单位数
            initial_nav: 期初单位净值
            final_units: 期末单位数
            final_nav: 期末单位净值
            years: 存续年数
            
        Returns:
            投连险收益指标字典
        """
        initial_value = initial_units * initial_nav
        final_value = final_units * final_nav
        
        if initial_value <= 0 or years <= 0:
            return {
                'nav_growth_rate': None,
                'total_return_rate': None,
                'annual_return_rate': None
            }
        
        # 净值增长率
        nav_growth_rate = (final_nav - initial_nav) / initial_nav
        
        # 总收益率
        total_return_rate = (final_value - initial_value) / initial_value
        
        # 年化收益率
        annual_return_rate = self.calculate_annual_return(
            initial_value, final_value, years
        )
        
        return {
            'nav_growth_rate': nav_growth_rate,
            'total_return_rate': total_return_rate,
            'annual_return_rate': annual_return_rate
        }
    
    def calculate_comprehensive_return(self,
                                       cumulative_premium: float,
                                       cash_value: float,
                                       cumulative_dividend: float,
                                       years: float) -> Dict[str, float]:
        """
        计算综合收益率 (现金价值 + 分红)
        
        Args:
            cumulative_premium: 累计已交保费
            cash_value: 当前现金价值
            cumulative_dividend: 累计分红
            years: 存续年数
            
        Returns:
            综合收益指标字典
        """
        total_value = cash_value + cumulative_dividend
        
        if cumulative_premium <= 0 or years <= 0:
            return {
                'total_value': total_value,
                'absolute_return': None,
                'total_return_rate': None,
                'annual_return_rate': None
            }
        
        absolute_return = total_value - cumulative_premium
        total_return_rate = absolute_return / cumulative_premium
        annual_return_rate = self.calculate_annual_return(
            cumulative_premium, total_value, years
        )
        
        return {
            'total_value': total_value,
            'absolute_return': absolute_return,
            'total_return_rate': total_return_rate,
            'annual_return_rate': annual_return_rate
        }
