import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.dal.user_dal import register_user

def add_test_user():
    """添加测试用户账号"""
    test_username = "test"
    test_password = "test123"
    
    print(f"开始创建测试用户账号: {test_username}/{test_password}")
    
    # 调用注册函数
    result = register_user(test_username, test_password)
    
    if result:
        print(f"✅ 测试用户账号创建成功！")
        print(f"\n请使用以下账号登录系统：")
        print(f"用户名: {test_username}")
        print(f"密码: {test_password}")
    else:
        print(f"❌ 测试用户账号创建失败！")
        print("可能的原因：")
        print("1. 用户名已存在")
        print("2. 数据库连接问题")
        print("3. 其他系统错误")

if __name__ == "__main__":
    add_test_user()