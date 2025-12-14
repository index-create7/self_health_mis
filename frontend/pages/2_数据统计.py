import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd
from typing import Optional, Dict, Any, List, Union
from self_health_mis.frontend.session_state import SessionState
from self_health_mis.data.model.exercise_model import FitnessRecord

# ====================== 页面配置 & 会话初始化（原逻辑不变） ======================
st.set_page_config(
    page_title="锻炼数据 - 学生体育锻炼管理系统",
    page_icon="📝",
    layout="wide"
)
session_manager = SessionState()  # 原会话管理，保持不变


# ====================== 核心DB操作函数（直接调用，适配原方法） ======================
def update_fitness_record(record_id: int, update_data: Dict[str, Any]) -> bool:
    """直接调用DB层更新记录（适配原DB方法）"""
    try:
        # 1. 直接从DB获取原始记录（原方法：get_fitness_records + 过滤ID）
        all_records = session_manager.db.get_fitness_records(st.session_state.user_id)
        target_record = next((r for r in all_records if r.id == record_id), None)

        if not target_record:
            st.error(f"记录ID {record_id} 不存在")
            return False

        # 2. 仅更新允许的字段（直接修改对象属性）
        allowed_fields = ["is_checkin", "intensity", "recovery_quality", "notes"]
        for field in allowed_fields:
            if field in update_data:
                setattr(target_record, field, update_data[field])

        # 3. 直接调用DB层更新方法（原方法名：update_fitness_record）
        # 若DB层更新方法参数为(record)，则传对象；若为(id, data)，则调整为：
        # session_manager.db.update_fitness_record(record_id, update_data)
        session_manager.db.update_fitness_record(target_record)

        st.toast(f"记录ID {record_id} 更新成功！", icon="✅")
        return True
    except Exception as e:
        st.error(f"更新失败：{str(e)}")
        return False


def add_fitness_record(new_record: FitnessRecord) -> Optional[int]:
    """直接调用DB层添加记录（适配原DB方法）"""
    try:
        # 直接调用DB层添加方法（原方法名：add_fitness_record）
        record_id = session_manager.db.add_fitness_record(new_record)

        if record_id:
            st.success(f"锻炼记录添加成功！记录ID: {record_id}")
            # 原逻辑：更新目标进度（保留）
            session_manager.db._update_goal_progress(st.session_state.user_id)
            return record_id
        else:
            st.error("添加失败：DB返回空ID")
            return None
    except Exception as e:
        st.error(f"添加失败：{str(e)}")
        return None


# ====================== 核心渲染函数（前端适配DB层） ======================
def render_view_records_section():
    """渲染锻炼记录管理区域（直接DB调用，前端逻辑适配）"""
    # 直接调用DB层获取数据（原方法：get_fitness_records(user_id)）
    user_id = st.session_state.user_id
    all_records = session_manager.db.get_fitness_records(user_id)
    goals = session_manager.db.get_fitness_goals(user_id, include_completed=False)  # 原方法保留


    # ========== 2. 筛选控件（前端内存筛选，适配DB层返回数据） ==========
    st.subheader("编辑锻炼记录")
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_start = st.date_input("开始日期", date.today() - timedelta(days=7))
    with col2:
        filter_end = st.date_input("结束日期", date.today())
    with col3:
        filter_official = st.selectbox("记录类型", ["全部", "仅官方刷段", "仅自主锻炼"], index=0)

    # 前端内存筛选（适配DB层返回的FitnessRecord列表）
    official_filter = None
    if filter_official == "仅官方刷段":
        official_filter = True
    elif filter_official == "仅自主锻炼":
        official_filter = False

    filtered_records = []
    for r in all_records:
        try:
            # 适配DB层返回的date字段类型（datetime -> date）
            record_date = r.date.date() if isinstance(r.date, datetime) else None
        except:
            record_date = None

        if not record_date:
            continue
        # 日期筛选（前端逻辑）
        if not (filter_start <= record_date <= filter_end):
            continue
        # 官方/自主筛选（前端逻辑）
        if official_filter is not None and r.is_official != official_filter:
            continue

        filtered_records.append(r)

    # ========== 3. 可编辑表格（前端适配DB层数据格式） ==========
    if filtered_records:
        record_data = []
        for r in filtered_records:
            # 前端格式化DB层返回的字段
            date_str = r.date.strftime("%Y-%m-%d") if isinstance(r.date, datetime) else "-"
            exercise_type = r.exercise_type or "-"
            duration = f"{r.duration:.0f}" if r.duration is not None else "-"
            distance = f"{r.distance:.2f}" if r.distance is not None else "0.00"
            calories = f"{r.calories:.0f}" if r.calories is not None else "-"
            record_type = "官方刷段" if r.is_official else "自主锻炼"
            notes = r.notes or "-"

            # 适配DB层的新增字段
            checkin_status = r.is_checkin if hasattr(r, 'is_checkin') else False
            intensity = r.intensity if hasattr(r, 'intensity') and r.intensity is not None else 0.0
            recovery_quality = r.recovery_quality if hasattr(r,
                                                             'recovery_quality') and r.recovery_quality is not None else 0.0

            # 前端构造表格数据（适配st.data_editor）
            record_data.append({
                "记录ID": r.id,  # DB层返回的记录ID
                "日期": date_str,
                "锻炼类型": exercise_type,
                "时长(分钟)": duration,
                "距离(公里)": distance,
                "卡路里(kcal)": calories,
                "记录类型": record_type,
                "打卡状态": checkin_status,
                "运动强度": intensity,
                "恢复质量": recovery_quality,
                "备注": notes
            })

        df = pd.DataFrame(record_data)
        # 前端可编辑表格（原逻辑不变，仅适配DB层返回数据）
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "记录ID": st.column_config.NumberColumn("记录ID", disabled=True, width="small"),
                "日期": st.column_config.DateColumn("日期", format="YYYY-MM-DD", disabled=True),
                "锻炼类型": st.column_config.TextColumn("锻炼类型", disabled=True),
                "时长(分钟)": st.column_config.NumberColumn("时长(分钟)", format="%d", disabled=True),
                "距离(公里)": st.column_config.NumberColumn("距离(公里)", format="%.2f", disabled=True),
                "卡路里(kcal)": st.column_config.NumberColumn("卡路里(kcal)", format="%d", disabled=True),
                "记录类型": st.column_config.TextColumn("记录类型", disabled=True),
                "打卡状态": st.column_config.CheckboxColumn("打卡状态", help="勾选表示已打卡", default=False),
                "运动强度": st.column_config.NumberColumn("运动强度", help="0-10分制", min_value=0.0, max_value=10.0,
                                                          step=0.1, format="%.1f"),
                "恢复质量": st.column_config.NumberColumn("恢复质量", help="0-10分制", min_value=0.0, max_value=10.0,
                                                          step=0.1, format="%.1f"),
                "备注": st.column_config.TextColumn("备注", width="medium")
            },
            disabled=["记录ID", "日期", "锻炼类型", "时长(分钟)", "距离(公里)", "卡路里(kcal)", "记录类型"],
            key="fitness_records_editor"
        )

        # 处理表格编辑（前端适配DB层更新逻辑）
        if not df.equals(edited_df):
            for idx, (original, edited) in enumerate(zip(df.itertuples(), edited_df.itertuples())):
                if original != edited:
                    record_id = edited.记录ID
                    # 前端构造DB层需要的更新数据
                    update_data = {
                        "is_checkin": edited.打卡状态,
                        "intensity": edited.运动强度 if edited.运动强度 > 0 else None,
                        "recovery_quality": edited.恢复质量 if edited.恢复质量 > 0 else None,
                        "notes": edited.备注 if edited.备注 != "-" else None
                    }
                    # 直接调用DB更新函数
                    update_fitness_record(record_id, update_data)
            st.rerun()  # 刷新页面显示修改后数据

    else:
        st.info("没有找到符合条件的锻炼记录。")

# ====================== 主函数（仅调用前端渲染） ======================
def main():
    render_view_records_section()


if __name__ == "__main__":
    main()