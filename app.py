import streamlit as st
import requests

st.title("스팀 게임 추천")

tags = ["Action", "RPG", "Indie", "Strategy", "Roguelike", "MultiPlayer"]
selected_tag = st.selectbox("태그를 선택하세요", tags)

st.write(f"선택한 태그: {selected_tag}")

url = f"https://steamspy.com/api.php?request=tag&tag={selected_tag}"
response = requests.get(url)
data = response.json()

st.write(f"받아온 게임 개수: {len(data)}")

games = list(data.values())

games = [g for g in games if (g["positive"] + g["negative"]) >= 50]

def owners_min(g):
    first_part = g["owners"].split("..")[0]
    number = int(first_part.replace(",", "").strip())
    return number

games.sort(key=owners_min, reverse=True)

top_games = games[:12]

st.write()

st.subheader("추천 게임 목록")

cols = st.columns(3)

for i, game in enumerate(top_games):
    col = cols[i % 3]
    with col:
        image_url = f"https://cdn.akamai.steamstatic.com/steam/apps/{game['appid']}/header.jpg"
        st.image(image_url)
        st.write(f"**{game['name']}**")

        total_reviews = game["positive"] + game["negative"]
        score = game["positive"] / total_reviews
        st.progress(score)
        st.caption(f"긍정 리뷰 {round(score * 100)}%")

