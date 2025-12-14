from dataclasses import dataclass
from typing import List, Optional

@dataclass
class UserProfile:
    id: Optional[int] = None
    user_id: Optional[int] = None
    name: str = ""
    student_id: Optional[str] = None
    age: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    fitness_level: str = "初级"
    preferred_exercises: List[str] = None