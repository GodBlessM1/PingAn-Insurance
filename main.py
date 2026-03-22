"""
PingAn Life Returns Analyzer - 主入口
平安寿险收益分析器

Usage:
    python main.py --mode full
    python main.py --mode extract
    python main.py --mode transform
    python main.py --mode calculate
    python main.py --mode analyze
    python main.py --mode visualize
    python main.py --mode dashboard
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import get_config
from src.extract import LocalExtractor
from src.transform import DataPipeline
from src.calculate import PolicyCalculator
from src.analyze import DataAggregator, TrendAnalyzer
from src.visualize import ChartGenerator, ReportGenerator

# 配置日志
def setup_logging(config):
    """设置日志配置"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"analyzer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=config.get('logging.level', 'INFO'),
        format=config.get('logging.format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


class ReturnsAnalyzer:
    """
    收益分析器主类
    
    协调各模块完成完整分析流程
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化分析器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = get_config(config_path)
        self.logger = setup_logging(self.config.all)
        
        self.logger.info("=" * 60)
        self.logger.info("平安寿险收益分析器启动")
        self.logger.info("=" * 60)
        
        # 初始化各模块
        self.extractor = None
        self.pipeline = None
        self.calculator = None
        self.aggregator = None
        self.trend_analyzer = None
        self.chart_generator = None
        self.report_generator = None
        
        # 数据存储
        self.raw_data = {}
        self.processed_data = {}
        self.calculated_data = None
        self.aggregated_data = {}
        
    def extract_data(self) -> Dict[str, pd.DataFrame]:
        """
        阶段1: 数据提取
        
        Returns:
            原始数据字典
        """
        self.logger.info("\n" + "=" * 60)
        self.logger.info("阶段1: 数据提取")
        self.logger.info("=" * 60)
        
        # 使用本地提取器 (开发/测试环境)
        # 生产环境可替换为 HiveExtractor
        data_source_config = self.config.get('data_source.local', {})
        self.extractor = LocalExtractor(data_source_config)
        self.extractor.connect()
        
        # 尝试加载本地数据文件
        try:
            # 检查是否有本地数据文件
            raw_data_path = Path(data_source_config.get('raw_data_path', 'data/raw'))
            
            # 模拟数据 (如果没有真实数据)
            self.logger.info("加载数据文件...")
            
            # 尝试读取各表
            tables = ['POLICY', 'PREMIUM', 'CASH_VALUE', 'DIVIDEND']
            for table in tables:
                try:
                    df = self.extractor.extract_table(table.lower())
                    self.raw_data[table.lower()] = df
                    self.logger.info(f"  ✓ {table}: {len(df)} 行")
                except FileNotFoundError:
                    self.logger.warning(f"  ✗ {table}: 文件不存在，将使用模拟数据")
            
            # 如果没有数据，生成模拟数据
            if not self.raw_data:
                self.logger.info("生成模拟数据用于测试...")
                self.raw_data = self._generate_mock_data()
            
        except Exception as e:
            self.logger.error(f"数据提取失败: {str(e)}")
            raise
        
        self.logger.info(f"数据提取完成，共 {len(self.raw_data)} 个表")
        return self.raw_data
    
    def transform_data(self) -> Dict[str, pd.DataFrame]:
        """
        阶段2: 数据清洗与转换
        
        Returns:
            处理后数据字典
        """
        self.logger.info("\n" + "=" * 60)
        self.logger.info("阶段2: 数据清洗与转换")
        self.logger.info("=" * 60)
        
        processing_config = self.config.get('processing', {})
        product_categories = self.config.get('product_categories', {})
        
        self.pipeline = DataPipeline(processing_config, product_categories)
        
        # 获取原始数据
        policy_df = self.raw_data.get('policy', pd.DataFrame())
        premium_df = self.raw_data.get('premium', pd.DataFrame())
        cash_value_df = self.raw_data.get('cash_value', pd.DataFrame())
        dividend_df = self.raw_data.get('dividend', pd.DataFrame())
        
        if policy_df.empty:
            raise ValueError("保单数据为空，无法进行处理")
        
        # 执行处理流程
        self.processed_data = self.pipeline.process(
            policy_df, premium_df, cash_value_df, dividend_df
        )
        
        # 保存处理后的数据
        self.pipeline.save_processed_data(self.processed_data, format='parquet')
        
        self.logger.info("数据清洗与转换完成")
        return self.processed_data
    
    def calculate_returns(self) -> pd.DataFrame:
        """
        阶段3: 收益计算
        
        Returns:
            带收益指标的保单数据
        """
        self.logger.info("\n" + "=" * 60)
        self.logger.info("阶段3: 收益计算")
        self.logger.info("=" * 60)
        
        calculation_config = self.config.get('calculation', {})
        self.calculator = PolicyCalculator(calculation_config)
        
        # 获取数据
        policies_df = self.processed_data.get('analysis_wide')
        cashflow_df = self.processed_data.get('cashflow_annual')
        
        if policies_df is None or policies_df.empty:
            raise ValueError("保单数据为空，无法进行计算")
        
        # 批量计算收益
        self.calculated_data = self.calculator.batch_calculate(policies_df, cashflow_df)
        
        # 保存结果 (使用CSV格式避免pyarrow依赖)
        output_path = Path('data/processed/policies_with_returns.csv')
        self.calculated_data.to_csv(output_path, index=False, encoding='utf-8-sig')
        self.logger.info(f"计算结果已保存: {output_path}")
        
        self.logger.info(f"收益计算完成，共计算 {len(self.calculated_data)} 个保单")
        return self.calculated_data
    
    def analyze_data(self) -> Dict:
        """
        阶段4: 数据分析
        
        Returns:
            分析结果字典
        """
        self.logger.info("\n" + "=" * 60)
        self.logger.info("阶段4: 数据分析")
        self.logger.info("=" * 60)
        
        if self.calculated_data is None or self.calculated_data.empty:
            raise ValueError("计算数据为空，无法进行分析")
        
        # 初始化分析器
        percentiles = self.config.get('calculation.percentiles', [0.05, 0.25, 0.5, 0.75, 0.95])
        self.aggregator = DataAggregator(percentiles)
        self.trend_analyzer = TrendAnalyzer()
        
        results = {}
        
        # 1. 按产品聚合
        self.logger.info("执行按产品聚合...")
        results['by_product'] = self.aggregator.aggregate_by_product(self.calculated_data)
        
        # 2. 按年份聚合
        self.logger.info("执行按年份聚合...")
        results['by_year'] = self.aggregator.aggregate_by_year(self.calculated_data)
        
        # 3. 交叉聚合
        self.logger.info("执行交叉聚合...")
        results['by_category_year'] = self.aggregator.aggregate_by_category_year(
            self.calculated_data
        )
        
        # 4. 趋势分析
        self.logger.info("执行趋势分析...")
        results['trends'] = self.trend_analyzer.analyze_category_trends(
            self.calculated_data
        )
        
        # 5. 汇总统计
        self.logger.info("生成汇总统计...")
        results['summary'] = self.aggregator.generate_summary_statistics(
            self.calculated_data
        )
        
        self.aggregated_data = results
        self.logger.info("数据分析完成")
        return results
    
    def generate_visualizations(self):
        """
        阶段5: 生成可视化
        """
        self.logger.info("\n" + "=" * 60)
        self.logger.info("阶段5: 生成可视化")
        self.logger.info("=" * 60)
        
        viz_config = self.config.get('visualization', {})
        self.chart_generator = ChartGenerator(viz_config)
        
        # 1. 趋势图
        if 'by_category_year' in self.aggregated_data:
            trend_df = self.aggregated_data['by_category_year']
            if not trend_df.empty and 'issue_year' in trend_df.columns:
                self.chart_generator.plot_trend(
                    trend_df,
                    x_col='issue_year',
                    y_col='irr_mean',
                    category_col='product_category',
                    title='各类险种IRR趋势 (2020-2024)',
                    xlabel='年份',
                    ylabel='平均IRR',
                    save_path='trend_irr_by_category.png'
                )
                self.logger.info("  ✓ 趋势图已生成")
        
        # 2. 分布箱线图
        if self.calculated_data is not None and 'product_category' in self.calculated_data.columns:
            self.chart_generator.plot_box_distribution(
                self.calculated_data,
                value_col='irr',
                category_col='product_category',
                title='IRR分布对比',
                save_path='distribution_irr_boxplot.png'
            )
            self.logger.info("  ✓ 分布图已生成")
        
        # 3. 热力图
        if 'by_category_year' in self.aggregated_data:
            heatmap_df = self.aggregated_data['by_category_year']
            if not heatmap_df.empty:
                self.chart_generator.plot_heatmap(
                    heatmap_df,
                    index_col='product_category',
                    column_col='issue_year',
                    value_col='irr_mean',
                    title='各类险种年度IRR热力图',
                    save_path='heatmap_irr.png'
                )
                self.logger.info("  ✓ 热力图已生成")
        
        # 4. 综合仪表盘
        if (self.calculated_data is not None and 
            'by_category_year' in self.aggregated_data and
            'by_product' in self.aggregated_data):
            
            self.chart_generator.plot_returns_dashboard(
                trend_df=self.aggregated_data['by_category_year'],
                distribution_df=self.calculated_data,
                comparison_df=self.aggregated_data['by_category_year'],
                save_path='dashboard_summary.png'
            )
            self.logger.info("  ✓ 综合仪表盘已生成")
        
        self.chart_generator.close_all()
        self.logger.info("可视化生成完成")
    
    def generate_reports(self):
        """
        阶段6: 生成报告
        """
        self.logger.info("\n" + "=" * 60)
        self.logger.info("阶段6: 生成报告")
        self.logger.info("=" * 60)
        
        self.report_generator = ReportGenerator(output_dir='reports')
        
        # 1. 汇总报告
        if (self.calculated_data is not None and 
            'summary' in self.aggregated_data and
            'by_product' in self.aggregated_data):
            
            self.report_generator.generate_summary_report(
                summary_data=self.aggregated_data['summary'],
                policies_df=self.calculated_data,
                aggregated_df=self.aggregated_data['by_product'],
                filename='summary_report.xlsx'
            )
            self.logger.info("  ✓ Excel汇总报告已生成")
        
        # 2. HTML报告
        if 'summary' in self.aggregated_data:
            # 生成趋势摘要
            trend_summary = ""
            if 'trends' in self.aggregated_data:
                for category, trend in self.aggregated_data['trends'].items():
                    if 'error' not in trend:
                        trend_summary += f"\\n【{category}】"
                        trend_summary += f"\\n  趋势: {trend.get('trend_direction', 'N/A')}"
                        trend_summary += f"\\n  年均变化: {trend.get('avg_annual_change', 0):.2%}"
                        trend_summary += f"\\n"
            
            # 准备表格
            tables = {}
            if 'by_product' in self.aggregated_data:
                tables['产品汇总'] = self.aggregated_data['by_product']
            if 'by_year' in self.aggregated_data:
                tables['年度汇总'] = self.aggregated_data['by_year']
            
            # 图表路径
            chart_paths = [
                'reports/charts/trend_irr_by_category.png',
                'reports/charts/distribution_irr_boxplot.png',
                'reports/charts/dashboard_summary.png'
            ]
            
            self.report_generator.generate_html_report(
                title='平安寿险收益分析报告',
                summary=trend_summary,
                tables=tables,
                chart_paths=[p for p in chart_paths if Path(p).exists()],
                filename='analysis_report.html'
            )
            self.logger.info("  ✓ HTML报告已生成")
        
        self.logger.info("报告生成完成")
    
    def run_full_pipeline(self):
        """
        执行完整分析流程
        """
        try:
            self.extract_data()
            self.transform_data()
            self.calculate_returns()
            self.analyze_data()
            self.generate_visualizations()
            self.generate_reports()
            
            self.logger.info("\n" + "=" * 60)
            self.logger.info("分析流程全部完成!")
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error(f"分析流程失败: {str(e)}", exc_info=True)
            raise
    
    def run_with_mock_data(self, mode: str):
        """
        使用模拟数据运行指定模式
        
        Args:
            mode: 运行模式
        """
        self.raw_data = self._generate_mock_data()
        self.transform_data()
        
        if mode in ['calculate', 'analyze', 'visualize', 'reports']:
            self.calculate_returns()
        
        if mode in ['analyze', 'visualize', 'reports']:
            self.analyze_data()
        
        if mode == 'visualize':
            self.generate_visualizations()
        
        if mode == 'reports':
            self.generate_visualizations()
            self.generate_reports()
    
    def _generate_mock_data(self) -> Dict[str, pd.DataFrame]:
        """
        生成模拟数据用于测试
        
        Returns:
            模拟数据字典
        """
        np.random.seed(42)
        
        n_policies = 1000
        years = list(range(2020, 2024))
        
        categories = ['传统寿险', '分红险', '万能险', '投连险']
        category_weights = [0.3, 0.4, 0.2, 0.1]
        
        # 1. 保单主表
        policies = []
        for i in range(n_policies):
            issue_year = np.random.choice(years)
            category = np.random.choice(categories, p=category_weights)
            
            policy = {
                'policy_id': f'P{issue_year}{i:05d}',
                'product_code': f'{category[:2]}{np.random.randint(1, 10):02d}',
                'product_category': category,
                'issue_date': pd.Timestamp(f'{issue_year}-{np.random.randint(1, 13):02d}-01'),
                'issue_year': issue_year,
                'annual_premium': np.random.randint(5000, 100000),
                'payment_term': np.random.choice([5, 10, 15, 20]),
                'sum_assured': np.random.randint(100000, 5000000),
                'insured_age': np.random.randint(25, 60),
                'policy_status': 'ACTIVE'
            }
            policies.append(policy)
        
        policy_df = pd.DataFrame(policies)
        
        # 2. 保费流水
        premiums = []
        for _, policy in policy_df.iterrows():
            for year in range(policy['issue_year'], min(policy['issue_year'] + policy['payment_term'], 2025)):
                premium = {
                    'policy_id': policy['policy_id'],
                    'payment_date': pd.Timestamp(f'{year}-01-15'),
                    'premium_amount': policy['annual_premium'],
                    'year': year
                }
                premiums.append(premium)
        
        premium_df = pd.DataFrame(premiums)
        
        # 3. 现金价值
        cash_values = []
        for _, policy in policy_df.iterrows():
            base_rate = {'传统寿险': 0.025, '分红险': 0.03, '万能险': 0.035, '投连险': 0.04}[policy['product_category']]
            
            for year in range(policy['issue_year'], 2025):
                years_passed = year - policy['issue_year'] + 1
                # 模拟现金价值增长
                cv_rate = base_rate + np.random.normal(0, 0.005)
                cash_value = policy['annual_premium'] * years_passed * (1 + cv_rate) ** years_passed * 0.8
                
                cv = {
                    'policy_id': policy['policy_id'],
                    'valuation_date': pd.Timestamp(f'{year}-12-31'),
                    'cash_value': max(0, cash_value),
                    'year': year
                }
                cash_values.append(cv)
        
        cash_value_df = pd.DataFrame(cash_values)
        
        # 4. 分红数据 (仅分红险)
        dividends = []
        participating_policies = policy_df[policy_df['product_category'] == '分红险']
        
        for _, policy in participating_policies.iterrows():
            for year in range(policy['issue_year'], 2025):
                years_passed = year - policy['issue_year'] + 1
                dividend_rate = 0.015 + np.random.normal(0, 0.002)
                dividend_amount = policy['annual_premium'] * years_passed * dividend_rate
                
                div = {
                    'policy_id': policy['policy_id'],
                    'dividend_date': pd.Timestamp(f'{year}-06-30'),
                    'dividend_amount': max(0, dividend_amount),
                    'year': year
                }
                dividends.append(div)
        
        dividend_df = pd.DataFrame(dividends)
        
        return {
            'policy': policy_df,
            'premium': premium_df,
            'cash_value': cash_value_df,
            'dividend': dividend_df
        }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='平安寿险收益分析器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python main.py --mode full                    # 执行完整流程
  python main.py --mode extract                 # 仅数据提取
  python main.py --mode transform               # 仅数据清洗
  python main.py --mode calculate               # 仅收益计算
  python main.py --mode analyze                 # 仅数据分析
  python main.py --mode visualize               # 仅生成可视化
  python main.py --mode reports                 # 仅生成报告
        '''
    )
    
    parser.add_argument(
        '--mode',
        choices=['full', 'extract', 'transform', 'calculate', 'analyze', 'visualize', 'reports'],
        default='full',
        help='运行模式 (默认: full)'
    )
    
    parser.add_argument(
        '--config',
        default=None,
        help='配置文件路径 (默认: config/config.yaml)'
    )
    
    args = parser.parse_args()
    
    analyzer = ReturnsAnalyzer(config_path=args.config)
    
    if args.mode == 'full':
        analyzer.run_full_pipeline()
    elif args.mode == 'extract':
        analyzer.extract_data()
    elif args.mode == 'transform':
        analyzer.run_with_mock_data('transform')
    elif args.mode == 'calculate':
        analyzer.run_with_mock_data('calculate')
    elif args.mode == 'analyze':
        analyzer.run_with_mock_data('analyze')
    elif args.mode == 'visualize':
        analyzer.run_with_mock_data('visualize')
    elif args.mode == 'reports':
        analyzer.run_with_mock_data('reports')


if __name__ == '__main__':
    main()
