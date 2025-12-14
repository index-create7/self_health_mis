# E:\trae_ide\mis\self_health_mis\frontend\app.py
import sys
import os

from self_health_mis.data.dal.exercise_dal import add_fitness_record
from self_health_mis.data.model.exercise_model import FitnessRecord

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from self_health_mis.core.exercise_service import add_user_exercise_record,ExerciseServiceError, ValidationError, DatabaseError
import time
import matplotlib.pyplot as plt


# 设置中文字体（解决matplotlib中文显示问题）
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

from self_health_mis.ai.bailian_adapter import call_with_session_d,call_with_session_a
from self_health_mis.frontend import session_state

# 导入SessionState类
from session_state import SessionState

from components.data_display import process_ai_response

# 创建会话状态管理器实例
session_manager = SessionState()


# 登录和注册页面
def render_login_page():
    st.title("学生体育锻炼管理系统")
    st.markdown("---")

    # 创建标签页组件
    login_tab, register_tab = st.tabs(["登录", "注册"])

    # 登录标签页
    with login_tab:
        with st.form("login_form"):
            username = st.text_input("用户名")
            password = st.text_input("密码", type="password")
            login_button = st.form_submit_button("登录", type="primary", use_container_width=True)

            if login_button:
                if session_manager.login(username, password):
                    st.success("登录成功！")
                    st.rerun()
                else:
                    st.error("用户名或密码错误")

        # 显示测试账号信息
        st.markdown("""
        **测试账号：**
        - 用户名：test
        - 密码：test123
        """)

    # 注册标签页
    with register_tab:
        # 显示注册说明
        st.info("请创建您的账号，用户名至少3个字符，密码至少6个字符")

        with st.form("register_form"):
            new_username = st.text_input("用户名")
            new_password = st.text_input("密码", type="password")
            confirm_password = st.text_input("确认密码", type="password")
            register_button = st.form_submit_button("注册", type="primary", use_container_width=True)

            if register_button:
                # 输入验证
                if not new_username or not new_password:
                    st.error("用户名和密码不能为空")
                elif len(new_username.strip()) < 3:
                    st.error("用户名至少需要3个字符")
                elif len(new_password) < 6:
                    st.error("密码至少需要6个字符")
                elif new_password != confirm_password:
                    st.error("两次输入的密码不一致")
                else:
                    try:
                        if session_manager.register(new_username, new_password):
                            st.success("注册成功！正在自动登录...")
                            # 修正：使用session_manager登录而非session_state
                            session_manager.login(new_username, new_password)
                            st.rerun()
                        else:
                            st.error("注册失败，该用户名可能已被使用，请尝试其他用户名")
                    except Exception as e:
                        st.error(f"注册过程中出现错误: {str(e)}")
                        st.info("请稍后重试或联系系统管理员")


def calculate_achievements(fitness_df):
    """基于健身数据计算成就进度"""
    checkin_df = fitness_df[fitness_df["is_checkin"]]
    total_checkin = checkin_df.shape[0]
    total_duration = checkin_df["duration"].sum()  # 总锻炼时长（分钟）
    total_days = len(fitness_df)
    max_streak = 0  # 计算连续打卡天数
    current_streak = 0

    # 计算连续打卡天数（按日期排序）
    sorted_df = fitness_df.sort_values("date")
    for _, row in sorted_df.iterrows():
        if row["is_checkin"]:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0

    # 定义成就列表（名称、解锁条件、当前进度、描述）
    achievements = [
        {
            "name": "打卡萌新",
            "condition": "总打卡天数≥5天",
            "current": total_checkin,
            "target": 5,
            "description": "完成5天打卡，迈出健身第一步！",
            "category": "打卡类"
        },
        {
            "name": "连续作战",
            "condition": "连续打卡≥7天",
            "current": max_streak,
            "target": 7,
            "description": "坚持一周打卡，养成运动习惯！",
            "category": "打卡类"
        },
        {
            "name": "运动达人",
            "condition": "总锻炼时长≥500分钟",
            "current": total_duration,
            "target": 500,
            "description": "累计运动500分钟，突破自我！",
            "category": "时长类"
        },
        {
            "name": "高强度玩家",
            "condition": "平均强度≥7分",
            "current": round(checkin_df["intensity"].mean(), 1) if not checkin_df.empty else 0,
            "target": 7,
            "description": "保持高运动强度，效果拉满！",
            "category": "强度类"
        },
        {
            "name": "全勤标兵",
            "condition": "周打卡率≥80%",
            "current": round(total_checkin / total_days * 100, 1) if total_days > 0 else 0,
            "target": 80,
            "description": "打卡率超80%，自律王者！",
            "category": "打卡类"
        }
    ]

    # 标记是否解锁
    for ach in achievements:
        # 特殊处理百分比类成就
        if "打卡率" in ach["condition"]:
            ach["unlocked"] = ach["current"] >= ach["target"]
        else:
            ach["unlocked"] = ach["current"] >= ach["target"]
        # 计算进度（百分比）
        ach["progress"] = min(ach["current"] / ach["target"] * 100, 100) if ach["target"] > 0 else 0
    return achievements

def render_achievement_tab(fitness_df):
    st.write("### 🏆 我的成就")

    # 计算成就数据
    achievements = calculate_achievements(fitness_df)

    # 按分类筛选成就
    tab1, tab2, tab3 = st.tabs(["打卡类", "时长类", "强度类"])
    category_mapping = {
        "打卡类": tab1,
        "时长类": tab2,
        "强度类": tab3
    }

    # 遍历成就，按分类展示
    for category, tab in category_mapping.items():
        with tab:
            category_achs = [a for a in achievements if a["category"] == category]
            if not category_achs:
                st.info(f"暂无{category}成就")
                continue

            # 逐个展示成就卡片
            for ach in category_achs:
                # 卡片样式：解锁为绿色，未解锁为灰色
                bg_color = "#e8f5e9" if ach["unlocked"] else "#f5f5f5"
                border_color = "#4caf50" if ach["unlocked"] else "#9e9e9e"

                # 成就卡片
                with st.container(border=True):
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        # 成就徽章（emoji区分状态）
                        st.markdown(f"""
                        <div style="width:60px; height:60px; border-radius:50%; 
                                    background-color:{bg_color}; border:2px solid {border_color};
                                    display:flex; align-items:center; justify-content:center;
                                    font-size:24px;">
                            {'✅' if ach["unlocked"] else '🔒'}
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        st.write(f"**{ach['name']}**")
                        st.caption(ach["condition"])
                        # 进度条
                        st.progress(ach["progress"] / 100, text=f"进度：{ach['current']}/{ach['target']}")
                        # 成就描述
                        with st.expander("成就详情"):
                            st.write(ach["description"])
                            st.write(f"当前进度：{ach['current']} / 目标：{ach['target']}")

    st.markdown("---")
    st.write("### 📊 成就统计")
    total_achs = len(achievements)
    unlocked_achs = len([a for a in achievements if a["unlocked"]])
    unlock_rate = round(unlocked_achs / total_achs * 100, 1) if total_achs > 0 else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总成就数", total_achs)
    with col2:
        st.metric("已解锁成就", unlocked_achs)
    with col3:
        st.metric("成就解锁率", f"{unlock_rate}%")


import random
def render_visualization_tab(fitness_df):
    # 1. 核心指标卡片（Metric）
    st.write("### 核心指标概览")
    col1, col2, col3, col4 = st.columns(4)

    checkin_df = fitness_df[fitness_df["is_checkin"]]
    total_checkin_days = checkin_df.shape[0]
    total_days = len(fitness_df)

    # 2. 计算平均强度（空值/空数据保护 + 内置round）
    avg_intensity = round(checkin_df["intensity"].mean(), 1) if not checkin_df.empty else 0.0

    # 3. 计算平均恢复质量（同上）
    avg_recovery = round(checkin_df["recovery_quality"].mean(), 1) if not checkin_df.empty else 0.0

    # 4. 计算周打卡率（分母保护 + 内置round）
    if total_days == 0:
        weekly_checkin_rate = 0.0
    else:
        weekly_checkin_rate = round(total_checkin_days / total_days * 100, 1)

    with col1:
        st.metric(
            label="总打卡天数",
            value=total_checkin_days,
            delta=f"{len(fitness_df) - total_checkin_days}天未打卡",
            delta_color="inverse"
        )
    with col2:
        st.metric(
            label="平均锻炼强度",
            value=avg_intensity if not pd.isna(avg_intensity) else 0,
            delta="近30天均值",
            delta_color="normal"
        )
    with col3:
        st.metric(
            label="平均恢复质量",
            value=avg_recovery if not pd.isna(avg_recovery) else 0,
            delta="近30天均值",
            delta_color="normal"
        )
    with col4:
        st.metric(
            label="打卡率",
            value=f"{weekly_checkin_rate}%",
            delta="近30天",
            delta_color="normal"
        )
    col1, col2 = st.columns([3,1])
    with col2:
        with st.expander("打卡日历热力图"):
                fitness_df['date'] = pd.to_datetime(fitness_df['date'])  # 确保日期格式正确
                heatmap_data = fitness_df.set_index('date')['intensity']

                # 空数据保护：若所有强度为0/空，生成提示
                if heatmap_data.sum() == 0:
                    st.info("暂无运动强度数据，无法生成热力图")
                else:
                    # 1. 自定义红色系配色（无需norm，直接定义渐变映射）
                    import matplotlib.colors as mcolors
                    import numpy as np

                    # 定义颜色节点：0→浅灰 | 5→浅红 | 10→深红（自动渐变）
                    color_list = [
                        (0.0, '#f5f5f5'),  # 强度0：浅灰（未打卡）
                        (0.1, '#fee2e2'),  # 强度1：极浅红
                        (0.2, '#fecaca'),  # 强度2：浅红
                        (0.3, '#fca5a5'),  # 强度3：淡红
                        (0.4, '#f87171'),  # 强度4：橘红
                        (0.5, '#ef4444'),  # 强度5：亮红（临界点）
                        (0.6, '#dc2626'),  # 强度6：深红
                        (0.7, '#b91c1c'),  # 强度7：暗红
                        (0.8, '#991b1b'),  # 强度8：更深红
                        (0.9, '#7f1d1d'),  # 强度9：酒红
                        (1.0, '#4b0000')  # 强度10：暗酒红（最高强度）
                    ]
                    # 创建线性渐变配色（自动适配0-10的数值范围）
                    cmap = mcolors.LinearSegmentedColormap.from_list('custom_red', color_list)

                    # 2. 获取数据包含的月份列表（用于下拉选择）
                    available_months = sorted(heatmap_data.index.month.unique())
                    month_names = {1: '1月', 2: '2月', 3: '3月', 4: '4月', 5: '5月', 6: '6月',
                                7: '7月', 8: '8月', 9: '9月', 10: '10月', 11: '11月', 12: '12月'}
                    # 下拉选择框（显示中文月份）
                    selected_month_num = st.selectbox(
                        "选择月份",
                        options=available_months,
                        format_func=lambda x: month_names[x],  # 显示中文
                        index=len(available_months) - 1  # 默认选最新月份
                    )
                    target_year = heatmap_data.index.max().year  # 数据所在年份

                    # 3. 过滤出「选中年份+月份」的数据集（仅保留该月数据）
                    filtered_data = heatmap_data[
                        (heatmap_data.index.year == target_year) &
                        (heatmap_data.index.month == selected_month_num)
                        ]

                    # 4. 补全该月所有日期（避免缺失日期导致热力图不完整）
                    month_start = pd.Timestamp(year=target_year, month=selected_month_num, day=1)
                    month_end = (month_start + pd.offsets.MonthEnd(1))
                    full_dates = pd.date_range(start=month_start, end=month_end, freq='D')
                    full_series = pd.Series(pd.NA, index=full_dates, name='intensity')  # 初始化全NaN序列
                    # 合并真实数据（先填充有效数据，再补0）
                    combined_data = full_series.fillna(filtered_data).fillna(0)

                    # 核心修正：重新计算当月周数（避免超大数）
                    combined_data = combined_data.reset_index()
                    combined_data.columns = ['date', 'intensity']
                    combined_data['weekday'] = combined_data['date'].dt.weekday  # 0=周一，6=周日
                    combined_data['day_of_month'] = combined_data['date'].dt.day
                    combined_data['week_of_month'] = (combined_data['day_of_month'] - 1) // 7 + 1

                    # 数值保护：限制max_week在1-6之间（当月最多6周）
                    max_week = combined_data['week_of_month'].max()
                    max_week = min(max_week, 6)  # 强制上限6，避免异常值
                    if max_week < 1:
                        max_week = 1  # 保底至少1周

                    # 填充网格（行数=7行（周一到周日），列数=当月最大周数）
                    heatmap_grid = np.zeros((7, max_week))  # 7行×最多6列
                    for _, row in combined_data.iterrows():
                        y = row['weekday']  # 行：周一=0，周日=6
                        x = row['week_of_month'] - 1  # 列：从0开始
                        # 边界保护：防止x/y超出网格范围
                        if 0 <= x < max_week and 0 <= y < 7:
                            heatmap_grid[y, x] = row['intensity']

                    # ---------------------- 5. 绘制单月热力图（XY轴调换+缩小尺寸） ----------------------
                    # 关键1：缩小画布尺寸（原(max_week*1.2,7) → 新(max_week*1, 4)，更紧凑）
                    fig, ax = plt.subplots(figsize=(max_week * 0.5, 1.2))

                    # 关键2：网格转置（heatmap_grid.T）实现XY轴调换
                    im = ax.imshow(heatmap_grid.T, cmap=cmap, aspect='auto')

                    # 关键3：调整刻度/标签适配新轴方向
                    ax.set_xticks(range(7))  # X轴：星期（原Y轴）
                    ax.set_xticklabels(['一', '二', '三', '四', '五', '六', '日'], fontsize=4)  # 缩小标签字体
                    ax.set_yticks(range(max_week))  # Y轴：周数（原X轴）
                    ax.set_yticklabels([f'第{i + 1}周' for i in range(max_week)], fontsize=4)  # 缩小标签字体
                    ax.set_title(f'{target_year}年{selected_month_num}月', fontsize=6, pad=10)  # 缩小标题字体

                    # 隐藏边框+调整间距
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    ax.spines['bottom'].set_visible(False)
                    ax.spines['left'].set_visible(False)
                    plt.tight_layout()

                    # 显示热力图
                    st.pyplot(fig)
    with col1:
        # 3. 强度+恢复质量双Y轴图
        with st.expander("锻炼强度 vs 恢复质量趋势（近30天）"):
            fig, ax1 = plt.subplots(figsize=(12, 4))

            # 左Y轴：锻炼强度（折线）
            ax1.set_xlabel("日期", fontsize=10)
            ax1.set_ylabel("锻炼强度", color="#e74c3c", fontsize=10)
            ax1.plot(
                fitness_df["date_str"],
                fitness_df["intensity"],
                color="#e74c3c",
                marker="o",
                markersize=4,
                label="锻炼强度"
            )
            ax1.tick_params(axis="y", labelcolor="#e74c3c")
            ax1.tick_params(axis="x", rotation=60, labelsize=8)

            # 右Y轴：恢复质量（柱状）
            ax2 = ax1.twinx()
            ax2.set_ylabel("恢复质量", color="#3498db", fontsize=10)
            ax2.bar(
                fitness_df["date_str"],
                fitness_df["recovery_quality"],
                alpha=0.5,
                color="#3498db",
                label="恢复质量",
                width=0.6
            )
            ax2.tick_params(axis="y", labelcolor="#3498db")

            # 图例
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

            plt.title("锻炼强度与恢复质量双维度趋势", fontsize=12, pad=10)
            plt.tight_layout()
            st.pyplot(fig)


        # 4. 辅助折线图：时长/卡路里趋势
        with st.expander("锻炼时长 & 卡路里消耗趋势"):
            col1, col2 = st.columns(2)
            with col1:
                st.line_chart(
                    fitness_df,
                    x="date_str",
                    y="duration",
                    color="#2ecc71",
                    use_container_width=True,
                    height=300
                )
            with col2:
                st.line_chart(
                    fitness_df,
                    x="date_str",
                    y="calories",
                    color="#f39c12",
                    use_container_width=True,
                    height=300
                )

    # 5. 锻炼类型分布分析
    with st.expander("锻炼类型分布"):
        col1, col2 = st.columns(2)
        
        # 锻炼类型分布饼图
        with col1:
            exercise_type_counts = checkin_df["exercise_type"].value_counts()
            if not exercise_type_counts.empty:
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.pie(exercise_type_counts.values, labels=exercise_type_counts.index, autopct='%1.1f%%', startangle=90)
                ax.set_title('锻炼类型分布饼图')
                ax.axis('equal')  # 保持圆形
                st.pyplot(fig)
            else:
                st.info("暂无锻炼类型数据")
        
        # 锻炼类型分布柱状图
        with col2:
            if not exercise_type_counts.empty:
                fig, ax = plt.subplots(figsize=(8, 6))
                exercise_type_counts.plot(kind='bar', ax=ax, color=['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6'])
                ax.set_xlabel('锻炼类型')
                ax.set_ylabel('次数')
                ax.set_title('锻炼类型分布柱状图')
                plt.xticks(rotation=45)
                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.info("暂无锻炼类型数据")
    
    # 6. 锻炼强度分布直方图
    with st.expander("锻炼强度直方图"):
        if not checkin_df.empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.hist(checkin_df["intensity"], bins=10, range=(0, 10), color='#e74c3c', alpha=0.7, edgecolor='black')
            ax.set_xlabel('锻炼强度（0-10）')
            ax.set_ylabel('次数')
            ax.set_title('锻炼强度分布直方图')
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
        else:
            st.info("暂无锻炼强度数据")
    
    # 7. 周打卡趋势图
    with st.expander("周打卡率趋势"):
        if not checkin_df.empty:
            # 添加周数列
            checkin_df['week'] = checkin_df['date'].dt.isocalendar().week
            week_counts = checkin_df.groupby('week').size()
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(week_counts.index, week_counts.values, marker='o', color='#3498db', linewidth=2)
            ax.set_xlabel('周数')
            ax.set_ylabel('打卡天数')
            ax.set_title('周打卡趋势图')
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
        else:
            st.info("暂无打卡数据")
    
    # 8. 锻炼时长与卡路里消耗散点图
    with st.expander("时长 vs 卡路里散点图"):
        if not checkin_df.empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            scatter = ax.scatter(checkin_df["duration"], checkin_df["calories"], c=checkin_df["intensity"], 
                                cmap='Reds', alpha=0.7, s=50)
            ax.set_xlabel('锻炼时长（分钟）')
            ax.set_ylabel('卡路里消耗')
            ax.set_title('锻炼时长与卡路里消耗关系')
            ax.grid(True, alpha=0.3)
            plt.colorbar(scatter, label='锻炼强度')
            st.pyplot(fig)
        else:
            st.info("暂无相关数据")

    st.markdown("---")


def generate_fitness_data(days=30):
    """生成12月全月的模拟数据（确保有有效打卡）"""
    # 强制从12月1日开始生成数据（保证是当前选择的12月）
    base_date = datetime(2025, 12, 1)
    dates = [base_date + timedelta(days=i) for i in range(days)]

    data = []
    for date in dates:
        # 提高打卡率到80%（减少无数据情况）
        is_checkin = random.random() > 0.2
        # 打卡时生成4-10的强度（非0）
        intensity = random.randint(4, 10) if is_checkin else 0
        recovery_quality = random.randint(5, 10) if is_checkin else 0
        duration = random.randint(20, 60) if is_checkin else 0
        calories = random.randint(100, 300) if is_checkin else 0
        exercise_type = random.choice(["跑步", "游泳", "跳绳", "力量训练", "瑜伽"]) if is_checkin else ""

        data.append({
            "date": date,
            "is_checkin": is_checkin,
            "intensity": intensity,
            "recovery_quality": recovery_quality,
            "duration": duration,
            "calories": calories,
            "exercise_type": exercise_type,
            "date_str": date.strftime("%Y-%m-%d")
        })

    df = pd.DataFrame(data)
    return df


def main():
    # ========== 全局会话状态初始化（刷新不丢失） ==========
    if "ai_extracted_data" not in st.session_state:
        st.session_state.ai_extracted_data = session_manager.db.get_ai_extracted_data() or None
    if "show_exercise_table" not in st.session_state:
        st.session_state.show_exercise_table = st.session_state.ai_extracted_data is not None
    if "manual_confirm_data" not in st.session_state:
        st.session_state.manual_confirm_data = st.session_state.ai_extracted_data or {}

    if not session_manager.is_logged_in():
        render_login_page()
    else:
        # 已经登录，显示主页内容
        st.sidebar.success(f"已登录用户ID: {st.session_state.user_id}")
        if st.sidebar.button("退出登录"):
            session_manager.logout()
            # 退出时清空所有会话状态
            st.session_state.ai_extracted_data = None
            st.session_state.show_exercise_table = False
            st.session_state.manual_confirm_data = {}
            st.rerun()

        # 刷新数据
        session_manager.refresh_data()

        # 获取用户数据
        profile = session_manager.db.get_user_profile(st.session_state.user_id)
        records = session_manager.db.get_fitness_records(st.session_state.user_id)
        goals = session_manager.db.get_fitness_goals(st.session_state.user_id, include_completed=False)

        # 计算统计数据
        total_workouts = len(records)
        total_duration = sum(r.duration for r in records) if records else 0
        avg_duration = total_duration / total_workouts if total_workouts > 0 else 0

        # 主界面标题
        st.markdown("<h1 style='text-align: center; color: grey;'>学生体育锻炼管理系统</h1>", unsafe_allow_html=True)
        col1, col2 = st.columns([1,1])
        with col1:
            fitness_df = generate_fitness_data(days=30)
            with st.expander("打卡日历热力图", expanded=True):
                    fitness_df['date'] = pd.to_datetime(fitness_df['date'])  # 确保日期格式正确
                    heatmap_data = fitness_df.set_index('date')['intensity']

                    # 空数据保护：若所有强度为0/空，生成提示
                    if heatmap_data.sum() == 0:
                        st.info("暂无运动强度数据，无法生成热力图")
                    else:
                        # 1. 自定义红色系配色（无需norm，直接定义渐变映射）
                        import matplotlib.colors as mcolors
                        import numpy as np

                        # 定义颜色节点：0→浅灰 | 5→浅红 | 10→深红（自动渐变）
                        color_list = [
                            (0.0, '#f5f5f5'),  # 强度0：浅灰（未打卡）
                            (0.1, '#fee2e2'),  # 强度1：极浅红
                            (0.2, '#fecaca'),  # 强度2：浅红
                            (0.3, '#fca5a5'),  # 强度3：淡红
                            (0.4, '#f87171'),  # 强度4：橘红
                            (0.5, '#ef4444'),  # 强度5：亮红（临界点）
                            (0.6, '#dc2626'),  # 强度6：深红
                            (0.7, '#b91c1c'),  # 强度7：暗红
                            (0.8, '#991b1b'),  # 强度8：更深红
                            (0.9, '#7f1d1d'),  # 强度9：酒红
                            (1.0, '#4b0000')  # 强度10：暗酒红（最高强度）
                        ]
                        # 创建线性渐变配色（自动适配0-10的数值范围）
                        cmap = mcolors.LinearSegmentedColormap.from_list('custom_red', color_list)

                        # 直接取当前月份，不再提供下拉选择
                        selected_month_num = datetime.now().month
                        target_year = datetime.now().year

                        # 3. 过滤出「选中年份+月份」的数据集（仅保留该月数据）
                        filtered_data = heatmap_data[
                            (heatmap_data.index.year == target_year) &
                            (heatmap_data.index.month == selected_month_num)
                            ]

                        # 4. 补全该月所有日期（避免缺失日期导致热力图不完整）
                        month_start = pd.Timestamp(year=target_year, month=selected_month_num, day=1)
                        month_end = (month_start + pd.offsets.MonthEnd(1))
                        full_dates = pd.date_range(start=month_start, end=month_end, freq='D')
                        full_series = pd.Series(pd.NA, index=full_dates, name='intensity')  # 初始化全NaN序列
                        # 合并真实数据（先填充有效数据，再补0）
                        combined_data = full_series.fillna(filtered_data).fillna(0)

                        # 核心修正：重新计算当月周数（避免超大数）
                        combined_data = combined_data.reset_index()
                        combined_data.columns = ['date', 'intensity']
                        combined_data['weekday'] = combined_data['date'].dt.weekday  # 0=周一，6=周日
                        combined_data['day_of_month'] = combined_data['date'].dt.day
                        combined_data['week_of_month'] = (combined_data['day_of_month'] - 1) // 7 + 1

                        # 数值保护：限制max_week在1-6之间（当月最多6周）
                        max_week = combined_data['week_of_month'].max()
                        max_week = min(max_week, 6)  # 强制上限6，避免异常值
                        if max_week < 1:
                            max_week = 1  # 保底至少1周

                        # 填充网格（行数=7行（周一到周日），列数=当月最大周数）
                        heatmap_grid = np.zeros((7, max_week))  # 7行×最多6列
                        for _, row in combined_data.iterrows():
                            y = row['weekday']  # 行：周一=0，周日=6
                            x = row['week_of_month'] - 1  # 列：从0开始
                            # 边界保护：防止x/y超出网格范围
                            if 0 <= x < max_week and 0 <= y < 7:
                                heatmap_grid[y, x] = row['intensity']

                        # ---------------------- 5. 绘制单月热力图（XY轴调换+缩小尺寸） ----------------------
                        # 关键1：缩小画布尺寸（原(max_week*1.2,7) → 新(max_week*1, 4)，更紧凑）
                        fig, ax = plt.subplots(figsize=(max_week * 0.5, 1.2))

                        # 关键2：网格转置（heatmap_grid.T）实现XY轴调换
                        im = ax.imshow(heatmap_grid.T, cmap=cmap, aspect='auto')

                        # 关键3：调整刻度/标签适配新轴方向
                        ax.set_xticks(range(7))  # X轴：星期（原Y轴）
                        ax.set_xticklabels(['一', '二', '三', '四', '五', '六', '日'], fontsize=4)  # 缩小标签字体
                        ax.set_yticks(range(max_week))  # Y轴：周数（原X轴）
                        ax.set_yticklabels([f'第{i + 1}周' for i in range(max_week)], fontsize=4)  # 缩小标签字体
                        ax.set_title(f'{target_year}年{selected_month_num}月', fontsize=6, pad=10)  # 缩小标题字体

                        # 隐藏边框+调整间距
                        ax.spines['top'].set_visible(False)
                        ax.spines['right'].set_visible(False)
                        ax.spines['bottom'].set_visible(False)
                        ax.spines['left'].set_visible(False)
                        plt.tight_layout()

                        # 显示热力图
                        st.pyplot(fig)
        with col2:
            st.subheader("目标")
            if goals:
                for goal in goals:
                    with st.expander(f"目标: {goal.name if hasattr(goal, 'name') else '未命名目标'}"):
                        st.write(f"描述: {goal.description if hasattr(goal, 'description') else '无描述'}")
            else:
                st.info("还没有设置锻炼目标")



        tab1, tab2, tab3, tab4, tab5 = st.tabs([ "主页","数据分析","成就","ai对话","刷段记录"])

        with tab1:
            with st.container():
                st.subheader("💬 AI导入")
                user_input = st.text_area(
                    "请输入今日锻炼情况：",
                    height=200
                )

                # AI发送按钮逻辑
                if st.button("发送", type="primary"):

                    st.info("正在处理您的请求，请稍等...")
                    if user_input.strip():
                        response = call_with_session_d(user_input)
                        # 处理AI响应，尝试识别锻炼记录
                        is_processed, data = process_ai_response(response, current_user_id=st.session_state.user_id)

                        if is_processed and data is not None:
                            st.snow()
                            # AI解析成功：更新会话状态
                            st.session_state.ai_extracted_data = data
                            st.session_state.manual_confirm_data = data  # 初始化手工确认数据
                            st.session_state.show_exercise_table = True
                            # 同步保存到全局DB
                            session_manager.db.save_ai_extracted_data(data)
                        # AI未解析出锻炼记录
                        if not is_processed:
                            st.write(f"AI助手回复: {response}")
                            st.session_state.show_exercise_table = False
                            st.session_state.manual_confirm_data = {}


                # ========== 普通表格展示 + 手工确认输入框 ==========
                if st.session_state.show_exercise_table and st.session_state.ai_extracted_data is not None:
                    # 1. 展示普通只读表格（优化null值展示）
                    st.write("### AI提取的锻炼记录（只读）")
                    ai_data = st.session_state.ai_extracted_data

                    # 处理null/None值，显示为空字符串（而非0/False）
                    def get_safe_value(key, default=""):
                        val = ai_data.get(key)
                        return val if val is not None else default

                    table_data = pd.DataFrame({
                        "日期": [get_safe_value("date")],
                        "运动项目": [get_safe_value("exercise_type")],
                        "时长（分钟）": [get_safe_value("duration")],
                        "距离（米）": [get_safe_value("distance")],  # AI返回400默认是米，修正单位更合理
                        "卡路里消耗": [get_safe_value("calories")],
                        "是否官方记录": [get_safe_value("is_official")],
                        "备注": [get_safe_value("notes")],
                    })

                    # 日期格式处理（失败则保留原始值）
                    table_data["日期"] = pd.to_datetime(table_data["日期"], format="%Y-%m-%d", errors="ignore")
                    st.dataframe(table_data, width=800, height=200)  # 普通只读表格

                    # ========== 新增：提交记录逻辑（适配AI返回的null值） ==========
                    if st.button("提交锻炼记录到我的档案", type="primary"):
                        # 1. 取出AI解析的原始数据
                        ai_data = st.session_state.ai_extracted_data
                        submit_data = {}

                        # 2. 数据预处理（精准处理null值，适配业务层校验规则）
                        try:
                            # ---------------- 核心必填字段（严格校验） ----------------
                            # 日期：转为datetime类型，null/空直接报错
                            raw_date = ai_data.get("date")
                            if raw_date is None or raw_date.strip() == "":
                                raise ValidationError("锻炼日期不能为空！")
                            submit_data["date"] = pd.to_datetime(raw_date, format="%Y-%m-%d", errors="raise")

                            # 运动类型：非空校验（null/空字符串都报错）
                            exercise_type = ai_data.get("exercise_type")
                            if exercise_type is None or exercise_type.strip() == "":
                                raise ValidationError("运动项目不能为空！")
                            submit_data["exercise_type"] = exercise_type.strip()

                            # 时长：必须>0的数值（null/≤0都报错）
                            duration = ai_data.get("duration")
                            if duration is None:
                                raise ValidationError("锻炼时长不能为空！")
                            try:
                                duration = float(duration)
                            except (ValueError, TypeError):
                                raise ValidationError("锻炼时长必须为数字！")
                            if duration <= 0:
                                raise ValidationError("锻炼时长必须大于0分钟！")
                            submit_data["duration"] = duration

                            # ---------------- 可选字段（兼容null值） ----------------
                            # 距离：null则设为None，非null则转float
                            distance = ai_data.get("distance")
                            if distance is not None:
                                try:
                                    submit_data["distance"] = float(distance) / 1000  # 米转公里（适配业务层公里单位）
                                except (ValueError, TypeError):
                                    raise ValidationError("锻炼距离必须为数字！")
                            else:
                                submit_data["distance"] = None

                            # 卡路里：null则设为None，非null则转int
                            calories = ai_data.get("calories")
                            if calories is not None:
                                try:
                                    submit_data["calories"] = int(calories)
                                except (ValueError, TypeError):
                                    raise ValidationError("卡路里消耗必须为整数！")
                            else:
                                submit_data["calories"] = None

                            # 是否官方记录：null则设为False，确保是布尔值
                            is_official = ai_data.get("is_official")
                            submit_data["is_official"] = bool(is_official) if is_official is not None else False

                            # 备注：null则设为空字符串，去重空格
                            notes = ai_data.get("notes")
                            submit_data["notes"] = notes.strip() if notes is not None else ""

                        except ValidationError as e:
                            st.error(f"数据验证失败：{str(e)}")
                            st.stop()
                        except Exception as e:
                            st.error(f"数据格式错误：{str(e)}")
                            st.stop()

                        # 3. 调用业务层方法添加记录
                        try:
                            record_id = add_user_exercise_record(
                                user_id=st.session_state.user_id,
                                record_data=submit_data
                            )
                            if record_id and record_id > 0:
                                st.success(f"✅ 锻炼记录提交成功！记录ID：{record_id}")
                                # 重置状态
                                st.session_state.show_exercise_table = False
                                st.session_state.ai_extracted_data = None
                                st.session_state.manual_confirm_data = {}
                                st.rerun()
                            else:
                                st.error("❌ 锻炼记录提交失败，请重试！")

                        except ValidationError as e:
                            st.error(f"数据校验失败：{str(e)}")
                        except DatabaseError as e:
                            st.error(f"数据库操作失败：{str(e)}")
                        except ExerciseServiceError as e:
                            st.error(f"服务处理失败：{str(e)}")
                        except Exception as e:
                            st.error(f"⚠️ 提交失败：未知错误 - {str(e)}")


            st.subheader("添加锻炼记录", anchor=False)
            with st.form("add_record_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    # 前端输入适配DB层的datetime类型
                    exercise_date = st.date_input("锻炼日期", value=date.today())
                    exercise_type = st.selectbox(
                        "锻炼类型",
                        ["跑步", "游泳", "篮球", "羽毛球", "骑行", "瑜伽", "力量训练", "跳绳", "其他"]
                    )
                    duration = st.number_input("持续时间(分钟)", min_value=5.0, value=30.0, step=5.0)
                    distance = st.number_input("距离(公里)", min_value=0.0, value=3.0, step=0.5, help="无距离则填0")
                with col2:
                    calories = st.number_input("卡路里消耗(kcal)", min_value=10, value=300, step=50)
                    is_official = st.checkbox("是否为官方刷段", value=False)
                    notes = st.text_area("备注（选填）", height=60)

                    submit_btn = st.form_submit_button("保存新记录", type="primary", use_container_width=True)

            # 处理新增记录（前端构造DB层需要的FitnessRecord对象）
            if submit_btn:
                # 适配DB层的日期类型（datetime.combine）
                record_date = datetime.combine(exercise_date, datetime.min.time())
                # 适配DB层的空值处理（距离为0则存None）
                distance_val = distance if distance > 0 else None
                # 适配DB层的FitnessRecord模型（原模型字段）
                new_record = FitnessRecord(
                    user_id = st.session_state.user_id,
                    date=record_date,
                    exercise_type=exercise_type.strip(),
                    duration=duration,
                    distance=distance_val,
                    calories=calories,
                    is_official=is_official,
                    notes=notes.strip() if notes else None,
                    is_checkin=False,  # 原模型新增字段
                    intensity=None,  # 原模型新增字段
                    recovery_quality=None  # 原模型新增字段
                )

                if add_fitness_record(new_record):
                    st.rerun()

        with tab2:
            fitness_df = generate_fitness_data(days=30)
            render_visualization_tab(fitness_df)

        with tab3:
            fitness_df = generate_fitness_data(days=30)  # 模拟数据，后续替换为真实数据
            render_achievement_tab(fitness_df)

        with tab4:
            aichat()
            
        with tab5:
            records = session_manager.db.get_fitness_records(st.session_state.user_id)
            render_brush_section_tab(records)

def response_generator():
    response = random.choice(
        [
            "Hello there! How can I assist you today?",
            "Hi, human! Is there anything I can help you with?",
            "Do you need help?",
        ]
    )
    for word in response.split():
        yield word + " "
        time.sleep(0.05)

import inspect  # 确保导入此模块（放在文件顶部）

def aichat():
    st.title("AI chat")

    # 初始化聊天历史
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 空历史友好提示
    if not st.session_state.messages:
        with st.chat_message("assistant"):
            st.markdown("你好！我是你的运动AI助手，有什么可以帮助你的吗？")
    
    # 渲染历史消息
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 处理用户输入
    if prompt := st.chat_input("例如：今天跑步30分钟，距离5公里"):
        # 记录用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        assistant_content = ""
        try:
            # ========== 1. 调用AI接口 ==========
            client = call_with_session_a(prompt)
            
            # ========== 2. 调试信息（前端可见，便于定位问题） ==========
            st.markdown("### 🛠️ 调试信息（可隐藏）")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"返回对象类型：`{type(client)}`")
                st.write(f"是否生成器：`{inspect.isgenerator(client)}`")
            with col2:
                st.write(f"是否可迭代：`{hasattr(client, '__iter__')}`")
            st.markdown("---")

            # ========== 3. 核心响应处理（优先级：判空→错误字典→生成器→其他） ==========
            # 3.1 空响应
            if client is None:
                assistant_content = "AI服务返回空响应，请重试"
                with st.chat_message("assistant"):
                    st.markdown(assistant_content)
            
            # 3.2 错误字典（标准化异常）
            elif isinstance(client, dict):
                error_msg = client.get('message', '未知错误')
                assistant_content = f"请求失败：{error_msg}"
                with st.chat_message("assistant"):
                    st.error(assistant_content)
                    # 显示详细错误（调试用）
                    if "request_id" in client:
                        st.caption(f"请求ID：{client['request_id']}")
            
            # 3.3 流式生成器（核心修复：不检查status_code）
            elif inspect.isgenerator(client) or (hasattr(client, '__iter__') and not isinstance(client, (str, list, tuple, dict))):
                with st.chat_message("assistant"):
                    # 安全解析流式响应
                    def extract_stream_text(stream):
                        full_text = ""
                        try:
                            for idx, chunk in enumerate(stream):
                                # 调试每个分片 - 更详细的信息
                                if idx < 3:  # 仅显示前3个分片的调试信息
                                    chunk_repr = repr(chunk)[:100]  # 使用repr获取更准确的对象表示
                                    st.caption(f"[DEBUG] 分片{idx+1}：类型={type(chunk).__name__}, 内容={chunk_repr}...")
                                
                                # 适配百炼SDK所有分片格式，增加异常保护
                                chunk_text = ""
                                try:
                                    if hasattr(chunk, "text"):
                                        chunk_text = getattr(chunk, "text", "")
                                    elif hasattr(chunk, "output"):
                                        chunk_output = getattr(chunk, "output", None)
                                        if chunk_output:
                                            chunk_text = getattr(chunk_output, "text", "")
                                    elif hasattr(chunk, "content"):
                                        chunk_text = getattr(chunk, "content", "")
                                    elif isinstance(chunk, (str, bytes)):
                                        chunk_text = str(chunk)
                                    else:
                                        # 尝试将其他类型转换为字符串
                                        chunk_text = str(chunk)
                                except Exception as attr_e:
                                    st.caption(f"[DEBUG] 分片{idx+1}属性访问错误：{str(attr_e)}")
                                
                                if chunk_text:
                                    full_text += chunk_text
                                    yield chunk_text
                        except StopIteration:
                            # 正常结束迭代
                            pass
                        except Exception as e:
                            err_msg = f"\n\n⚠️ 流式解析失败：{str(type(e).__name__)}: {str(e)}"
                            full_text += err_msg
                            yield err_msg
                        return full_text

                    # 流式输出
                    assistant_content = st.write_stream(extract_stream_text(client))
            
            # 3.4 其他类型（字符串/数字等）
            else:
                assistant_content = str(client) if client else "AI返回非流式响应，无法解析"
                with st.chat_message("assistant"):
                    st.markdown(assistant_content)

        # 全局异常捕获（兜底）
        except Exception as e:
            assistant_content = f"AI服务调用异常：{str(e)}"
            with st.chat_message("assistant"):
                st.error(assistant_content)
                # 显示异常详情（调试用）
                st.code(f"异常类型：{type(e)}\n异常信息：{str(e)}", language="python")
        
        # 记录AI响应到历史
        final_content = assistant_content or "未获取到有效响应，请稍后重试"
        st.session_state.messages.append({"role": "assistant", "content": final_content})



        # client = call_with_session_a(prompt)
        # # Display assistant response in chat message container
        # if client is None:
        #     assistant_content = "AI服务返回空响应，请重试"
        #     st.markdown(assistant_content)
        # elif hasattr(client, "status_code") and client.status_code != 200:
        #     # 处理接口错误
        #     assistant_content = f"请求失败：{client.status_code} - {getattr(client, 'message', '未知错误')}"
        #     st.error(assistant_content)
        # else:
        #     # 3. 提取官方流式文本（适配百炼SDK结构）
        #     def extract_stream_text(stream):
        #         """安全提取流式分片文本，避免迭代错误"""
        #         try:
        #             for chunk in stream:
        #                 # 适配百炼SDK实际分片结构（根据实际情况调整字段）
        #                 chunk_text = getattr(chunk, "text", "") or getattr(chunk.output, "text", "")
        #                 if chunk_text:
        #                     yield chunk_text
        #         except Exception as e:
        #             yield f"\n\n提取流式响应失败：{str(e)}"
        #
        #     # 直接将官方流式文本传给st.write_stream
        #     assistant_content = st.write_stream(extract_stream_text( client))
        # st.session_state.messages.append({"role": "assistant", "content": assistant_content or "未获取到有效响应"})
        #

def render_brush_section_tab(records):
    """渲染刷段记录界面"""
    
    # 目标总距离
    TOTAL_TARGET_KM = 80
    
    # 过滤出非官方的记录（is_official=False）
    non_official_records = [record for record in records if record.is_official == False]
    
    # 初始化刷段记录字典
    brush_records = {
        "running": [],  # 跑步记录，单位：km
        "swimming": [],  # 游泳记录，单位：次
        "rope_skipping": []  # 跳绳记录，单位：个
    }
    
    # 将数据库记录转换为刷段记录格式
    for record in non_official_records:
        if record.exercise_type == "跑步" and record.distance:
            brush_records["running"].append(record.distance)
        elif record.exercise_type == "游泳":
            brush_records["swimming"].append(1)  # 每次游泳算1次
        elif record.exercise_type == "跳绳" and record.distance:
            # 跳绳记录中distance字段存储的是跳绳个数
            brush_records["rope_skipping"].append(record.distance)
    
    # 转换逻辑：计算总km数
    def calculate_total_km():
        # 跑步：直接算km
        running_km = sum(brush_records["running"])
        
        # 游泳：1次=2km
        swimming_km = sum(brush_records["swimming"]) * 2
        
        # 跳绳：400个=1km
        rope_skipping_km = sum(brush_records["rope_skipping"]) / 400
        
        total_km = running_km + swimming_km + rope_skipping_km
        return total_km
    
    # 计算当前进度
    current_total_km = calculate_total_km()
    progress_percentage = (current_total_km / TOTAL_TARGET_KM) * 100
    
    # 显示进度
    st.subheader("📊 刷段进度")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("当前累计", f"{current_total_km:.2f} km")
    with col2:
        st.metric("目标总距离", f"{TOTAL_TARGET_KM} km")
    with col3:
        st.metric("完成进度", f"{progress_percentage:.1f}%")
    
    # 进度条
    st.progress(min(progress_percentage / 100, 1.0), text=f"已完成 {current_total_km:.2f} km / {TOTAL_TARGET_KM} km")
    
    # 详细统计信息
    st.markdown("---")
    st.subheader("📋 详细统计")
    
    # 计算各运动类型的贡献
    running_km = sum(brush_records["running"])
    swimming_km = sum(brush_records["swimming"]) * 2
    rope_skipping_km = sum(brush_records["rope_skipping"]) / 400
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🏃 跑步")
        st.write(f"总距离: {running_km:.2f} km")
        st.write(f"贡献: {running_km:.2f} km")
        st.write(f"记录次数: {len(brush_records['running'])}")
    
    with col2:
        st.markdown("### 🏊 游泳")
        st.write(f"总次数: {sum(brush_records['swimming'])} 次")
        st.write(f"贡献: {swimming_km:.2f} km")
        st.write(f"记录次数: {len(brush_records['swimming'])}")
    
    with col3:
        st.markdown("### 🪢 跳绳")
        st.write(f"总个数: {sum(brush_records['rope_skipping'])} 个")
        st.write(f"贡献: {rope_skipping_km:.2f} km")
        st.write(f"记录次数: {len(brush_records['rope_skipping'])}")
    
    # 可视化图表
    st.markdown("---")
    st.subheader("📊 运动类型贡献比例")
    
    if current_total_km > 0:
        # 准备数据
        labels = ['跑步', '游泳', '跳绳']
        sizes = [running_km, swimming_km, rope_skipping_km]
        colors = ['#ff9999', '#66b3ff', '#99ff99']
        
        # 创建饼图
        fig, ax = plt.subplots()
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')  # 保持圆形
        
        # 显示图表
        st.pyplot(fig)
    else:
        st.info("暂无数据")
    
    # 历史记录表格
    st.markdown("---")
    st.subheader("📝 历史记录")
    
    # 合并所有记录
    all_records = []
    
    # 添加跑步记录
    for i, km in enumerate(brush_records['running']):
        all_records.append({
            '序号': i+1,
            '运动类型': '跑步',
            '数量': f'{km:.2f} km',
            '转换后km': f'{km:.2f} km'
        })
    
    # 添加游泳记录
    for i, times in enumerate(brush_records['swimming']):
        converted_km = times * 2
        all_records.append({
            '序号': len(all_records)+1,
            '运动类型': '游泳',
            '数量': f'{times} 次',
            '转换后km': f'{converted_km:.2f} km'
        })
    
    # 添加跳绳记录
    for i, counts in enumerate(brush_records['rope_skipping']):
        converted_km = counts / 400
        all_records.append({
            '序号': len(all_records)+1,
            '运动类型': '跳绳',
            '数量': f'{counts} 个',
            '转换后km': f'{converted_km:.2f} km'
        })
    
    # 显示表格
    if all_records:
        df = pd.DataFrame(all_records)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("暂无历史记录")

# 调用主函数
if __name__ == "__main__":
    main()