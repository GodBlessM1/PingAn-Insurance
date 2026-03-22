"""
风险预警模块
使用机器学习模型预测风险事件和异常
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import pickle
import logging
from datetime import datetime, timedelta

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (classification_report, confusion_matrix, 
                             roc_auc_score, roc_curve, precision_recall_curve)
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class RiskForecaster:
    """
    风险预警器
    
    功能：
    - 风险分类（高风险/低风险）
    - 异常检测
    - 风险评分
    - 预警等级划分
    """
    
    def __init__(self, model_type: str = 'random_forest'):
        """
        初始化风险预警器
        
        Args:
            model_type: 模型类型 ('random_forest', 'gradient_boosting', 'logistic', 'isolation_forest')
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_trained = False
        self.threshold = 0.5  # 风险阈值
        self.metrics = {}
        
        self._init_model()
    
    def _init_model(self):
        """初始化模型"""
        if self.model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == 'gradient_boosting':
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        elif self.model_type == 'logistic':
            self.model = LogisticRegression(random_state=42, max_iter=1000)
        elif self.model_type == 'isolation_forest':
            self.model = IsolationForest(
                n_estimators=100,
                contamination=0.1,
                random_state=42
            )
        else:
            raise ValueError(f"不支持的模型类型: {self.model_type}")
        
        logger.info(f"初始化风险预警模型: {self.model_type}")
    
    def create_risk_labels(self, 
                          df: pd.DataFrame,
                          return_col: str = 'irr',
                          volatility_col: Optional[str] = None,
                          risk_threshold: float = 0.02) -> pd.Series:
        """
        创建风险标签
        
        Args:
            df: 数据DataFrame
            return_col: 收益率列
            volatility_col: 波动率列
            risk_threshold: 风险阈值
            
        Returns:
            风险标签Series (0=低风险, 1=高风险)
        """
        logger.info("创建风险标签...")
        
        risk_labels = pd.Series(0, index=df.index)
        
        # 基于收益率判断
        if return_col in df.columns:
            # 收益率过低为高风险
            low_return = df[return_col] < risk_threshold
            risk_labels[low_return] = 1
        
        # 基于波动率判断
        if volatility_col and volatility_col in df.columns:
            # 波动率过高为高风险
            high_volatility = df[volatility_col] > df[volatility_col].quantile(0.8)
            risk_labels[high_volatility] = 1
        
        # 基于最大回撤判断
        if 'max_drawdown' in df.columns:
            large_drawdown = df['max_drawdown'] < -0.05  # 回撤超过5%
            risk_labels[large_drawdown] = 1
        
        # 基于VaR判断
        if 'var_95' in df.columns:
            high_var_risk = df['var_95'] < -0.03  # VaR小于-3%
            risk_labels[high_var_risk] = 1
        
        logger.info(f"风险标签分布: 低风险={(risk_labels==0).sum()}, 高风险={(risk_labels==1).sum()}")
        
        return risk_labels
    
    def train(self,
              X: pd.DataFrame,
              y: pd.Series,
              test_size: float = 0.2,
              scale_features: bool = True) -> Dict:
        """
        训练风险预警模型
        
        Args:
            X: 特征DataFrame
            y: 风险标签 (0=低风险, 1=高风险)
            test_size: 测试集比例
            scale_features: 是否标准化
            
        Returns:
            训练指标
        """
        logger.info(f"开始训练风险预警模型: {self.model_type}")
        
        self.feature_names = X.columns.tolist()
        
        # 划分数据集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # 标准化
        if scale_features and self.model_type in ['logistic']:
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
        else:
            X_train_scaled = X_train
            X_test_scaled = X_test
        
        # 训练
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
        
        # 预测
        y_train_pred = self.model.predict(X_train_scaled)
        y_test_pred = self.model.predict(X_test_scaled)
        y_test_proba = self.model.predict_proba(X_test_scaled)[:, 1] if hasattr(self.model, 'predict_proba') else None
        
        # 计算指标
        self.metrics = {
            'train': {
                'accuracy': (y_train_pred == y_train).mean(),
                'confusion_matrix': confusion_matrix(y_train, y_train_pred).tolist()
            },
            'test': {
                'accuracy': (y_test_pred == y_test).mean(),
                'confusion_matrix': confusion_matrix(y_test, y_test_pred).tolist(),
                'classification_report': classification_report(y_test, y_test_pred, output_dict=True)
            }
        }
        
        if y_test_proba is not None:
            self.metrics['test']['roc_auc'] = roc_auc_score(y_test, y_test_proba)
        
        logger.info(f"模型训练完成")
        logger.info(f"测试集准确率: {self.metrics['test']['accuracy']:.4f}")
        if 'roc_auc' in self.metrics['test']:
            logger.info(f"测试集 AUC: {self.metrics['test']['roc_auc']:.4f}")
        
        return self.metrics
    
    def predict_risk(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        预测风险
        
        Args:
            X: 特征DataFrame
            
        Returns:
            风险预测结果DataFrame
        """
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        # 标准化
        if hasattr(self.scaler, 'mean_'):
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X
        
        # 预测
        risk_pred = self.model.predict(X_scaled)
        
        result = pd.DataFrame({
            'risk_label': risk_pred,
            'risk_level': ['低风险' if r == 0 else '高风险' for r in risk_pred]
        })
        
        # 概率预测
        if hasattr(self.model, 'predict_proba'):
            proba = self.model.predict_proba(X_scaled)
            result['risk_probability'] = proba[:, 1]
            result['confidence'] = np.max(proba, axis=1)
        
        return result
    
    def detect_anomalies(self, X: pd.DataFrame, 
                         contamination: float = 0.1) -> pd.DataFrame:
        """
        异常检测
        
        Args:
            X: 特征DataFrame
            contamination: 异常比例
            
        Returns:
            异常检测结果
        """
        logger.info("执行异常检测...")
        
        # 使用隔离森林
        iso_forest = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=42
        )
        
        # 标准化
        X_scaled = self.scaler.fit_transform(X)
        
        # 预测
        anomaly_labels = iso_forest.fit_predict(X_scaled)
        anomaly_scores = iso_forest.decision_function(X_scaled)
        
        result = pd.DataFrame({
            'is_anomaly': anomaly_labels == -1,
            'anomaly_score': -anomaly_scores  # 转换为正值，越大越异常
        })
        
        anomaly_count = result['is_anomaly'].sum()
        logger.info(f"检测到 {anomaly_count} 个异常样本 ({anomaly_count/len(X)*100:.2f}%)")
        
        return result
    
    def calculate_risk_score(self, X: pd.DataFrame) -> pd.Series:
        """
        计算风险评分 (0-100)
        
        Args:
            X: 特征DataFrame
            
        Returns:
            风险评分Series
        """
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        # 标准化
        if hasattr(self.scaler, 'mean_'):
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X
        
        # 获取概率
        if hasattr(self.model, 'predict_proba'):
            proba = self.model.predict_proba(X_scaled)[:, 1]
            # 转换为0-100分
            risk_score = (proba * 100).round(2)
        else:
            # 使用预测结果
            pred = self.model.predict(X_scaled)
            risk_score = pd.Series(pred * 100, index=X.index)
        
        return risk_score
    
    def get_risk_alerts(self, 
                       df: pd.DataFrame,
                       risk_scores: pd.Series,
                       alert_levels: Dict[str, Tuple[float, str]] = None) -> pd.DataFrame:
        """
        获取风险预警
        
        Args:
            df: 原始数据
            risk_scores: 风险评分
            alert_levels: 预警等级配置
            
        Returns:
            预警信息DataFrame
        """
        if alert_levels is None:
            alert_levels = {
                'info': (0, 30, '正常'),
                'warning': (30, 60, '关注'),
                'danger': (60, 80, '警告'),
                'critical': (80, 100, '危险')
            }
        
        alerts = []
        
        for idx, score in risk_scores.items():
            for level, (min_score, max_score, desc) in alert_levels.items():
                if min_score <= score < max_score:
                    alerts.append({
                        'index': idx,
                        'risk_score': score,
                        'alert_level': level,
                        'alert_description': desc,
                        'alert_time': datetime.now()
                    })
                    break
        
        alerts_df = pd.DataFrame(alerts)
        
        # 合并原始数据
        if not alerts_df.empty:
            alerts_df = alerts_df.merge(
                df.reset_index(),
                left_on='index',
                right_index=True,
                how='left'
            )
        
        return alerts_df
    
    def get_feature_importance(self) -> pd.DataFrame:
        """
        获取特征重要性
        
        Returns:
            特征重要性DataFrame
        """
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        if hasattr(self.model, 'feature_importances_'):
            importance = self.model.feature_importances_
        elif hasattr(self.model, 'coef_'):
            importance = np.abs(self.model.coef_[0])
        else:
            return pd.DataFrame()
        
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        return importance_df
    
    def cross_validate(self, X: pd.DataFrame, y: pd.Series, cv: int = 5) -> Dict:
        """
        交叉验证
        
        Args:
            X: 特征DataFrame
            y: 标签
            cv: 折数
            
        Returns:
            交叉验证结果
        """
        logger.info(f"开始{cv}折交叉验证...")
        
        # 标准化
        if self.model_type in ['logistic']:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = X
        
        # 交叉验证
        scores = cross_val_score(self.model, X_scaled, y, cv=cv, scoring='accuracy')
        roc_scores = cross_val_score(self.model, X_scaled, y, cv=cv, scoring='roc_auc')
        
        cv_results = {
            'accuracy_mean': scores.mean(),
            'accuracy_std': scores.std(),
            'roc_auc_mean': roc_scores.mean(),
            'roc_auc_std': roc_scores.std()
        }
        
        logger.info(f"交叉验证准确率: {cv_results['accuracy_mean']:.4f}")
        
        return cv_results
    
    def save_model(self, filepath: str):
        """保存模型"""
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'model_type': self.model_type,
            'metrics': self.metrics,
            'threshold': self.threshold
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"风险预警模型已保存: {filepath}")
    
    def load_model(self, filepath: str):
        """加载模型"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        self.model_type = model_data['model_type']
        self.metrics = model_data['metrics']
        self.threshold = model_data.get('threshold', 0.5)
        self.is_trained = True
        
        logger.info(f"风险预警模型已加载: {filepath}")
