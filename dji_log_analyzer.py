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
    raw_data = uploaded_file.getvalue()

    # 인코딩 자동 감지 및 복수 시도
    result = chardet.detect(raw_data)
    encoding = result['encoding'] if result['encoding'] else 'utf-8'
    decoded = None

    encodings_to_try = [encoding, 'utf-8', 'utf-8-sig', 'utf-16', 'utf-16le', 'utf-16be', 'cp949', 'euc-kr']
    for enc in encodings_to_try:
        try:
            decoded = raw_data.decode(enc)
            st.caption(f"✅ 감지된 인코딩: {enc}")
            break
        except:
            continue

    if not decoded:
        st.error("파일을 읽을 수 없습니다. 인코딩 문제일 수 있습니다.")
        st.stop()

    stringio = StringIO(decoded)
    df = pd.read_csv(stringio, on_bad_lines='skip')

    st.subheader("1. 비행 데이터 미리보기")
    st.dataframe(df.head())

    # 위경도 칼럼 이름 자동 추측
    lat_col = [col for col in df.columns if 'lat' in col.lower()][0]
    lon_col = [col for col in df.columns if 'lon' in col.lower()][0]
    alt_col = [col for col in df.columns if 'alt' in col.lower() or 'height' in col.lower()][0]
    speed_col = [col for col in df.columns if 'speed' in col.lower()][0]

    # 경로 지도 표시
    st.subheader("2. 비행 경로 시각화")
    start_coords = (df[lat_col].iloc[0], df[lon_col].iloc[0])
    m = folium.Map(location=start_coords, zoom_start=16)
    folium.PolyLine(df[[lat_col, lon_col]].values, color="blue").add_to(m)
    folium.Marker(start_coords, tooltip="출발지").add_to(m)
    st_folium(m, width=700, height=500)

    # 고도 및 속도 그래프
    st.subheader("3. 고도 및 속도 그래프")
    fig, ax1 = plt.subplots()
    ax1.plot(df[alt_col].values, color='green', label='고도')
    ax1.set_ylabel('고도 (m)')

    ax2 = ax1.twinx()
    ax2.plot(df[speed_col].values, color='blue', label='속도')
    ax2.set_ylabel('속도 (m/s)')
    st.pyplot(fig)

    # 통계 정보 계산
    st.subheader("4. 비행 요약")
    max_alt = df[alt_col].max()
    max_speed = df[speed_col].max()
    flight_time = len(df) / 10  # 예: 10Hz 샘플링 가정

    # 비행 거리 계산 (단순 유클리드 기반 추정)
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371000  # 지구 반지름 (m)
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    total_distance = 0
    for i in range(1, len(df)):
        total_distance += haversine(df[lat_col].iloc[i-1], df[lon_col].iloc[i-1], df[lat_col].iloc[i], df[lon_col].iloc[i])

    st.metric("총 비행 시간 (예상)", f"{flight_time:.1f} 초")
    st.metric("최고 고도", f"{max_alt:.1f} m")
    st.metric("최고 속도", f"{max_speed:.1f} m/s")
    st.metric("총 이동 거리", f"{total_distance/1000:.2f} km")
