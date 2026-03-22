"""
报告生成模块
生成Excel、PDF格式的分析报告
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    报告生成器
    
    生成以下格式报告：
    - Excel报告 (多工作表)
    - PDF报告
    - HTML报告
    """
    
    def __init__(self, output_dir: str = 'reports'):
        """
        初始化报告生成器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_excel_report(self,
                             data_dict: Dict[str, pd.DataFrame],
                             filename: str = 'analysis_report.xlsx',
                             include_charts: bool = False) -> Path:
        """
        生成Excel报告
        
        Args:
            data_dict: 数据字典 {工作表名: DataFrame}
            filename: 文件名
            include_charts: 是否包含图表
            
        Returns:
            生成的文件路径
        """
        output_path = self.output_dir / filename
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, df in data_dict.items():
                # 工作表名长度限制
                sheet_name = sheet_name[:31]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # 获取工作表
                worksheet = writer.sheets[sheet_name]
                
                # 调整列宽
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        
        logger.info(f"Excel报告已生成: {output_path}")
        return output_path
    
    def generate_summary_report(self,
                               summary_data: Dict,
                               policies_df: pd.DataFrame,
                               aggregated_df: pd.DataFrame,
                               filename: str = 'summary_report.xlsx') -> Path:
        """
        生成汇总分析报告
        
        Args:
            summary_data: 汇总统计数据
            policies_df: 保单明细数据
            aggregated_df: 聚合数据
            filename: 文件名
            
        Returns:
            生成的文件路径
        """
        # 准备各工作表数据
        data_dict = {
            '汇总统计': self._create_summary_sheet(summary_data),
            '保单明细': policies_df,
            '产品聚合': aggregated_df,
        }
        
        # 添加趋势数据 (如果有年份列)
        if 'issue_year' in policies_df.columns:
            trend_df = policies_df.groupby(['product_category', 'issue_year']).agg({
                'irr': 'mean',
                'annual_return_rate': 'mean',
                'policy_id': 'count'
            }).reset_index()
            trend_df.rename(columns={'policy_id': 'policy_count'}, inplace=True)
            data_dict['年度趋势'] = trend_df
        
        return self.generate_excel_report(data_dict, filename)
    
    def _create_summary_sheet(self, summary_data: Dict) -> pd.DataFrame:
        """
        创建汇总统计工作表
        
        Args:
            summary_data: 汇总数据字典
            
        Returns:
            汇总统计DataFrame
        """
        rows = []
        
        # 基本信息
        rows.append(['指标', '数值'])
        rows.append(['总保单数', summary_data.get('total_policies', 0)])
        
        date_range = summary_data.get('date_range', {})
        rows.append(['数据起始年份', date_range.get('start', 'N/A')])
        rows.append(['数据结束年份', date_range.get('end', 'N/A')])
        
        # 产品分布
        rows.append(['', ''])
        rows.append(['产品分布', ''])
        product_dist = summary_data.get('product_distribution', {})
        for product, count in product_dist.items():
            rows.append([product, count])
        
        # 收益指标统计
        rows.append(['', ''])
        rows.append(['收益指标统计', ''])
        metrics = summary_data.get('metrics', {})
        for metric_name, stats in metrics.items():
            rows.append(['', ''])
            rows.append([f"【{metric_name}】", ''])
            for stat_name, value in stats.items():
                rows.append([f'  {stat_name}', f"{value:.4f}" if value is not None else 'N/A'])
        
        return pd.DataFrame(rows[1:], columns=rows[0])
    
    def generate_comparison_report(self,
                                  current_period: pd.DataFrame,
                                  previous_period: pd.DataFrame,
                                  comparison_metrics: List[str],
                                  filename: str = 'comparison_report.xlsx') -> Path:
        """
        生成对比分析报告
        
        Args:
            current_period: 本期数据
            previous_period: 上期数据
            comparison_metrics: 对比指标列表
            filename: 文件名
            
        Returns:
            生成的文件路径
        """
        data_dict = {
            '本期数据': current_period,
            '上期数据': previous_period,
        }
        
        # 计算对比
        comparison_rows = []
        for metric in comparison_metrics:
            if metric in current_period.columns and metric in previous_period.columns:
                current_avg = current_period[metric].mean()
                previous_avg = previous_period[metric].mean()
                change = current_avg - previous_avg
                pct_change = (change / previous_avg * 100) if previous_avg != 0 else 0
                
                comparison_rows.append({
                    '指标': metric,
                    '本期平均': current_avg,
                    '上期平均': previous_avg,
                    '绝对变化': change,
                    '变化百分比': pct_change
                })
        
        data_dict['对比分析'] = pd.DataFrame(comparison_rows)
        
        return self.generate_excel_report(data_dict, filename)
    
    def generate_html_report(self,
                            title: str,
                            summary: str,
                            tables: Dict[str, pd.DataFrame],
                            chart_paths: List[str],
                            filename: str = 'report.html') -> Path:
        """
        生成HTML报告
        
        Args:
            title: 报告标题
            summary: 摘要文本
            tables: 表格数据字典
            chart_paths: 图表路径列表
            filename: 文件名
            
        Returns:
            生成的文件路径
        """
        output_path = self.output_dir / filename
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 40px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #333;
                    border-bottom: 3px solid #1f77b4;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #555;
                    margin-top: 30px;
                }}
                .summary {{
                    background-color: #f9f9f9;
                    padding: 20px;
                    border-left: 4px solid #1f77b4;
                    margin: 20px 0;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 20px 0;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }}
                th {{
                    background-color: #1f77b4;
                    color: white;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                .chart {{
                    margin: 20px 0;
                    text-align: center;
                }}
                .chart img {{
                    max-width: 100%;
                    height: auto;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    color: #999;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{title}</h1>
                
                <div class="summary">
                    <h2>执行摘要</h2>
                    <pre>{summary}</pre>
                </div>
        """
        
        # 添加表格
        for table_name, df in tables.items():
            html_content += f"<h2>{table_name}</h2>"
            html_content += df.to_html(index=False, classes='data-table')
        
        # 添加图表
        if chart_paths:
            html_content += "<h2>可视化图表</h2>"
            for chart_path in chart_paths:
                chart_name = Path(chart_path).name
                html_content += f'''
                <div class="chart">
                    <h3>{chart_name}</h3>
                    <img src="{chart_path}" alt="{chart_name}">
                </div>
                '''
        
        html_content += f"""
                <div class="footer">
                    <p>生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>PingAn Life Returns Analyzer v1.0</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML报告已生成: {output_path}")
        return output_path
