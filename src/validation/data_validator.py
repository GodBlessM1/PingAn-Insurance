"""
数据验证器
提供全面的数据质量检查功能
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """
    数据验证器
    
    提供以下验证功能：
    - 完整性检查（缺失值）
    - 一致性检查（数据逻辑）
    - 准确性检查（异常值）
    - 业务规则验证
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化验证器
        
        Args:
            config: 验证配置
        """
        self.config = config or {}
        self.validation_results = {}
        
        self.business_rules = {
            'policy': {
                'annual_premium': {'min': 1000, 'max': 10000000},
                'sum_assured': {'min': 10000, 'max': 100000000},
                'insured_age': {'min': 0, 'max': 80},
                'payment_term': {'min': 1, 'max': 30}
            },
            'premium': {
                'premium_amount': {'min': 100, 'max': 10000000}
            },
            'cash_value': {
                'cash_value': {'min': 0, 'max': 100000000}
            },
            'dividend': {
                'dividend_amount': {'min': 0, 'max': 10000000}
            }
        }
        
        self.required_columns = {
            'policy': ['policy_id', 'product_code', 'issue_date', 'annual_premium', 
                      'payment_term', 'sum_assured', 'insured_age', 'policy_status'],
            'premium': ['policy_id', 'payment_date', 'premium_amount'],
            'cash_value': ['policy_id', 'valuation_date', 'cash_value'],
            'dividend': ['policy_id', 'dividend_date', 'dividend_amount']
        }
        
    def validate_all(self, 
                    policy_df: pd.DataFrame,
                    premium_df: pd.DataFrame,
                    cash_value_df: pd.DataFrame,
                    dividend_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        执行全面数据验证
        
        Args:
            policy_df: 保单数据
            premium_df: 保费数据
            cash_value_df: 现金价值数据
            dividend_df: 分红数据
            
        Returns:
            验证结果字典
        """
        logger.info("=" * 50)
        logger.info("开始数据验证")
        logger.info("=" * 50)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'tables': {}
        }
        
        results['tables']['policy'] = self.validate_policy_data(policy_df)
        results['tables']['premium'] = self.validate_premium_data(premium_df)
        results['tables']['cash_value'] = self.validate_cash_value_data(cash_value_df)
        
        if dividend_df is not None and not dividend_df.empty:
            results['tables']['dividend'] = self.validate_dividend_data(dividend_df)
        
        results['cross_table'] = self.validate_cross_table_integrity(
            policy_df, premium_df, cash_value_df, dividend_df
        )
        
        results['summary'] = self._generate_summary(results)
        
        self.validation_results = results
        logger.info("数据验证完成")
        
        return results
    
    def validate_policy_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        验证保单数据
        
        Args:
            df: 保单数据
            
        Returns:
            验证结果
        """
        if df.empty:
            return {'status': 'error', 'message': '保单数据为空'}
        
        results = {
            'total_records': len(df),
            'completeness': {},
            'validity': {},
            'consistency': {},
            'anomalies': {}
        }
        
        results['completeness'] = self._check_completeness(df, 'policy')
        results['validity'] = self._check_validity(df, 'policy')
        results['consistency'] = self._check_policy_consistency(df)
        results['anomalies'] = self._detect_anomalies(df, 'policy')
        
        results['quality_score'] = self._calculate_quality_score(results)
        
        return results
    
    def validate_premium_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        验证保费数据
        """
        if df.empty:
            return {'status': 'warning', 'message': '保费数据为空'}
        
        results = {
            'total_records': len(df),
            'completeness': {},
            'validity': {},
            'anomalies': {}
        }
        
        results['completeness'] = self._check_completeness(df, 'premium')
        results['validity'] = self._check_validity(df, 'premium')
        results['anomalies'] = self._detect_anomalies(df, 'premium')
        results['quality_score'] = self._calculate_quality_score(results)
        
        return results
    
    def validate_cash_value_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        验证现金价值数据
        """
        if df.empty:
            return {'status': 'warning', 'message': '现金价值数据为空'}
        
        results = {
            'total_records': len(df),
            'completeness': {},
            'validity': {},
            'anomalies': {}
        }
        
        results['completeness'] = self._check_completeness(df, 'cash_value')
        results['validity'] = self._check_validity(df, 'cash_value')
        results['anomalies'] = self._detect_anomalies(df, 'cash_value')
        results['quality_score'] = self._calculate_quality_score(results)
        
        return results
    
    def validate_dividend_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        验证分红数据
        """
        if df.empty:
            return {'status': 'info', 'message': '分红数据为空'}
        
        results = {
            'total_records': len(df),
            'completeness': {},
            'validity': {},
            'anomalies': {}
        }
        
        results['completeness'] = self._check_completeness(df, 'dividend')
        results['validity'] = self._check_validity(df, 'dividend')
        results['anomalies'] = self._detect_anomalies(df, 'dividend')
        results['quality_score'] = self._calculate_quality_score(results)
        
        return results
    
    def _check_completeness(self, df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """
        检查数据完整性
        """
        results = {
            'missing_counts': {},
            'missing_rates': {},
            'total_cells': len(df) * len(df.columns)
        }
        
        required_cols = self.required_columns.get(table_name, [])
        
        for col in df.columns:
            missing_count = df[col].isna().sum()
            missing_rate = missing_count / len(df) if len(df) > 0 else 0
            
            results['missing_counts'][col] = int(missing_count)
            results['missing_rates'][col] = float(missing_rate)
        
        results['critical_missing'] = [
            col for col in required_cols 
            if col in df.columns and results['missing_rates'].get(col, 0) > 0.05
        ]
        
        return results
    
    def _check_validity(self, df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """
        检查数据有效性
        """
        results = {
            'out_of_range': {},
            'invalid_format': {},
            'invalid_values': {}
        }
        
        rules = self.business_rules.get(table_name, {})
        
        for col, rule in rules.items():
            if col not in df.columns:
                continue
            
            col_data = df[col].dropna()
            
            if 'min' in rule:
                below_min = (col_data < rule['min']).sum()
                if below_min > 0:
                    results['out_of_range'][f'{col}_below_min'] = int(below_min)
            
            if 'max' in rule:
                above_max = (col_data > rule['max']).sum()
                if above_max > 0:
                    results['out_of_range'][f'{col}_above_max'] = int(above_max)
        
        if table_name == 'policy':
            if 'policy_status' in df.columns:
                valid_statuses = ['ACTIVE', 'LAPSED', 'SURRENDERED', 'MATURED', 'PENDING']
                invalid = ~df['policy_status'].isin(valid_statuses)
                if invalid.sum() > 0:
                    results['invalid_values']['policy_status'] = int(invalid.sum())
        
        return results
    
    def _check_policy_consistency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        检查保单数据一致性
        """
        results = {
            'duplicate_policies': 0,
            'date_issues': 0,
            'logic_issues': 0
        }
        
        if 'policy_id' in df.columns:
            results['duplicate_policies'] = int(df['policy_id'].duplicated().sum())
        
        if 'issue_date' in df.columns and 'maturity_date' in df.columns:
            try:
                issue_dates = pd.to_datetime(df['issue_date'])
                maturity_dates = pd.to_datetime(df['maturity_date'])
                invalid_dates = (maturity_dates <= issue_dates).sum()
                results['date_issues'] = int(invalid_dates)
            except Exception:
                pass
        
        if 'sum_assured' in df.columns and 'annual_premium' in df.columns:
            ratio = df['sum_assured'] / df['annual_premium'].replace(0, np.nan)
            unusual_ratio = ((ratio < 1) | (ratio > 1000)).sum()
            results['logic_issues'] = int(unusual_ratio)
        
        return results
    
    def _detect_anomalies(self, df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """
        检测异常值
        """
        results = {
            'statistical_outliers': {},
            'distribution_anomalies': {}
        }
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            col_data = df[col].dropna()
            
            if len(col_data) < 10:
                continue
            
            Q1 = col_data.quantile(0.25)
            Q3 = col_data.quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = ((col_data < lower_bound) | (col_data > upper_bound)).sum()
            
            if outliers > 0:
                results['statistical_outliers'][col] = {
                    'count': int(outliers),
                    'rate': float(outliers / len(col_data)),
                    'bounds': (float(lower_bound), float(upper_bound))
                }
        
        return results
    
    def validate_cross_table_integrity(self,
                                       policy_df: pd.DataFrame,
                                       premium_df: pd.DataFrame,
                                       cash_value_df: pd.DataFrame,
                                       dividend_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        验证跨表数据完整性
        """
        results = {
            'orphan_records': {},
            'missing_related_records': {}
        }
        
        policy_ids = set(policy_df['policy_id'].unique()) if 'policy_id' in policy_df.columns else set()
        
        for name, df in [('premium', premium_df), ('cash_value', cash_value_df)]:
            if df.empty or 'policy_id' not in df.columns:
                continue
            
            df_policy_ids = set(df['policy_id'].unique())
            
            orphan_ids = df_policy_ids - policy_ids
            if orphan_ids:
                results['orphan_records'][name] = {
                    'count': len(orphan_ids),
                    'sample_ids': list(orphan_ids)[:5]
                }
        
        if dividend_df is not None and not dividend_df.empty and 'policy_id' in dividend_df.columns:
            div_policy_ids = set(dividend_df['policy_id'].unique())
            orphan_div = div_policy_ids - policy_ids
            if orphan_div:
                results['orphan_records']['dividend'] = {
                    'count': len(orphan_div),
                    'sample_ids': list(orphan_div)[:5]
                }
        
        return results
    
    def _calculate_quality_score(self, results: Dict) -> float:
        """
        计算数据质量评分 (0-100)
        """
        score = 100.0
        
        completeness = results.get('completeness', {})
        missing_rates = completeness.get('missing_rates', {})
        if missing_rates:
            avg_missing = np.mean(list(missing_rates.values()))
            score -= avg_missing * 30
        
        validity = results.get('validity', {})
        out_of_range = validity.get('out_of_range', {})
        if out_of_range:
            score -= len(out_of_range) * 5
        
        consistency = results.get('consistency', {})
        if consistency:
            score -= consistency.get('duplicate_policies', 0) * 0.1
            score -= consistency.get('date_issues', 0) * 0.5
            score -= consistency.get('logic_issues', 0) * 0.2
        
        anomalies = results.get('anomalies', {})
        outliers = anomalies.get('statistical_outliers', {})
        if outliers:
            outlier_rate = np.mean([v['rate'] for v in outliers.values()])
            score -= outlier_rate * 20
        
        return max(0, min(100, score))
    
    def _generate_summary(self, results: Dict) -> Dict[str, Any]:
        """
        生成验证摘要
        """
        summary = {
            'total_tables_validated': len(results.get('tables', {})),
            'quality_scores': {},
            'critical_issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        for table_name, table_results in results.get('tables', {}).items():
            if 'quality_score' in table_results:
                summary['quality_scores'][table_name] = table_results['quality_score']
        
        cross_table = results.get('cross_table', {})
        orphan_records = cross_table.get('orphan_records', {})
        if orphan_records:
            for table, info in orphan_records.items():
                summary['critical_issues'].append(
                    f"表 {table} 存在 {info['count']} 条孤儿记录（无对应保单）"
                )
        
        for table_name, table_results in results.get('tables', {}).items():
            completeness = table_results.get('completeness', {})
            critical_missing = completeness.get('critical_missing', [])
            if critical_missing:
                summary['warnings'].append(
                    f"表 {table_name} 关键字段 {critical_missing} 存在较高缺失率"
                )
        
        avg_quality = np.mean(list(summary['quality_scores'].values())) if summary['quality_scores'] else 0
        
        if avg_quality < 80:
            summary['recommendations'].append("数据质量较低，建议进行数据清洗后再进行分析")
        elif avg_quality < 90:
            summary['recommendations'].append("数据质量一般，建议关注缺失值和异常值处理")
        else:
            summary['recommendations'].append("数据质量良好，可以进行后续分析")
        
        summary['overall_quality_score'] = float(avg_quality)
        
        return summary
    
    def get_validation_report(self) -> str:
        """
        生成文本格式的验证报告
        """
        if not self.validation_results:
            return "尚未执行数据验证"
        
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("数据质量验证报告")
        report_lines.append("=" * 60)
        report_lines.append(f"验证时间: {self.validation_results['timestamp']}")
        report_lines.append("")
        
        summary = self.validation_results.get('summary', {})
        report_lines.append(f"整体质量评分: {summary.get('overall_quality_score', 0):.1f}/100")
        report_lines.append("")
        
        report_lines.append("各表质量评分:")
        for table, score in summary.get('quality_scores', {}).items():
            report_lines.append(f"  - {table}: {score:.1f}")
        report_lines.append("")
        
        if summary.get('critical_issues'):
            report_lines.append("严重问题:")
            for issue in summary['critical_issues']:
                report_lines.append(f"  ❌ {issue}")
            report_lines.append("")
        
        if summary.get('warnings'):
            report_lines.append("警告:")
            for warning in summary['warnings']:
                report_lines.append(f"  ⚠️ {warning}")
            report_lines.append("")
        
        if summary.get('recommendations'):
            report_lines.append("建议:")
            for rec in summary['recommendations']:
                report_lines.append(f"  💡 {rec}")
        
        report_lines.append("")
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
