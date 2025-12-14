import streamlit as st
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入认证模块
from core.auth import user_login

# 页面标题
st.title("登录功能测试")

# 登录表单
with st.form("login_form"):
    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")
    login_button = st.form_submit_button("登录", type="primary")
    
    if login_button:
        st.write("正在处理登录...")
        
        # 添加调试信息
        st.write(f"尝试登录，用户名: '{username}', 密码长度: {len(password)}")
        
        # 直接调用认证函数
        try:
            result = user_login(username, password)
            st.write(f"认证结果: {result}")
            
            if result["status"]:
                st.success(f"登录成功！用户ID: {result['user_id']}")
            else:
                st.error(f"登录失败: {result['message']}")
        except Exception as e:
            st.error(f"发生错误: {str(e)}")

# 显示测试账号信息
st.markdown("""
**测试账号：**
- 用户名：test
- 密码：test123
""")