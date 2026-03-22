"""
图表生成模块
使用Matplotlib、Seaborn、Plotly生成可视化图表
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# 设置中文字体 - 添加更多字体选项以兼容不同系统
plt.rcParams['font.sans-serif'] = [
    'SimHei', 'Microsoft YaHei', 'SimSun', 'KaiTi', 
    'FangSong', 'STHeiti', 'STKaiti', 'STSong',
    'DejaVu Sans', 'Arial Unicode MS', 'Segoe UI'
]
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = 'sans-serif'


class ChartGenerator:
    """
    图表生成器
    
    生成以下类型图表：
    - 趋势折线图
    - 对比柱状图
    - 分布箱线图
    - 热力图
    - 散点图
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化图表生成器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.colors = self.config.get('colors', {
            '传统寿险': '#1f77b4',
            '分红险': '#ff7f0e',
            '万能险': '#2ca02c',
            '投连险': '#d62728',
            '年金险': '#9467bd',
            '其他': '#8c564b'
        })
        self.output_dir = Path(self.config.get('output_dir', 'reports/charts'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置默认样式和字体
        sns.set_style("whitegrid")
        plt.style.use('seaborn-v0_8-whitegrid')
        
        # 确保字体设置在样式设置后仍然有效
        plt.rcParams['font.sans-serif'] = [
            'SimHei', 'Microsoft YaHei', 'SimSun', 'KaiTi', 
            'FangSong', 'STHeiti', 'STKaiti', 'STSong',
            'DejaVu Sans', 'Arial Unicode MS', 'Segoe UI'
        ]
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['font.family'] = 'sans-serif'
        
    def plot_trend(self,
                   df: pd.DataFrame,
                   x_col: str,
                   y_col: str,
                   category_col: Optional[str] = None,
                   title: str = "趋势图",
                   xlabel: str = None,
                   ylabel: str = None,
                   figsize: Tuple[int, int] = (12, 6),
                   save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制趋势折线图
        
        Args:
            df: 输入数据
            x_col: X轴列名
            y_col: Y轴列名
            category_col: 分类列名
            title: 图表标题
            xlabel: X轴标签
            ylabel: Y轴标签
            figsize: 图表尺寸
            save_path: 保存路径
            
        Returns:
            matplotlib Figure对象
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        if category_col and category_col in df.columns:
            for category in df[category_col].unique():
                data = df[df[category_col] == category]
                color = self.colors.get(category, None)
                ax.plot(data[x_col], data[y_col], marker='o', label=category, 
                       color=color, linewidth=2)
            ax.legend(loc='best')
        else:
            ax.plot(df[x_col], df[y_col], marker='o', linewidth=2, color='#1f77b4')
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(xlabel or x_col, fontsize=12)
        ax.set_ylabel(ylabel or y_col, fontsize=12)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            full_path = self.output_dir / save_path
            plt.savefig(full_path, dpi=150, bbox_inches='tight')
            logger.info(f"图表已保存: {full_path}")
        
        return fig
    
    def plot_bar_comparison(self,
                           df: pd.DataFrame,
                           x_col: str,
                           y_col: str,
                           category_col: Optional[str] = None,
                           title: str = "对比图",
                           horizontal: bool = False,
                           figsize: Tuple[int, int] = (12, 6),
                           save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制对比柱状图
        
        Args:
            df: 输入数据
            x_col: X轴列名
            y_col: Y轴列名
            category_col: 分类列名
            title: 图表标题
            horizontal: 是否水平柱状图
            figsize: 图表尺寸
            save_path: 保存路径
            
        Returns:
            matplotlib Figure对象
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        if category_col and category_col in df.columns:
            # 分组柱状图
            pivot_df = df.pivot(index=x_col, columns=category_col, values=y_col)
            pivot_df.plot(kind='barh' if horizontal else 'bar', ax=ax, 
                         color=[self.colors.get(c, None) for c in pivot_df.columns])
        else:
            if horizontal:
                ax.barh(df[x_col], df[y_col], color='#1f77b4')
            else:
                ax.bar(df[x_col], df[y_col], color='#1f77b4')
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(x_col if horizontal else y_col, fontsize=12)
        ax.set_ylabel(y_col if horizontal else x_col, fontsize=12)
        
        if not horizontal:
            plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            full_path = self.output_dir / save_path
            plt.savefig(full_path, dpi=150, bbox_inches='tight')
            logger.info(f"图表已保存: {full_path}")
        
        return fig
    
    def plot_box_distribution(self,
                             df: pd.DataFrame,
                             value_col: str,
                             category_col: str,
                             title: str = "分布图",
                             figsize: Tuple[int, int] = (12, 6),
                             save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制箱线图展示分布
        
        Args:
            df: 输入数据
            value_col: 数值列名
            category_col: 分类列名
            title: 图表标题
            figsize: 图表尺寸
            save_path: 保存路径
            
        Returns:
            matplotlib Figure对象
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        actual_categories = df[category_col].unique()
        palette = {}
        default_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
        for i, cat in enumerate(actual_categories):
            if cat in self.colors:
                palette[cat] = self.colors[cat]
            else:
                palette[cat] = default_colors[i % len(default_colors)]
        
        sns.boxplot(data=df, x=category_col, y=value_col, ax=ax,
                   hue=category_col, palette=palette, legend=False)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(category_col, fontsize=12)
        ax.set_ylabel(value_col, fontsize=12)
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if save_path:
            full_path = self.output_dir / save_path
            plt.savefig(full_path, dpi=150, bbox_inches='tight')
            logger.info(f"图表已保存: {full_path}")
        
        return fig
    
    def plot_heatmap(self,
                    df: pd.DataFrame,
                    index_col: str,
                    column_col: str,
                    value_col: str,
                    title: str = "热力图",
                    figsize: Tuple[int, int] = (12, 8),
                    save_path: Optional[str] = None,
                    annot: bool = True,
                    cmap: str = 'RdYlGn') -> plt.Figure:
        """
        绘制热力图
        
        Args:
            df: 输入数据
            index_col: 行索引列名
            column_col: 列索引列名
            value_col: 值列名
            title: 图表标题
            figsize: 图表尺寸
            save_path: 保存路径
            annot: 是否显示数值
            cmap: 颜色映射
            
        Returns:
            matplotlib Figure对象
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # 透视表
        pivot = df.pivot(index=index_col, columns=column_col, values=value_col)
        
        # 绘制热力图
        sns.heatmap(pivot, annot=annot, fmt='.2%', cmap=cmap, 
                   center=0, ax=ax, cbar_kws={'label': value_col})
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            full_path = self.output_dir / save_path
            plt.savefig(full_path, dpi=150, bbox_inches='tight')
            logger.info(f"图表已保存: {full_path}")
        
        return fig
    
    def plot_scatter(self,
                    df: pd.DataFrame,
                    x_col: str,
                    y_col: str,
                    category_col: Optional[str] = None,
                    title: str = "散点图",
                    figsize: Tuple[int, int] = (10, 8),
                    save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制散点图
        
        Args:
            df: 输入数据
            x_col: X轴列名
            y_col: Y轴列名
            category_col: 分类列名
            title: 图表标题
            figsize: 图表尺寸
            save_path: 保存路径
            
        Returns:
            matplotlib Figure对象
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        if category_col and category_col in df.columns:
            for category in df[category_col].unique():
                data = df[df[category_col] == category]
                color = self.colors.get(category, None)
                ax.scatter(data[x_col], data[y_col], label=category, 
                          alpha=0.6, s=50, color=color)
            ax.legend(loc='best')
        else:
            ax.scatter(df[x_col], df[y_col], alpha=0.6, s=50, color='#1f77b4')
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(x_col, fontsize=12)
        ax.set_ylabel(y_col, fontsize=12)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            full_path = self.output_dir / save_path
            plt.savefig(full_path, dpi=150, bbox_inches='tight')
            logger.info(f"图表已保存: {full_path}")
        
        return fig
    
    def plot_returns_dashboard(self,
                               trend_df: pd.DataFrame,
                               distribution_df: pd.DataFrame,
                               comparison_df: pd.DataFrame,
                               save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制综合收益分析仪表盘
        
        Args:
            trend_df: 趋势数据
            distribution_df: 分布数据
            comparison_df: 对比数据
            save_path: 保存路径
            
        Returns:
            matplotlib Figure对象
        """
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. 趋势图
        ax1 = axes[0, 0]
        for category in trend_df['product_category'].unique():
            data = trend_df[trend_df['product_category'] == category]
            value_col = 'irr_mean' if 'irr_mean' in data.columns else 'irr'
            ax1.plot(data['issue_year'], data[value_col], marker='o', label=category)
        ax1.set_title('各类险种IRR趋势 (2020-2024)', fontsize=12, fontweight='bold')
        ax1.set_xlabel('年份')
        ax1.set_ylabel('IRR')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 分布箱线图
        ax2 = axes[0, 1]
        actual_categories = distribution_df['product_category'].unique()
        palette = {}
        default_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
        for i, cat in enumerate(actual_categories):
            if cat in self.colors:
                palette[cat] = self.colors[cat]
            else:
                palette[cat] = default_colors[i % len(default_colors)]
        sns.boxplot(data=distribution_df, x='product_category', y='irr', ax=ax2,
                   hue='product_category', palette=palette, legend=False)
        ax2.set_title('IRR分布对比', fontsize=12, fontweight='bold')
        ax2.set_xlabel('险种')
        ax2.set_ylabel('IRR')
        ax2.tick_params(axis='x', rotation=45)
        
        # 3. 年度对比柱状图
        ax3 = axes[1, 0]
        value_col = 'irr_mean' if 'irr_mean' in comparison_df.columns else 'irr'
        pivot = comparison_df.pivot(index='issue_year', columns='product_category', values=value_col)
        pivot.plot(kind='bar', ax=ax3)
        ax3.set_title('各年度IRR对比', fontsize=12, fontweight='bold')
        ax3.set_xlabel('年份')
        ax3.set_ylabel('IRR')
        ax3.tick_params(axis='x', rotation=0)
        ax3.legend(title='险种')
        
        # 4. 统计摘要
        ax4 = axes[1, 1]
        ax4.axis('off')
        
        summary_text = "收益分析摘要\n" + "=" * 30 + "\n\n"
        
        for category in distribution_df['product_category'].unique():
            cat_data = distribution_df[distribution_df['product_category'] == category]['irr']
            summary_text += f"【{category}】\n"
            summary_text += f"  平均IRR: {cat_data.mean():.2%}\n"
            summary_text += f"  中位数: {cat_data.median():.2%}\n"
            summary_text += f"  标准差: {cat_data.std():.2%}\n\n"
        
        ax4.text(0.1, 0.9, summary_text, transform=ax4.transAxes,
                fontsize=10, verticalalignment='top')
        
        plt.suptitle('平安寿险收益分析仪表盘', fontsize=16, fontweight='bold', y=0.98)
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        if save_path:
            full_path = self.output_dir / save_path
            plt.savefig(full_path, dpi=150, bbox_inches='tight')
            logger.info(f"仪表盘已保存: {full_path}")
        
        return fig
    
    def close_all(self):
        """关闭所有图表"""
        plt.close('all')
