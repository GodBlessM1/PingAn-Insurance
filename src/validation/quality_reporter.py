"""
数据质量报告生成器
生成可视化的数据质量报告
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class QualityReporter:
    """
    数据质量报告生成器
    
    生成以下报告：
    - HTML质量报告
    - Excel质量报告
    - 质量趋势报告
    """
    
    def __init__(self, output_dir: str = 'reports/quality'):
        """
        初始化报告生成器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_html_report(self,
                            validation_results: Dict[str, Any],
                            filename: str = 'quality_report.html') -> Path:
        """
        生成HTML格式的质量报告
        
        Args:
            validation_results: 验证结果
            filename: 文件名
            
        Returns:
            报告文件路径
        """
        summary = validation_results.get('summary', {})
        
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>数据质量报告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1f77b4;
            border-bottom: 3px solid #1f77b4;
            padding-bottom: 10px;
        }}
        .score-card {{
            display: inline-block;
            padding: 20px;
            margin: 10px;
            border-radius: 10px;
            text-align: center;
            min-width: 150px;
        }}
        .score-excellent {{
            background: linear-gradient(135deg, #4CAF50, #8BC34A);
            color: white;
        }}
        .score-good {{
            background: linear-gradient(135deg, #2196F3, #03A9F4);
            color: white;
        }}
        .score-warning {{
            background: linear-gradient(135deg, #FF9800, #FFC107);
            color: white;
        }}
        .score-poor {{
            background: linear-gradient(135deg, #f44336, #E91E63);
            color: white;
        }}
        .score-value {{
            font-size: 2.5em;
            font-weight: bold;
        }}
        .score-label {{
            font-size: 0.9em;
            margin-top: 5px;
        }}
        .section {{
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
        }}
        .section h2 {{
            color: #333;
            margin-top: 0;
        }}
        .issue-item {{
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
        }}
        .issue-critical {{
            background: #ffebee;
            border-left: 4px solid #f44336;
        }}
        .issue-warning {{
            background: #fff3e0;
            border-left: 4px solid #ff9800;
        }}
        .issue-info {{
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #1f77b4;
            color: white;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .progress-bar {{
            width: 100%;
            height: 20px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
            border-radius: 10px;
            transition: width 0.5s ease;
        }}
        .timestamp {{
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 数据质量验证报告</h1>
        <p class="timestamp">生成时间: {validation_results.get('timestamp', 'N/A')}</p>
        
        <div class="section">
            <h2>整体质量评分</h2>
            {self._generate_score_card(summary.get('overall_quality_score', 0), '整体评分')}
        </div>
        
        <div class="section">
            <h2>各表质量评分</h2>
            {self._generate_table_scores_html(summary.get('quality_scores', {}))}
        </div>
        
        {self._generate_issues_section_html(summary)}
        
        {self._generate_table_details_html(validation_results)}
        
        <div class="section">
            <h2>💡 改进建议</h2>
            {self._generate_recommendations_html(summary.get('recommendations', []))}
        </div>
    </div>
</body>
</html>
"""
        
        file_path = self.output_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML质量报告已生成: {file_path}")
        return file_path
    
    def _generate_score_card(self, score: float, label: str) -> str:
        """
        生成分数卡片HTML
        """
        if score >= 90:
            css_class = 'score-excellent'
        elif score >= 80:
            css_class = 'score-good'
        elif score >= 60:
            css_class = 'score-warning'
        else:
            css_class = 'score-poor'
        
        return f"""
        <div class="score-card {css_class}">
            <div class="score-value">{score:.1f}</div>
            <div class="score-label">{label}</div>
        </div>
        """
    
    def _generate_table_scores_html(self, quality_scores: Dict[str, float]) -> str:
        """
        生成表格评分HTML
        """
        if not quality_scores:
            return "<p>无评分数据</p>"
        
        cards_html = ""
        for table, score in quality_scores.items():
            cards_html += self._generate_score_card(score, table)
        
        return f'<div style="display: flex; flex-wrap: wrap;">{cards_html}</div>'
    
    def _generate_issues_section_html(self, summary: Dict) -> str:
        """
        生成问题区域HTML
        """
        sections = []
        
        critical_issues = summary.get('critical_issues', [])
        if critical_issues:
            issues_html = ""
            for issue in critical_issues:
                issues_html += f'<div class="issue-item issue-critical">❌ {issue}</div>'
            sections.append(f"""
            <div class="section">
                <h2>严重问题</h2>
                {issues_html}
            </div>
            """)
        
        warnings = summary.get('warnings', [])
        if warnings:
            warnings_html = ""
            for warning in warnings:
                warnings_html += f'<div class="issue-item issue-warning">⚠️ {warning}</div>'
            sections.append(f"""
            <div class="section">
                <h2>警告</h2>
                {warnings_html}
            </div>
            """)
        
        return "\n".join(sections)
    
    def _generate_table_details_html(self, validation_results: Dict) -> str:
        """
        生成表格详情HTML
        """
        tables = validation_results.get('tables', {})
        if not tables:
            return ""
        
        details_html = '<div class="section"><h2>详细统计</h2><table>'
        details_html += '<tr><th>表名</th><th>记录数</th><th>质量评分</th><th>缺失率</th><th>异常值</th></tr>'
        
        for table_name, table_results in tables.items():
            if 'quality_score' not in table_results:
                continue
            
            total_records = table_results.get('total_records', 0)
            quality_score = table_results.get('quality_score', 0)
            
            completeness = table_results.get('completeness', {})
            missing_rates = completeness.get('missing_rates', {})
            avg_missing = np.mean(list(missing_rates.values())) if missing_rates else 0
            
            anomalies = table_results.get('anomalies', {})
            outliers = anomalies.get('statistical_outliers', {})
            outlier_count = sum(v['count'] for v in outliers.values())
            
            details_html += f"""
            <tr>
                <td>{table_name}</td>
                <td>{total_records:,}</td>
                <td>{quality_score:.1f}</td>
                <td>{avg_missing:.2%}</td>
                <td>{outlier_count:,}</td>
            </tr>
            """
        
        details_html += '</table></div>'
        return details_html
    
    def _generate_recommendations_html(self, recommendations: List[str]) -> str:
        """
        生成建议HTML
        """
        if not recommendations:
            return "<p>无改进建议</p>"
        
        rec_html = ""
        for rec in recommendations:
            rec_html += f'<div class="issue-item issue-info">💡 {rec}</div>'
        
        return rec_html
    
    def generate_excel_report(self,
                             validation_results: Dict[str, Any],
                             filename: str = 'quality_report.xlsx') -> Path:
        """
        生成Excel格式的质量报告
        
        Args:
            validation_results: 验证结果
            filename: 文件名
            
        Returns:
            报告文件路径
        """
        file_path = self.output_dir / filename
        
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            summary_data = {
                '指标': ['验证时间', '整体质量评分', '验证表数量'],
                '值': [
                    validation_results.get('timestamp', 'N/A'),
                    validation_results.get('summary', {}).get('overall_quality_score', 0),
                    validation_results.get('summary', {}).get('total_tables_validated', 0)
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='概览', index=False)
            
            quality_scores = validation_results.get('summary', {}).get('quality_scores', {})
            if quality_scores:
                scores_df = pd.DataFrame([
                    {'表名': k, '质量评分': v} for k, v in quality_scores.items()
                ])
                scores_df.to_excel(writer, sheet_name='质量评分', index=False)
            
            tables = validation_results.get('tables', {})
            for table_name, table_results in tables.items():
                if 'completeness' in table_results:
                    completeness = table_results['completeness']
                    missing_rates = completeness.get('missing_rates', {})
                    if missing_rates:
                        missing_df = pd.DataFrame([
                            {'列名': k, '缺失率': f"{v:.2%}"}
                            for k, v in missing_rates.items()
                        ])
                        sheet_name = f'{table_name}_缺失'
                        missing_df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        
        logger.info(f"Excel质量报告已生成: {file_path}")
        return file_path
    
    def generate_summary_dict(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成摘要字典，用于其他模块调用
        
        Args:
            validation_results: 验证结果
            
        Returns:
            摘要字典
        """
        summary = validation_results.get('summary', {})
        
        return {
            'overall_quality': summary.get('overall_quality_score', 0),
            'is_acceptable': summary.get('overall_quality_score', 0) >= 70,
            'critical_issues_count': len(summary.get('critical_issues', [])),
            'warnings_count': len(summary.get('warnings', [])),
            'tables_validated': summary.get('total_tables_validated', 0),
            'recommendations': summary.get('recommendations', [])
        }
