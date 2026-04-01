"""
延边黄牛肉高端品牌 - 数据驱动的商业模式验证仪表板
作者：方裕娜
版本：2.0 (优化版)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta
import plotly.io as pio
# 在文件开头的导入部分添加
from ai_assistant import AIAssistant, get_app_context

# 导入自定义计算模块
from utils.calculations import (
    calculate_financials, 
    calculate_sensitivity_analysis, 
    run_advanced_monte_carlo,
    TOTAL_OUTPUT,
    N_SIMULATIONS
)

# ===== 修复：解决 timedelta JSON 序列化问题 =====
class CustomJSONEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理timedelta等特殊类型"""
    def default(self, obj):
        if isinstance(obj, (np.generic, np.ndarray)):
            return obj.tolist() if isinstance(obj, np.ndarray) else obj.item()
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif isinstance(obj, timedelta):
            return obj.total_seconds()  # 将timedelta转换为秒数
        elif hasattr(obj, 'isoformat'):
            return obj.isoformat()
        return super().default(obj)

# 覆盖plotly的默认JSON编码器
pio.json.config.default_encoder = CustomJSONEncoder

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="延边黄牛肉数据分析 | 方裕娜",
    page_icon="🐂",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 自定义CSS样式 ====================
# 定义全局颜色主题
COLOR_PRIMARY = "#3B82F6"  # 蓝色
COLOR_SUCCESS = "#10B981"  # 绿色
COLOR_WARNING = "#F59E0B"  # 橙色
COLOR_DANGER = "#EF4444"   # 红色
COLOR_NEUTRAL = "#6B7280"  # 灰色

# 图表颜色序列
PLOTLY_COLOR_SEQUENCE = [COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER, COLOR_NEUTRAL]

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E293B;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #64748B;
        text-align: center;
        margin-bottom: 2rem;
    }
    .kpi-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
    }
    .kpi-value {
        font-size: 2.5rem;
        font-weight: 700;
    }
    .kpi-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .metric-container {
        background-color: #F8FAFC;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3B82F6;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 初始化会话状态 ====================
# 在侧边栏渲染前，确保所有可能由侧边栏控件控制的session_state变量都有初始值
# 这能极大避免前端渲染时的状态不一致错误
if 'use_advanced_model' not in st.session_state:
    st.session_state.use_advanced_model = False
# 可以继续初始化其他可能由控件影响的状态，例如：
# if 'some_slider_value' not in st.session_state:
#     st.session_state.some_slider_value = 100


# ==================== 侧边栏参数控制 ====================
with st.sidebar:
    st.header("🎛️ 参数调整")
    st.markdown("---")
    
    # 财务参数
    st.subheader("💰 财务参数")
    investment_unit = st.slider(
        "投资单元金额（元/头）",
        min_value=5000,
        max_value=20000,
        value=10000,
        step=1000
    )
    
    guaranteed_return_rate = st.slider(
        "保底收益率（%）",
        min_value=3.0,
        max_value=15.0,
        value=6.0,
        step=0.5
    )
    
    sales_price = st.slider(
        "销售单价（元/斤）",
        min_value=150,
        max_value=250,
        value=198,
        step=5
    )
    
    # 运营参数
    st.subheader("📊 运营参数")
    sales_achievement = st.slider(
        "销量达成率（%）",
        min_value=20,
        max_value=100,
        value=75,
        step=5
    )
    
    mortality_rate = st.slider(
        "牛只死亡率（%）",
        min_value=0,
        max_value=20,
        value=5,
        step=1
    )
    
    # 营销预算
    st.subheader("📢 营销预算")
    marketing_budget = st.slider(
        "总营销预算（万元）",
        min_value=5,
        max_value=15,
        value=8,
        step=1
    )
    
    st.markdown("---")
    
    # 模型复杂度选择
    st.subheader("🧠 模型复杂度")
    use_advanced_model = st.checkbox(
        "启用高级风险模型", 
        value=False,
        help="启用价格弹性、对数正态分布等高级假设"
    )
    
    st.info("💡 **提示**：拖动滑块实时查看分析结果变化")
    
    # GitHub链接
    st.markdown("""
    ### 🔗 项目链接
    - [GitHub仓库](https://github.com/Fyuna777/yanbian-beef-analysis)
    - [在线作品](https://Fyuna777.github.io/yanbian-beef-analysis/)
    """)

# ==================== 主标题区 ====================
st.markdown('<h1 class="main-header">🐂 数据驱动的商业模式验证</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">延边黄牛肉高端品牌全链路分析 | 项目负责人：方裕娜 | 2025年3月-7月</p>', unsafe_allow_html=True)

# ==================== 财务指标计算 ====================
# 使用模块化函数计算财务指标
financials = calculate_financials(
    investment_unit=investment_unit,
    sales_price=sales_price,
    sales_achievement=sales_achievement,
    mortality_rate=mortality_rate,
    total_output=TOTAL_OUTPUT,
    guaranteed_return_rate=guaranteed_return_rate/100
)

# 解包财务指标
sales_volume = financials['sales_volume']
revenue = financials['revenue']
total_cost = financials['total_cost']
guaranteed_return = financials['guaranteed_return']
net_profit = financials['net_profit']
roi = financials['roi']
breakeven_sales = financials['breakeven_sales']
breakeven_rate = financials['breakeven_rate']

# ==================== KPI指标卡片 ====================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="kpi-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
        <div class="kpi-value">{sales_achievement:.0f}%</div>
        <div class="kpi-label">销量达成率</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
        <div class="kpi-value">¥{revenue:,.0f}</div>
        <div class="kpi-label">预期收入</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
        <div class="kpi-value">{roi:.1f}%</div>
        <div class="kpi-label">投资回报率</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
        <div class="kpi-value">{breakeven_rate:.1f}%</div>
        <div class="kpi-label">保本产销率</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==================== 选项卡式内容区 ====================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 财务可行性分析",
    "📈 营销渠道归因",
    "⚠️ 风险量化模拟",
    "👥 用户画像分析",
    "📅 项目时间线"
])

# ==================== Tab 1: 财务可行性分析 ====================
with tab1:
    st.header("💰 财务可行性预测模型")
    
    # 添加分析叙事
    st.info(f"""
    **分析目标**：验证商业模式在给定约束下的财务可行性，识别关键风险因素。  
    **核心方法**：动态财务模型 + 龙卷风图敏感性分析。  
    **关键结论**：在当前参数下，仅需售出 **{breakeven_sales:.1f}斤**（{breakeven_rate:.1f}%）即可覆盖保底收益，**投资回报率{roi:.1f}%**。
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 龙卷风图 - 敏感性分析
        st.subheader("🌪️ 敏感性分析（龙卷风图）")
        
        # 使用模块化函数进行敏感性分析
        try:
            factors, impact_low, impact_high = calculate_sensitivity_analysis(
                base_price=sales_price,
                base_volume=TOTAL_OUTPUT * (sales_achievement/100),
                base_cost=total_cost
            )
            
            fig_tornado = go.Figure()
            
            fig_tornado.add_trace(go.Bar(
                y=factors,
                x=impact_low,
                orientation='h',
                name='负面情景',
                marker_color=COLOR_DANGER
            ))
            
            fig_tornado.add_trace(go.Bar(
                y=factors,
                x=impact_high,
                orientation='h',
                name='正面情景',
                marker_color=COLOR_SUCCESS
            ))
            
            fig_tornado.update_layout(
                barmode='relative',
                height=400,
                xaxis_title="净利润影响（元）",
                showlegend=True,
                template="plotly_white"
            )
            
            st.plotly_chart(fig_tornado, use_container_width=True)
            
        except Exception as e:
            st.error(f"生成敏感性分析图表时出错: {e}")
            st.info("请检查输入参数是否在合理范围内。")
    
    with col2:
        # 关键财务指标
        st.subheader("📋 核心财务指标")
        
        st.metric("总投资额", f"¥{investment_unit:,.0f}")
        st.metric("预期收入", f"¥{revenue:,.0f}")
        st.metric("总成本", f"¥{total_cost:,.0f}")
        st.metric("净利润", f"¥{net_profit:,.0f}", delta=f"{roi:.1f}%")
        st.metric("保本销量", f"{breakeven_sales:.1f} 斤")
        st.metric("保本产销率", f"{breakeven_rate:.1f}%")
        
        st.info(f"""
        💡 **关键洞察**：
        - 仅需售出 **{breakeven_sales:.1f} 斤**（{breakeven_rate:.1f}%）即可覆盖{guaranteed_return_rate}%保底收益
        - 当前销量达成率 **{sales_achievement}%** 下，预期净利润 **¥{net_profit:,.0f}**
        - 投资回报率 **{roi:.1f}%**，高于行业平均水平
        """)

# ==================== Tab 2: 营销渠道归因 ====================
with tab2:
    st.header("📈 营销渠道归因与 A/B 测试分析")
    
    # 添加分析叙事
    st.info("""
    **分析目标**：量化各营销渠道的ROI，优化8万元营销预算分配。  
    **核心方法**：UTM全渠道追踪 + 转化漏斗分析 + 归因建模。  
    **关键结论**：**小红书**渠道转化率最高（2.3%），ROI达3.8，建议分配**60%线上预算**。
    """)
    
    # 渠道转化漏斗
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 渠道转化漏斗")
        
        try:
            funnel_data = dict(
                number=[10000, 5000, 1200, 380, 95],
                stage=["曝光量", "点击量", "咨询量", "意向客户", "成交客户"]
            )
            
            fig_funnel = px.funnel(
                funnel_data,
                x='number',
                y='stage',
                title="整体转化漏斗",
                color='stage',
                color_discrete_sequence=px.colors.sequential.Bluered
            )
            fig_funnel.update_layout(height=400, showlegend=False)
            
            st.plotly_chart(fig_funnel, use_container_width=True)
        except Exception as e:
            st.error(f"生成转化漏斗图表时出错: {e}")
    
    with col2:
        st.subheader("📊 渠道 ROI 对比")
        
        # 读取渠道数据
        try:
            # 尝试从文件读取渠道数据
            channel_data = pd.read_csv('data/channel_performance.csv')
        except FileNotFoundError:
            st.warning("未找到外部数据文件，使用内置模拟数据。")
            channel_data = pd.DataFrame({
                '渠道': ['小红书', '抖音', '拼多多', '线下活动'],
                'ROI': [3.8, 2.5, 1.9, 2.2],
                '转化率': [0.023, 0.018, 0.012, 0.015],
                'CAC': [45, 68, 52, 75]
            })
        
        # 确保转化率是小数格式
        channel_data['转化率'] = channel_data['转化率'].astype(float)
        
        try:
            fig_roi = go.Figure(data=[
                go.Bar(name='ROI', x=channel_data['渠道'], y=channel_data['ROI'], marker_color=COLOR_PRIMARY),
                go.Bar(name='转化率%', x=channel_data['渠道'], y=channel_data['转化率']*20, marker_color=COLOR_SUCCESS)
            ])
            
            fig_roi.update_layout(
                barmode='group',
                height=400,
                yaxis_title="数值",
                template="plotly_white"
            )
            
            st.plotly_chart(fig_roi, use_container_width=True)
        except Exception as e:
            st.error(f"生成渠道ROI图表时出错: {e}")
    
    # 渠道详细数据表
    st.subheader("📋 渠道表现详情")
    try:
        st.dataframe(
            channel_data.style.format({
                'ROI': '{:.2f}',
                '转化率': '{:.1%}',
                'CAC': '¥{:.0f}'
            }).background_gradient(subset=['ROI'], cmap='Greens'),
            use_container_width=True
        )
    except Exception as e:
        st.error(f"显示渠道数据时出错: {e}")
    
    st.success("""
    💡 **策略建议**：
    - **小红书**渠道转化率最高（2.3%），建议分配 **60%** 线上预算
    - **抖音**渠道曝光点击率最优（1.8%），适合品牌曝光
    - 建议采用**首次触点归因模型**评估渠道贡献
    """)

# ==================== Tab 3: 风险量化模拟 ====================
with tab3:
    st.header("⚠️ 基于蒙特卡洛模拟的风险量化分析")
    
    # 添加分析叙事
    st.info(f"""
    **分析目标**：量化项目不确定性，计算成功概率与潜在最大损失。  
    **核心方法**：{N_SIMULATIONS:,}次蒙特卡洛模拟 + 收益分布分析 + VaR计算。  
    **关键结论**：项目成功概率 **待计算**，95%置信度下最大可能损失 **待计算**。
    """)
    
    # 模型说明
    if use_advanced_model:
        st.success("""
        ✅ **高级风险模型已启用**
        - 价格：对数正态分布（避免负价格）
        - 销量：与价格负相关（价格弹性 = -1.5）
        - 成本：固定成本 + 可变成本结构
        - 更接近真实商业环境
        """)
    else:
        st.info("""
        ℹ️ **基础风险模型**
        - 价格、销量、成本：独立正态分布
        - 计算简单，运行快速
        - 适合快速估算
        """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎲 收益分布直方图")
        
        # 蒙特卡洛模拟
        try:
            expected_volume = TOTAL_OUTPUT * sales_achievement / 100
            
            # 使用缓存装饰器包装模拟函数
            @st.cache_data
            def get_cached_simulation(_n_simulations, _sales_price, _expected_volume, _total_cost, 
                                     _mortality_rate, _guaranteed_return, _use_advanced):
                """缓存的蒙特卡洛模拟函数"""
                return run_advanced_monte_carlo(
                    n_simulations=_n_simulations,
                    sales_price=_sales_price,
                    expected_volume=_expected_volume,
                    total_cost=_total_cost,
                    mortality_rate=_mortality_rate,
                    guaranteed_return=_guaranteed_return,
                    use_advanced=_use_advanced
                )
            
            # 获取模拟结果
            sim_result = get_cached_simulation(
                N_SIMULATIONS, sales_price, expected_volume, total_cost, 
                mortality_rate, guaranteed_return, use_advanced_model
            )
            
            profit_sim = sim_result['profit_sim']
            var_95 = sim_result['var_95']
            success_rate = sim_result['success_rate']
            
            # 生成直方图
            fig_hist = px.histogram(
                x=profit_sim,
                nbins=50,
                title=f"{N_SIMULATIONS:,} 次模拟收益分布",
                labels={'x': '净利润（元）'},
                color_discrete_sequence=[COLOR_PRIMARY]
            )
            
            # 添加VaR标注线
            fig_hist.add_vline(
                x=var_95,
                line_dash="dash",
                line_color=COLOR_DANGER,
                annotation_text=f"VaR 95%: ¥{var_95:,.0f}"
            )
            
            fig_hist.add_vline(
                x=guaranteed_return,
                line_dash="dot",
                line_color=COLOR_SUCCESS,
                annotation_text=f"保底收益：¥{guaranteed_return:,.0f}"
            )
            
            fig_hist.update_layout(
                showlegend=False, 
                height=400,
                template="plotly_white"
            )
            
            st.plotly_chart(fig_hist, use_container_width=True)
            
        except Exception as e:
            st.error(f"运行蒙特卡洛模拟时出错: {e}")
            st.info("请检查输入参数是否合理。")
    
    with col2:
        st.subheader("📊 风险指标")
        
        try:
            # 显示风险指标
            st.metric("模拟次数", f"{N_SIMULATIONS:,}")
            st.metric("成功概率", f"{success_rate:.1f}%")
            st.metric("VaR (95%)", f"¥{var_95:,.0f}")
            st.metric("期望收益", f"¥{np.mean(profit_sim):,.0f}")
            st.metric("收益标准差", f"¥{np.std(profit_sim):,.0f}")
            
            # 累积概率图
            sorted_profits = np.sort(profit_sim)
            cumulative_prob = np.arange(1, N_SIMULATIONS+1) / N_SIMULATIONS
            
            fig_cdf = go.Figure()
            fig_cdf.add_trace(go.Scatter(
                x=sorted_profits,
                y=cumulative_prob*100,
                mode='lines',
                name='累积概率',
                line=dict(color=COLOR_PRIMARY, width=2)
            ))
            
            fig_cdf.add_vline(
                x=var_95,
                line_dash="dash",
                line_color=COLOR_DANGER,
                annotation_text="VaR 95%"
            )
            
            fig_cdf.update_layout(
                title="累积概率分布",
                xaxis_title="净利润（元）",
                yaxis_title="累积概率（%）",
                height=300,
                template="plotly_white"
            )
            
            st.plotly_chart(fig_cdf, use_container_width=True)
            
        except Exception as e:
            st.error(f"计算风险指标时出错: {e}")
    
    st.warning(f"""
    ⚠️ **风险提示**：
    - 项目成功（满足保底收益）的概率为 **{success_rate:.1f}%**
    - 95%置信度下的最大在险价值（VaR）为 **¥{var_95:,.0f}**
    - 建议设立 **20%** 风险共担池应对极端情况
    """)

# ==================== Tab 4: 用户画像分析 ====================
with tab4:
    st.header("👥 用户分群与画像分析")
    
    # 雷达图
    st.subheader("🕸️ 用户特征雷达图")
    
    try:
        categories = ['价格敏感度', '品质关注度', '溯源信任度', '渠道偏好', '复购意愿']
        
        # 不同用户群体的得分
        segments = {
            '价格敏感型': [85, 60, 50, 40, 30],
            '品质追求型': [40, 90, 85, 75, 80],
            '理性消费型': [60, 75, 80, 65, 70],
            '冲动购买型': [70, 50, 40, 85, 25]
        }
        
        fig_radar = go.Figure()
        
        colors = [COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER]
        
        for i, (segment, scores) in enumerate(segments.items()):
            fig_radar.add_trace(go.Scatterpolar(
                r=scores,
                theta=categories,
                fill='toself',
                name=segment,
                line_color=colors[i % len(colors)]
            ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            height=500,
            template="plotly_white"
        )
        
        st.plotly_chart(fig_radar, use_container_width=True)
        
    except Exception as e:
        st.error(f"生成用户雷达图时出错: {e}")
    
    # 用户分群策略
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 分群策略建议")
        st.info("""
        **品质追求型**（占比 35%）
        - 关注点：肉质、溯源、品牌
        - 营销策略：强调品质认证、养殖过程透明化
        - 定价策略：溢价接受度高，可定 220 元+/斤
        
        **理性消费型**（占比 40%）
        - 关注点：性价比、口碑、评价
        - 营销策略：用户评价、KOL 推荐
        - 定价策略：198 元/斤主力价位
        """)
    
    with col2:
        st.subheader("💡 营销建议")
        st.success("""
        **价格敏感型**（占比 15%）
        - 关注点：价格、促销、折扣
        - 营销策略：限时优惠、拼团活动
        - 定价策略：168 元/斤引流款
        
        **冲动购买型**（占比 10%）
        - 关注点：包装、故事、情感
        - 营销策略：内容种草、直播带货
        - 定价策略：礼盒装 298 元
        """)

# ==================== Tab 5: 项目时间线 ====================
with tab5:
    st.header("📅 项目时间线与里程碑")
    
    # 使用表格替代甘特图
    tasks = [
        dict(Task="市场调研", Start="2025-03-01", Finish="2025-03-20", Progress=100),
        dict(Task="数据收集", Start="2025-03-15", Finish="2025-04-10", Progress=100),
        dict(Task="数据清洗", Start="2025-04-01", Finish="2025-04-20", Progress=100),
        dict(Task="财务建模", Start="2025-04-15", Finish="2025-05-10", Progress=100),
        dict(Task="营销分析", Start="2025-05-01", Finish="2025-05-25", Progress=90),
        dict(Task="风险模拟", Start="2025-05-20", Finish="2025-06-10", Progress=85),
        dict(Task="仪表板开发", Start="2025-06-01", Finish="2025-06-25", Progress=80),
        dict(Task="作品完善", Start="2025-06-20", Finish="2025-07-10", Progress=60),
        dict(Task="最终汇报", Start="2025-07-05", Finish="2025-07-15", Progress=0)
    ]
    
    df_tasks = pd.DataFrame(tasks)
    
    # 显示时间线表格
    st.subheader("📅 项目时间线详情")
    try:
        st.dataframe(
            df_tasks,
            column_config={
                "Task": "任务",
                "Start": "开始时间",
                "Finish": "结束时间",
                "Progress": st.column_config.ProgressColumn("进度", format="%d%%", min_value=0, max_value=100)
            },
            hide_index=True,
            use_container_width=True
        )
    except Exception as e:
        st.error(f"显示时间线表格时出错: {e}")
    
    # 用简单的文本描述替代甘特图
    st.subheader("📈 项目时间线概览")
    st.info("""
    **项目周期**: 2025年3月1日 - 2025年7月15日（共4.5个月）
    
    **关键阶段**:
    1. **市场调研** (3月1日-3月20日)：完成200份用户问卷
    2. **数据分析** (4月1日-5月25日)：财务建模、营销归因、风险模拟
    3. **开发实现** (6月1日-7月10日)：仪表板开发与作品完善
    4. **最终汇报** (7月5日-7月15日)：项目总结与展示
    """)
    
    # 里程碑
    st.subheader("🎯 关键里程碑")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("问卷回收", "200 份", "✅ 已完成")
    with col2:
        st.metric("众筹目标", "30 万元", "🔄 75% 达成")
    with col3:
        st.metric("作品提交", "2025-07-15", "📅 进行中")
# ==================== AI 智能助手 ====================
st.sidebar.markdown("---")
st.sidebar.subheader("🤖 AI 分析助手")

# 输入API Key（首次使用时需要）
api_key_input = st.sidebar.text_input(
    "智谱API Key（首次使用需输入）", 
    type="password",
    help="请输入您的智谱AI API Key。获取地址：https://open.bigmodel.cn/dev/api"
)

# 存储API Key到session_state
if api_key_input:
    st.session_state.zhipu_api_key = api_key_input
elif 'zhipu_api_key' not in st.session_state:
    st.session_state.zhipu_api_key = ""

# 用户问题输入框
user_question = st.sidebar.text_area(
    "请输入您的问题：",
    placeholder="例如：当前设置的参数有哪些风险？如果牛肉降价10%会怎样？如何提高投资回报率？",
    height=100
)

# 提问按钮
ask_button = st.sidebar.button("🚀 提问", use_container_width=True)       

# ==================== 页脚 ====================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748B; padding: 2rem;">
    <p><strong>个人在校项目展示 | 方裕娜</strong></p>
    <p>完整代码与数据：<a href="https://github.com/Fyuna777/yanbian-beef-analysis" target="_blank">https://github.com/Fyuna777/yanbian-beef-analysis</a></p>
    <p>联系方式：zhaowen2003@qq.com</p>
</div>
""", unsafe_allow_html=True)