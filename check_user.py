import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.sqlite_conn import db_instance  # 导入全局数据库实例

def check_user_accounts():
    """检查用户表中的账号信息"""
    try:
        with db_instance._connect() as conn:
            # 查询所有用户账号信息
            cursor = conn.execute("SELECT id, username, password FROM user_accounts")
            users = cursor.fetchall()
            
            print(f"发现 {len(users)} 个用户账号")
            print("=" * 50)
            
            for idx, user in enumerate(users):
                user_id = user['id']
                username = user['username']
                password_hash = user['password']
                
                print(f"用户 #{idx+1}:")
                print(f"  ID: {user_id}")
                print(f"  用户名: {username}")
                print(f"  密码哈希: {password_hash}")
                
                # 测试密码加密
                test_password = "test123"
                test_hash = db_instance._encrypt_password(test_password)
                print(f"  测试密码 '{test_password}' 加密后: {test_hash}")
                print(f"  密码匹配: {'✅ 是' if password_hash == test_hash else '❌ 否'}")
                print("-" * 50)
                
    except Exception as e:
        print(f"❌ 查询用户账号时出错: {str(e)}")
        
if __name__ == "__main__":
    print("开始检查用户账号信息...")
    check_user_accounts()