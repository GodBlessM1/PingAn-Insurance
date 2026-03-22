# PingAn Life Returns Analyzer
# 平安寿险收益分析器

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 项目简介

平安寿险收益分析器是一个专业的保险数据分析工具，用于计算和分析平安寿险各类险种的保单收益情况。该工具支持传统寿险、分红险、万能险、投连险等多种险种的收益计算，并提供可视化报告和交互式Web仪表盘。

## 核心功能

### 1. 数据提取与处理
- 支持多种数据源 (Hive、Oracle、MySQL、本地文件)
- 自动化数据清洗与特征工程
- 数据脱敏与隐私保护

### 2. 收益计算
- **IRR (内部收益率)**: 基于现金流法的精确计算
- **年化现金价值回报率**: 衡量现金价值增长
- **分红收益率**: 分红险特有的收益指标
- **账户价值增长率**: 万能险/投连险专用

### 3. 数据分析
- 按产品、年份、客户分层多维度聚合
- 趋势分析与同比/环比对比
- 基准对比 (演示利率、结算利率、行业平均)

### 4. 数据质量验证
- 完整性检查（缺失值检测）
- 一致性检查（数据逻辑验证）
- 准确性检查（异常值检测）
- 业务规则验证
- 数据质量评分报告

### 5. 统计分析
- **假设检验**: t检验、ANOVA方差分析
- **相关性分析**: Pearson、Spearman相关系数
- **回归分析**: 线性回归、多元回归
- **正态性检验**: Jarque-Bera检验
- **驱动因素分析**: IRR关键影响因素识别

### 6. 可视化与报告
- 趋势折线图、分布箱线图、热力图
- Excel、PDF、HTML多格式报告
- 交互式Web仪表盘

## 项目结构

```
PingAn_Life_Returns_Analyzer/
├── config/                  # 配置文件
│   ├── config.yaml          # 主配置文件
│   └── __init__.py          # 配置加载模块
├── data/                    # 数据目录
│   ├── raw/                 # 原始数据 (勿提交Git)
│   └── processed/           # 处理后数据
├── src/                     # 核心代码
│   ├── extract/             # 数据提取模块
│   │   ├── data_extractor.py
│   │   ├── hive_extractor.py
│   │   └── local_extractor.py
│   ├── transform/           # 数据清洗与特征工程
│   │   ├── data_cleaner.py
│   │   ├── feature_engineer.py
│   │   └── data_pipeline.py
│   ├── calculate/           # 收益计算核心
│   │   ├── irr_calculator.py
│   │   ├── returns_calculator.py
│   │   └── policy_calculator.py
│   ├── analyze/             # 数据分析
│   │   ├── aggregator.py
│   │   ├── trend_analyzer.py
│   │   └── benchmark_analyzer.py
│   ├── validation/          # 数据验证模块
│   │   ├── data_validator.py
│   │   └── quality_reporter.py
│   ├── statistics/          # 统计分析模块
│   │   ├── hypothesis_tester.py
│   │   ├── correlation_analyzer.py
│   │   └── regression_analyzer.py
│   └── visualize/           # 可视化与报告
│       ├── chart_generator.py
│       └── report_generator.py
├── website/                 # Web仪表盘
│   └── index.html           # 交互式分析页面
├── notebooks/               # Jupyter笔记本
├── reports/                 # 输出报告
│   └── charts/              # 图表文件
├── tests/                   # 单元测试
├── logs/                    # 日志文件
├── main.py                  # 主入口
├── requirements.txt         # 依赖包
├── .gitignore              # Git忽略配置
└── README.md               # 项目说明
```

## 安装与配置

### 环境要求
- Python 3.10+
- 推荐: Anaconda 或 Miniconda

### 安装步骤

1. 克隆项目
```bash
git clone https://github.com/GodBlessM1/PingAn-Insurance.git
cd PingAn_Life_Returns_Analyzer
```

2. 创建虚拟环境
```bash
conda create -n pingan_analyzer python=3.10
conda activate pingan_analyzer
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置数据源
编辑 `config/config.yaml` 文件，配置您的数据源连接信息：
```yaml
data_source:
  type: "local"  # 或 "hive", "oracle", "mysql"
  # 根据类型配置相应参数
```

## 使用方法

### 快速开始

执行完整分析流程：
```bash
python main.py --mode full
```

### 分阶段执行

```bash
# 仅数据提取
python main.py --mode extract

# 仅数据清洗
python main.py --mode transform

# 仅收益计算
python main.py --mode calculate

# 仅数据分析
python main.py --mode analyze

# 仅数据质量验证
python main.py --mode validate

# 仅统计分析
python main.py --mode statistics

# 仅生成可视化
python main.py --mode visualize

# 仅生成报告
python main.py --mode reports
```

### 启动Web仪表盘

```bash
cd website
python -m http.server 8888
```

然后在浏览器中访问 `http://localhost:8888`

## Web仪表盘功能

### 数据仪表板
- 总览统计卡片（保单数、平均IRR、总保费、活跃保单）
- 产品IRR分布对比
- 渠道保费分布
- 年龄分布分析

### 趋势分析
- 年度IRR趋势图
- 保费趋势分析
- 产品类别趋势对比

### 分布分析
- IRR分布直方图
- 保费分布分析
- 产品类型分布饼图

### 产品对比
- 多产品IRR对比表
- 关键指标对比
- 产品性能排名

### 热力图分析
- 产品×地区交叉分析
- 渠道×年龄热力图
- 多维度数据透视

### 交叉分析
- 自定义维度组合分析
- 多指标切换
- 详细数据表格

### 地图分析
- 全国保单分布地图
- 地区排名TOP 10
- 地区数据明细表

### 统计分析
- **假设检验**: IRR差异检验、保费差异检验、地区差异检验
- **相关性分析**: 相关系数矩阵热力图
- **回归分析**: 线性回归模型、系数显著性检验
- **IRR驱动因素**: 关键影响因素排序
- **正态性检验**: 分布直方图、偏度峰度分析

## 核心指标说明

| 指标名称 | 说明 | 适用险种 |
|---------|------|---------|
| IRR | 内部收益率，考虑时间价值的年化收益率 | 全部 |
| 年化现金价值回报率 | (期末现金价值 - 累计保费) / 累计保费 / 年数 | 全部 |
| 分红收益率 | 累计分红 / 累计保费 | 分红险 |
| 账户价值增长率 | 万能账户价值的年化增长 | 万能险 |
| 净值增长率 | 投连险单位净值增长 | 投连险 |

## 配置说明

### 产品分类配置

在 `config/config.yaml` 中定义产品分类：

```yaml
product_categories:
  traditional_life:
    name: "传统寿险"
    codes: ["TL01", "TL02"]
  participating:
    name: "分红型寿险"
    codes: ["PA01", "PA02"]
  universal_life:
    name: "万能险"
    codes: ["UL01", "UL02"]
  investment_linked:
    name: "投连险"
    codes: ["IL01", "IL02"]
```

### 分析周期配置

```yaml
analysis_period:
  start_year: 2020
  end_year: 2024
```

## 数据格式要求

### 保单主表 (POLICY)
| 字段名 | 类型 | 说明 |
|-------|------|------|
| policy_id | string | 保单号 |
| product_code | string | 产品代码 |
| issue_date | date | 承保日期 |
| annual_premium | decimal | 年缴保费 |
| payment_term | int | 缴费年限 |
| sum_assured | decimal | 保额 |

### 保费流水 (PREMIUM)
| 字段名 | 类型 | 说明 |
|-------|------|------|
| policy_id | string | 保单号 |
| payment_date | date | 缴费日期 |
| premium_amount | decimal | 缴费金额 |

### 现金价值 (CASH_VALUE)
| 字段名 | 类型 | 说明 |
|-------|------|------|
| policy_id | string | 保单号 |
| valuation_date | date | 评估日期 |
| cash_value | decimal | 现金价值 |

### 分红数据 (DIVIDEND)
| 字段名 | 类型 | 说明 |
|-------|------|------|
| policy_id | string | 保单号 |
| dividend_date | date | 分红日期 |
| dividend_amount | decimal | 分红金额 |

## 输出报告

运行完成后，将在 `reports/` 目录生成：

- `summary_report.xlsx` - Excel汇总报告
- `analysis_report.html` - HTML可视化报告
- `charts/` - 图表文件

## 注意事项

1. **数据隐私**: 所有输出自动脱敏处理，不包含客户敏感信息
2. **精算口径**: 计算逻辑需与精算部门确认一致
3. **数据权限**: 确保拥有数据表访问权限
4. **合规要求**: 符合《个人信息保护法》和公司内控要求

## 开发与扩展

### 添加新的收益计算逻辑

在 `src/calculate/policy_calculator.py` 中添加新的计算方法：

```python
def _calculate_new_type_returns(self, policy_data, cashflow_data):
    # 实现新的计算逻辑
    pass
```

### 添加新的统计分析方法

在 `src/statistics/` 目录下扩展：

```python
# hypothesis_tester.py - 添加新的假设检验方法
def anova_test(self, df, value_col, group_col):
    # 实现ANOVA检验
    pass

# correlation_analyzer.py - 添加新的相关性分析方法
def partial_correlation(self, df, col1, col2, control_cols):
    # 实现偏相关分析
    pass
```

### 添加新的数据验证规则

在 `src/validation/data_validator.py` 中添加：

```python
def _check_custom_rule(self, df, rule_name):
    # 实现自定义验证规则
    pass
```

## 测试

运行单元测试：
```bash
pytest tests/
```

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 项目维护: 平安寿险数据分析团队
- GitHub: https://github.com/GodBlessM1/PingAn-Insurance

## 更新日志

### v1.1.0 (2025-03-23)
- 新增数据验证模块 (DataValidator, QualityReporter)
- 新增统计分析模块 (HypothesisTester, CorrelationAnalyzer, RegressionAnalyzer)
- 新增Web交互式仪表盘
- 新增统计分析页面（假设检验、相关性分析、回归分析、正态性检验）
- 优化网站布局，提升用户体验
- 删除未使用的模块 (ml, utils, risk_analyzer, interactive_charts)

### v1.0.0 (2024-XX-XX)
- 初始版本发布
- 支持传统寿险、分红险、万能险、投连险收益计算
- 提供趋势分析、对比分析、基准对比功能
- 支持Excel、PDF、HTML报告生成

---

**免责声明**: 本工具仅供内部数据分析使用，计算结果仅供参考，不构成投资建议。
