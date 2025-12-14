import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入核心认证模块
from core.auth import user_login

# 直接测试登录
print("开始测试test用户登录...")
result = user_login("test", "test123")
print(f"登录结果: {result}")

if result.get("status"):
    print("✅ 登录成功！")
else:
    print("❌ 登录失败！")
    print(f"失败原因: {result.get('message', '未知错误')}")
