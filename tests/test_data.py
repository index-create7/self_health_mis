#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
临时测试脚本：验证fitness.db数据库读写功能
"""

import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.sqlite_conn import SQLiteDatabase
from data.model.exercise_model import FitnessRecord
from data.model.goal_model import FitnessGoal


def test_database_connection():
    """
    测试数据库连接和表创建
    """
    print("\n=== 测试1: 数据库连接 ===")
    try:
        # 使用相对路径，确保数据库文件在正确位置
        db = SQLiteDatabase(db_name="fitness.db")
        print("✅ 数据库连接测试通过")
        return db
    except Exception as e:
        print(f"❌ 数据库连接测试失败: {e}")
        return None


def test_create_test_user(db):
    """
    创建测试用户（如果不存在）
    """
    print("\n=== 测试2: 创建测试用户 ===")
    try:
        # 先检查是否已有测试用户
        with db._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM user_accounts WHERE username = ?", ("test_user",))
            result = cursor.fetchone()
            
            if result:
                user_id = result[0]
                print(f"✅ 测试用户已存在，用户ID: {user_id}")
                return user_id
            
            # 创建测试用户
            cursor.execute(
                "INSERT INTO user_accounts (username, password, create_time) VALUES (?, ?, ?)",
                ("test_user", db._encrypt_password("test123"), datetime.now().isoformat())
            )
            user_id = cursor.lastrowid
            conn.commit()
            print(f"✅ 测试用户创建成功，用户ID: {user_id}")
            return user_id
    except Exception as e:
        print(f"❌ 创建测试用户失败: {e}")
        return None


def test_write_fitness_record(db, user_id):
    """
    写入一条锻炼记录
    """
    print("\n=== 测试3: 写入锻炼记录 ===")
    try:
        # 创建测试锻炼记录
        record = FitnessRecord(
            user_id=user_id,
            date=datetime.now() - timedelta(days=1),  # 昨天
            exercise_type="跑步",
            duration=30.0,  # 30分钟
            distance=5.0,   # 5公里
            calories=300,   # 300卡路里
            is_official=True,
            notes="测试记录"
        )
        
        # 写入数据库
        with db._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO fitness_records 
                (user_id, date, exercise_type, duration, distance, calories, is_official, notes) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.user_id,
                    record.date.isoformat(),
                    record.exercise_type,
                    record.duration,
                    record.distance,
                    record.calories,
                    1 if record.is_official else 0,
                    record.notes
                )
            )
            record_id = cursor.lastrowid
            conn.commit()
            
        print(f"✅ 锻炼记录写入成功，记录ID: {record_id}")
        return record_id
    except Exception as e:
        print(f"❌ 锻炼记录写入失败: {e}")
        return None


def test_write_fitness_goal(db, user_id):
    """
    写入一条锻炼目标
    """
    print("\n=== 测试4: 写入锻炼目标 ===")
    try:
        # 创建测试锻炼目标
        goal = FitnessGoal(
            user_id=user_id,
            goal_type="每周跑步",
            target_value=20.0,  # 目标20公里
            current_value=5.0,   # 已完成5公里
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now() + timedelta(days=7),
            is_completed=False
        )
        
        # 写入数据库
        with db._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO fitness_goals 
                (user_id, goal_type, target_value, current_value, start_date, end_date, is_completed) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    goal.user_id,
                    goal.goal_type,
                    goal.target_value,
                    goal.current_value,
                    goal.start_date.isoformat(),
                    goal.end_date.isoformat(),
                    1 if goal.is_completed else 0
                )
            )
            goal_id = cursor.lastrowid
            conn.commit()
            
        print(f"✅ 锻炼目标写入成功，目标ID: {goal_id}")
        return goal_id
    except Exception as e:
        print(f"❌ 锻炼目标写入失败: {e}")
        return None


def test_read_fitness_records(db, user_id):
    """
    读取并验证锻炼记录
    """
    print("\n=== 测试5: 读取锻炼记录 ===")
    try:
        with db._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM fitness_records WHERE user_id = ? ORDER BY date DESC LIMIT 3",
                (user_id,)
            )
            records = cursor.fetchall()
            
            if not records:
                print("⚠️  没有找到锻炼记录")
                return False
                
            print(f"✅ 找到 {len(records)} 条锻炼记录")
            # 打印最近的一条记录详情
            for i, record in enumerate(records, 1):
                print(f"\n记录 {i}:")
                print(f"  ID: {record['id']}")
                print(f"  类型: {record['exercise_type']}")
                print(f"  时长: {record['duration']}分钟")
                print(f"  距离: {record['distance']}公里")
                print(f"  卡路里: {record['calories']}")
                print(f"  日期: {record['date']}")
            
            return True
    except Exception as e:
        print(f"❌ 读取锻炼记录失败: {e}")
        return False


def test_read_fitness_goals(db, user_id):
    """
    读取并验证锻炼目标
    """
    print("\n=== 测试6: 读取锻炼目标 ===")
    try:
        with db._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM fitness_goals WHERE user_id = ?",
                (user_id,)
            )
            goals = cursor.fetchall()
            
            if not goals:
                print("⚠️  没有找到锻炼目标")
                return False
                
            print(f"✅ 找到 {len(goals)} 个锻炼目标")
            # 打印所有目标
            for i, goal in enumerate(goals, 1):
                print(f"\n目标 {i}:")
                print(f"  ID: {goal['id']}")
                print(f"  类型: {goal['goal_type']}")
                print(f"  目标值: {goal['target_value']}")
                print(f"  当前值: {goal['current_value']}")
                print(f"  完成度: {goal['is_completed']}")
                print(f"  开始日期: {goal['start_date']}")
                print(f"  结束日期: {goal['end_date']}")
            
            return True
    except Exception as e:
        print(f"❌ 读取锻炼目标失败: {e}")
        return False


def main():
    """
    主测试函数
    """
    print("====================================")
    print("     Fitness Database 测试脚本      ")
    print("====================================")
    
    # 1. 测试数据库连接
    db = test_database_connection()
    if not db:
        print("\n❌ 测试失败：无法连接数据库")
        return
    
    # 2. 创建测试用户
    user_id = test_create_test_user(db)
    if not user_id:
        print("\n❌ 测试失败：无法创建测试用户")
        return
    
    # 3. 写入锻炼记录
    test_write_fitness_record(db, user_id)
    
    # 4. 写入锻炼目标
    test_write_fitness_goal(db, user_id)
    
    # 5. 读取锻炼记录
    read_records = test_read_fitness_records(db, user_id)
    
    # 6. 读取锻炼目标
    read_goals = test_read_fitness_goals(db, user_id)
    
    # 总结测试结果
    print("\n====================================")
    if read_records and read_goals:
        print("✅ 数据库读写测试全部通过！")
        print(f"\n📊 测试统计：")
        print(f"   数据库文件: fitness.db")
        print(f"   测试用户ID: {user_id}")
        print(f"   测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("⚠️  部分测试未通过，请检查日志")
    print("====================================")


if __name__ == "__main__":
    main()
