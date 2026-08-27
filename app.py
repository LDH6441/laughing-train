import streamlit as st
from recommend import load_data, get_recommendations

st.title("스팀 게임 추천")

@st.cache_data
def get_games_data():
    return load_data()

df_games = get_games_data()

st.sidebar.subheader("추천 조건")

available_tags = ["Action", "RPG", "Indie", "Strategy", "Adventure",
                   "Open World", "Horror", "Simulation", "Sports"]

preferred_tags = st.sidebar.multiselect("좋아하는 태그", available_tags)
excluded_tags = st.sidebar.multiselect("제외할 태그", available_tags)
mode_choice = st.sidebar.selectbox(
    "플레이 모드",
    ["상관없음", "Single-player", "Multi-player", "Co-op", "PVP"]
)
top_n = st.sidebar.slider("추천 개수", min_value=3, max_value=20, value=6)

if st.sidebar.button("추천"):
    results = get_recommendations(
        df = df_games,
        preferred_tags= preferred_tags,
        excluded_tags= excluded_tags,
        mode_choice= mode_choice,
        top_n=top_n,
    )

    if results.empty:
        st.warning("조건에 맞는 게임을 찾지 못했어요. 제외 태그를 줄여보세요.")
    else:
        st.subheader(f"추천 게임 TOP {len(results)}")
        cols = st.columns(3)

        for i, (_, game) in enumerate(results.iterrows()):
            col = cols[i % 3]
            with col:
                image_url = f"https://cdn.akamai.steamstatic.com/steam/apps/{game['app_id']}/header.jpg"
                st.image(image_url)
                st.write(f"**{game['name']}**")
                st.progress(min(game["match_score"] / 100, 1.0))
                st.caption(f"적합도 {game['match_score']}점 · ${game['final_price']:.2f}")
else:
    st.info("왼쪽에서 조건을 고르고 '추천받기'를 눌러보세요.")