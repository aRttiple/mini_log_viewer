import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
from io import StringIO
import math
import chardet
import time

st.set_page_config(page_title="DJI 비행로그 분석기", layout="wide")
st.title("🛸 DJI 비행로그 분석기")

progress_bar = st.progress(0)
start_time = time.time()

uploaded_file = st.file_uploader("비행 로그 파일 업로드 (.CSV 또는 .TXT)", type=["csv", "txt"])

if uploaded_file:
    progress_bar.progress(10)

    # 인코딩 감지 및 디코딩 처리
    raw_data = uploaded_file.getvalue()
    result = chardet.detect(raw_data)
    encoding = result["encoding"] if result["encoding"] else "utf-8"

    try:
        stringio = StringIO(raw_data.decode(encoding))
    except UnicodeDecodeError:
        try:
            stringio = StringIO(raw_data.decode("utf-16"))
        except:
            try:
                stringio = StringIO(raw_data.decode("cp949"))
            except:
                st.error("파일을 읽을 수 없습니다. 인코딩 문제일 수 있습니다.")
                st.stop()

    progress_bar.progress(30)

    try:
        df = pd.read_csv(stringio, on_bad_lines='skip')
    except Exception as e:
        st.error(f"CSV 파일을 불러올 수 없습니다: {e}")
        st.stop()

    progress_bar.progress(50)

    st.subheader("1. 비행 데이터 미리보기")
    st.dataframe(df.head())

    lat_col = st.selectbox("위도 컬럼 선택", df.columns)
    lon_col = st.selectbox("경도 컬럼 선택", df.columns)
    alt_col = st.selectbox("고도 컬럼 선택", df.columns)
    speed_col = st.selectbox("속도 컬럼 선택", df.columns)

    progress_bar.progress(60)

    st.subheader("2. 비행 경로 시각화")
    start_coords = (df[lat_col].iloc[0], df[lon_col].iloc[0])
    m = folium.Map(location=start_coords, zoom_start=16)
    folium.PolyLine(df[[lat_col, lon_col]].values, color="blue").add_to(m)
    folium.Marker(start_coords, tooltip="출발지").add_to(m)
    st_folium(m, width=700, height=500)

    progress_bar.progress(80)

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
    flight_time = len(df) / 10

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

    progress_bar.progress(100)

    end_time = time.time()
    elapsed = end_time - start_time
    st.success(f"✅ 분석 완료 (총 소요 시간: {elapsed:.2f}초)")
