"""
模型训练管理模块
统一管理和训练多个ML模型
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import logging
from datetime import datetime

from .returns_predictor import ReturnsPredictor
from .risk_forecaster import RiskForecaster
from .feature_engineering_ml import MLFeatureEngineer

logger = logging.getLogger(__name__)


class ModelTrainer:
    """
    模型训练管理器
    
    功能：
    - 端到端模型训练流程
    - 多模型对比
    - 模型评估报告
    - 模型持久化
    """
    
    def __init__(self, output_dir: str = 'models'):
        """
        初始化模型训练管理器
        
        Args:
            output_dir: 模型输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.feature_engineer = MLFeatureEngineer()
        self.models = {}
        self.training_history = []
    
    def train_returns_prediction_model(self,
                                        df: pd.DataFrame,
                                        target_col: str = 'irr',
                                        feature_cols: Optional[List[str]] = None,
                                        model_types: List[str] = ['random_forest', 'gradient_boosting'],
                                        test_size: float = 0.2) -> Dict:
        """
        训练收益预测模型
        
        Args:
            df: 训练数据
            target_col: 目标列
            feature_cols: 特征列
            model_types: 模型类型列表
            test_size: 测试集比例
            
        Returns:
            训练结果
        """
        logger.info("=" * 60)
        logger.info("开始训练收益预测模型")
        logger.info("=" * 60)
        
        # 特征工程
        logger.info("执行特征工程...")
        df_features = self.feature_engineer.build_all_features(df)
        
        # 准备特征
        X, y = self.feature_engineer.prepare_features_for_ml(
            df_features, target_col, feature_cols
        )
        
        results = {}
        
        # 训练多个模型
        for model_type in model_types:
            logger.info(f"\n训练模型: {model_type}")
            
            model = ReturnsPredictor(model_type=model_type)
            
            # 训练
            metrics = model.train(X, y, test_size=test_size)
            
            # 交叉验证
            cv_results = model.cross_validate(X, y, cv=5)
            
            # 特征重要性
            feature_importance = model.get_feature_importance()
            
            results[model_type] = {
                'metrics': metrics,
                'cv_results': cv_results,
                'feature_importance': feature_importance.head(10).to_dict()
            }
            
            # 保存模型
            model_path = self.output_dir / f'returns_predictor_{model_type}.pkl'
            model.save_model(str(model_path))
            
            self.models[f'returns_{model_type}'] = model
            
            logger.info(f"模型 {model_type} 训练完成")
            logger.info(f"  测试集 R²: {metrics['test']['r2']:.4f}")
            logger.info(f"  交叉验证 R²: {cv_results['r2_mean']:.4f}")
        
        # 记录训练历史
        self.training_history.append({
            'task': 'returns_prediction',
            'timestamp': datetime.now().isoformat(),
            'models': model_types,
            'best_model': max(results.keys(), key=lambda x: results[x]['metrics']['test']['r2'])
        })
        
        return results
    
    def train_risk_forecast_model(self,
                                   df: pd.DataFrame,
                                   return_col: str = 'irr',
                                   model_types: List[str] = ['random_forest', 'gradient_boosting'],
                                   risk_threshold: float = 0.02) -> Dict:
        """
        训练风险预警模型
        
        Args:
            df: 训练数据
            return_col: 收益率列
            model_types: 模型类型列表
            risk_threshold: 风险阈值
            
        Returns:
            训练结果
        """
        logger.info("=" * 60)
        logger.info("开始训练风险预警模型")
        logger.info("=" * 60)
        
        # 特征工程
        logger.info("执行特征工程...")
        df_features = self.feature_engineer.build_all_features(df)
        
        # 准备特征（排除目标相关列）
        exclude_cols = [return_col, 'risk_label', 'risk_level']
        feature_cols = [c for c in df_features.columns 
                       if c not in exclude_cols and df_features[c].dtype in ['float64', 'int64']]
        
        X = df_features[feature_cols].fillna(0)
        
        # 创建风险标签
        risk_forecaster = RiskForecaster()
        y = risk_forecaster.create_risk_labels(df_features, return_col, risk_threshold=risk_threshold)
        
        # 移除无标签的数据
        valid_idx = y.notna()
        X = X[valid_idx]
        y = y[valid_idx]
        
        results = {}
        
        # 训练多个模型
        for model_type in model_types:
            logger.info(f"\n训练模型: {model_type}")
            
            model = RiskForecaster(model_type=model_type)
            
            # 训练
            metrics = model.train(X, y)
            
            # 交叉验证
            cv_results = model.cross_validate(X, y, cv=5)
            
            # 特征重要性
            feature_importance = model.get_feature_importance()
            
            results[model_type] = {
                'metrics': metrics,
                'cv_results': cv_results,
                'feature_importance': feature_importance.head(10).to_dict()
            }
            
            # 保存模型
            model_path = self.output_dir / f'risk_forecaster_{model_type}.pkl'
            model.save_model(str(model_path))
            
            self.models[f'risk_{model_type}'] = model
            
            logger.info(f"模型 {model_type} 训练完成")
            logger.info(f"  测试集准确率: {metrics['test']['accuracy']:.4f}")
            logger.info(f"  交叉验证准确率: {cv_results['accuracy_mean']:.4f}")
        
        # 记录训练历史
        self.training_history.append({
            'task': 'risk_forecast',
            'timestamp': datetime.now().isoformat(),
            'models': model_types,
            'best_model': max(results.keys(), key=lambda x: results[x]['metrics']['test']['accuracy'])
        })
        
        return results
    
    def generate_training_report(self) -> str:
        """
        生成训练报告
        
        Returns:
            报告文本
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("机器学习模型训练报告")
        report_lines.append("=" * 80)
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        for history in self.training_history:
            report_lines.append(f"任务: {history['task']}")
            report_lines.append(f"时间: {history['timestamp']}")
            report_lines.append(f"训练模型: {', '.join(history['models'])}")
            report_lines.append(f"最佳模型: {history['best_model']}")
            report_lines.append("-" * 80)
        
        report_lines.append("")
        report_lines.append("模型保存位置:")
        report_lines.append(str(self.output_dir))
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def save_report(self, filepath: Optional[str] = None):
        """
        保存训练报告
        
        Args:
            filepath: 报告文件路径
        """
        if filepath is None:
            filepath = self.output_dir / 'training_report.txt'
        
        report = self.generate_training_report()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"训练报告已保存: {filepath}")
    
    def load_model(self, model_name: str, model_path: str):
        """
        加载模型
        
        Args:
            model_name: 模型名称
            model_path: 模型文件路径
        """
        model_path = Path(model_path)
        
        if 'returns' in model_name:
            model = ReturnsPredictor()
            model.load_model(str(model_path))
        elif 'risk' in model_name:
            model = RiskForecaster()
            model.load_model(str(model_path))
        else:
            raise ValueError(f"未知的模型类型: {model_name}")
        
        self.models[model_name] = model
        logger.info(f"模型已加载: {model_name}")
    
    def predict(self, model_name: str, X: pd.DataFrame) -> Any:
        """
        使用指定模型预测
        
        Args:
            model_name: 模型名称
            X: 特征数据
            
        Returns:
            预测结果
        """
        if model_name not in self.models:
            raise ValueError(f"模型 {model_name} 未加载")
        
        model = self.models[model_name]
        
        if isinstance(model, ReturnsPredictor):
            return model.predict(X)
        elif isinstance(model, RiskForecaster):
            return model.predict_risk(X)
        else:
            raise ValueError(f"未知的模型类型: {type(model)}")
    
    def get_model_comparison(self) -> pd.DataFrame:
        """
        获取模型对比表
        
        Returns:
            模型对比DataFrame
        """
        comparison = []
        
        for name, model in self.models.items():
            if isinstance(model, ReturnsPredictor) and model.is_trained:
                comparison.append({
                    'model_name': name,
                    'model_type': model.model_type,
                    'task': '回归',
                    'metric': 'R²',
                    'train_score': model.metrics['train']['r2'],
                    'test_score': model.metrics['test']['r2']
                })
            elif isinstance(model, RiskForecaster) and model.is_trained:
                comparison.append({
                    'model_name': name,
                    'model_type': model.model_type,
                    'task': '分类',
                    'metric': 'Accuracy',
                    'train_score': model.metrics['train']['accuracy'],
                    'test_score': model.metrics['test']['accuracy']
                })
        
        return pd.DataFrame(comparison)
    
    def export_model_summary(self, filepath: str):
        """
        导出模型摘要（JSON格式）
        
        Args:
            filepath: 输出文件路径
        """
        summary = {
            'training_history': self.training_history,
            'models': {}
        }
        
        for name, model in self.models.items():
            if model.is_trained:
                summary['models'][name] = {
                    'type': model.model_type,
                    'is_trained': model.is_trained,
                    'metrics': model.metrics,
                    'feature_count': len(model.feature_names) if hasattr(model, 'feature_names') else 0
                }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"模型摘要已导出: {filepath}")
