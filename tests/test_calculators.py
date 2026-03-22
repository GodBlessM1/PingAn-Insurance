"""
计算器模块单元测试
测试IRR计算、收益率计算等核心功能
"""

import unittest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.calculate.irr_calculator import IRRCalculator
from src.calculate.returns_calculator import ReturnsCalculator
from src.calculate.policy_calculator import PolicyCalculator


class TestIRRCalculator(unittest.TestCase):
    """IRR计算器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.calc = IRRCalculator()
    
    def test_calculate_irr_simple(self):
        """测试简单IRR计算"""
        # 标准案例：初始投资1000，后续4年回报
        cashflows = [-1000, 300, 400, 400, 300]
        irr = self.calc.calculate_irr(cashflows, 'TEST001')
        
        self.assertIsNotNone(irr)
        self.assertGreater(irr, 0)
        # 验证IRR约等于14.5%
        self.assertAlmostEqual(irr, 0.145, places=2)
    
    def test_calculate_irr_single_period(self):
        """测试单期IRR"""
        cashflows = [-1000, 1100]
        irr = self.calc.calculate_irr(cashflows)
        
        self.assertIsNotNone(irr)
        self.assertAlmostEqual(irr, 0.10, places=5)  # 10%回报
    
    def test_calculate_irr_no_negative(self):
        """测试无负现金流情况"""
        cashflows = [100, 100, 100]
        irr = self.calc.calculate_irr(cashflows)
        
        self.assertIsNone(irr)
    
    def test_calculate_irr_no_positive(self):
        """测试无正现金流情况"""
        cashflows = [-100, -100, -100]
        irr = self.calc.calculate_irr(cashflows)
        
        self.assertIsNone(irr)
    
    def test_calculate_irr_insufficient_data(self):
        """测试数据不足"""
        cashflows = [-1000]
        irr = self.calc.calculate_irr(cashflows)
        
        self.assertIsNone(irr)
    
    def test_calculate_irr_zero_cashflow(self):
        """测试包含零现金流"""
        cashflows = [-1000, 0, 500, 600]
        irr = self.calc.calculate_irr(cashflows)
        
        self.assertIsNotNone(irr)
        self.assertGreater(irr, 0)


class TestReturnsCalculator(unittest.TestCase):
    """收益率计算器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.calc = ReturnsCalculator()
    
    def test_calculate_cash_value_return(self):
        """测试现金价值回报率计算"""
        cumulative_premium = 100000
        cash_value = 120000
        years = 5
        
        result = self.calc.calculate_cash_value_return(
            cumulative_premium, cash_value, years
        )
        
        self.assertIn('total_return_rate', result)
        self.assertIn('annual_return_rate', result)
        
        # 总回报率应为20%
        self.assertAlmostEqual(result['total_return_rate'], 0.20, places=2)
        # 年化回报率约为3.7%
        self.assertGreater(result['annual_return_rate'], 0)
    
    def test_calculate_cash_value_return_zero_premium(self):
        """测试零保费情况"""
        result = self.calc.calculate_cash_value_return(0, 1000, 5)
        
        self.assertEqual(result['total_return_rate'], 0)
        self.assertEqual(result['annual_return_rate'], 0)
    
    def test_calculate_cash_value_return_negative(self):
        """测试亏损情况"""
        result = self.calc.calculate_cash_value_return(100000, 80000, 5)
        
        self.assertLess(result['total_return_rate'], 0)
        self.assertLess(result['annual_return_rate'], 0)
    
    def test_calculate_dividend_yield(self):
        """测试分红收益率计算"""
        annual_dividend = 5000
        premium = 100000
        
        result = self.calc.calculate_dividend_yield(annual_dividend, premium)
        
        self.assertIn('dividend_yield', result)
        self.assertAlmostEqual(result['dividend_yield'], 0.05, places=5)
    
    def test_calculate_dividend_yield_zero_premium(self):
        """测试零保费分红"""
        result = self.calc.calculate_dividend_yield(5000, 0)
        
        self.assertEqual(result['dividend_yield'], 0)


class TestPolicyCalculator(unittest.TestCase):
    """保单计算器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.calc = PolicyCalculator()
    
    def test_calculate_traditional_returns(self):
        """测试传统寿险收益计算"""
        policy_data = pd.Series({
            'policy_id': 'TEST001',
            'product_category': '传统寿险',
            'cumulative_premium': 100000,
            'latest_cash_value': 115000,
            'observation_years': 5
        })
        
        # 创建现金流数据
        cashflow_data = pd.DataFrame({
            'year': [2020, 2021, 2022, 2023, 2024],
            'premium_outflow': [20000, 20000, 20000, 20000, 20000],
            'cash_value_eoy': [15000, 45000, 70000, 95000, 115000],
            'dividend_amount': [0, 0, 0, 0, 0]
        })
        
        result = self.calc._calculate_traditional_returns(policy_data, cashflow_data)
        
        self.assertIn('irr', result)
        self.assertIn('total_return_rate', result)
        self.assertIn('annual_return_rate', result)
    
    def test_calculate_participating_returns(self):
        """测试分红险收益计算"""
        policy_data = pd.Series({
            'policy_id': 'TEST002',
            'product_category': '分红险',
            'cumulative_premium': 100000,
            'latest_cash_value': 120000,
            'total_dividend': 15000,
            'observation_years': 5
        })
        
        cashflow_data = pd.DataFrame({
            'year': [2020, 2021, 2022, 2023, 2024],
            'premium_outflow': [20000, 20000, 20000, 20000, 20000],
            'cash_value_eoy': [18000, 48000, 75000, 100000, 120000],
            'dividend_amount': [2000, 3000, 3500, 3200, 3300]
        })
        
        result = self.calc._calculate_participating_returns(policy_data, cashflow_data)
        
        self.assertIn('irr', result)
        self.assertIn('total_return_rate', result)
        self.assertIn('dividend_yield', result)


class TestEdgeCases(unittest.TestCase):
    """边界情况测试"""
    
    def test_very_small_numbers(self):
        """测试极小数值"""
        calc = IRRCalculator()
        cashflows = [-0.01, 0.011]
        irr = calc.calculate_irr(cashflows)
        self.assertIsNotNone(irr)
    
    def test_very_large_numbers(self):
        """测试极大数值"""
        calc = ReturnsCalculator()
        result = calc.calculate_cash_value_return(1e9, 1.2e9, 10)
        self.assertAlmostEqual(result['total_return_rate'], 0.20, places=2)
    
    def test_empty_dataframe(self):
        """测试空DataFrame"""
        calc = PolicyCalculator()
        policy_data = pd.Series()
        cashflow_data = pd.DataFrame()
        
        # 应该抛出异常或返回None
        try:
            result = calc.calculate_policy_returns(policy_data, cashflow_data)
            # 如果执行到这里，检查结果
            self.assertIsInstance(result, dict)
        except (KeyError, IndexError):
            # 预期可能抛出异常
            pass


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestIRRCalculator))
    suite.addTests(loader.loadTestsFromTestCase(TestReturnsCalculator))
    suite.addTests(loader.loadTestsFromTestCase(TestPolicyCalculator))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
