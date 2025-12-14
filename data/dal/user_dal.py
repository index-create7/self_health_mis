# data/dal/user_dal.py
from typing import Optional
from datetime import datetime
from data.sqlite_conn import db_instance  # 导入全局数据库实例
from data.model.user_model import UserProfile

# 数据访问层专注于纯数据库操作，业务逻辑应由服务层处理

# 注册用户（纯数据库操作，无业务校验）
def register_user(username: str, password: str) -> bool:
    try:
        normalized_username = username.strip().lower()
        # 检查用户名是否已存在
        with db_instance._connect() as conn:
            cursor = conn.execute(
                "SELECT username FROM user_accounts WHERE LOWER(username) = ?",
                (normalized_username,)
            )
            if cursor.fetchone():
                print(f"❌ 用户名 {normalized_username} 已存在")
                return False

            # 加密密码并插入用户表
            # 注意：当前使用MD5加密密码仅为临时实现，存在安全风险
            encrypted_pwd = db_instance._encrypt_password(password)
            cursor.execute('''
                INSERT INTO user_accounts (username, password, create_time)
                VALUES (?, ?, ?)
            ''', (normalized_username, encrypted_pwd, datetime.now().isoformat()))
            user_id = cursor.lastrowid

            # 创建默认个人资料
            profile_created = _create_default_profile(user_id, normalized_username)
            if not profile_created:
                print(f"⚠️ 用户已创建，但个人资料创建失败")
                
        print(f"✅ 注册成功：用户ID {user_id}")
        return True
    except Exception as e:
        print(f"❌ 注册失败：{str(e)}")
        return False

# 内部方法：创建默认个人资料
def _create_default_profile(user_id: int, username: str) -> bool:
    """
    为新注册用户创建默认个人资料
    
    Args:
        user_id: 用户ID
        username: 用户名
        
    Returns:
        bool: 创建成功返回True，失败返回False
    """
    try:
        if user_id is None or user_id <= 0:
            print(f"❌ 无效的用户ID: {user_id}")
            return False
            
        with db_instance._connect() as conn:
            # 显式事务控制
            conn.execute('BEGIN TRANSACTION')
            try:
                # 使用默认空列表字符串而非具体值，让用户自行设置偏好
                conn.execute('''
                    INSERT INTO user_profile (user_id, name, fitness_level, preferred_exercises)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, username, "初级", ""))
                conn.execute('COMMIT')
                return True
            except Exception:
                conn.execute('ROLLBACK')
                raise
                
    except Exception as e:
        print(f"❌ 创建默认资料失败：{str(e)}")
        return False

# 用户登录（纯数据库操作）
def login_user(username: str, password: str) -> Optional[int]:
    if not username or not password:  # 基本输入验证
        return None
        
    normalized_username = username.strip().lower()
    encrypted_pwd = db_instance._encrypt_password(password)
    user_id = None
    
    try:
        with db_instance._connect() as conn:
            cursor = conn.execute('''
                SELECT id FROM user_accounts
                WHERE username = ? AND password = ?
            ''', (normalized_username, encrypted_pwd))
            result = cursor.fetchone()
            user_id = result["id"] if result else None
            
            # 注意：登录成功时不打印敏感信息，提高安全性
            if user_id is None:
                print(f"⚠️  登录失败：用户名或密码错误")
                
        return user_id
    except Exception as e:
        print(f"❌ 登录异常：{str(e)}")
        return None

# 获取个人资料（纯数据库查询）
def get_user_profile(user_id: int) -> UserProfile:
    try:
        # 输入参数校验
        if user_id is None or user_id <= 0:
            print(f"❌ 无效的用户ID: {user_id}")
            return UserProfile(name="默认用户", user_id=None)
            
        with db_instance._connect() as conn:
            cursor = conn.execute("SELECT * FROM user_profile WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()

        if not row:
            # 创建默认配置文件时，使用空列表而非None
            return UserProfile(name="默认用户", user_id=user_id, preferred_exercises=[])

        # 转换偏好锻炼类型为列表，处理空字符串和None值
        exercises_str = row["preferred_exercises"]
        preferred_exercises = []
        if exercises_str:
            preferred_exercises = [ex.strip() for ex in exercises_str.split(',') if ex.strip()]  # 清理空白
            
        return UserProfile(
            id=row["id"],
            user_id=row["user_id"],
            name=row["name"] or "",  # 确保name不为None
            student_id=row["student_id"],
            age=row["age"],
            height=row["height"],
            weight=row["weight"],
            fitness_level=row["fitness_level"] or "初级",  # 提供默认值
            preferred_exercises=preferred_exercises
        )
    except Exception as e:
        print(f"❌ 获取个人资料失败：{str(e)}")
        # 确保返回安全的默认值
        return UserProfile(name="默认用户", user_id=user_id, preferred_exercises=[])

# 更新个人资料（纯数据库更新）
def update_user_profile(profile: UserProfile) -> bool:
    try:
        # 确保preferred_exercises不为None，防止join操作失败
        if profile.preferred_exercises is None:
            profile.preferred_exercises = []
            
        exercises_str = ','.join(profile.preferred_exercises)
        affected_rows = 0
        
        with db_instance._connect() as conn:
            # 显式开始事务
            conn.execute('BEGIN TRANSACTION')
            try:
                cursor = conn.execute('''
                    UPDATE user_profile
                    SET name = ?, student_id = ?, age = ?, height = ?,
                        weight = ?, fitness_level = ?, preferred_exercises = ?
                    WHERE user_id = ?
                ''', (
                    profile.name, profile.student_id, profile.age, profile.height,
                    profile.weight, profile.fitness_level, exercises_str,
                    profile.user_id
                ))
                affected_rows = cursor.rowcount
                conn.execute('COMMIT')  # 提交事务
            except Exception:
                conn.execute('ROLLBACK')  # 发生异常时回滚事务
                raise
                
        return affected_rows > 0  # 判断是否更新成功
    except Exception as e:
        print(f"❌ 更新资料失败：{str(e)}")
        return False