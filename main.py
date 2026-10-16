
# main.py
import random
import uuid

import streamlit as st
from supabase import create_client


# =====================================
# 기본 설정
# =====================================
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
st.caption("8강 4경기 · 4강 2경기 · 결승 1경기")


# =====================================
# Supabase 연결
# =====================================
@st.cache_resource
def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


# =====================================
# 게임 초기화
# =====================================
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


# =====================================
# 대결 결과 저장 및 확인
# =====================================
def save_duel(round_name, left_menu, right_menu, winner):
    if left_menu == right_menu:
        raise ValueError("서로 다른 반찬을 선택해야 합니다.")

    client = get_supabase()

    payload = {
        "game_id": st.session_state.game_id,
        "round": round_name,
        "left_menu": left_menu,
        "right_menu": right_menu,
        "winner": winner,
    }

    # 기존 menu_duels 표에 한 행 추가
    response = (
        client.table("menu_duels")
        .insert(payload)
        .select("id, game_id, round, left_menu, right_menu, winner")
        .execute()
    )

    rows = response.data

    if not isinstance(rows, list) or len(rows) != 1:
        raise RuntimeError("저장 결과를 확인할 수 없습니다.")

    saved = rows[0]

    # DB가 반환한 저장 결과와 요청 내용 비교
    for column, expected in payload.items():
        if saved.get(column) != expected:
            raise RuntimeError(
                "DB에 저장된 내용이 요청한 결과와 일치하지 않습니다."
            )

    if saved.get("id") is None:
        raise RuntimeError("저장된 행의 ID를 확인할 수 없습니다.")

    return saved


# =====================================
# 게임 종료 화면
# =====================================
if st.session_state.champion is not None:
    st.balloons()
    st.success("🏆 최종 우승 반찬")
    st.header(f"🥇 {st.session_state.champion}")
    st.write("급식 반찬 월드컵이 끝났습니다!")

    if st.button("🔄 다시 시작하기", use_container_width=True):
        start_game()
        st.rerun()

    st.stop()


# =====================================
# 저장 오류 화면
# =====================================
if st.session_state.locked:
    st.error("⚠️ 대결 결과의 저장 여부를 확인할 수 없습니다.")
    st.write(
        "중복 저장을 방지하기 위해 재선택과 다음 대결 진행을 잠갔습니다. "
        "교사가 Supabase의 menu_duels 표에서 저장 여부를 확인해야 합니다."
    )
    st.info(
        "확인 전에는 다시 선택하지 마세요. "
        "결과가 이미 저장되었을 가능성이 있으므로 새 대결을 시작하지 않는 것이 안전합니다."
    )
    st.stop()


# =====================================
# 현재 대결 정보
# =====================================
round_index = st.session_state.round_index
match_index = st.session_state.match_index
round_name = ROUND_NAMES[round_index]

current_menus = st.session_state.participants
left_menu = current_menus[match_index * 2]
right_menu = current_menus[match_index * 2 + 1]

total_matches = 7
completed_matches = (
    4 * 0
    if round_index == 0
    else 4
    if round_index == 1
    else 6
) + match_index

st.progress(completed_matches / total_matches)

st.subheader(f"{round_name}  ·  {match_index + 1}번째 대결")
st.write(f"총 7번 중 **{completed_matches + 1}번째 선택**")
st.write("두 반찬 중 더 먹고 싶은 반찬 하나를 선택하세요.")


# =====================================
# 반찬 선택
# =====================================
col1, col2 = st.columns(2)

with col1:
    st.markdown(
        f"""
        <div style="
            border: 2px solid #ff8a65;
            border-radius: 16px;
            padding: 24px 8px;
            text-align: center;
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        ">
            <div style="font-size: 36px;">🍚</div>
            <div style="font-size: 20px; font-weight: bold;">
                {left_menu}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    choose_left = st.button(
        left_menu,
        key=f"left_{completed_matches}_{st.session_state.game_id}",
        use_container_width=True,
        disabled=st.session_state.locked,
    )

with col2:
    st.markdown(
        f"""
        <div style="
            border: 2px solid #64b5f6;
            border-radius: 16px;
            padding: 24px 8px;
            text-align: center;
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        ">
            <div style="font-size: 36px;">🍚</div>
            <div style="font-size: 20px; font-weight: bold;">
                {right_menu}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    choose_right = st.button(
        right_menu,
        key=f"right_{completed_matches}_{st.session_state.game_id}",
        use_container_width=True,
        disabled=st.session_state.locked,
    )


# =====================================
# 선택 처리
# =====================================
if choose_left or choose_right:
    winner = left_menu if choose_left else right_menu

    # 저장을 확인하기 전에는 다음 대결 상태를 변경하지 않는다.
    try:
        save_duel(
            round_name=round_name,
            left_menu=left_menu,
            right_menu=right_menu,
            winner=winner,
        )

    except Exception:
        # DB 응답이 불확실할 때 재선택하면 중복 저장 위험이 있으므로 잠금
        st.session_state.locked = True
        st.session_state.message = (
            "저장 결과를 확인하지 못했습니다. "
            "교사가 DB에서 확인해야 합니다."
        )
        st.rerun()

    # 저장 확인 성공 후에만 승자 등록 및 다음 대결 진행
    st.session_state.round_winners.append(winner)
    st.session_state.match_index += 1

    matches_in_round = len(current_menus) // 2

    if st.session_state.match_index >= matches_in_round:
        winners = st.session_state.round_winners.copy()

        if round_index == 2:
            st.session_state.champion = winners[0]
        else:
            st.session_state.participants = winners
            st.session_state.round_winners = []
            st.session_state.round_index += 1
            st.session_state.match_index = 0

    st.rerun()


# =====================================
# 하단 안내
# =====================================
st.divider()
st.caption(
    "개인정보를 입력하지 않습니다. "
    "대결 기록은 교사가 준비한 Supabase 표에 저장됩니다."
)
