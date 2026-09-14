import streamlit as st
import joblib
import pandas as pd
from scipy import sparse
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
import os
import requests
import altair as alt

st.set_page_config(page_title="지하철 이용객 예측", page_icon="🚇")

load_dotenv()
FIGMA_TOKEN = os.getenv("FIGMA_TOKEN")

@st.cache_data(ttl=3600)
def get_figma_node_color(file_key, node_id):
    url = f"https://api.figma.com/v1/files/{file_key}/nodes"
    headers = {"X-Figma-Token": FIGMA_TOKEN}
    params = {"ids": node_id}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    node = data["nodes"][node_id]["document"]
    fill = node["fills"][0]["color"]

    r = round(fill["r"] * 255)
    g = round(fill["g"] * 255)
    b = round(fill["b"] * 255)
    return f"#{r:02X}{g:02X}{b:02X}"

FIGMA_FILE_KEY = "Wj9SvWTQJ3S54ryzMHdnUB"
BUTTON_NODE_ID = "4:374"
primary_color = get_figma_node_color(FIGMA_FILE_KEY, BUTTON_NODE_ID)

st.markdown(f"""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

html, body, [class*="css"] {{
    font-family: 'Pretendard', sans-serif !important;
}}

.block-container {{
    max-width: 900px;
    padding-top: 3rem;
    margin: 0 auto;
}}

h1 {{
    font-size: 16px !important;
    font-weight: 600 !important;
    padding-bottom: 16px !important;
    border-bottom: 1px solid #E5E7EB !important;
    margin-bottom: 24px !important;
}}

h2 {{
    font-size: 28px !important;
    font-weight: 600 !important;
}}

label p {{
    font-size: 14px !important;
    font-weight: 500 !important;
}}

div[data-testid="stVerticalBlockBorderWrapper"] {{
    border-color: {primary_color} !important;
}}

div[data-testid="stElementContainer"] {{
    margin-bottom: 16px !important;
}}
</style>
""", unsafe_allow_html=True)

st.title("🚇 지하철 이용객 예측")

# 1) 모델 / 인코더 / 옵션 목록 불러오기
model = joblib.load("model/subway_model.pkl")
encoder = joblib.load("model/subway_encoder.pkl")
options = joblib.load("model/subway_options.pkl")

client = MongoClient("mongodb://localhost:27017/")
db = client["subway_prediction"]
collection = db["predictions"]

@st.cache_data
def load_역_매핑():
    df = pd.read_csv("data/subway.csv", encoding="cp949")
    df = df.drop_duplicates()
    return df.groupby("호선명")["지하철역"].unique().apply(sorted).to_dict()

역_매핑 = load_역_매핑()

@st.cache_data
def load_raw_df():
    df = pd.read_csv("data/subway.csv", encoding="cp949")
    df = df.drop_duplicates()
    return df

raw_df = load_raw_df()

tab1, tab2, tab3 = st.tabs(["예측하기", "기록 조회", "인사이트"])

# ---------------- 탭 1: 예측하기 ----------------
with tab1:
    st.subheader("지하철 이용객 수 예측")
    st.caption("연도, 월, 호선, 역, 시간대를 선택하면 예상 승차 인원을 알려드려요.")

    if "has_predicted" not in st.session_state:
        st.session_state.has_predicted = False

    if not st.session_state.has_predicted:
        st.info("처음이신가요? 아래에서 조건을 선택하고 '예측하기' 버튼을 눌러보세요.")

    연도_최소, 연도_최대 = options["연도_범위"]

    col1, col2 = st.columns(2)
    with col1:
        선택_연도 = st.selectbox("연도", list(range(연도_최소, 연도_최대 + 1)))
        선택_호선 = st.selectbox("호선명", options["호선명_목록"])
    with col2:
        선택_월 = st.selectbox("월", list(range(1, 13)))
        선택_역 = st.selectbox("지하철역", 역_매핑[선택_호선])

    선택_시간대 = st.selectbox("시간대", options["시간대_목록"])

    if st.button("예측하기", type="primary"):
        입력_카테고리 = pd.DataFrame({
            "호선명": [선택_호선],
            "지하철역": [선택_역],
            "시간대": [선택_시간대]
        })

        입력_인코딩 = encoder.transform(입력_카테고리)
        입력_숫자 = sparse.csr_matrix([[선택_연도, 선택_월]])
        입력_최종 = sparse.hstack([입력_숫자, 입력_인코딩]).tocsr()

        예측값 = model.predict(입력_최종)[0]

        collection.insert_one({
            "연도": 선택_연도,
            "월": 선택_월,
            "호선명": 선택_호선,
            "지하철역": 선택_역,
            "시간대": 선택_시간대,
            "예측인원": int(예측값),
            "예측시각": datetime.now()
        })

        시간대_컬럼 = f"{선택_시간대} 승차인원"
        역_추이 = raw_df[(raw_df["호선명"] == 선택_호선) & (raw_df["지하철역"] == 선택_역)][["사용월", 시간대_컬럼]].sort_values("사용월").tail(6)
        역_추이.columns = ["사용월", "실제 승차인원"]
        역_추이["사용월"] = 역_추이["사용월"].astype(str)

        with st.container(border=True):
            st.metric(label="예상 승차 인원", value=f"{int(예측값):,} 명")
            st.caption("예측값은 참고용이며 실제 인원과 다를 수 있어요.")

        if len(역_추이) > 0:
            st.markdown(f"**{선택_역}역 {선택_시간대} 최근 추이**")
            st.caption("선택하신 연도와 상관없이, 가장 최근 6개월의 실제 데이터예요.")

            trend_chart = alt.Chart(역_추이).mark_line(point=True, color="#2563EB").encode(
                x=alt.X("사용월", sort=None, title=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("실제 승차인원", title=None, scale=alt.Scale(zero=False))
            ).properties(height=200)
            st.altair_chart(trend_chart, use_container_width=True)

    st.markdown("---")
    st.caption("데이터 출처: 서울 열린데이터광장 · 본 서비스는 학습 목적의 프로젝트입니다.")

# ---------------- 탭 2: 기록 조회 ----------------
with tab2:
    st.subheader("예측 기록 조회")
    st.caption("최근 예측 20건을 최신순으로 보여드려요.")

    기록 = list(collection.find().sort("예측시각", -1).limit(20))

    if 기록:
        기록_df = pd.DataFrame(기록)
        기록_df = 기록_df.drop(columns=["_id"])

        m1, m2, m3 = st.columns(3)
        m1.metric("총 예측 횟수", f"{len(기록_df)}건")
        m2.metric("평균 예측 인원", f"{int(기록_df['예측인원'].mean()):,} 명")
        m3.metric("가장 많이 조회한 역", 기록_df["지하철역"].mode()[0])

        st.dataframe(기록_df, use_container_width=True)

        csv_데이터 = 기록_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="CSV로 다운로드",
            data=csv_데이터,
            file_name="예측_기록.csv",
            mime="text/csv"
        )
    else:
        st.markdown("#### 아직 예측 기록이 없어요")
        st.write("예측하기 화면에서 조건을 선택하고 예측을 실행하면 여기에 기록이 쌓여요.")

    st.markdown("---")
    st.caption("데이터 출처: 서울 열린데이터광장 · 본 서비스는 학습 목적의 프로젝트입니다.")

# ---------------- 탭 3: 인사이트 ----------------
with tab3:
    st.subheader("데이터 인사이트")
    st.caption("2015년 1월부터 2026년 8월까지의 승하차 데이터를 기준으로 정리했어요.")

    df = pd.read_csv("data/subway.csv", encoding="cp949")
    df = df.drop_duplicates()
    boarding_cols = [c for c in df.columns if "승차인원" in c]

    m1, m2, m3 = st.columns([1, 1, 1.5])
    m1.metric("전체 데이터 건수", f"{len(df):,}건")
    m2.metric("역 개수", f"{df['지하철역'].nunique()}개")
    m3.metric("데이터 기간", f"{str(df['사용월'].min())[:4]}.{str(df['사용월'].min())[4:]}~{str(df['사용월'].max())[:4]}.{str(df['사용월'].max())[4:]}")

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("**시간대별 전체 승차인원**")
        시간대_합계 = df[boarding_cols].sum().reset_index()
        시간대_합계.columns = ["시간대", "승차인원"]
        시간대_합계["시간대"] = 시간대_합계["시간대"].str.replace(" 승차인원", "", regex=False)
        시간대_합계["승차인원(억 명)"] = (시간대_합계["승차인원"] / 100_000_000).round(1)

        chart1 = alt.Chart(시간대_합계).mark_bar(size=10, color="#2563EB").encode(
            x=alt.X("시간대", sort=None, title=None, axis=alt.Axis(labelAngle=-45)),
            y=alt.Y("승차인원(억 명)", title="승차인원 (억 명)")
        ).properties(height=400)
        st.altair_chart(chart1, use_container_width=True)

    with col2:
        st.markdown("**승차인원 많은 상위 5개 역**")
        역별_합계 = df.groupby("지하철역")[boarding_cols].sum().sum(axis=1).reset_index()
        역별_합계.columns = ["지하철역", "승차인원"]
        역별_합계["승차인원(억 명)"] = (역별_합계["승차인원"] / 100_000_000).round(1)
        상위5 = 역별_합계.sort_values("승차인원", ascending=False).head(5)

        chart2 = alt.Chart(상위5).mark_bar(size=30, color="#2563EB").encode(
            y=alt.Y("지하철역", sort="-x", title=None),
            x=alt.X("승차인원(억 명)", title="승차인원 (억 명)")
        ).properties(height=400)
        st.altair_chart(chart2, use_container_width=True)

    st.markdown("---")
    st.caption("데이터 출처: 서울 열린데이터광장 · 본 서비스는 학습 목적의 프로젝트입니다.")