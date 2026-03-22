"""
交互式图表生成模块
使用Plotly生成交互式可视化图表
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# 尝试导入plotly
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import plotly.offline as pyo
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("Plotly未安装，交互式图表功能不可用")


class InteractiveChartGenerator:
    """
    交互式图表生成器
    
    生成以下交互式图表：
    - 交互式趋势图
    - 交互式散点图
    - 交互式热力图
    - 交互式箱线图
    - 交互式仪表盘
    - 3D可视化
    """
    
    def __init__(self, output_dir: str = 'reports/charts'):
        """
        初始化交互式图表生成器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if not PLOTLY_AVAILABLE:
            logger.error("Plotly库未安装，请运行: pip install plotly")
        
        # 默认配色方案
        self.color_scheme = {
            '传统寿险': '#1f77b4',
            '分红险': '#ff7f0e',
            '万能险': '#2ca02c',
            '投连险': '#d62728',
            '年金险': '#9467bd',
            '其他': '#8c564b'
        }
    
    def create_interactive_trend(self, 
                                  df: pd.DataFrame,
                                  x_col: str,
                                  y_col: str,
                                  color_col: Optional[str] = None,
                                  title: str = "趋势分析",
                                  hover_data: Optional[List[str]] = None) -> Optional[Any]:
        """
        创建交互式趋势图
        
        Args:
            df: 数据DataFrame
            x_col: X轴列
            y_col: Y轴列
            color_col: 颜色分组列
            title: 图表标题
            hover_data: 悬停显示的数据列
            
        Returns:
            Plotly图表对象
        """
        if not PLOTLY_AVAILABLE:
            logger.error("Plotly不可用，无法创建交互式图表")
            return None
        
        try:
            fig = px.line(
                df,
                x=x_col,
                y=y_col,
                color=color_col,
                title=title,
                hover_data=hover_data,
                markers=True
            )
            
            fig.update_layout(
                xaxis_title=x_col,
                yaxis_title=y_col,
                hovermode='x unified',
                legend_title_text=color_col if color_col else '',
                template='plotly_white'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"创建交互式趋势图失败: {e}")
            return None
    
    def create_interactive_scatter(self,
                                   df: pd.DataFrame,
                                   x_col: str,
                                   y_col: str,
                                   color_col: Optional[str] = None,
                                   size_col: Optional[str] = None,
                                   title: str = "散点分析",
                                   hover_data: Optional[List[str]] = None) -> Optional[Any]:
        """
        创建交互式散点图
        
        Args:
            df: 数据DataFrame
            x_col: X轴列
            y_col: Y轴列
            color_col: 颜色分组列
            size_col: 气泡大小列
            title: 图表标题
            hover_data: 悬停显示的数据列
            
        Returns:
            Plotly图表对象
        """
        if not PLOTLY_AVAILABLE:
            return None
        
        try:
            fig = px.scatter(
                df,
                x=x_col,
                y=y_col,
                color=color_col,
                size=size_col,
                title=title,
                hover_data=hover_data,
                opacity=0.7
            )
            
            fig.update_layout(
                xaxis_title=x_col,
                yaxis_title=y_col,
                template='plotly_white'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"创建交互式散点图失败: {e}")
            return None
    
    def create_interactive_heatmap(self,
                                   df: pd.DataFrame,
                                   x_col: str,
                                   y_col: str,
                                   value_col: str,
                                   title: str = "热力图") -> Optional[Any]:
        """
        创建交互式热力图
        
        Args:
            df: 数据DataFrame
            x_col: X轴列
            y_col: Y轴列
            value_col: 值列
            title: 图表标题
            
        Returns:
            Plotly图表对象
        """
        if not PLOTLY_AVAILABLE:
            return None
        
        try:
            # 透视数据
            pivot_df = df.pivot(index=y_col, columns=x_col, values=value_col)
            
            fig = px.imshow(
                pivot_df,
                title=title,
                color_continuous_scale='RdYlGn',
                aspect='auto'
            )
            
            fig.update_layout(
                xaxis_title=x_col,
                yaxis_title=y_col
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"创建交互式热力图失败: {e}")
            return None
    
    def create_interactive_box(self,
                               df: pd.DataFrame,
                               y_col: str,
                               x_col: Optional[str] = None,
                               title: str = "分布分析") -> Optional[Any]:
        """
        创建交互式箱线图
        
        Args:
            df: 数据DataFrame
            y_col: Y轴列（数值）
            x_col: X轴列（分类）
            title: 图表标题
            
        Returns:
            Plotly图表对象
        """
        if not PLOTLY_AVAILABLE:
            return None
        
        try:
            fig = px.box(
                df,
                x=x_col,
                y=y_col,
                title=title,
                points='all'  # 显示所有数据点
            )
            
            fig.update_layout(
                xaxis_title=x_col if x_col else '',
                yaxis_title=y_col,
                template='plotly_white'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"创建交互式箱线图失败: {e}")
            return None
    
    def create_interactive_dashboard(self,
                                     trend_df: pd.DataFrame,
                                     scatter_df: pd.DataFrame,
                                     title: str = "综合分析仪表盘") -> Optional[Any]:
        """
        创建交互式综合仪表盘
        
        Args:
            trend_df: 趋势数据
            scatter_df: 散点数据
            title: 仪表盘标题
            
        Returns:
            Plotly图表对象
        """
        if not PLOTLY_AVAILABLE:
            return None
        
        try:
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('趋势分析', '分布散点', '类别对比', '统计摘要'),
                specs=[
                    [{"type": "scatter"}, {"type": "scatter"}],
                    [{"type": "bar"}, {"type": "table"}]
                ]
            )
            
            # 添加趋势图
            if 'issue_year' in trend_df.columns and 'irr_mean' in trend_df.columns:
                for category in trend_df.get('product_category', pd.Series()).unique():
                    cat_data = trend_df[trend_df.get('product_category') == category]
                    fig.add_trace(
                        go.Scatter(
                            x=cat_data['issue_year'],
                            y=cat_data['irr_mean'],
                            name=f'{category}趋势',
                            mode='lines+markers'
                        ),
                        row=1, col=1
                    )
            
            # 添加散点图
            if 'irr' in scatter_df.columns and 'annual_return_rate' in scatter_df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=scatter_df['irr'],
                        y=scatter_df['annual_return_rate'],
                        mode='markers',
                        name='收益分布',
                        marker=dict(
                            size=8,
                            color=scatter_df.get('product_category', 'blue'),
                            opacity=0.6
                        )
                    ),
                    row=1, col=2
                )
            
            # 添加柱状图
            if 'product_category' in scatter_df.columns:
                category_counts = scatter_df['product_category'].value_counts()
                fig.add_trace(
                    go.Bar(
                        x=category_counts.index,
                        y=category_counts.values,
                        name='保单数量'
                    ),
                    row=2, col=1
                )
            
            # 添加统计表
            if 'irr' in scatter_df.columns:
                stats_data = {
                    '指标': ['平均值', '中位数', '标准差', '最小值', '最大值'],
                    'IRR': [
                        f"{scatter_df['irr'].mean():.4f}",
                        f"{scatter_df['irr'].median():.4f}",
                        f"{scatter_df['irr'].std():.4f}",
                        f"{scatter_df['irr'].min():.4f}",
                        f"{scatter_df['irr'].max():.4f}"
                    ]
                }
                fig.add_trace(
                    go.Table(
                        header=dict(values=list(stats_data.keys())),
                        cells=dict(values=list(stats_data.values()))
                    ),
                    row=2, col=2
                )
            
            fig.update_layout(
                title=title,
                height=800,
                showlegend=True
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"创建交互式仪表盘失败: {e}")
            return None
    
    def create_3d_scatter(self,
                          df: pd.DataFrame,
                          x_col: str,
                          y_col: str,
                          z_col: str,
                          color_col: Optional[str] = None,
                          title: str = "3D分析") -> Optional[Any]:
        """
        创建3D散点图
        
        Args:
            df: 数据DataFrame
            x_col: X轴列
            y_col: Y轴列
            z_col: Z轴列
            color_col: 颜色分组列
            title: 图表标题
            
        Returns:
            Plotly图表对象
        """
        if not PLOTLY_AVAILABLE:
            return None
        
        try:
            fig = px.scatter_3d(
                df,
                x=x_col,
                y=y_col,
                z=z_col,
                color=color_col,
                title=title,
                opacity=0.7
            )
            
            fig.update_layout(
                scene=dict(
                    xaxis_title=x_col,
                    yaxis_title=y_col,
                    zaxis_title=z_col
                )
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"创建3D散点图失败: {e}")
            return None
    
    def save_chart(self, fig, filename: str, format: str = 'html') -> Optional[Path]:
        """
        保存图表
        
        Args:
            fig: Plotly图表对象
            filename: 文件名
            format: 格式 ('html', 'png', 'json')
            
        Returns:
            保存的文件路径
        """
        if fig is None:
            return None
        
        try:
            output_path = self.output_dir / f"{filename}.{format}"
            
            if format == 'html':
                fig.write_html(str(output_path))
            elif format == 'png':
                fig.write_image(str(output_path))
            elif format == 'json':
                fig.write_json(str(output_path))
            else:
                logger.warning(f"不支持的格式: {format}")
                return None
            
            logger.info(f"交互式图表已保存: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"保存图表失败: {e}")
            return None
    
    def create_risk_return_scatter(self,
                                   df: pd.DataFrame,
                                   return_col: str = 'irr',
                                   risk_col: str = 'volatility',
                                   category_col: str = 'product_category',
                                   title: str = "风险-收益分析") -> Optional[Any]:
        """
        创建风险-收益散点图
        
        Args:
            df: 数据DataFrame
            return_col: 收益率列
            risk_col: 风险列（波动率）
            category_col: 类别列
            title: 图表标题
            
        Returns:
            Plotly图表对象
        """
        if not PLOTLY_AVAILABLE:
            return None
        
        try:
            fig = px.scatter(
                df,
                x=risk_col,
                y=return_col,
                color=category_col,
                title=title,
                labels={
                    risk_col: '风险（波动率）',
                    return_col: '收益率'
                },
                size='policy_count' if 'policy_count' in df.columns else None,
                hover_data=['policy_count'] if 'policy_count' in df.columns else None
            )
            
            # 添加象限分割线
            mean_return = df[return_col].mean()
            mean_risk = df[risk_col].mean()
            
            fig.add_hline(y=mean_return, line_dash="dash", line_color="gray")
            fig.add_vline(x=mean_risk, line_dash="dash", line_color="gray")
            
            # 添加象限标注
            fig.add_annotation(x=mean_risk*0.5, y=mean_return*1.1, 
                              text="低风险高收益", showarrow=False)
            fig.add_annotation(x=mean_risk*1.5, y=mean_return*1.1, 
                              text="高风险高收益", showarrow=False)
            
            fig.update_layout(template='plotly_white')
            
            return fig
            
        except Exception as e:
            logger.error(f"创建风险-收益散点图失败: {e}")
            return None
