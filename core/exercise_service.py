# core/exercise_service.py
from typing import List, Optional, Dict, Any, Union, TypedDict, Final
from datetime import datetime
import pandas as pd
from data.dal.exercise_dal import (
    add_fitness_record, get_fitness_records, add_fitness_goal,
    get_fitness_goals, get_exercise_stats, auto_update_goal_progress,
    update_goal_progress, update_goal_target
)
from self_health_mis.data.model.exercise_model import FitnessRecord
from self_health_mis.data.model.goal_model import FitnessGoal

from self_health_mis.data.sqlite_conn import db_instance

class ExerciseServiceError(Exception):
    """
    锻炼服务相关的自定义异常基类
    """
    pass


class ValidationError(ExerciseServiceError):
    """
    数据验证错误异常类
    """
    pass


class DatabaseError(ExerciseServiceError):
    """
    数据库操作错误异常类
    """
    pass


# 定义锻炼记录数据的类型结构
class ExerciseRecordData(TypedDict, total=False):
    """
    锻炼记录数据的类型定义
    """
    date: datetime  # 锻炼日期，必填
    exercise_type: str  # 锻炼类型，必填
    duration: Union[int, float]  # 锻炼时长(分钟)，必填
    distance: Optional[Union[int, float]]  # 距离，可选
    calories: Optional[int]  # 消耗的卡路里，可选
    is_official: Optional[bool]  # 是否官方记录，可选
    notes: Optional[str]  # 备注信息，可选


# 定义锻炼目标数据的类型结构
class FitnessGoalData(TypedDict):
    """
    锻炼目标数据的类型定义
    """
    goal_type: str  # 目标类型，必填
    target_value: Union[int, float]  # 目标值，必填
    start_date: datetime  # 开始日期，必填
    end_date: datetime  # 结束日期，必填


def validate_user_id(user_id: int) -> None:
    """
    验证用户ID的有效性
    
    参数:
        user_id: Any - 待验证的用户ID
    
    返回:
        None - 验证通过不返回值
    
    异常:
        ValidationError - 当user_id不是正整数时抛出
    """
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValidationError("用户ID必须为正整数")


def validate_exercise_data(record_data: Union[Dict[str, Any], ExerciseRecordData]) -> None:
    """
    验证锻炼记录数据的有效性，增强安全性和健壮性
    
    参数:
        record_data: Dict[str, Any] - 待验证的锻炼记录数据
    
    返回:
        None - 验证通过不返回值
    
    异常:
        ValidationError - 当数据不符合业务规则时抛出
    """
    # 确保record_data是字典类型
    if not isinstance(record_data, dict):
        raise ValidationError("锻炼记录数据必须是字典类型")
    
    # 验证必填字段存在
    required_fields = ["date", "exercise_type", "duration"]
    for field in required_fields:
        if field not in record_data:
            raise ValidationError(f"缺少必填字段: {field}")
    
    # 验证日期类型
    if not isinstance(record_data["date"], datetime):
        raise ValidationError("日期必须为datetime类型")
    
    # 验证日期不能是未来时间
    if record_data["date"] > datetime.now():
        raise ValidationError("锻炼日期不能是未来时间")
    
    # 验证锻炼类型
    exercise_type = str(record_data["exercise_type"].strip())
    if exercise_type == "":
        raise ValidationError("锻炼类型不能为空")
    # 限制锻炼类型长度，防止注入攻击
    if len(exercise_type) > 100:
        raise ValidationError("锻炼类型名称过长，最多100个字符")
    
    # 验证时长
    duration = record_data["duration"]
    if not isinstance(duration, (int, float)):
        raise ValidationError("锻炼时长必须是数值类型")
    if duration <= 0:
        raise ValidationError("锻炼时长必须大于0分钟")
    # 限制单次锻炼时长上限，防止不合理数据
    if duration > 1440:  # 24小时
        raise ValidationError("锻炼时长不能超过24小时")
    
    # 验证可选字段
    if "distance" in record_data and record_data["distance"] is not None:
        if not isinstance(record_data["distance"], (int, float)):
            raise ValidationError("距离必须是数值类型")
        if record_data["distance"] < 0:
            raise ValidationError("距离不能为负数")
    
    if "calories" in record_data and record_data["calories"] is not None:
        if not isinstance(record_data["calories"], int):
            raise ValidationError("卡路里必须是整数类型")
        if record_data["calories"] < 0:
            raise ValidationError("卡路里不能为负数")
    
    if "notes" in record_data and record_data["notes"] is not None:
        notes = str(record_data["notes"])
        # 限制备注长度
        if len(notes) > 1000:
            raise ValidationError("备注内容过长，最多1000个字符")
        record_data["notes"] = notes


def validate_goal_data(goal_data: Union[Dict[str, Any], FitnessGoalData]) -> None:
    """
    验证锻炼目标数据的有效性，增强安全性和健壮性
    
    参数:
        goal_data: Dict[str, Any] - 待验证的锻炼目标数据
    
    返回:
        None - 验证通过不返回值
    
    异常:
        ValidationError - 当数据不符合业务规则时抛出
    """
    # 确保goal_data是字典类型
    if not isinstance(goal_data, dict):
        raise ValidationError("锻炼目标数据必须是字典类型")
    
    # 验证必填字段存在
    required_fields = ["goal_type", "target_value", "start_date", "end_date"]
    for field in required_fields:
        if field not in goal_data:
            raise ValidationError(f"缺少必填字段: {field}")
    
    # 验证目标类型
    goal_type = str(goal_data["goal_type"].strip())
    if goal_type == "":
        raise ValidationError("目标类型不能为空")
    # 限制目标类型长度
    if len(goal_type) > 100:
        raise ValidationError("目标类型名称过长，最多100个字符")
    
    # 验证目标值
    target_value = goal_data["target_value"]
    if not isinstance(target_value, (int, float)):
        raise ValidationError("目标值必须是数值类型")
    if target_value <= 0:
        raise ValidationError("目标值必须大于0")
    
    # 验证日期类型和逻辑
    start_date = goal_data["start_date"]
    end_date = goal_data["end_date"]
    if not isinstance(start_date, datetime) or not isinstance(end_date, datetime):
        raise ValidationError("开始日期和结束日期必须为datetime类型")
    
    # 验证日期逻辑关系
    if start_date > datetime.now():
        raise ValidationError("目标开始日期不能晚于当前日期")
    if start_date >= end_date:
        raise ValidationError("开始日期不能晚于或等于结束日期")
    # 限制目标有效期，防止设置过长的目标
    max_goal_duration_days = 365
    if (end_date - start_date).days > max_goal_duration_days:
        raise ValidationError(f"目标有效期不能超过{max_goal_duration_days}天")


def add_user_exercise_record(user_id: int, record_data: Union[Dict[str, Any], ExerciseRecordData]) -> Optional[int]:
    """
    添加用户锻炼记录，包含完整的业务规则校验
    
    参数:
        user_id: int - 用户ID，必须为正整数
        record_data: dict - 锻炼记录数据字典，包含以下字段：
            - date: datetime - 锻炼日期
            - exercise_type: str - 锻炼类型，不能为空
            - duration: int/float - 锻炼时长（分钟），必须大于0
            - distance: (可选) float - 锻炼距离
            - calories: (可选) int - 消耗卡路里
            - is_official: (可选) bool - 是否为官方记录，默认为False
            - notes: (可选) str - 备注信息
    
    返回:
        Union[int, None] - 添加成功返回记录ID，失败返回None
    
    异常:
        ExerciseServiceError - 当发生服务相关错误时抛出
    """
    # 业务规则校验（核心！原代码隐含的规则显式提出来）
    validate_user_id(user_id)
    validate_exercise_data(record_data)

    # 确保is_official和notes的默认值正确处理
    is_official = record_data.get("is_official", False)
    if not isinstance(is_official, bool):
        is_official = False
        
    notes = record_data.get("notes", "")
    if notes is not None:
        notes = str(notes).strip()
    else:
        notes = ""
    
    # 封装为FitnessRecord对象
    record = FitnessRecord(
        user_id=user_id,
        date=record_data["date"],
        exercise_type=str(record_data["exercise_type"]).strip(),
        duration=float(record_data["duration"]),
        distance=float(record_data["distance"]) if record_data.get("distance") is not None else None,
        calories=int(record_data["calories"]) if record_data.get("calories") is not None else None,
        is_official=is_official,
        notes=notes
    )

    try:
        # 调用DAL添加记录
        record_id = add_fitness_record(record)
        if record_id > 0:
            # 添加成功后自动更新目标进度
            auto_update_goal_progress(user_id)
        return record_id
    except Exception as e:
        # 捕获数据库操作相关错误
        raise DatabaseError(f"添加锻炼记录失败: {str(e)}") from e

def get_user_exercise_records(
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    is_official: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """
    查询用户锻炼记录，封装DAL层调用，简化使用
    
    参数:
        user_id: int - 用户ID，必须为正整数
        start_date: (可选) datetime - 查询开始日期
        end_date: (可选) datetime - 查询结束日期
        is_official: (可选) bool - 是否筛选官方记录
    
    返回:
        List[FitnessRecord] - 符合条件的锻炼记录列表，若参数无效或查询失败返回空列表
    """
    try:
        validate_user_id(user_id)
        return get_fitness_records(user_id, start_date, end_date, is_official)
    except ExerciseServiceError:
        return []
    except Exception as e:
        raise DatabaseError(f"查询锻炼记录失败: {str(e)}") from e

def add_user_fitness_goal(user_id: int, goal_data: Union[Dict[str, Any], FitnessGoalData]) -> Optional[int]:
    """
    添加用户锻炼目标，包含完整的业务规则校验
    
    参数:
        user_id: int - 用户ID，必须为正整数
        goal_data: dict - 锻炼目标数据字典，包含以下字段：
            - goal_type: str - 目标类型，不能为空
            - target_value: int/float - 目标值，必须大于0
            - start_date: datetime - 目标开始日期
            - end_date: datetime - 目标结束日期，必须晚于开始日期
    
    返回:
        Union[int, None] - 添加成功返回目标ID，失败返回None
    
    异常:
        ExerciseServiceError - 当发生服务相关错误时抛出
    """
    # 业务校验
    validate_user_id(user_id)
    validate_goal_data(goal_data)

    # 封装为FitnessGoal对象
    goal = FitnessGoal(
        user_id=user_id,
        goal_type=goal_data["goal_type"].strip(),
        target_value=goal_data["target_value"],
        current_value=0.0,
        start_date=goal_data["start_date"],
        end_date=goal_data["end_date"],
        is_completed=False
    )
    try:
        return add_fitness_goal(goal)
    except Exception as e:
        # 捕获数据库操作相关错误
        raise DatabaseError(f"添加锻炼目标失败: {str(e)}") from e

def get_user_fitness_goals(user_id: int, include_completed: bool = True) -> List[Dict[str, Any]]:
    """
    获取用户锻炼目标，封装DAL层调用，简化使用
    
    参数:
        user_id: int - 用户ID，必须为正整数
        include_completed: bool - 是否包含已完成的目标，默认为True
    
    返回:
        List[FitnessGoal] - 用户的锻炼目标列表，若参数无效或查询失败返回空列表
    """
    try:
        validate_user_id(user_id)
        return get_fitness_goals(user_id, include_completed)
    except ExerciseServiceError:
        return []
    except Exception as e:
        raise DatabaseError(f"查询锻炼目标失败: {str(e)}") from e

def get_user_exercise_stats(user_id: int, period: str = "month") -> Dict[str, Any]:
    """
    获取用户锻炼统计数据，封装DAL层调用，简化使用
    
    参数:
        user_id: int - 用户ID，必须为正整数
        period: str - 统计周期，可以是'day'、'week'、'month'或'year'，默认为'month'
    
    返回:
        Dict[str, Any] - 锻炼统计数据字典，若参数无效或查询失败返回空字典
    """
    validate_user_id(user_id)
    
    # 验证统计周期参数
    valid_periods = {'day', 'week', 'month', 'year'}
    if not isinstance(period, str) or period.lower() not in valid_periods:
        raise ValidationError(f"无效的统计周期: {period}，必须是{valid_periods}之一")
    
    try:
        # 调用数据访问层获取统计数据
        stats = get_exercise_stats(user_id, period.lower())
        # 确保返回的是字典类型
        if hasattr(stats, 'to_dict'):
            return stats.to_dict()
        elif isinstance(stats, dict):
            return stats
        else:
            return {}
    except ExerciseServiceError:
        # 直接传递服务层异常
        raise
    except Exception as e:
        raise DatabaseError(f"获取锻炼统计数据失败: {str(e)}") from e



def get_user_fitness_metrics(user_id: int):
    """业务层封装：获取用户健身核心指标"""
    return db_instance.calculate_core_metrics(user_id)