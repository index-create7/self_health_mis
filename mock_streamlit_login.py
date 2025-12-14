import os
import sys
import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入必要的模块
from core.auth import user_login as auth_user_login

class MockStreamlitSession:
    """模拟Streamlit的会话状态"""
    def __init__(self):
        self.logged_in = False
        self.user_id = None
        self.username = None
        self.user_profile = None
        self.fitness_records = []
        self.fitness_goals = []
        self.cache_timestamp = datetime.datetime.now()

# 模拟Streamlit的st.session_state
class MockSt:
    def __init__(self):
        self.session_state = MockStreamlitSession()

# 模拟SessionState类的登录方法
def mock_login(username, password):
    """模拟登录功能"""
    print(f"[模拟Streamlit] 尝试登录，用户名: '{username}', 密码长度: {len(password)}")
    
    try:
        # 调用认证服务进行登录
        login_result = auth_user_login(username, password)
        print(f"[模拟Streamlit] 认证服务返回结果: {login_result}")
        
        if login_result["status"]:
            # 登录成功，设置会话状态
            mock_st = MockSt()
            mock_st.session_state.logged_in = True
            mock_st.session_state.user_id = login_result["user_id"]
            mock_st.session_state.username = username
            mock_st.session_state.cache_timestamp = datetime.datetime.now()
            print(f"[模拟Streamlit] 登录成功，用户ID: {login_result['user_id']}")
            return True
        else:
            print(f"[模拟Streamlit] 登录失败，消息: {login_result.get('message')}")
            return False
    except Exception as e:
        print(f"[模拟Streamlit] 登录异常: {str(e)}")
        return False

# 测试函数
def test_mock_login():
    """测试模拟登录"""
    test_username = "test"
    test_password = "test123"
    
    print(f"测试模拟登录: 用户名='{test_username}', 密码='{test_password}'")
    print("=" * 50)
    
    result = mock_login(test_username, test_password)
    print(f"模拟登录结果: {'✅ 成功' if result else '❌ 失败'}")

if __name__ == "__main__":
    test_mock_login()