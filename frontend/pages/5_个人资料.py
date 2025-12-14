# 个人资料页面
import sys
import os
import streamlit as st
from typing import List

# 设置中文字体
st.set_page_config(
    page_title="个人资料",
    page_icon="👤",
    layout="wide"
)

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入必要的模块
from self_health_mis.data.dal.user_dal import get_user_profile, update_user_profile
from self_health_mis.data.model.user_model import UserProfile
from self_health_mis.frontend.session_state import SessionState

# 创建会话状态管理器实例
session_manager = SessionState()

# 定义可用的健身等级和运动项目
FITNESS_LEVELS = ["初级", "中级", "高级", "专业"]
EXERCISE_OPTIONS = ["跑步", "游泳", "自行车", "力量训练", "瑜伽", "篮球", "足球", "网球", "羽毛球", "其他"]

def main():
    # 检查用户是否登录
    if not st.session_state.get('logged_in', False):
        st.warning("请先登录")
        if st.button("返回登录页面"):
            st.switch_page("app.py")
        return
    
    # 设置页面标题
    st.title("👤 个人资料管理")
    
    # 获取用户ID
    user_id = st.session_state.get('user_id')
    
    # 获取用户资料
    user_profile = get_user_profile(user_id)
    
    # 显示用户资料
    show_user_profile(user_profile)
    
    # 编辑用户资料
    edit_user_profile(user_profile)

def show_user_profile(profile: UserProfile):
    """显示用户资料"""
    st.subheader("当前资料")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**姓名**: {profile.name or '未设置'}")
        st.write(f"**学号**: {profile.student_id or '未设置'}")
        st.write(f"**年龄**: {profile.age or '未设置'}")
    
    with col2:
        st.write(f"**身高**: {profile.height} cm" if profile.height else "**身高**: 未设置")
        st.write(f"**体重**: {profile.weight} kg" if profile.weight else "**体重**: 未设置")
        st.write(f"**健身等级**: {profile.fitness_level}")
    
    st.write(f"**偏好运动**: {', '.join(profile.preferred_exercises) if profile.preferred_exercises else '未设置'}")

def edit_user_profile(profile: UserProfile):
    """编辑用户资料"""
    st.subheader("编辑资料")
    
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("姓名", value=profile.name or "")
            student_id = st.text_input("学号", value=profile.student_id or "")
            age = st.number_input("年龄", min_value=0, max_value=150, value=profile.age or 0, step=1)
            
        with col2:
            height = st.number_input("身高 (cm)", min_value=0.0, max_value=250.0, value=profile.height or 0.0, step=1.0)
            weight = st.number_input("体重 (kg)", min_value=0.0, max_value=200.0, value=profile.weight or 0.0, step=0.1)
            fitness_level = st.selectbox("健身等级", FITNESS_LEVELS, index=FITNESS_LEVELS.index(profile.fitness_level) if profile.fitness_level in FITNESS_LEVELS else 0)
        
        # 处理偏好运动项目
        selected_exercises = []
        if profile.preferred_exercises:
            # 转换为小写以便比较
            current_exercises_lower = [ex.lower() for ex in profile.preferred_exercises]
            selected_exercises = [ex for ex in EXERCISE_OPTIONS if ex.lower() in current_exercises_lower]
        
        # 多选框选择偏好运动
        preferred_exercises = st.multiselect("偏好运动项目", EXERCISE_OPTIONS, default=selected_exercises)
        
        # 提交按钮
        submit_button = st.form_submit_button("保存更新", type="primary")
        
        if submit_button:
            # 验证输入
            if not name:
                st.error("姓名不能为空")
                return
            
            # 创建更新后的资料对象
            updated_profile = UserProfile(
                id=profile.id,
                user_id=profile.user_id,
                name=name,
                student_id=student_id if student_id else None,
                age=age if age > 0 else None,
                height=height if height > 0 else None,
                weight=weight if weight > 0 else None,
                fitness_level=fitness_level,
                preferred_exercises=preferred_exercises
            )
            
            # 更新用户资料
            if update_user_profile(updated_profile):
                st.success("个人资料更新成功！")
                # 刷新页面
                st.rerun()
            else:
                st.error("个人资料更新失败，请重试")

if __name__ == "__main__":
    main()