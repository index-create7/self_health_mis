
import sys
import os

import json
import pandas as pd
import streamlit as st
from datetime import datetime
from typing import Tuple, Optional, Dict, Any

from self_health_mis.data.model.exercise_model import FitnessRecord
from self_health_mis.data.dal.exercise_dal import add_fitness_record


def process_ai_response(response: str, current_user_id: int = None) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    处理AI助手响应，判断是否为锻炼记录并转换为可编辑表格

    Args:
        response: AI助手的响应内容
        current_user_id: 当前登录用户ID，用于保存记录

    Returns:
        Tuple[bool, Optional[Dict]]: 如果是锻炼记录则返回(True, 记录数据)，否则返回(False, None)
    """
    is_exercise_record = False
    exercise_data = None

    try:
        # 检查是否为有效JSON字符串（以{}包裹）
        response_stripped = response.strip()
        if response_stripped.startswith('{') and response_stripped.endswith('}'):
            # 尝试解析JSON
            data = json.loads(response_stripped)
            # 判断是否为锻炼记录：必须包含3个核心字段，且是字典类型
            required_keys = ['date', 'exercise_type', 'duration']
            if isinstance(data, dict) and all(key in data for key in required_keys):
                is_exercise_record = True
                exercise_data = data
    except (json.JSONDecodeError, TypeError):
        # JSON解析失败，判定为“不是锻炼记录”
        return False, None  # 关键修正：返回False而非True

    # 最终判定：是锻炼记录则返回(True, 数据)，否则返回(False, None)
    # 在return前增加调试信息
    print(f"process_ai_response判定结果：is_exercise_record={is_exercise_record}, exercise_data={exercise_data}")
    return is_exercise_record, exercise_data