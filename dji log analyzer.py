import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
from io import StringIO
import math
import chardet

st.set_page_config(page_title="DJI 비행로그 분석기", layout="wide")
st.title("🛸 DJI 비행로그 분석기")

uploaded_file = st.file_uploader("비행 로그 파일 업로드 (.CSV 또는 .TXT)", type=["csv", "txt"])

if uploaded_file:
    # 인코딩 감지 및 디코딩 처리
    raw_data = uploaded_file.getvalue()
    result = chardet.detect(raw_data)
    encoding = result["encoding"] if result["encoding"] else "utf-8"

    try:
        stringio = StringIO(raw_data.decode(encoding))
    except UnicodeDecodeError:
        stringio = StringIO(raw_data.decode("utf-16", errors="ignore"))

    try:
        df = pd.read_csv(stringio, on_bad_lines='skip')  # 잘못된 줄 무시
    except Exception as e:
        st.error(f"CSV 파일을 불러올 수 없습니다: {e}")
        st.stop()

    st.subheader("1. 비행 데이터 미리보기")
    st.dataframe(df.head())

    # 위경도/고도/속도 컬럼 자동 추정
    try:
        lat_col = [col for col in df.columns if 'lat' in col.lower()][0]
        lon_col = [col for col in df.columns if 'lon' in col.lower()][0]
        alt_col = [col for col in df.columns if 'alt' in col.lower() or 'height' in col.lower()][0]
        speed_col = [col for col in df.columns if 'speed' in col.lower()][0]
    except IndexError:
        st.error("위도, 경도, 고도, 속도 관련 컬럼을 찾을 수 없습니다.")
        st.stop()

    st.subheader("2. 비행 경로 시각화")
    start_coords = (df[lat_col].iloc[0], df[lon_col].iloc[0])
    m = folium.Map(location=start_coords, zoom_start=16)
    folium.PolyLine(df[[lat_col, lon_col]].values, color="blue").add_to(m)
    folium.Marker(start_coords, tooltip="출발지").add_to(m)
    st_folium(m, width=700, height=500)

    st.subheader("3. 고도 및 속도 그래프")
    fig, ax1 = plt.subplots()
    ax1.plot(df[alt_col].values, color='green', label='고도')
    ax1.set_ylabel('고도 (m)')
    ax2 = ax1.twinx()
    ax2.plot(df[speed_col].values, color='blue', label='속도')
    ax2.set_ylabel('속도 (m/s)')
    st.pyplot(fig)

    st.subheader("4. 비행 요약")

    max_alt = df[alt_col].max()
    max_speed = df[speed_col].max()
    flight_time = len(df) / 10  # 샘플링 10Hz 가정

    # 거리 계산 함수
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371000
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    total_distance = 0
    for i in range(1, len(df)):
        total_distance += haversine(
            df[lat_col].iloc[i-1], df[lon_col].iloc[i-1],
            df[lat_col].iloc[i], df[lon_col].iloc[i]
        )

    st.metric("총 비행 시간", f"{flight_time:.1f} 초")
    st.metric("최고 고도", f"{max_alt:.1f} m")
    st.metric("최고 속도", f"{max_speed:.1f} m/s")
    st.metric("총 이동 거리", f"{total_distance/1000:.2f} km")
