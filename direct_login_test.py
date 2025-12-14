import streamlit as st
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入认证模块
from core.auth import user_login

# 初始化会话状态（使用Streamlit原生会话状态）
def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None

# 登录函数
def handle_login(username, password):
    st.write(f"🔍 开始处理登录请求")
    st.write(f"用户名: '{username}', 密码长度: {len(password)}")
    
    # 基本验证
    if not username or not password:
        st.error("用户名和密码不能为空")
        return False
    
    try:
        # 直接调用认证服务
        result = user_login(username, password)
        st.write(f"📊 认证结果: {result}")
        
        if result.get('status'):
            # 登录成功，更新会话状态
            st.session_state.logged_in = True
            st.session_state.user_id = result.get('user_id')
            st.session_state.username = username
            st.success(f"✅ 登录成功！用户ID: {result.get('user_id')}")
            return True
        else:
            st.error(f"❌ 登录失败: {result.get('message', '未知错误')}")
            return False
    except Exception as e:
        st.error(f"❌ 登录过程发生异常: {str(e)}")
        return False

# 登出函数
def handle_logout():
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.info("已退出登录")

# 主页面函数
def main():
    # 初始化会话状态
    init_session_state()
    
    # 设置页面标题
    st.title("直接登录测试应用")
    
    # 检查登录状态
    if not st.session_state.logged_in:
        # 登录表单
        st.subheader("请登录")
        with st.form("login_form"):
            username = st.text_input("用户名")
            password = st.text_input("密码", type="password")
            login_button = st.form_submit_button("登录", type="primary")
            
            if login_button:
                # 处理登录请求
                handle_login(username, password)
                
                # 如果登录成功，刷新页面
                if st.session_state.logged_in:
                    st.rerun()
        
        # 显示测试账号信息
        st.markdown("""
        ### 测试账号
        - **用户名**: test
        - **密码**: test123
        """)
    else:
        # 已登录状态
        st.success(f"已登录为: {st.session_state.username} (ID: {st.session_state.user_id})")
        
        # 显示会话状态信息
        st.markdown("### 当前会话状态")
        st.json({
            "logged_in": st.session_state.logged_in,
            "user_id": st.session_state.user_id,
            "username": st.session_state.username
        })
        
        # 登出按钮
        if st.button("退出登录", type="secondary"):
            handle_logout()
            st.rerun()

# 运行应用
if __name__ == "__main__":
    main()