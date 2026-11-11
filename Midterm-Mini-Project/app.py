
import os
import json
from pathlib import Path

import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv


# ==========================================
# 1. 基本設定
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(
    dotenv_path=BASE_DIR / ".env",
    override=True
)

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
MAX_LENGTH = 1000

st.set_page_config(
    page_title="AI 運動計畫安排器",
    page_icon="🏃",
    layout="centered"
)


# ==========================================
# 2. AI 回傳資料格式
# ==========================================

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "plan_title": {
            "type": "string"
        },
        "weekly_summary": {
            "type": "string"
        },
        "sessions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "day": {
                        "type": "string"
                    },
                    "focus": {
                        "type": "string"
                    },
                    "exercises": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },
                    "duration": {
                        "type": "integer"
                    },
                    "safety_note": {
                        "type": "string"
                    }
                },
                "required": [
                    "day",
                    "focus",
                    "exercises",
                    "duration",
                    "safety_note"
                ],
                "additionalProperties": False
            }
        },
        "general_advice": {
            "type": "array",
            "items": {
                "type": "string"
            }
        }
    },
    "required": [
        "plan_title",
        "weekly_summary",
        "sessions",
        "general_advice"
    ],
    "additionalProperties": False
}


# ==========================================
# 3. AI 角色設定
# ==========================================

INSTRUCTIONS = """
你是一位安全、專業且友善的 AI 運動計畫助理。

你的任務是根據使用者提供的運動目標、運動程度、
每週可運動天數、每次運動時間及器材，
安排一份適合使用者的每週運動計畫。

請遵守以下原則：

1. 使用繁體中文回答。
2. 提供清楚、容易執行的運動安排。
3. 運動內容應符合使用者的程度。
4. 安排適當的暖身、休息及恢復時間。
5. 不安排過度激烈或不安全的運動。
6. 不鼓勵極端節食、過度運動或快速減重。
7. 如果使用者感到疼痛或身體不適，應停止運動。
8. 不要提供醫療診斷。
9. 每個運動日都要有運動內容及安全提醒。
10. 嚴格依照指定的 JSON 格式輸出。
"""


# ==========================================
# 4. 取得 API Key
# ==========================================

def get_api_key():
    """從 .env 或 Streamlit Secrets 取得 API Key。"""

    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if not api_key:
        try:
            api_key = st.secrets.get(
                "OPENAI_API_KEY", ""
            ).strip()
        except Exception:
            api_key = ""

    return api_key


# ==========================================
# 5. 呼叫 OpenAI API
# ==========================================

def generate_workout_plan(user_input):
    """呼叫 AI 產生運動計畫。"""

    api_key = get_api_key()

    if not api_key:
        raise ValueError(
            "找不到 OPENAI_API_KEY，請檢查 .env 或 Cloud Secrets。"
        )

    client = OpenAI(
        api_key=api_key,
        timeout=60,
        max_retries=0
    )

    response = client.responses.create(
        model=MODEL,
        instructions=INSTRUCTIONS,
        input=json.dumps(
            user_input,
            ensure_ascii=False
        ),
        text={
            "format": {
                "type": "json_schema",
                "name": "workout_plan",
                "strict": True,
                "schema": PLAN_SCHEMA
            }
        },
        store=False
    )

    result_text = response.output_text

    if not result_text:
        raise ValueError("AI 沒有回傳有效內容，請重新嘗試。")

    result = json.loads(result_text)

    return result


# ==========================================
# 6. 檢查 AI 回傳內容
# ==========================================

def validate_plan(plan):
    """確認 AI 回傳的資料是否完整。"""

    required_fields = [
        "plan_title",
        "weekly_summary",
        "sessions",
        "general_advice"
    ]

    for field in required_fields:
        if field not in plan:
            raise ValueError(f"缺少必要欄位：{field}")

    if not isinstance(plan["sessions"], list):
        raise ValueError("運動計畫格式錯誤。")

    for session in plan["sessions"]:
        for field in [
            "day",
            "focus",
            "exercises",
            "duration",
            "safety_note"
        ]:
            if field not in session:
                raise ValueError(f"運動安排缺少欄位：{field}")

    return True


# ==========================================
# 7. 網頁標題與說明
# ==========================================

st.title("🏃 AI 運動計畫安排器")

st.write(
    "輸入你的運動目標與時間安排，"
    "讓 AI 幫你規劃一份適合自己的每週運動計畫。"
)

st.caption(f"目前使用模型：{MODEL}")

st.divider()


# ==========================================
# 8. 使用者輸入表單
# ==========================================

with st.form("workout_form"):

    st.subheader("📋 基本資料")

    goal = st.selectbox(
        "你的運動目標",
        [
            "提升體能",
            "增加肌力",
            "改善心肺耐力",
            "增加活動量",
            "維持健康"
        ]
    )

    level = st.selectbox(
        "目前運動程度",
        [
            "初學者",
            "中等程度",
            "有運動經驗"
        ]
    )

    days = st.slider(
        "每週可以運動幾天？",
        min_value=1,
        max_value=5,
        value=3
    )

    minutes = st.slider(
        "每次可以運動幾分鐘？",
        min_value=15,
        max_value=60,
        value=30,
        step=5
    )

    equipment = st.selectbox(
        "目前有的運動器材",
        [
            "不需要器材",
            "瑜珈墊",
            "啞鈴",
            "彈力帶",
            "多種器材"
        ]
    )

    preference = st.text_area(
        "其他運動偏好或需求（選填）",
        placeholder="例如：希望以居家運動為主，避免跳躍動作。",
        max_chars=MAX_LENGTH
    )

    api_enabled = st.checkbox(
        "我同意使用 OpenAI API 產生運動計畫",
        value=True
    )

    submitted = st.form_submit_button(
        "✨ 產生我的運動計畫",
        use_container_width=True
    )


# ==========================================
# 9. 執行計畫產生
# ==========================================

if "record" not in st.session_state:
    st.session_state.record = None

if "error" not in st.session_state:
    st.session_state.error = None


if submitted:

    st.session_state.record = None
    st.session_state.error = None

    if len(preference) > MAX_LENGTH:

        st.session_state.error = (
            f"其他需求不能超過 {MAX_LENGTH} 個字。"
        )

    elif not api_enabled:

        st.session_state.error = (
            "請先勾選同意使用 API。"
        )

    else:

        api_key = get_api_key()

    if not api_key:
            st.session_state.error = (
                "找不到 OPENAI_API_KEY，"
                "請檢查 .env 或 Cloud Secrets。"
            )

    else:
            user_input = {
                "goal": goal,
                "level": level,
                "days_per_week": days,
                "minutes_per_session": minutes,
                "equipment": equipment,
                "preference": preference
            }
            user_input = {
                "goal": goal,
                "level": level,
                "days_per_week": days,
                "minutes_per_session": minutes,
                "equipment": equipment,
                "preference": preference
            }

            with st.spinner("AI 正在幫你安排運動計畫，請稍候..."):

                try:

                    result = generate_workout_plan(
                        user_input
                    )

                    validate_plan(result)

                    st.session_state.record = {
                        "input": user_input,
                        "plan": result
                    }

                except json.JSONDecodeError:

                    st.session_state.error = (
                        "AI 回傳格式不正確，請重新產生。"
                    )

                except Exception as e:

                    st.session_state.error = (
                        f"產生計畫時發生錯誤：{str(e)}"
                    )


# ==========================================
# 10. 顯示錯誤訊息
# ==========================================

if st.session_state.error:

    st.error(st.session_state.error)


# ==========================================
# 11. 顯示運動計畫
# ==========================================

if st.session_state.record:

    record = st.session_state.record
    plan = record["plan"]

    st.divider()

    st.success("運動計畫產生成功！")

    st.header(plan["plan_title"])

    st.write(plan["weekly_summary"])

    st.subheader("📅 每週運動安排")

    for session in plan["sessions"]:

        with st.expander(
            f'{session["day"]}｜{session["focus"]}',
            expanded=True
        ):

            st.write(
                f'**運動時間：** {session["duration"]} 分鐘'
            )

            st.write("**運動內容：**")

            for exercise in session["exercises"]:
                st.write(f"- {exercise}")

            st.info(
                f'安全提醒：{session["safety_note"]}'
            )

    st.subheader("💡 其他建議")

    for advice in plan["general_advice"]:
        st.write(f"- {advice}")

    st.divider()

    st.subheader("📝 本次輸入資料")

    st.json(record["input"])

    st.caption(
        "本計畫僅供一般運動參考，"
        "請依照自己的身體狀況調整。"
        "若有疼痛或不適，請停止運動並尋求專業協助。"
    )
