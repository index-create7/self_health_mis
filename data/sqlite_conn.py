import sqlite3
import hashlib
from datetime import datetime
import pandas as pd
from typing import Optional, List, Tuple

from self_health_mis.data.model.user_model import UserProfile
from self_health_mis.data.model.exercise_model import FitnessRecord
from self_health_mis.data.model.goal_model import FitnessGoal


class SQLiteDatabase:
    def __init__(self, db_name: str = "fitness_db.sqlite"):
        self.db_name = db_name
        self._create_tables()  # 初始化表（含新增字段）
        print(f"✅ 数据库初始化完成，文件路径：{self.db_name}")

    def _connect(self):
        try:
            conn = sqlite3.connect(self.db_name)
            conn.row_factory = sqlite3.Row  # 让查询结果支持字典式访问
            print(f"🔌 数据库连接成功")
            return conn
        except Exception as e:
            print(f"❌ 数据库连接失败：{str(e)}")
            raise

    def _create_tables(self):
        try:
            with self._connect() as conn:
                # 1. 用户账户表（不变）
                conn.execute('''
                             CREATE TABLE IF NOT EXISTS user_accounts
                             (
                                 id
                                 INTEGER
                                 PRIMARY
                                 KEY
                                 AUTOINCREMENT,
                                 username
                                 TEXT
                                 NOT
                                 NULL
                                 UNIQUE,
                                 password
                                 TEXT
                                 NOT
                                 NULL,
                                 create_time
                                 TEXT
                                 NOT
                                 NULL
                             )
                             ''')

                # 2. 运动记录表（核心修改：注释符从#改为--）
                conn.execute('''
                             CREATE TABLE IF NOT EXISTS fitness_records
                             (
                                 id
                                 INTEGER
                                 PRIMARY
                                 KEY
                                 AUTOINCREMENT,
                                 user_id
                                 INTEGER
                                 NOT
                                 NULL,
                                 date
                                 TEXT
                                 NOT
                                 NULL,
                                 exercise_type
                                 TEXT
                                 NOT
                                 NULL,
                                 duration
                                 REAL
                                 NOT
                                 NULL,
                                 distance
                                 REAL,
                                 calories
                                 INTEGER,
                                 is_official
                                 BOOLEAN
                                 NOT
                                 NULL
                                 DEFAULT
                                 0,
                                 notes
                                 TEXT,
                                 -- 新增核心指标相关字段（替换#为--）
                                 is_checkin
                                 BOOLEAN
                                 NOT
                                 NULL
                                 DEFAULT
                                 0,    -- 是否打卡（0/1）
                                 intensity
                                 REAL, -- 运动强度（如1-10分）
                                 recovery_quality
                                 REAL, -- 恢复质量（如1-10分）
                                 FOREIGN
                                 KEY
                             (
                                 user_id
                             ) REFERENCES user_accounts
                             (
                                 id
                             )
                                 )
                             ''')

                # 3. 运动目标表（不变）
                conn.execute('''
                             CREATE TABLE IF NOT EXISTS fitness_goals
                             (
                                 id
                                 INTEGER
                                 PRIMARY
                                 KEY
                                 AUTOINCREMENT,
                                 user_id
                                 INTEGER
                                 NOT
                                 NULL,
                                 goal_type
                                 TEXT
                                 NOT
                                 NULL,
                                 target_value
                                 REAL
                                 NOT
                                 NULL,
                                 current_value
                                 REAL
                                 NOT
                                 NULL
                                 DEFAULT
                                 0,
                                 start_date
                                 TEXT
                                 NOT
                                 NULL,
                                 end_date
                                 TEXT
                                 NOT
                                 NULL,
                                 is_completed
                                 BOOLEAN
                                 NOT
                                 NULL
                                 DEFAULT
                                 0,
                                 FOREIGN
                                 KEY
                             (
                                 user_id
                             ) REFERENCES user_accounts
                             (
                                 id
                             )
                                 )
                             ''')

                # 4. 用户资料表（不变）
                conn.execute('''
                             CREATE TABLE IF NOT EXISTS user_profile
                             (
                                 id
                                 INTEGER
                                 PRIMARY
                                 KEY
                                 AUTOINCREMENT,
                                 user_id
                                 INTEGER
                                 NOT
                                 NULL
                                 UNIQUE,
                                 name
                                 TEXT
                                 NOT
                                 NULL,
                                 student_id
                                 TEXT,
                                 age
                                 INTEGER,
                                 height
                                 REAL,
                                 weight
                                 REAL,
                                 fitness_level
                                 TEXT
                                 DEFAULT
                                 '初级',
                                 preferred_exercises
                                 TEXT,
                                 FOREIGN
                                 KEY
                             (
                                 user_id
                             ) REFERENCES user_accounts
                             (
                                 id
                             )
                                 )
                             ''')
                print("📋 所有数据表创建成功（含核心指标字段）")
        except Exception as e:
            print(f"❌ 创建数据表失败：{str(e)}")
            raise

    # 保留密码加密方法
    @staticmethod
    def _encrypt_password(password: str) -> str:
        salt = "fitness_system_salt_2025"
        return hashlib.md5((password + salt).encode()).hexdigest()

    # ========== 新增：获取用户健身记录并转换为DataFrame ==========
    def get_user_fitness_records(self, user_id: int) -> pd.DataFrame:
        """
        获取指定用户的所有健身记录，返回DataFrame
        :param user_id: 用户ID
        :return: 健身记录DataFrame（含is_checkin/intensity/recovery_quality字段）
        """
        try:
            with self._connect() as conn:
                query = '''
                        SELECT * \
                        FROM fitness_records \
                        WHERE user_id = ? \
                        '''
                # 读取数据并转换为DataFrame
                df = pd.read_sql(query, conn, params=(user_id,))
                # 确保布尔字段类型正确（SQLite返回0/1，转为bool）
                df["is_checkin"] = df["is_checkin"].astype(bool)
                df["is_official"] = df["is_official"].astype(bool)
                print(f"📊 成功获取用户{user_id}的健身记录，共{len(df)}条")
                return df
        except Exception as e:
            print(f"❌ 获取用户健身记录失败：{str(e)}")
            raise

    # ========== 新增：计算核心指标 ==========
    def calculate_core_metrics(self, user_id: int) -> Tuple[int, float, float, float]:
        """
        计算指定用户的健身核心指标
        :param user_id: 用户ID
        :return: (总打卡天数, 平均强度, 平均恢复质量, 周打卡率)
        """
        # 1. 获取用户健身记录DataFrame
        fitness_df = self.get_user_fitness_records(user_id)

        # 2. 空数据保护（无记录时直接返回0）
        if len(fitness_df) == 0:
            print(f"⚠️ 用户{user_id}无健身记录，核心指标默认返回0")
            return 0, 0.0, 0.0, 0.0

        # 3. 筛选有效打卡记录（过滤空值）
        checkin_df = fitness_df[fitness_df["is_checkin"]].dropna(
            subset=["intensity", "recovery_quality"]
        )
        total_checkin_days = checkin_df.shape[0]

        # 4. 计算平均强度（空值保护）
        avg_intensity = checkin_df["intensity"].mean().round(1) if not checkin_df.empty else 0.0

        # 5. 计算平均恢复质量（空值保护）
        avg_recovery = checkin_df["recovery_quality"].mean().round(1) if not checkin_df.empty else 0.0

        # 6. 计算周打卡率（分母保护，避免除以0）
        weekly_checkin_rate = (total_checkin_days / len(fitness_df) * 100).round(1)

        print(f"""
        📈 用户{user_id}核心指标计算完成：
        - 总打卡天数：{total_checkin_days}
        - 平均强度：{avg_intensity}
        - 平均恢复质量：{avg_recovery}
        - 周打卡率：{weekly_checkin_rate}%
        """)
        return total_checkin_days, avg_intensity, avg_recovery, weekly_checkin_rate


# 创建数据库实例（修改为fitness.db，和你的项目路径一致）
db_instance = SQLiteDatabase(db_name="fitness.db")
