import streamlit as st
import requests

st.title("스팀 게임 추천")

tags = ["Action", "RPG", "Indie", "Strategy", "Soulike", "MultiPlay"]
selected_tag = st.selectbox("태그를 선택하세요", tags)

st.write(f"선택한 태그: {selected_tag}")

url = f"https://steamspy.com/api.php?request=tag&tag={selected_tag}"
response = requests.get(url)
data = response.json()

st.write(f"받아온 게임 개수: {len(data)}")