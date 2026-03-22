#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成模拟的平安保险公司真实数据
基于平安保险真实业务逻辑和数据结构
"""

import pandas as pd
import numpy as np
from pathlib import Path

# 确保数据目录存在
raw_data_dir = Path('data/raw')
raw_data_dir.mkdir(parents=True, exist_ok=True)

# 平安保险产品类型映射
PINGAN_PRODUCTS = {
    '传统寿险': {
        'code_prefix': 'TL',
        'products': ['平安福', '守护百分百', '鑫盛'],
        'base_irr': 0.025,
        'irr_std': 0.003
    },
    '分红险': {
        'code_prefix': 'PA',
        'products': ['平安金裕人生', '平安财富金瑞', '平安御享金瑞'],
        'base_irr': 0.030,
        'irr_std': 0.004
    },
    '万能险': {
        'code_prefix': 'UL',
        'products': ['平安智胜人生', '平安聚财宝', '平安金管家'],
        'base_irr': 0.035,
        'irr_std': 0.005
    },
    '投连险': {
        'code_prefix': 'IL',
        'products': ['平安世纪理财', '平安智富人生', '平安投连优选'],
        'base_irr': 0.040,
        'irr_std': 0.015
    },
    '年金险': {
        'code_prefix': 'AN',
        'products': ['平安颐享年金', '平安鑫利', '平安年金赢家'],
        'base_irr': 0.032,
        'irr_std': 0.004
    }
}

# 平安保险业务地区分布
PINGAN_REGIONS = {
    '一线城市': ['北京', '上海', '广州', '深圳'],
    '二线城市': ['杭州', '南京', '成都', '武汉', '西安', '重庆'],
    '三线城市': ['苏州', '郑州', '长沙', '青岛', '宁波', '东莞'],
    '其他地区': ['其他省会城市', '地级市', '县级市']
}

# 客户年龄段分布
AGE_GROUPS = {
    '25-35岁': {'range': (25, 35), 'weight': 0.35},
    '36-45岁': {'range': (36, 45), 'weight': 0.30},
    '46-55岁': {'range': (46, 55), 'weight': 0.20},
    '56-65岁': {'range': (56, 65), 'weight': 0.15}
}

# 缴费期限分布
PAYMENT_TERMS = {
    3: 0.10,
    5: 0.20,
    10: 0.30,
    15: 0.20,
    20: 0.15,
    30: 0.05
}

def generate_policy_data(n_policies=5000):
    """生成保单主数据"""
    np.random.seed(42)
    
    policies = []
    
    # 产品分布权重
    product_weights = {
        '传统寿险': 0.35,
        '分红险': 0.30,
        '万能险': 0.15,
        '投连险': 0.10,
        '年金险': 0.10
    }
    
    # 地区分布权重
    region_weights = {
        '一线城市': 0.30,
        '二线城市': 0.40,
        '三线城市': 0.20,
        '其他地区': 0.10
    }
    
    for i in range(n_policies):
        # 随机选择产品类型
        product_category = np.random.choice(
            list(product_weights.keys()),
            p=list(product_weights.values())
        )
        
        product_info = PINGAN_PRODUCTS[product_category]
        product_name = np.random.choice(product_info['products'])
        product_code = f"{product_info['code_prefix']}{np.random.randint(1, 100):02d}"
        
        # 随机选择地区
        region_type = np.random.choice(
            list(region_weights.keys()),
            p=list(region_weights.values())
        )
        region = np.random.choice(PINGAN_REGIONS[region_type])
        
        # 随机选择年龄段
        age_group = np.random.choice(
            list(AGE_GROUPS.keys()),
            p=[g['weight'] for g in AGE_GROUPS.values()]
        )
        age_range = AGE_GROUPS[age_group]['range']
        insured_age = np.random.randint(age_range[0], age_range[1] + 1)
        
        # 随机选择缴费期限
        payment_term = np.random.choice(
            list(PAYMENT_TERMS.keys()),
            p=list(PAYMENT_TERMS.values())
        )
        
        # 随机生成保单信息
        issue_year = np.random.randint(2018, 2026)
        issue_month = np.random.randint(1, 13)
        issue_date = pd.Timestamp(f"{issue_year}-{issue_month:02d}-{np.random.randint(1, 29):02d}")
        
        # 保费和保额
        annual_premium = np.random.randint(5000, 200000, size=1)[0]
        sum_assured = annual_premium * np.random.randint(10, 30)
        
        # 保单状态
        policy_status = 'ACTIVE' if np.random.random() > 0.05 else 'LAPSED'
        
        policy = {
            'policy_id': f"PA{issue_year}{i:06d}",
            'product_code': product_code,
            'product_name': product_name,
            'product_category': product_category,
            'issue_date': issue_date,
            'issue_year': issue_year,
            'issue_month': issue_month,
            'annual_premium': annual_premium,
            'payment_term': payment_term,
            'sum_assured': sum_assured,
            'insured_age': insured_age,
            'region': region,
            'region_type': region_type,
            'policy_status': policy_status,
            'sales_channel': np.random.choice(['代理人', '银行', '电销', '网销']),
            'underwriter': f"UW{np.random.randint(1000, 9999):04d}"
        }
        
        policies.append(policy)
    
    return pd.DataFrame(policies)

def generate_premium_data(policy_df):
    """生成保费缴费数据"""
    premiums = []
    
    for _, policy in policy_df.iterrows():
        if policy['policy_status'] == 'LAPSED' and np.random.random() > 0.5:
            # 失效保单可能缴费不足
            actual_terms = np.random.randint(1, policy['payment_term'] + 1)
        else:
            actual_terms = policy['payment_term']
        
        for year in range(policy['issue_year'], policy['issue_year'] + actual_terms):
            # 每年缴费日期
            payment_month = policy['issue_month']
            payment_day = min(policy['issue_date'].day, 28)
            payment_date = pd.Timestamp(f"{year}-{payment_month:02d}-{payment_day:02d}")
            
            # 可能的缴费延迟
            if np.random.random() > 0.9:
                payment_date += pd.Timedelta(days=np.random.randint(1, 30))
            
            premium = {
                'policy_id': policy['policy_id'],
                'payment_date': payment_date,
                'premium_amount': policy['annual_premium'],
                'payment_year': year,
                'payment_period': year - policy['issue_year'] + 1,
                'payment_status': 'PAID' if np.random.random() > 0.02 else 'PENDING'
            }
            
            premiums.append(premium)
    
    return pd.DataFrame(premiums)

def generate_cash_value_data(policy_df):
    """生成现金价值数据"""
    cash_values = []
    
    for _, policy in policy_df.iterrows():
        product_info = PINGAN_PRODUCTS[policy['product_category']]
        base_irr = product_info['base_irr']
        irr_std = product_info['irr_std']
        
        # 计算每年的现金价值
        for year in range(policy['issue_year'], 2026):
            years_passed = year - policy['issue_year'] + 1
            
            # 现金价值增长模型
            if years_passed == 1:
                # 第一年现金价值较低
                cv_factor = 0.3
            elif years_passed == 2:
                cv_factor = 0.5
            elif years_passed == 3:
                cv_factor = 0.7
            else:
                cv_factor = min(0.95, 0.7 + (years_passed - 3) * 0.05)
            
            # 累计保费
            cumulative_premium = policy['annual_premium'] * min(years_passed, policy['payment_term'])
            
            # 投资收益
            annual_return = base_irr + np.random.normal(0, irr_std)
            investment_gain = cumulative_premium * ((1 + annual_return) ** years_passed - 1)
            
            # 现金价值 = 累计保费 * 退保系数 + 投资收益
            cash_value = cumulative_premium * cv_factor + investment_gain
            cash_value = max(0, cash_value)
            
            cv = {
                'policy_id': policy['policy_id'],
                'valuation_date': pd.Timestamp(f"{year}-12-31"),
                'cash_value': cash_value,
                'year': year,
                'years_passed': years_passed,
                'cumulative_premium': cumulative_premium
            }
            
            cash_values.append(cv)
    
    return pd.DataFrame(cash_values)

def generate_dividend_data(policy_df):
    """生成分红数据"""
    dividends = []
    
    # 只给分红险和部分年金险分红
    dividend_policies = policy_df[
        (policy_df['product_category'] == '分红险') | 
        ((policy_df['product_category'] == '年金险') & (np.random.random(len(policy_df)) > 0.5))
    ]
    
    for _, policy in dividend_policies.iterrows():
        # 分红起始时间（通常从第二年开始）
        start_year = policy['issue_year'] + 1
        
        for year in range(start_year, 2026):
            # 分红率（基于产品类型）
            if policy['product_category'] == '分红险':
                dividend_rate = 0.015 + np.random.normal(0, 0.003)
            else:  # 年金险
                dividend_rate = 0.010 + np.random.normal(0, 0.002)
            
            # 分红金额 = 累计保费 * 分红率
            years_paid = min(year - policy['issue_year'], policy['payment_term'])
            cumulative_premium = policy['annual_premium'] * years_paid
            dividend_amount = cumulative_premium * dividend_rate
            dividend_amount = max(0, dividend_amount)
            
            # 分红日期
            dividend_date = pd.Timestamp(f"{year}-06-30")
            
            div = {
                'policy_id': policy['policy_id'],
                'dividend_date': dividend_date,
                'dividend_amount': dividend_amount,
                'year': year,
                'dividend_rate': dividend_rate,
                'cumulative_premium': cumulative_premium
            }
            
            dividends.append(div)
    
    return pd.DataFrame(dividends)

def save_as_csv(df, filename):
    """保存为CSV格式"""
    df.to_csv(raw_data_dir / f"{filename}.csv", index=False, encoding='utf-8-sig')
    print(f"✓ 已生成 {filename}.csv，共 {len(df)} 条记录")

def main():
    """主函数"""
    print("开始生成平安保险模拟数据...")
    print("=" * 60)
    
    # 生成保单数据
    print("1. 生成保单数据...")
    policy_df = generate_policy_data(n_policies=5000)
    save_as_csv(policy_df, "policy")
    
    # 生成保费数据
    print("2. 生成保费数据...")
    premium_df = generate_premium_data(policy_df)
    save_as_csv(premium_df, "premium")
    
    # 生成现金价值数据
    print("3. 生成现金价值数据...")
    cash_value_df = generate_cash_value_data(policy_df)
    save_as_csv(cash_value_df, "cash_value")
    
    # 生成分红数据
    print("4. 生成分红数据...")
    dividend_df = generate_dividend_data(policy_df)
    save_as_csv(dividend_df, "dividend")
    
    print("=" * 60)
    print("数据生成完成！")
    print(f"总保单数: {len(policy_df)}")
    print(f"总保费记录: {len(premium_df)}")
    print(f"总现金价值记录: {len(cash_value_df)}")
    print(f"总分红记录: {len(dividend_df)}")

if __name__ == "__main__":
    main()
