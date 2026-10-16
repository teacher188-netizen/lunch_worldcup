
# main.py
import random
import uuid

import streamlit as st
from supabase import create_client


# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(
    page_title="급식 반찬 월드컵",
    page_icon="🏆",
    layout="centered",
)

MENUS = [
    "제육볶음",
    "간장찜닭",
    "가자미순살튀김",
    "돈육불백",
    "미트볼데리야끼볶음",
    "수육",
    "진미채고추장볶음",
    "치즈떡닭갈비",
]

ROUND_NAMES = ["8강", "4강", "결승"]

st.title("🏆 급식 반찬 월드컵")
st.write("오늘 가장 먹고 싶은 반찬을 골라 보세요!")
st.caption("8강부터 결승까지, 총 7번 선택하면 우승 반찬이 결정됩니다.")


# -----------------------------
# Supabase 연결
# -----------------------------
@st.cache_resource
def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


# -----------------------------
# 게임 초기화
# -----------------------------
def start_game():
    menus = MENUS.copy()
    random.shuffle(menus)

    st.session_state.game_id = str(uuid.uuid4())
    st.session_state.participants = menus
    st.session_state.round_index = 0
    st.session_state.match_index = 0
    st.session_state.round_winners = []
    st.session_state.champion = None
    st.session_state.locked = False
    st.session_state.message = None


if "game_id" not in st.session_state:
    start_game()


# -----------------------------
# 대결 결과 저장
# -----------------------------
def save_duel(round_name, left_menu, right_menu, winner):
    """
    기존 menu_duels 표에 대결 결과 한 행을 저장한다.
    id와 created_at은 DB 기본값을 사용한다.
    저장된 행을 다시 조회하여 실제 저장 결과를 확인한다.
    """
    if left_menu == right_menu:
        raise ValueError("서로 다른 두 반찬을 선택해야 합니다.")

    client = get_supabase()

    payload = {
        "game_id": st.session_state.game_id,
        "round": round_name,
        "left_menu": left_menu,
        "right_menu": right_menu,
        "winner": winner,
    }

    response = (
        client.table("menu_duels")
        .insert(payload)
        .select("id, game_id, round, left_menu, right_menu, winner")
        .execute()
    )

    rows = response.data

    if not isinstance(rows, list) or len(rows) != 1:
        raise RuntimeError("저장된 결과를 확인할 수 없습니다.")

    saved = rows[0]

    # 저장된 행이 이번 대결과 정확히 일치하는지 확인
    for column, expected in payload.items():
        if saved.get(column) != expected:
            raise RuntimeError("저장된 결과가 요청한 대결과 일치하지 않습니다.")

    if saved.get("id") is None:
        raise RuntimeError("저장된 행의 ID를 확인할 수 없습니다.")

    return saved


# -----------------------------
# 우승 화면
# -----------------------------
if st.session_state.champion:
    st.success("🎉 급
