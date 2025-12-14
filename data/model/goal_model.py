from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class FitnessGoal:
    id: Optional[int] = None
    user_id: Optional[int] = None
    goal_type: str = ""
    target_value: float = 0.0
    current_value: float = 0.0
    start_date: datetime = datetime.now()
    end_date: datetime = datetime.now()
    is_completed: bool = False