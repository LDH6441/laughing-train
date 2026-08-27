import os
import sqlite3
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 1. DB 경로 설정 (steam_data2.db)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "steam_data2.db")

def calculate_wilson_score(positive: int, negative: int, z: float = 1.96) -> float:
    """리뷰 추천/비추천 수 기반 윌슨 신뢰구간 하한 점수 (0~1)"""
    n = positive + negative
    if n == 0:
        return 0.5
    p_hat = positive / n
    num = p_hat + (z**2) / (2 * n) - z * np.sqrt((p_hat * (1 - p_hat) + (z**2) / (4 * n)) / n)
    denom = 1 + (z**2) / n
    return float(num / denom)

def load_data():
    """SQLite DB에서 게임 메타데이터, 태그, 리뷰 평점 로드 및 전처리"""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"❌ DB 파일을 찾을 수 없습니다: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    
    # 게임 기본 정보 로드
    df_games = pd.read_sql("SELECT app_id, name, final_price FROM games", conn)
    
    # 태그 데이터 로드 후 게임별 문자열로 결합
    df_tags = pd.read_sql("SELECT app_id, tag_name FROM game_tags", conn)
    df_tags_grouped = df_tags.groupby("app_id")["tag_name"].apply(
        lambda tags: " ".join([t.replace(" ", "_") for t in tags])
    ).reset_index()
    
    # 리뷰 데이터 로드 후 윌슨 스코어 계산
    df_reviews = pd.read_sql("SELECT app_id, voted_up FROM game_reviews", conn)
    wilson_dict = {}
    for app_id, group in df_reviews.groupby("app_id"):
        pos = (group["voted_up"] == 1).sum()
        neg = (group["voted_up"] == 0).sum()
        wilson_dict[app_id] = calculate_wilson_score(pos, neg)
        
    conn.close()
    
    # 전체 데이터 병합
    df_final = df_games.merge(df_tags_grouped, on="app_id", how="left").fillna({"tag_name": ""})
    df_final["wilson_score"] = df_final["app_id"].map(wilson_dict).fillna(0.5)
    
    return df_final

def get_recommendations(df, preferred_tags, excluded_tags, mode_choice="상관없음", top_n=5):
    """통계 기반 복합 추천도 계산 및 Top-N 반환"""
    df_pool = df.copy()
    
    # [1단계] 하드 필터링: 제외 태그 제거
    if excluded_tags:
        for ex_tag in excluded_tags:
            formatted_ex = ex_tag.replace(" ", "_")
            df_pool = df_pool[~df_pool["tag_name"].str.contains(formatted_ex, case=False, regex=False)]
            
    if df_pool.empty:
        print("⚠️ 제외 필터로 인해 남은 게임이 없습니다.")
        return pd.DataFrame()

    # [2단계] 다차원 통계 지표 산출
    # 1) 태그 TF-IDF 코사인 유사도
    if preferred_tags:
        user_query = " ".join([t.replace(" ", "_") for t in preferred_tags])
        vectorizer = TfidfVectorizer()
        corpus = [user_query] + df_pool["tag_name"].tolist()
        tfidf_matrix = vectorizer.fit_transform(corpus)
        sim_genre = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    else:
        sim_genre = np.ones(len(df_pool)) * 0.5

    # 2) 플레이 모드 일치도
    if mode_choice == "상관없음":
        sim_mode = np.ones(len(df_pool))
    else:
        mode_tag = mode_choice.replace(" ", "_")
        sim_mode = df_pool["tag_name"].apply(lambda x: 1.0 if mode_tag.lower() in x.lower() else 0.0).to_numpy()

    # 3) 게임 퀄리티 (윌슨 신뢰 점수)
    sim_quality = df_pool["wilson_score"].to_numpy()

    # [3단계] 선형 결합 (장르 50%, 모드 25%, 퀄리티 25%)
    final_score = (0.50 * sim_genre + 0.25 * sim_mode + 0.25 * sim_quality) * 100.0
    df_pool["match_score"] = np.round(final_score, 1)
    
    # 점수 기준 내림차순 정렬
    return df_pool.sort_values(by="match_score", ascending=False).head(top_n)

# -------------------------------------------------------------
# 테스트 실행부 (터미널에서 직접 실행)
# -------------------------------------------------------------
if __name__ == "__main__":
    print("📊 데이터 로드 중...")
    df_games = load_data()
    print(f"✅ 총 {len(df_games)}개 게임 데이터 로드 완료!\n")
    
    # 🎯 가상 테스트 조건 설정 (원하는 조건으로 바꿔보세요)
    test_preferred_tags = ["Action", "RPG", "Open World"]  # 선호 태그
    test_excluded_tags = ["Horror"]                         # 제외 태그
    test_mode = "Single-player"                             # Single-player / Multi-player / Co-op / PvP / 상관없음
    
    print(f"🎯 [테스트 조건]")
    print(f" - 선호 태그: {test_preferred_tags}")
    print(f" - 제외 태그: {test_excluded_tags}")
    print(f" - 플레이 모드: {test_mode}\n")
    
    # 알고리즘 계산
    results = get_recommendations(
        df=df_games,
        preferred_tags=test_preferred_tags,
        excluded_tags=test_excluded_tags,
        mode_choice=test_mode,
        top_n=5
    )
    
    # 콘솔 결과 출력
    print("🏆 [추천 결과 TOP 5]")
    print("=" * 60)
    for rank, (_, row) in enumerate(results.iterrows(), start=1):
        print(f"{rank}위: {row['name']}")
        print(f"   - 추천 적합도: {row['match_score']}점 / 100점")
        print(f"   - 가격: ${row['final_price']:.2f}")
        print(f"   - 윌슨 신뢰 점수: {row['wilson_score']:.3f}")
        print("-" * 60)