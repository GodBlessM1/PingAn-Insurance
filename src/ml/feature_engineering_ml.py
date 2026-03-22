"""
机器学习特征工程模块
为ML模型构建专门的特征
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from sklearn.preprocessing import StandardScaler, LabelEncoder
import logging

logger = logging.getLogger(__name__)


class MLFeatureEngineer:
    """
    机器学习特征工程类
    
    构建以下特征：
    - 时间序列特征（滞后、滑动窗口统计）
    - 比率特征
    - 编码特征
    - 交互特征
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = []
    
    def create_time_series_features(self, 
                                     df: pd.DataFrame,
                                     value_col: str,
                                     group_col: Optional[str] = None,
                                     lags: List[int] = [1, 3, 6, 12]) -> pd.DataFrame:
        """
        创建时间序列特征
        
        Args:
            df: 输入数据
            value_col: 数值列
            group_col: 分组列
            lags: 滞后阶数
            
        Returns:
            带特征的DataFrame
        """
        logger.info("创建时间序列特征...")
        result = df.copy()
        
        if group_col:
            # 按组创建滞后特征
            for lag in lags:
                result[f'{value_col}_lag_{lag}'] = result.groupby(group_col)[value_col].shift(lag)
            
            # 滑动窗口统计
            windows = [3, 6, 12]
            for window in windows:
                result[f'{value_col}_ma_{window}'] = (
                    result.groupby(group_col)[value_col]
                    .transform(lambda x: x.rolling(window=window, min_periods=1).mean())
                )
                result[f'{value_col}_std_{window}'] = (
                    result.groupby(group_col)[value_col]
                    .transform(lambda x: x.rolling(window=window, min_periods=1).std())
                )
                result[f'{value_col}_max_{window}'] = (
                    result.groupby(group_col)[value_col]
                    .transform(lambda x: x.rolling(window=window, min_periods=1).max())
                )
                result[f'{value_col}_min_{window}'] = (
                    result.groupby(group_col)[value_col]
                    .transform(lambda x: x.rolling(window=window, min_periods=1).min())
                )
        else:
            # 全局滞后特征
            for lag in lags:
                result[f'{value_col}_lag_{lag}'] = result[value_col].shift(lag)
            
            # 全局滑动窗口
            windows = [3, 6, 12]
            for window in windows:
                result[f'{value_col}_ma_{window}'] = result[value_col].rolling(window=window, min_periods=1).mean()
                result[f'{value_col}_std_{window}'] = result[value_col].rolling(window=window, min_periods=1).std()
        
        # 变化率特征
        result[f'{value_col}_change_1m'] = result[value_col].pct_change(1)
        result[f'{value_col}_change_3m'] = result[value_col].pct_change(3)
        result[f'{value_col}_change_12m'] = result[value_col].pct_change(12)
        
        logger.info(f"时间序列特征创建完成，新增 {len(result.columns) - len(df.columns)} 个特征")
        return result
    
    def create_ratio_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        创建比率特征
        
        Args:
            df: 输入数据
            
        Returns:
            带比率特征的DataFrame
        """
        logger.info("创建比率特征...")
        result = df.copy()
        
        # 保费相关比率
        if 'annual_premium' in df.columns and 'sum_assured' in df.columns:
            result['premium_coverage_ratio'] = df['annual_premium'] / df['sum_assured'].replace(0, np.nan)
        
        if 'cumulative_premium' in df.columns and 'cash_value' in df.columns:
            result['cash_value_ratio'] = df['cash_value'] / df['cumulative_premium'].replace(0, np.nan)
        
        # 年龄相关
        if 'insured_age' in df.columns:
            result['age_group'] = pd.cut(df['insured_age'], 
                                         bins=[0, 30, 40, 50, 60, 100],
                                         labels=['<30', '30-40', '40-50', '50-60', '60+'])
        
        # 时间相关
        if 'issue_year' in df.columns:
            current_year = pd.Timestamp.now().year
            result['years_since_issue'] = current_year - df['issue_year']
        
        if 'payment_term' in df.columns and 'years_since_issue' in result.columns:
            result['payment_progress'] = result['years_since_issue'] / df['payment_term'].replace(0, np.nan)
        
        logger.info(f"比率特征创建完成")
        return result
    
    def encode_categorical_features(self, 
                                     df: pd.DataFrame,
                                     categorical_cols: List[str],
                                     fit: bool = True) -> pd.DataFrame:
        """
        编码分类特征
        
        Args:
            df: 输入数据
            categorical_cols: 分类列列表
            fit: 是否拟合编码器
            
        Returns:
            编码后的DataFrame
        """
        logger.info("编码分类特征...")
        result = df.copy()
        
        for col in categorical_cols:
            if col not in df.columns:
                continue
            
            if fit:
                self.label_encoders[col] = LabelEncoder()
                result[f'{col}_encoded'] = self.label_encoders[col].fit_transform(df[col].astype(str))
            else:
                if col in self.label_encoders:
                    # 处理未见过的类别
                    result[f'{col}_encoded'] = df[col].astype(str).apply(
                        lambda x: self.label_encoders[col].transform([x])[0] 
                        if x in self.label_encoders[col].classes_ else -1
                    )
        
        return result
    
    def create_interaction_features(self, df: pd.DataFrame,
                                     numeric_cols: List[str]) -> pd.DataFrame:
        """
        创建交互特征
        
        Args:
            df: 输入数据
            numeric_cols: 数值列列表
            
        Returns:
            带交互特征的DataFrame
        """
        logger.info("创建交互特征...")
        result = df.copy()
        
        # 两两交互
        for i, col1 in enumerate(numeric_cols):
            for col2 in numeric_cols[i+1:]:
                if col1 in df.columns and col2 in df.columns:
                    result[f'{col1}_x_{col2}'] = df[col1] * df[col2]
                    result[f'{col1}_div_{col2}'] = df[col1] / (df[col2] + 1e-8)
        
        logger.info(f"交互特征创建完成")
        return result
    
    def prepare_features_for_ml(self,
                                 df: pd.DataFrame,
                                 target_col: str,
                                 feature_cols: Optional[List[str]] = None,
                                 drop_na: bool = True) -> Tuple[pd.DataFrame, pd.Series]:
        """
        准备ML特征
        
        Args:
            df: 输入数据
            target_col: 目标列
            feature_cols: 特征列列表（None则自动选择）
            drop_na: 是否删除缺失值
            
        Returns:
            (特征DataFrame, 目标Series)
        """
        logger.info("准备ML特征...")
        
        # 自动选择数值型特征
        if feature_cols is None:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            feature_cols = [c for c in numeric_cols if c != target_col]
        
        X = df[feature_cols].copy()
        y = df[target_col].copy()
        
        # 处理无穷值
        X = X.replace([np.inf, -np.inf], np.nan)
        
        # 填充缺失值
        X = X.fillna(X.median())
        
        if drop_na:
            mask = y.notna()
            X = X[mask]
            y = y[mask]
        
        self.feature_names = feature_cols
        
        logger.info(f"特征准备完成: X.shape={X.shape}, y.shape={y.shape}")
        return X, y
    
    def scale_features(self, X: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """
        标准化特征
        
        Args:
            X: 特征DataFrame
            fit: 是否拟合scaler
            
        Returns:
            标准化后的DataFrame
        """
        if fit:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = self.scaler.transform(X)
        
        return pd.DataFrame(X_scaled, columns=X.columns, index=X.index)
    
    def build_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        构建所有特征
        
        Args:
            df: 原始数据
            
        Returns:
            完整特征DataFrame
        """
        logger.info("构建完整特征集...")
        
        result = df.copy()
        
        # 时间序列特征
        if 'irr' in df.columns:
            result = self.create_time_series_features(result, 'irr', 'product_category')
        
        # 比率特征
        result = self.create_ratio_features(result)
        
        # 编码分类特征
        categorical_cols = result.select_dtypes(include=['object', 'category']).columns.tolist()
        if categorical_cols:
            result = self.encode_categorical_features(result, categorical_cols)
        
        # 交互特征
        numeric_cols = result.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [c for c in numeric_cols if 'lag' not in c and 'ma' not in c][:5]  # 限制数量
        result = self.create_interaction_features(result, numeric_cols)
        
        logger.info(f"完整特征集构建完成: {len(result.columns)} 个特征")
        return result
