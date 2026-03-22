"""
收益预测模块
使用机器学习模型预测保单收益
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import pickle
import logging

from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class ReturnsPredictor:
    """
    收益预测器
    
    支持以下模型：
    - 随机森林 (Random Forest)
    - 梯度提升 (Gradient Boosting)
    - 岭回归 (Ridge)
    - Lasso回归
    - ElasticNet
    
    功能：
    - 训练预测模型
    - 交叉验证
    - 超参数调优
    - 特征重要性分析
    """
    
    def __init__(self, model_type: str = 'random_forest'):
        """
        初始化收益预测器
        
        Args:
            model_type: 模型类型 ('random_forest', 'gradient_boosting', 'ridge', 'lasso', 'elasticnet')
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_trained = False
        self.metrics = {}
        
        # 初始化模型
        self._init_model()
    
    def _init_model(self):
        """初始化机器学习模型"""
        if self.model_type == 'random_forest':
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == 'gradient_boosting':
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        elif self.model_type == 'ridge':
            self.model = Ridge(alpha=1.0, random_state=42)
        elif self.model_type == 'lasso':
            self.model = Lasso(alpha=0.1, random_state=42)
        elif self.model_type == 'elasticnet':
            self.model = ElasticNet(alpha=0.1, l1_ratio=0.5, random_state=42)
        else:
            raise ValueError(f"不支持的模型类型: {self.model_type}")
        
        logger.info(f"初始化模型: {self.model_type}")
    
    def train(self, 
              X: pd.DataFrame, 
              y: pd.Series,
              test_size: float = 0.2,
              scale_features: bool = True) -> Dict:
        """
        训练模型
        
        Args:
            X: 特征DataFrame
            y: 目标Series
            test_size: 测试集比例
            scale_features: 是否标准化特征
            
        Returns:
            训练指标字典
        """
        logger.info(f"开始训练模型: {self.model_type}")
        
        self.feature_names = X.columns.tolist()
        
        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        # 标准化特征
        if scale_features and self.model_type in ['ridge', 'lasso', 'elasticnet']:
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
        else:
            X_train_scaled = X_train
            X_test_scaled = X_test
        
        # 训练模型
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
        
        # 预测
        y_train_pred = self.model.predict(X_train_scaled)
        y_test_pred = self.model.predict(X_test_scaled)
        
        # 计算指标
        self.metrics = {
            'train': {
                'mse': mean_squared_error(y_train, y_train_pred),
                'rmse': np.sqrt(mean_squared_error(y_train, y_train_pred)),
                'mae': mean_absolute_error(y_train, y_train_pred),
                'r2': r2_score(y_train, y_train_pred)
            },
            'test': {
                'mse': mean_squared_error(y_test, y_test_pred),
                'rmse': np.sqrt(mean_squared_error(y_test, y_test_pred)),
                'mae': mean_absolute_error(y_test, y_test_pred),
                'r2': r2_score(y_test, y_test_pred)
            }
        }
        
        logger.info(f"模型训练完成")
        logger.info(f"训练集 R²: {self.metrics['train']['r2']:.4f}")
        logger.info(f"测试集 R²: {self.metrics['test']['r2']:.4f}")
        
        return self.metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        预测收益
        
        Args:
            X: 特征DataFrame
            
        Returns:
            预测值数组
        """
        if not self.is_trained:
            raise ValueError("模型尚未训练，请先调用train()")
        
        # 标准化
        if hasattr(self.scaler, 'mean_'):
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X
        
        predictions = self.model.predict(X_scaled)
        return predictions
    
    def cross_validate(self, X: pd.DataFrame, y: pd.Series, cv: int = 5) -> Dict:
        """
        交叉验证
        
        Args:
            X: 特征DataFrame
            y: 目标Series
            cv: 折数
            
        Returns:
            交叉验证结果
        """
        logger.info(f"开始{cv}折交叉验证...")
        
        # 标准化
        if self.model_type in ['ridge', 'lasso', 'elasticnet']:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = X
        
        # 交叉验证
        scores = cross_val_score(self.model, X_scaled, y, cv=cv, scoring='r2')
        mse_scores = -cross_val_score(self.model, X_scaled, y, cv=cv, scoring='neg_mean_squared_error')
        
        cv_results = {
            'r2_mean': scores.mean(),
            'r2_std': scores.std(),
            'mse_mean': mse_scores.mean(),
            'mse_std': mse_scores.std(),
            'r2_scores': scores.tolist(),
            'mse_scores': mse_scores.tolist()
        }
        
        logger.info(f"交叉验证 R²: {cv_results['r2_mean']:.4f} (+/- {cv_results['r2_std']*2:.4f})")
        
        return cv_results
    
    def hyperparameter_tuning(self, 
                              X: pd.DataFrame, 
                              y: pd.Series,
                              param_grid: Optional[Dict] = None,
                              cv: int = 3) -> Dict:
        """
        超参数调优
        
        Args:
            X: 特征DataFrame
            y: 目标Series
            param_grid: 参数网格
            cv: 折数
            
        Returns:
            最优参数和得分
        """
        logger.info("开始超参数调优...")
        
        # 默认参数网格
        if param_grid is None:
            if self.model_type == 'random_forest':
                param_grid = {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [5, 10, 15],
                    'min_samples_split': [2, 5, 10]
                }
            elif self.model_type == 'gradient_boosting':
                param_grid = {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [3, 5, 7],
                    'learning_rate': [0.05, 0.1, 0.2]
                }
            elif self.model_type == 'ridge':
                param_grid = {'alpha': [0.01, 0.1, 1.0, 10.0]}
            elif self.model_type == 'lasso':
                param_grid = {'alpha': [0.001, 0.01, 0.1, 1.0]}
            elif self.model_type == 'elasticnet':
                param_grid = {
                    'alpha': [0.01, 0.1, 1.0],
                    'l1_ratio': [0.2, 0.5, 0.8]
                }
        
        # 标准化
        if self.model_type in ['ridge', 'lasso', 'elasticnet']:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = X
        
        # 网格搜索
        grid_search = GridSearchCV(
            self.model,
            param_grid,
            cv=cv,
            scoring='r2',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_scaled, y)
        
        # 更新模型
        self.model = grid_search.best_estimator_
        
        results = {
            'best_params': grid_search.best_params_,
            'best_score': grid_search.best_score_,
            'cv_results': grid_search.cv_results_
        }
        
        logger.info(f"最优参数: {results['best_params']}")
        logger.info(f"最优得分: {results['best_score']:.4f}")
        
        return results
    
    def get_feature_importance(self) -> pd.DataFrame:
        """
        获取特征重要性
        
        Returns:
            特征重要性DataFrame
        """
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        # 树模型特征重要性
        if hasattr(self.model, 'feature_importances_'):
            importance = self.model.feature_importances_
        # 线性模型系数
        elif hasattr(self.model, 'coef_'):
            importance = np.abs(self.model.coef_)
        else:
            return pd.DataFrame()
        
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        return importance_df
    
    def save_model(self, filepath: str):
        """
        保存模型
        
        Args:
            filepath: 保存路径
        """
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'model_type': self.model_type,
            'metrics': self.metrics
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"模型已保存: {filepath}")
    
    def load_model(self, filepath: str):
        """
        加载模型
        
        Args:
            filepath: 模型文件路径
        """
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        self.model_type = model_data['model_type']
        self.metrics = model_data['metrics']
        self.is_trained = True
        
        logger.info(f"模型已加载: {filepath}")
    
    def predict_with_confidence(self, X: pd.DataFrame, 
                                confidence: float = 0.95) -> pd.DataFrame:
        """
        带置信区间的预测（仅支持随机森林）
        
        Args:
            X: 特征DataFrame
            confidence: 置信水平
            
        Returns:
            包含预测值和置信区间的DataFrame
        """
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        if self.model_type != 'random_forest':
            raise ValueError("置信区间预测仅支持随机森林模型")
        
        # 标准化
        if hasattr(self.scaler, 'mean_'):
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X
        
        # 获取所有树的预测
        predictions = []
        for estimator in self.model.estimators_:
            pred = estimator.predict(X_scaled)
            predictions.append(pred)
        
        predictions = np.array(predictions)
        
        # 计算统计量
        mean_pred = predictions.mean(axis=0)
        std_pred = predictions.std(axis=0)
        
        # 计算置信区间
        alpha = 1 - confidence
        lower = np.percentile(predictions, alpha/2 * 100, axis=0)
        upper = np.percentile(predictions, (1 - alpha/2) * 100, axis=0)
        
        result = pd.DataFrame({
            'prediction': mean_pred,
            'std': std_pred,
            'lower_bound': lower,
            'upper_bound': upper,
            'confidence_interval': upper - lower
        })
        
        return result
