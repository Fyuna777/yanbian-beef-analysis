# utils/calculations.py
"""
财务计算与模拟函数模块
此模块包含所有核心业务逻辑计算函数
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, List, Optional

# 业务常量
TOTAL_OUTPUT = 200  # 总产量（斤）
DEFAULT_SALES_PRICE = 198  # 默认销售单价
N_SIMULATIONS = 10000  # 蒙特卡洛模拟次数
PRICE_ELASTICITY = -1.5  # 价格弹性系数


def calculate_financials(
    investment_unit: float,
    sales_price: float,
    sales_achievement: float,
    mortality_rate: float,
    total_output: int = TOTAL_OUTPUT,
    guaranteed_return_rate: float = 0.06
) -> Dict[str, float]:
    """
    计算所有关键财务指标
    
    Args:
        investment_unit: 投资单元金额（元/头）
        sales_price: 销售单价（元/斤）
        sales_achievement: 销量达成率（%）
        mortality_rate: 牛只死亡率（%）
        total_output: 总产量（斤），默认200
        guaranteed_return_rate: 保底收益率，默认6%
    
    Returns:
        包含所有财务指标的字典
    """
    # 计算销量、收入、成本
    sales_volume = total_output * (sales_achievement / 100)
    revenue = sales_volume * sales_price
    total_cost = investment_unit * (1 + mortality_rate / 100)
    guaranteed_return = investment_unit * guaranteed_return_rate
    
    # 计算利润和回报率
    net_profit = revenue - total_cost
    roi = (net_profit / total_cost) * 100 if total_cost > 0 else 0
    
    # 计算保本点
    breakeven_sales = (total_cost + guaranteed_return) / sales_price
    breakeven_rate = (breakeven_sales / total_output) * 100 if total_output > 0 else 0
    
    return {
        'sales_volume': sales_volume,
        'revenue': revenue,
        'total_cost': total_cost,
        'guaranteed_return': guaranteed_return,
        'net_profit': net_profit,
        'roi': roi,
        'breakeven_sales': breakeven_sales,
        'breakeven_rate': breakeven_rate
    }


def calculate_sensitivity_analysis(
    base_price: float,
    base_volume: float,
    base_cost: float,
    price_range: float = 0.2,
    volume_range: float = 0.3,
    cost_range: float = 0.15
) -> Tuple[List[str], List[float], List[float]]:
    """
    龙卷风图敏感性分析
    
    Args:
        base_price: 基准销售单价
        base_volume: 基准销量
        base_cost: 基准总成本
        price_range: 价格波动范围，默认±20%
        volume_range: 销量波动范围，默认±30%
        cost_range: 成本波动范围，默认±15%
    
    Returns:
        (影响因素列表, 负面影响列表, 正面影响列表)
    """
    factors = ['销售单价', '销量达成率', '牛只死亡率', '投资成本']
    
    # 计算各因素的敏感系数
    price_impact = base_price * base_volume * price_range
    volume_impact = base_price * base_volume * volume_range
    mortality_impact = base_cost * cost_range * 0.5
    cost_impact = base_cost * cost_range
    
    impact_low = [-price_impact, -volume_impact, -mortality_impact, -cost_impact]
    impact_high = [price_impact, volume_impact, mortality_impact, cost_impact]
    
    return factors, impact_low, impact_high


def run_advanced_monte_carlo(
    n_simulations: int,
    sales_price: float,
    expected_volume: float,
    total_cost: float,
    mortality_rate: float,
    guaranteed_return: float,
    use_advanced: bool = True
) -> Dict[str, any]:
    """
    高级蒙特卡洛模拟函数
    
    Args:
        n_simulations: 模拟次数
        sales_price: 销售单价
        expected_volume: 期望销量
        total_cost: 总成本
        mortality_rate: 牛只死亡率
        guaranteed_return: 保底收益
        use_advanced: 是否使用高级模型，True为高级，False为基础
    
    Returns:
        包含模拟结果的字典
    """
    np.random.seed(42)  # 确保结果可复现
    
    if use_advanced:
        # 高级模型：引入价格弹性和对数正态分布
        # 1. 价格服从对数正态分布（避免负价格）
        mu = np.log(sales_price * 0.95)  # 略低于当前售价
        sigma = 0.2
        price_sim = np.random.lognormal(mu, sigma, n_simulations)
        
        # 2. 销量与价格负相关（价格弹性）
        demand_shift = (price_sim / sales_price - 1) * PRICE_ELASTICITY
        volume_sim = expected_volume * (1 + demand_shift) + np.random.normal(0, 10, n_simulations)
        volume_sim = np.maximum(volume_sim, 0)  # 销量不能为负
        
        # 3. 成本：固定成本 + 可变成本
        fixed_cost = total_cost * 0.7
        variable_cost_per_unit = 50
        cost_sim = fixed_cost + variable_cost_per_unit * volume_sim
        
    else:
        # 基础模型：独立正态分布
        price_sim = np.random.normal(sales_price, 20, n_simulations)
        volume_sim = np.random.normal(expected_volume, 30, n_simulations)
        cost_sim = np.random.normal(total_cost * (1 + mortality_rate/100), 1000, n_simulations)
    
    # 计算利润
    profit_sim = price_sim * volume_sim - cost_sim
    
    # 计算风险指标
    var_95 = np.percentile(profit_sim, 5)
    success_rate = np.sum(profit_sim > guaranteed_return) / n_simulations * 100
    
    return {
        'profit_sim': profit_sim,
        'var_95': var_95,
        'success_rate': success_rate,
        'price_sim': price_sim if use_advanced else None,
        'volume_sim': volume_sim if use_advanced else None,
        'model_type': 'advanced' if use_advanced else 'basic',
        'n_simulations': n_simulations
    }
    