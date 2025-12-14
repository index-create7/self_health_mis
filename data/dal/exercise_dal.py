# data/dal/exercise_dal.py
from typing import List, Optional
from datetime import datetime
import pandas as pd
from self_health_mis.data.sqlite_conn import db_instance
from self_health_mis.data.model.exercise_model import FitnessRecord
from self_health_mis.data.model.goal_model import FitnessGoal

# 添加锻炼记录
def add_fitness_record(record: FitnessRecord) -> int:
    """
    添加一条锻炼记录到数据库
    
    Args:
        record: 锻炼记录对象
        
    Returns:
        int: 成功返回记录ID，失败返回-1
    """
    # 参数验证
    if record is None or record.user_id is None or record.user_id <= 0:
        print("❌ 无效的用户ID或记录数据")
        return -1
        
    if not record.exercise_type or record.duration <= 0:
        print("❌ 锻炼类型不能为空且时长必须大于0")
        return -1
        
    try:
        with db_instance._connect() as conn:
            conn.execute('BEGIN TRANSACTION')
            try:
                cursor = conn.execute('''
                    INSERT INTO fitness_records
                    (user_id, date, exercise_type, duration, distance, calories, is_official, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record.user_id, record.date.isoformat(), record.exercise_type,
                    record.duration, record.distance, record.calories,
                    record.is_official, record.notes
                ))
                record_id = cursor.lastrowid
                conn.execute('COMMIT')
                
                # 添加记录成功后，自动更新相关目标进度
                update_goals_from_record(
                    user_id=record.user_id,
                    exercise_type=record.exercise_type,
                    duration=record.duration,
                    distance=record.distance,
                    calories=record.calories
                )
                
                return record_id  # 返回新增记录ID
            except Exception:
                conn.execute('ROLLBACK')
                raise
                
    except Exception as e:
        print(f"❌ 添加锻炼记录失败：{str(e)}")
        return -1

# 查询锻炼记录
def get_fitness_records(
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    is_official: Optional[bool] = None
) -> List[FitnessRecord]:
    """
    查询用户锻炼记录
    
    Args:
        user_id: 用户ID
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
        is_official: 是否为官方记录（可选）
        
    Returns:
        List[FitnessRecord]: 锻炼记录列表，如果出错返回空列表
    """
    # 参数验证
    if user_id is None or user_id <= 0:
        print("❌ 无效的用户ID")
        return []
        
    # 确保日期范围合法性
    if start_date and end_date and end_date < start_date:
        print("❌ 结束日期不能早于开始日期")
        return []
    
    query = "SELECT * FROM fitness_records WHERE user_id = ?"
    params = [user_id]

    # 拼接查询条件
    if start_date:
        query += " AND date >= ?"
        params.append(start_date.isoformat())
    if end_date:
        query += " AND date <= ?"
        params.append(end_date.isoformat())
    if is_official is not None:
        query += " AND is_official = ?"
        params.append(1 if is_official else 0)

    query += " ORDER BY date DESC"

    try:
        with db_instance._connect() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        # 转换为FitnessRecord列表
        records = []
        for row in rows:
            try:
                records.append(FitnessRecord(
                    id=row["id"],
                    user_id=row["user_id"],
                    date=datetime.fromisoformat(row["date"]),
                    exercise_type=row["exercise_type"],
                    duration=row["duration"],
                    distance=row["distance"] if row["distance"] is not None else None,
                    calories=row["calories"] if row["calories"] is not None else None,
                    is_official=bool(row["is_official"]),
                    notes=row["notes"] if row["notes"] is not None else None
                ))
            except Exception as parse_error:
                print(f"❌ 解析锻炼记录时出错：{str(parse_error)}")
                continue
        return records
    except Exception as e:
        print(f"❌ 查询锻炼记录失败：{str(e)}")
        return []

# 添加锻炼目标
def add_fitness_goal(goal: FitnessGoal) -> int:
    """
    添加一条锻炼目标到数据库
    
    Args:
        goal: 锻炼目标对象
        
    Returns:
        int: 成功返回目标ID，失败返回-1
    """
    # 参数验证
    if goal is None or goal.user_id is None or goal.user_id <= 0:
        print("❌ 无效的用户ID或目标数据")
        return -1
        
    if not goal.goal_type or goal.target_value <= 0:
        print("❌ 目标类型不能为空且目标值必须大于0")
        return -1
        
    if goal.end_date < goal.start_date:
        print("❌ 目标结束日期不能早于开始日期")
        return -1
        
    try:
        with db_instance._connect() as conn:
            conn.execute('BEGIN TRANSACTION')
            try:
                cursor = conn.execute('''
                    INSERT INTO fitness_goals
                    (user_id, goal_type, target_value, current_value, start_date, end_date, is_completed)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    goal.user_id, goal.goal_type, goal.target_value, goal.current_value,
                    goal.start_date.isoformat(), goal.end_date.isoformat(), goal.is_completed
                ))
                goal_id = cursor.lastrowid
                conn.execute('COMMIT')
                return goal_id
            except Exception:
                conn.execute('ROLLBACK')
                raise
                
    except Exception as e:
        print(f"❌ 添加锻炼目标失败：{str(e)}")
        return -1

# 查询锻炼目标
def get_fitness_goals(user_id: int, include_completed: bool = True) -> List[FitnessGoal]:
    """
    查询用户锻炼目标
    
    Args:
        user_id: 用户ID
        include_completed: 是否包含已完成的目标
        
    Returns:
        List[FitnessGoal]: 锻炼目标列表，如果出错返回空列表
    """
    # 参数验证
    if user_id is None or user_id <= 0:
        print("❌ 无效的用户ID")
        return []
    
    query = "SELECT * FROM fitness_goals WHERE user_id = ?"
    params = [user_id]

    if not include_completed:
        query += " AND is_completed = 0"
    query += " ORDER BY end_date"

    try:
        with db_instance._connect() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        goals = []
        for row in rows:
            try:
                goals.append(FitnessGoal(
                    id=row["id"],
                    user_id=row["user_id"],
                    goal_type=row["goal_type"],
                    target_value=row["target_value"],
                    current_value=row["current_value"],
                    start_date=datetime.fromisoformat(row["start_date"]),
                    end_date=datetime.fromisoformat(row["end_date"]),
                    is_completed=bool(row["is_completed"])
                ))
            except Exception as parse_error:
                print(f"❌ 解析锻炼目标时出错：{str(parse_error)}")
                continue
        return goals
    except Exception as e:
        print(f"❌ 查询锻炼目标失败：{str(e)}")
        return []

# 更新目标进度
def update_goal_progress(goal_id: int, user_id: int, progress: float) -> bool:
    """
    更新锻炼目标的进度
    
    Args:
        goal_id: 目标ID
        user_id: 用户ID
        progress: 新的进度值
        
    Returns:
        bool: 更新成功返回True，失败返回False
    """
    # 参数验证
    if goal_id is None or goal_id <= 0:
        print("❌ 无效的目标ID")
        return False
        
    if user_id is None or user_id <= 0:
        print("❌ 无效的用户ID")
        return False
        
    if progress is None or progress < 0:
        print("❌ 进度值不能为负数")
        return False
        
    try:
        with db_instance._connect() as conn:
            conn.execute('BEGIN TRANSACTION')
            try:
                # 先查目标值，判断是否完成
                cursor = conn.execute("SELECT target_value, is_completed FROM fitness_goals WHERE id = ? AND user_id = ?", 
                                     (goal_id, user_id))
                goal = cursor.fetchone()
                if not goal:
                    conn.execute('ROLLBACK')
                    print(f"❌ 找不到目标ID为 {goal_id} 的记录")
                    return False

                target_value = goal["target_value"]
                current_value = min(progress, target_value)  # 进度不超过目标值
                is_completed = current_value >= target_value
                was_completed = bool(goal["is_completed"])

                # 更新进度和完成状态
                cursor.execute('''
                    UPDATE fitness_goals
                    SET current_value = ?, is_completed = ?
                    WHERE id = ? AND user_id = ?
                ''', (current_value, is_completed, goal_id, user_id))
                
                # 如果目标刚刚完成，输出完成信息
                if is_completed and not was_completed:
                    print(f"✅ 目标 {goal_id} 已完成！")
                    
                conn.execute('COMMIT')
                return cursor.rowcount > 0
            except Exception:
                conn.execute('ROLLBACK')
                raise
                
    except Exception as e:
        print(f"❌ 更新目标进度失败：{str(e)}")
        return False

# 更新目标值
def update_goal_target(goal_id: int, user_id: int, new_target: float) -> bool:
    try:
        with db_instance._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE fitness_goals
                SET target_value = ?, is_completed = ?
                WHERE id = ? AND user_id = ?
            ''', (new_target, False, goal_id, user_id))
        return cursor.rowcount > 0
    except Exception as e:
        print(f"❌ 更新目标值失败：{str(e)}")
        return False

# 获取锻炼统计数据（返回DataFrame）
def get_exercise_stats(user_id: int, period: str = "month") -> pd.DataFrame:
    end_date = datetime.now().date()
    # 计算统计起始日期
    if period == "month":
        start_date = end_date - datetime.timedelta(days=30)
    elif period == "week":
        start_date = end_date - datetime.timedelta(days=7)
    else:
        start_date = end_date - datetime.timedelta(days=365)
    end_date += datetime.timedelta(days=1)  # 包含当天

    try:
        with db_instance._connect() as conn:
            df = pd.read_sql_query('''
                SELECT date, exercise_type, duration, distance, calories
                FROM fitness_records
                WHERE user_id = ? AND date >= ? AND date <= ?
            ''', conn, params=[user_id, start_date.isoformat(), end_date.isoformat()])

        if not df.empty:
            df['date'] = pd.to_datetime(df['date']).dt.date
        return df
    except Exception as e:
        print(f"❌ 获取锻炼统计失败：{str(e)}")
        return pd.DataFrame()

# 自动更新目标进度

def auto_update_goal_progress(user_id: int):
    """
    根据现有锻炼记录自动更新用户所有未完成目标的进度
    
    Args:
        user_id: 用户ID
    """
    # 参数验证
    if user_id is None or user_id <= 0:
        print("❌ 无效的用户ID")
        return
        
    try:
        goals = get_fitness_goals(user_id, include_completed=False)
        if not goals:
            print(f"ℹ️ 用户 {user_id} 没有未完成的锻炼目标")
            return
            
        updated_count = 0
        for goal in goals:
            try:
                if goal.goal_type == "每周跑步次数":
                    # 统计周期内跑步次数
                    runs = [r for r in get_fitness_records(user_id) if
                            r.exercise_type == "跑步" and
                            goal.start_date <= r.date <= goal.end_date]
                    if update_goal_progress(goal.id, user_id, len(runs)):
                        updated_count += 1

                elif goal.goal_type == "每周锻炼总时长(分钟)":
                    # 统计周期内总时长
                    exercises = [r for r in get_fitness_records(user_id) if
                                goal.start_date <= r.date <= goal.end_date]
                    total_duration = sum(e.duration for e in exercises)
                    if update_goal_progress(goal.id, user_id, total_duration):
                        updated_count += 1
                        
                elif goal.goal_type == "每月跑步距离":
                    # 统计周期内跑步距离
                    runs = [r for r in get_fitness_records(user_id) if
                            r.exercise_type == "跑步" and
                            goal.start_date <= r.date <= goal.end_date and
                            r.distance is not None]
                    total_distance = sum(r.distance for r in runs)
                    if update_goal_progress(goal.id, user_id, total_distance):
                        updated_count += 1
                        
                elif goal.goal_type == "力量训练次数":
                    # 统计周期内力量训练次数
                    strength_workouts = [r for r in get_fitness_records(user_id) if
                                        r.exercise_type in ["力量训练", "举重", "俯卧撑", "深蹲"] and
                                        goal.start_date <= r.date <= goal.end_date]
                    if update_goal_progress(goal.id, user_id, len(strength_workouts)):
                        updated_count += 1
                        
            except Exception as goal_error:
                print(f"❌ 更新目标 {goal.id} 进度时出错：{str(goal_error)}")
                continue
                
        print(f"✅ 自动更新目标进度完成，共处理 {updated_count}/{len(goals)} 个目标")
                
    except Exception as e:
        print(f"❌ 自动更新目标进度失败：{str(e)}")


# 删除锻炼目标
def delete_fitness_goal(goal_id: int, user_id: int) -> bool:
    """
    删除指定的锻炼目标
    
    Args:
        goal_id: 目标ID
        user_id: 用户ID
        
    Returns:
        bool: 删除成功返回True，失败返回False
    """
    # 参数验证
    if goal_id is None or goal_id <= 0:
        print("❌ 无效的目标ID")
        return False
        
    if user_id is None or user_id <= 0:
        print("❌ 无效的用户ID")
        return False
        
    try:
        with db_instance._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM fitness_goals WHERE id = ? AND user_id = ?",
                (goal_id, user_id)
            )
            return cursor.rowcount > 0
    except Exception as e:
        print(f"❌ 删除锻炼目标失败：{str(e)}")
        return False

# 基于单个锻炼记录即时更新目标进度
def update_goals_from_record(user_id: int, exercise_type: str, duration: float, distance: float = None, calories: int = None):
    """
    根据新增锻炼记录即时更新相关目标的进度
    
    Args:
        user_id: 用户ID
        exercise_type: 锻炼类型
        duration: 锻炼时长（分钟）
        distance: 锻炼距离（可选，单位：公里）
        calories: 消耗卡路里（可选）
    """
    # 参数验证
    if user_id is None or user_id <= 0:
        print("❌ 无效的用户ID")
        return
        
    if not exercise_type or duration <= 0:
        print("❌ 锻炼类型不能为空且时长必须大于0")
        return
        
    try:
        # 获取用户所有未完成目标
        goals = get_fitness_goals(user_id, include_completed=False)
        updated_count = 0
        
        # 遍历每个目标，判断是否需要更新
        for goal in goals:
            try:
                if goal.goal_type == "每周跑步次数" and exercise_type == "跑步":
                    # 跑步次数目标，直接将当前进度加1
                    if update_goal_progress(goal.id, user_id, goal.current_value + 1):
                        updated_count += 1
                        
                elif goal.goal_type == "每周锻炼总时长(分钟)":
                    # 总时长目标，将当前时长加到现有进度
                    if update_goal_progress(goal.id, user_id, goal.current_value + duration):
                        updated_count += 1
                        
                elif goal.goal_type == "每月跑步距离" and exercise_type == "跑步" and distance is not None:
                    # 跑步距离目标，加上本次距离
                    if update_goal_progress(goal.id, user_id, goal.current_value + distance):
                        updated_count += 1
                        
                elif goal.goal_type == "力量训练次数" and exercise_type in ["力量训练", "举重", "俯卧撑", "深蹲"]:
                    # 力量训练次数目标，进度加1
                    if update_goal_progress(goal.id, user_id, goal.current_value + 1):
                        updated_count += 1
                        
                # 其他目标类型可以根据需要继续扩展...
                
            except Exception as goal_error:
                print(f"❌ 基于记录更新目标 {goal.id} 进度时出错：{str(goal_error)}")
                continue
                
        if updated_count > 0:
            print(f"✅ 基于锻炼记录成功更新 {updated_count} 个目标进度")
            
    except Exception as e:
        print(f"❌ 基于锻炼记录更新目标进度失败：{str(e)}")