from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class FitnessRecord:
    id: Optional[int] = None
    user_id: Optional[int] = None
    date: datetime = datetime.now()
    exercise_type: str = ""
    duration: float = 0.0
    distance: Optional[float] = None
    calories: Optional[int] = None
    is_official: bool = False
    notes: Optional[str] = None
    # 新增字段
    is_checkin: bool = False          # 是否打卡
    intensity: Optional[float] = None # 运动强度
    recovery_quality: Optional[float] = None # 恢复质量
