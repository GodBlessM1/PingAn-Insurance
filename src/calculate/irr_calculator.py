"""
IRR (内部收益率) 计算模块
使用numpy-financial实现现金流IRR计算
"""

import numpy as np
import numpy_financial as npf
from typing import List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class IRRCalculator:
    """
    IRR计算类
    
    提供多种IRR计算方法：
    - 标准IRR (基于numpy_financial)
    - XIRR (考虑时间权重的IRR)
    - 修正IRR (MIRR)
    """
    
    def __init__(self, max_iterations: int = 1000, tolerance: float = 1e-6):
        """
        初始化IRR计算器
        
        Args:
            max_iterations: 最大迭代次数
            tolerance: 收敛容差
        """
        self.max_iterations = max_iterations
        self.tolerance = tolerance
        
    def calculate_irr(self, cashflows: List[float], policy_id: str = None) -> Optional[float]:
        """
        计算标准IRR
        
        Args:
            cashflows: 现金流列表 (负数为流出，正数为流入)
            policy_id: 保单ID (用于日志)
            
        Returns:
            IRR值 (年化)，计算失败返回None
        """
        try:
            if len(cashflows) < 2:
                logger.debug(f"保单 {policy_id or 'unknown'}: 观察期不足2年，跳过IRR计算")
                return None
            
            has_negative = any(cf < 0 for cf in cashflows)
            has_positive = any(cf > 0 for cf in cashflows)
            
            if not (has_negative and has_positive):
                logger.debug(f"保单 {policy_id or 'unknown'}: 现金流无正负变化，跳过IRR计算")
                return None
            
            irr = npf.irr(cashflows)
            
            if np.isnan(irr) or np.isinf(irr):
                logger.debug(f"保单 {policy_id or 'unknown'}: IRR计算结果无效")
                return None
            
            return float(irr)
            
        except Exception as e:
            logger.debug(f"保单 {policy_id or 'unknown'}: IRR计算异常 - {str(e)}")
            return None
    
    def calculate_xirr(self, 
                       dates: List,
                       cashflows: List[float]) -> Optional[float]:
        """
        计算XIRR (考虑时间权重的IRR)
        
        Args:
            dates: 日期列表
            cashflows: 现金流列表
            
        Returns:
            XIRR值 (年化)
        """
        try:
            from datetime import datetime
            
            if len(dates) != len(cashflows):
                raise ValueError("日期和现金流数量不匹配")
            
            # 转换为datetime
            dates = [pd.to_datetime(d) for d in dates]
            
            # 计算天数差
            base_date = dates[0]
            days = [(d - base_date).days for d in dates]
            
            # 使用牛顿迭代法求解XIRR
            guess = 0.1
            for _ in range(self.max_iterations):
                # 计算NPV
                npv = sum(
                    cf / ((1 + guess) ** (day / 365.0))
                    for cf, day in zip(cashflows, days)
                )
                
                # 计算导数
                d_npv = sum(
                    -cf * (day / 365.0) / ((1 + guess) ** ((day / 365.0) + 1))
                    for cf, day in zip(cashflows, days)
                )
                
                if abs(d_npv) < 1e-10:
                    break
                
                new_guess = guess - npv / d_npv
                
                if abs(new_guess - guess) < self.tolerance:
                    return float(new_guess)
                
                guess = new_guess
            
            return float(guess)
            
        except Exception as e:
            logger.error(f"XIRR计算异常: {str(e)}")
            return None
    
    def calculate_mirr(self,
                       cashflows: List[float],
                       finance_rate: float = 0.05,
                       reinvest_rate: float = 0.05) -> Optional[float]:
        """
        计算修正IRR (MIRR)
        
        考虑不同的融资利率和再投资利率
        
        Args:
            cashflows: 现金流列表
            finance_rate: 融资成本率
            reinvest_rate: 再投资收益率
            
        Returns:
            MIRR值
        """
        try:
            # 分离正负现金流
            negative_flows = [cf if cf < 0 else 0 for cf in cashflows]
            positive_flows = [cf if cf > 0 else 0 for cf in cashflows]
            
            n = len(cashflows)
            
            # 计算负现金流的现值 (PV)
            pv = sum(
                cf / ((1 + finance_rate) ** i)
                for i, cf in enumerate(negative_flows)
            )
            
            # 计算正现金流的终值 (FV)
            fv = sum(
                cf * ((1 + reinvest_rate) ** (n - 1 - i))
                for i, cf in enumerate(positive_flows)
            )
            
            if pv == 0 or fv == 0:
                return None
            
            # 计算MIRR
            mirr = (fv / abs(pv)) ** (1 / (n - 1)) - 1
            
            return float(mirr)
            
        except Exception as e:
            logger.error(f"MIRR计算异常: {str(e)}")
            return None
    
    def calculate_npv(self, 
                      rate: float,
                      cashflows: List[float]) -> float:
        """
        计算净现值 (NPV)
        
        Args:
            rate: 折现率
            cashflows: 现金流列表
            
        Returns:
            NPV值
        """
        return npf.npv(rate, cashflows)
    
    def batch_calculate_irr(self, 
                           cashflow_groups: List[List[float]]) -> List[Optional[float]]:
        """
        批量计算IRR
        
        Args:
            cashflow_groups: 多组现金流
            
        Returns:
            IRR结果列表
        """
        results = []
        for i, cashflows in enumerate(cashflow_groups):
            irr = self.calculate_irr(cashflows)
            results.append(irr)
            
            if i % 1000 == 0:
                logger.info(f"已计算 {i}/{len(cashflow_groups)} 个IRR")
        
        return results


# 导入pandas用于XIRR
try:
    import pandas as pd
except ImportError:
    pd = None
