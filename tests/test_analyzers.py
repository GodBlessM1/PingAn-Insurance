"""
分析模块单元测试
测试数据聚合、趋势分析等功能
"""

import unittest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.analyze.aggregator import DataAggregator
from src.analyze.trend_analyzer import TrendAnalyzer


class TestDataAggregator(unittest.TestCase):
    """数据聚合器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.aggregator = DataAggregator()
        
        # 创建测试数据
        np.random.seed(42)
        self.test_data = pd.DataFrame({
            'policy_id': [f'P{i:04d}' for i in range(100)],
            'product_category': np.random.choice(
                ['传统寿险', '分红险', '万能险', '投连险'], 100
            ),
            'issue_year': np.random.choice([2020, 2021, 2022, 2023], 100),
            'irr': np.random.normal(0.035, 0.015, 100),
            'annual_return_rate': np.random.normal(0.03, 0.01, 100),
            'total_return_rate': np.random.normal(0.15, 0.05, 100)
        })
    
    def test_aggregate_by_product(self):
        """测试按产品聚合"""
        result = self.aggregator.aggregate_by_product(self.test_data)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn('product_category', result.columns)
        
        # 应该有4个产品类别
        self.assertEqual(len(result), 4)
    
    def test_aggregate_by_year(self):
        """测试按年份聚合"""
        result = self.aggregator.aggregate_by_year(self.test_data)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn('issue_year', result.columns)
        
        # 应该有4个年份
        self.assertEqual(len(result), 4)
    
    def test_aggregate_by_category_year(self):
        """测试按类别和年份交叉聚合"""
        result = self.aggregator.aggregate_by_category_year(self.test_data)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn('product_category', result.columns)
        self.assertIn('issue_year', result.columns)
    
    def test_generate_summary_statistics(self):
        """测试生成汇总统计"""
        result = self.aggregator.generate_summary_statistics(self.test_data)
        
        self.assertIsInstance(result, dict)
        self.assertIn('total_policies', result)
        self.assertIn('avg_irr', result)
        self.assertIn('categories', result)
        
        self.assertEqual(result['total_policies'], 100)
    
    def test_empty_dataframe(self):
        """测试空DataFrame处理"""
        empty_df = pd.DataFrame()
        result = self.aggregator.aggregate_by_product(empty_df)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue(result.empty)
    
    def test_missing_columns(self):
        """测试缺少列的情况"""
        df = pd.DataFrame({'other_column': [1, 2, 3]})
        result = self.aggregator.aggregate_by_product(df)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue(result.empty)


class TestTrendAnalyzer(unittest.TestCase):
    """趋势分析器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.analyzer = TrendAnalyzer()
    
    def test_analyze_yearly_trend_upward(self):
        """测试上升趋势"""
        df = pd.DataFrame({
            'year': [2020, 2021, 2022, 2023, 2024],
            'irr_mean': [0.02, 0.025, 0.03, 0.035, 0.04]
        })
        
        result = self.analyzer.analyze_yearly_trend(df, 'year', 'irr_mean')
        
        self.assertIn('slope', result)
        self.assertIn('trend_direction', result)
        self.assertEqual(result['trend_direction'], '上升')
        self.assertGreater(result['slope'], 0)
    
    def test_analyze_yearly_trend_downward(self):
        """测试下降趋势"""
        df = pd.DataFrame({
            'year': [2020, 2021, 2022, 2023, 2024],
            'irr_mean': [0.04, 0.035, 0.03, 0.025, 0.02]
        })
        
        result = self.analyzer.analyze_yearly_trend(df, 'year', 'irr_mean')
        
        self.assertEqual(result['trend_direction'], '下降')
        self.assertLess(result['slope'], 0)
    
    def test_analyze_yearly_trend_flat(self):
        """测试平稳趋势"""
        df = pd.DataFrame({
            'year': [2020, 2021, 2022, 2023, 2024],
            'irr_mean': [0.03, 0.031, 0.029, 0.03, 0.03]
        })
        
        result = self.analyzer.analyze_yearly_trend(df, 'year', 'irr_mean')
        
        self.assertEqual(result['trend_direction'], '平稳')
    
    def test_analyze_yearly_trend_insufficient_data(self):
        """测试数据不足"""
        df = pd.DataFrame({
            'year': [2020, 2021],
            'irr_mean': [0.03, 0.035]
        })
        
        result = self.analyzer.analyze_yearly_trend(df, 'year', 'irr_mean')
        
        self.assertIn('error', result)
    
    def test_analyze_category_trends(self):
        """测试多类别趋势分析"""
        df = pd.DataFrame({
            'issue_year': [2020, 2021, 2022, 2023] * 3,
            'product_category': ['传统寿险'] * 4 + ['分红险'] * 4 + ['万能险'] * 4,
            'irr': [0.02, 0.025, 0.03, 0.035,
                   0.03, 0.032, 0.035, 0.038,
                   0.025, 0.028, 0.03, 0.033]
        })
        
        result = self.analyzer.analyze_category_trends(df)
        
        self.assertIsInstance(result, dict)
        self.assertIn('传统寿险', result)
        self.assertIn('分红险', result)
        self.assertIn('万能险', result)
    
    def test_missing_columns_error(self):
        """测试缺少列的错误处理"""
        df = pd.DataFrame({'other_column': [1, 2, 3]})
        result = self.analyzer.analyze_yearly_trend(df, 'year', 'value')
        
        self.assertIn('error', result)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_full_analysis_pipeline(self):
        """测试完整分析流程"""
        # 创建测试数据
        np.random.seed(42)
        data = pd.DataFrame({
            'policy_id': [f'P{i:04d}' for i in range(50)],
            'product_category': np.random.choice(['传统寿险', '分红险'], 50),
            'issue_year': np.random.choice([2021, 2022, 2023], 50),
            'irr': np.random.normal(0.035, 0.01, 50)
        })
        
        # 聚合分析
        aggregator = DataAggregator()
        agg_result = aggregator.aggregate_by_category_year(data)
        
        # 趋势分析
        analyzer = TrendAnalyzer()
        trend_result = analyzer.analyze_category_trends(data)
        
        # 验证结果
        self.assertFalse(agg_result.empty)
        self.assertIsInstance(trend_result, dict)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestDataAggregator))
    suite.addTests(loader.loadTestsFromTestCase(TestTrendAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
