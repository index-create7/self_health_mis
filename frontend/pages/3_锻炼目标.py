# 锻炼目标页面
import sys
import os
from datetime import datetime, timedelta
import streamlit as st
import matplotlib.pyplot as plt

# 设置中文字体（解决matplotlib中文显示问题）
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from self_health_mis.data.dal.exercise_dal import (
    get_fitness_goals, add_fitness_goal, update_goal_progress, delete_fitness_goal,
    auto_update_goal_progress
)
from self_health_mis.data.model.goal_model import FitnessGoal
from self_health_mis.frontend.session_state import SessionState

# 创建会话状态管理器实例
session_manager = SessionState()

def main():
    # 检查用户是否登录
    if not st.session_state.get('logged_in', False):
        st.warning("请先登录")
        if st.button("返回登录页面"):
            st.switch_page("app.py")
        return
    
    # 设置页面标题和导航
    st.title("💪 锻炼目标管理")
    
    # 侧边栏显示用户信息
    st.sidebar.header("用户信息")
    st.sidebar.write(f"用户名: {st.session_state.get('username', '未知')}")
    st.sidebar.write(f"用户ID: {st.session_state.get('user_id', '未知')}")
    
    # 自动更新目标进度
    user_id = st.session_state.get('user_id')
    if user_id:
        auto_update_goal_progress(user_id)
    
    # 获取用户目标
    goals = get_fitness_goals(user_id, include_completed=True)
    
    # 显示目标列表
    display_goals(goals)
    
    # 创建新目标
    create_new_goal()
    
    # 目标进度可视化
    visualize_goals(goals)

def display_goals(goals):
    """显示用户的锻炼目标列表"""
    st.subheader("📋 我的锻炼目标")
    
    if not goals:
        st.info("暂无锻炼目标，点击下方按钮创建新目标")
        return
    
    # 创建目标卡片展示
    for goal in goals:
        with st.expander(f"{goal.goal_type} - {'已完成' if goal.is_completed else '进行中'}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**目标值**: {goal.target_value}")
                st.write(f"**当前进度**: {goal.current_value}")
                st.write(f"**开始日期**: {goal.start_date.strftime('%Y-%m-%d')}")
                st.write(f"**结束日期**: {goal.end_date.strftime('%Y-%m-%d')}")
            
            with col2:
                # 计算进度百分比
                progress_percentage = (goal.current_value / goal.target_value) * 100 if goal.target_value > 0 else 0
                st.progress(progress_percentage / 100)  # 转换为0-1范围
                st.write(f"**完成度**: {progress_percentage:.1f}%")
                
                # 计算剩余天数
                today = datetime.now()
                if goal.end_date > today and not goal.is_completed:
                    remaining_days = (goal.end_date - today).days
                    st.write(f"**剩余天数**: {remaining_days} 天")
                elif goal.end_date <= today and not goal.is_completed:
                    st.warning("目标已过期")
                
            # 更新和删除按钮
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if not goal.is_completed:
                    update_progress = st.number_input(
                        f"更新进度: {goal.goal_type}",
                        min_value=0.0,
                        value=goal.current_value,
                        step=0.1,
                        key=f"update_{goal.id}"
                    )
                    
                    if st.button("保存进度", key=f"save_{goal.id}"):
                        if update_goal_progress(goal.id, st.session_state.user_id, update_progress):
                            st.success("进度更新成功")
                            st.rerun()
                        else:
                            st.error("进度更新失败")
            
            with col2:
                if st.button("删除目标", key=f"delete_{goal.id}", type="primary", help="删除此目标"):
                    if delete_fitness_goal(goal.id, st.session_state.user_id):
                        st.success("目标删除成功")
                        st.rerun()
                    else:
                        st.error("目标删除失败")

def create_new_goal():
    """创建新的锻炼目标"""
    st.subheader("➕ 创建新目标")
    
    with st.form("new_goal_form"):
        # 目标类型选择
        goal_types = ["每周跑步次数", "每周锻炼总时长(分钟)", "每月跑步距离", "力量训练次数"]
        selected_type = st.selectbox("选择目标类型", goal_types)
        
        # 目标值
        target_value = st.number_input("目标值", min_value=1.0, step=1.0)
        
        # 日期选择
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("开始日期", value=datetime.now().date())
        with col2:
            # 默认结束日期为开始日期后30天
            default_end_date = start_date + timedelta(days=30)
            end_date = st.date_input("结束日期", value=default_end_date)
        
        # 提交按钮
        submit_button = st.form_submit_button("创建目标", type="primary")
        
        if submit_button:
            # 验证日期
            if end_date < start_date:
                st.error("结束日期不能早于开始日期")
                return
            
            # 创建目标对象
            new_goal = FitnessGoal(
                user_id=st.session_state.user_id,
                goal_type=selected_type,
                target_value=target_value,
                current_value=0.0,
                start_date=datetime.combine(start_date, datetime.min.time()),
                end_date=datetime.combine(end_date, datetime.min.time()),
                is_completed=False
            )
            
            # 保存目标
            goal_id = add_fitness_goal(new_goal)
            if goal_id > 0:
                st.success(f"目标创建成功！目标ID: {goal_id}")
                st.rerun()
            else:
                st.error("目标创建失败")

def visualize_goals(goals):
    """目标进度可视化"""
    st.subheader("📊 目标进度可视化")
    
    if not goals:
        return
    
    # 准备数据
    active_goals = [goal for goal in goals if not goal.is_completed]
    completed_goals = [goal for goal in goals if goal.is_completed]
    
    # 目标完成状态统计
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**进行中目标**: {len(active_goals)}")
    with col2:
        st.markdown(f"**已完成目标**: {len(completed_goals)}")
    
    # 绘制目标进度条形图
    if active_goals:
        fig, ax = plt.subplots(figsize=(10, len(active_goals) * 0.5))
        
        goal_names = [f"{goal.goal_type} (ID: {goal.id})\n{goal.start_date.strftime('%Y-%m-%d')} 至 {goal.end_date.strftime('%Y-%m-%d')}" for goal in active_goals]
        current_values = [goal.current_value for goal in active_goals]
        target_values = [goal.target_value for goal in active_goals]
        
        # 创建堆叠条形图
        ax.barh(goal_names, current_values, label='当前进度', color='#4CAF50')
        ax.barh(goal_names, [t - c for t, c in zip(target_values, current_values)], 
                left=current_values, label='剩余目标', color='#FF9800')
        
        # 设置图表样式
        ax.set_xlabel('数值')
        ax.set_title('当前目标进度')
        ax.legend()
        
        # 在条形图上显示数值
        for i, (c, t) in enumerate(zip(current_values, target_values)):
            ax.text(c / 2, i, f'{c:.1f}', ha='center', va='center', color='white', fontweight='bold')
            ax.text(c + (t - c) / 2, i, f'{t - c:.1f}', ha='center', va='center', color='white', fontweight='bold')
        
        st.pyplot(fig)

if __name__ == "__main__":
    main()
