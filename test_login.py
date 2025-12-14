import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.auth import user_login

def test_login_function():
    """测试登录功能"""
    test_username = "test"
    test_password = "test123"
    
    print(f"测试登录: 用户名='{test_username}', 密码='{test_password}'")
    print("=" * 50)
    
    # 直接调用认证服务的登录函数
    result = user_login(test_username, test_password)
    
    print(f"登录结果: {result}")
    print(f"状态: {'✅ 成功' if result['status'] else '❌ 失败'}")
    print(f"用户ID: {result.get('user_id')}")
    print(f"消息: {result.get('message')}")
    
    # 再测试另一个账号
    print("\n" + "=" * 50)
    print("测试登录: 用户名='test_user', 密码='test123'")
    result2 = user_login("test_user", "test123")
    print(f"登录结果: {result2}")
    print(f"状态: {'✅ 成功' if result2['status'] else '❌ 失败'}")
    print(f"用户ID: {result2.get('user_id')}")
    print(f"消息: {result2.get('message')}")

if __name__ == "__main__":
    test_login_function()