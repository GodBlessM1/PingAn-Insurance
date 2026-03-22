"""
保单收益计算器
整合IRR和收益率计算，按险种类型计算保单收益
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

from .irr_calculator import IRRCalculator
from .returns_calculator import ReturnsCalculator

logger = logging.getLogger(__name__)


class PolicyCalculator:
    """
    保单收益计算器
    
    针对不同险种类型计算收益：
    - 传统寿险: IRR + 现金价值回报率
    - 分红险: IRR + 现金价值回报率 + 分红收益率
    - 万能险: IRR + 账户价值增长率
    - 投连险: IRR + 单位净值增长率
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化保单计算器
        
        Args:
            config: 计算配置
        """
        self.config = config or {}
        self.irr_calc = IRRCalculator(
            max_iterations=self.config.get('max_iterations', 1000),
            tolerance=self.config.get('tolerance', 1e-6)
        )
        self.returns_calc = ReturnsCalculator(
            annualization_method=self.config.get('annualization_method', 'compound')
        )
        
    def calculate_policy_returns(self,
                                  policy_data: pd.Series,
                                  cashflow_data: pd.DataFrame) -> Dict[str, float]:
        """
        计算单个保单的收益指标
        
        Args:
            policy_data: 保单信息 (Series)
            cashflow_data: 该保单的现金流数据
            
        Returns:
            收益指标字典
        """
        policy_id = policy_data.get('policy_id', 'unknown')
        product_category = policy_data.get('product_category', '其他')
        
        logger.debug(f"计算保单 {policy_id} ({product_category}) 的收益")
        
        # 根据险种类型选择计算方法
        if '分红' in product_category:
            return self._calculate_participating_returns(policy_data, cashflow_data)
        elif '万能' in product_category:
            return self._calculate_universal_life_returns(policy_data, cashflow_data)
        elif '投连' in product_category:
            return self._calculate_investment_linked_returns(policy_data, cashflow_data)
        else:
            return self._calculate_traditional_returns(policy_data, cashflow_data)
    
    def _calculate_traditional_returns(self,
                                       policy_data: pd.Series,
                                       cashflow_data: pd.DataFrame) -> Dict[str, float]:
        """
        计算传统寿险收益
        
        Args:
            policy_data: 保单信息
            cashflow_data: 现金流数据
            
        Returns:
            收益指标字典
        """
        policy_id = policy_data.get('policy_id', 'unknown')
        results = {}
        
        cashflows = self._build_cashflow_series(cashflow_data)
        results['irr'] = self.irr_calc.calculate_irr(cashflows, policy_id)
        
        # 2. 计算现金价值回报率
        cumulative_premium = policy_data.get('cumulative_premium', 0)
        cash_value = policy_data.get('latest_cash_value', 0)
        years = policy_data.get('observation_years', 0)
        
        cv_returns = self.returns_calc.calculate_cash_value_return(
            cumulative_premium, cash_value, years
        )
        results.update(cv_returns)
        
        # 3. 标记险种类型
        results['product_category'] = '传统寿险'
        
        return results
    
    def _calculate_participating_returns(self,
                                         policy_data: pd.Series,
                                         cashflow_data: pd.DataFrame) -> Dict[str, float]:
        """
        计算分红险收益
        
        Args:
            policy_data: 保单信息
            cashflow_data: 现金流数据
            
        Returns:
            收益指标字典
        """
        policy_id = policy_data.get('policy_id', 'unknown')
        results = {}
        
        cashflows = self._build_cashflow_series_with_dividend(cashflow_data)
        results['irr'] = self.irr_calc.calculate_irr(cashflows, policy_id)
        
        # 2. 基础信息
        cumulative_premium = policy_data.get('cumulative_premium', 0)
        cash_value = policy_data.get('latest_cash_value', 0)
        cumulative_dividend = policy_data.get('cumulative_dividend', 0)
        years = policy_data.get('observation_years', 0)
        
        # 3. 现金价值回报率
        cv_returns = self.returns_calc.calculate_cash_value_return(
            cumulative_premium, cash_value, years
        )
        results.update({f'cv_{k}': v for k, v in cv_returns.items()})
        
        # 4. 分红收益率
        div_returns = self.returns_calc.calculate_dividend_return(
            cumulative_premium, cumulative_dividend, years
        )
        results.update(div_returns)
        
        # 5. 综合收益率 (现金价值 + 分红)
        comprehensive = self.returns_calc.calculate_comprehensive_return(
            cumulative_premium, cash_value, cumulative_dividend, years
        )
        results.update({f'total_{k}': v for k, v in comprehensive.items()})
        
        # 6. 标记险种类型
        results['product_category'] = '分红险'
        
        return results
    
    def _calculate_universal_life_returns(self,
                                          policy_data: pd.Series,
                                          cashflow_data: pd.DataFrame) -> Dict[str, float]:
        """
        计算万能险收益
        
        Args:
            policy_data: 保单信息
            cashflow_data: 现金流数据
            
        Returns:
            收益指标字典
        """
        policy_id = policy_data.get('policy_id', 'unknown')
        results = {}
        
        cashflows = self._build_cashflow_series(cashflow_data)
        results['irr'] = self.irr_calc.calculate_irr(cashflows, policy_id)
        
        # 2. 基础信息
        cumulative_premium = policy_data.get('cumulative_premium', 0)
        cash_value = policy_data.get('latest_cash_value', 0)
        years = policy_data.get('observation_years', 0)
        
        # 3. 计算账户价值相关指标
        # 假设第一年现金价值为初始账户价值
        initial_value = cashflow_data['cash_value_eoy'].iloc[0] if len(cashflow_data) > 0 else 0
        
        ul_returns = self.returns_calc.calculate_universal_life_return(
            initial_value, cash_value,
            settlement_rates=[],  # 可从外部传入
            years=years
        )
        results.update(ul_returns)
        
        # 4. 标记险种类型
        results['product_category'] = '万能险'
        
        return results
    
    def _calculate_investment_linked_returns(self,
                                             policy_data: pd.Series,
                                             cashflow_data: pd.DataFrame) -> Dict[str, float]:
        """
        计算投连险收益
        
        Args:
            policy_data: 保单信息
            cashflow_data: 现金流数据
            
        Returns:
            收益指标字典
        """
        policy_id = policy_data.get('policy_id', 'unknown')
        results = {}
        
        cashflows = self._build_cashflow_series(cashflow_data)
        results['irr'] = self.irr_calc.calculate_irr(cashflows, policy_id)
        
        # 2. 基础信息
        years = policy_data.get('observation_years', 0)
        
        # 3. 计算投连险特定指标
        # 需要单位净值数据，这里简化处理
        if len(cashflow_data) >= 2:
            initial_value = cashflow_data['cash_value_eoy'].iloc[0]
            final_value = cashflow_data['cash_value_eoy'].iloc[-1]
            
            il_returns = self.returns_calc.calculate_investment_linked_return(
                initial_units=1, initial_nav=initial_value,
                final_units=1, final_nav=final_value,
                years=years
            )
            results.update(il_returns)
        
        # 4. 标记险种类型
        results['product_category'] = '投连险'
        
        return results
    
    def _build_cashflow_series(self, cashflow_data: pd.DataFrame) -> List[float]:
        """
        构建现金流序列 (用于IRR计算)
        
        Args:
            cashflow_data: 现金流数据
            
        Returns:
            现金流列表
        """
        if cashflow_data.empty:
            return []
        
        # 按年份排序
        df = cashflow_data.sort_values('year')
        
        # 构建现金流: 保费为负，现金价值为正
        cashflows = []
        for _, row in df.iterrows():
            # 保费流出 (负)
            premium = -row.get('premium_outflow', 0)
            cashflows.append(premium)
        
        # 最后一期加入现金价值 (正)
        if len(cashflows) > 0:
            final_cash_value = df['cash_value_eoy'].iloc[-1]
            cashflows[-1] += final_cash_value
        
        return cashflows
    
    def _build_cashflow_series_with_dividend(self, 
                                             cashflow_data: pd.DataFrame) -> List[float]:
        """
        构建包含分红的现金流序列
        
        Args:
            cashflow_data: 现金流数据
            
        Returns:
            现金流列表
        """
        if cashflow_data.empty:
            return []
        
        df = cashflow_data.sort_values('year')
        
        cashflows = []
        for _, row in df.iterrows():
            # 保费流出 (负) + 分红流入 (正)
            net_flow = -row.get('premium_outflow', 0) + row.get('dividend_amount', 0)
            cashflows.append(net_flow)
        
        # 最后一期加入现金价值
        if len(cashflows) > 0:
            final_cash_value = df['cash_value_eoy'].iloc[-1]
            cashflows[-1] += final_cash_value
        
        return cashflows
    
    def batch_calculate(self,
                       policies_df: pd.DataFrame,
                       cashflow_df: pd.DataFrame) -> pd.DataFrame:
        """
        批量计算保单收益
        
        Args:
            policies_df: 保单数据表
            cashflow_df: 现金流数据表
            
        Returns:
            带收益指标的保单表
        """
        logger.info(f"开始批量计算 {len(policies_df)} 个保单的收益...")
        
        results = []
        
        for idx, policy in policies_df.iterrows():
            policy_id = policy['policy_id']
            
            # 获取该保单的现金流
            policy_cashflow = cashflow_df[cashflow_df['policy_id'] == policy_id]
            
            # 计算收益
            returns = self.calculate_policy_returns(policy, policy_cashflow)
            returns['policy_id'] = policy_id
            
            results.append(returns)
            
            if (idx + 1) % 1000 == 0:
                logger.info(f"已计算 {idx + 1}/{len(policies_df)} 个保单")
        
        # 转换为DataFrame
        results_df = pd.DataFrame(results)
        
        # 移除results_df中的product_category列，保留原始数据中的
        if 'product_category' in results_df.columns:
            results_df = results_df.drop(columns=['product_category'])
        
        # 合并回原表，保留原始的product_category
        final_df = policies_df.merge(results_df, on='policy_id', how='left')
        
        logger.info(f"批量计算完成，共计算 {len(results_df)} 个保单")
        
        return final_df
