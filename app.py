import streamlit as st
import sqlite3

st.title("스팀 게임 추천")

tags = ["Action", "RPG", "Indie", "Strategy", "Adventure", "Multi-player"]
selected_tag = st.selectbox("태그를 선택하세요", tags)

st.write(f"선택한 태그: {selected_tag}")

conn = sqlite3.connect("steam_data2.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

query = """
    SELECT g.app_id, g.name, g.current_players, g.review_summary
    FROM games g
    JOIN game_tags t ON g.app_id = t.app_id
    WHERE t.tag_name = ?
    ORDER BY g.current_players DESC
    LIMIT 12
"""
cursor.execute(query, (selected_tag,))
top_games = cursor.fetchall()

conn.close()

st.write(f"받아온 게임 개수: {len(top_games)}")

review_score_map = {
    "Overwhelmingly Positive": 0.98,
    "Very Positive": 0.90,
    "Positive": 0.80,
    "Mostly Positive": 0.70,
    "Mixed": 0.50,
    "Mostly Negative": 0.30,
    "Negative": 0.20,
    "Very Negative": 0.10,
    "Overwhelmingly Negative": 0.02,
}

st.subheader("추천 게임 목록")

cols = st.columns(3)

for i, game in enumerate(top_games):
    col = cols[i % 3]
    with col:
        image_url = f"https://cdn.akamai.steamstatic.com/steam/apps/{game['app_id']}/header.jpg"
        st.image(image_url)
        st.write(f"**{game['name']}**")

        score = review_score_map.get(game["review_summary"], 0.5)
        st.progress(score)
        st.caption(f"{game['review_summary']} · 현재 플레이어 {game['current_players']:,}명")