import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import os

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="강원도 경제/고령화 데이터 대시보드", layout="wide")
st.title("🌲 강원도 지역 경제 및 고령화 현황 분석")
st.markdown("강원도의 인구 변화와 경제 지표를 한눈에 확인하는 대시보드입니다.")

# 2. 데이터베이스 연결 확인
db_file = "강원도분석.db"

if not os.path.exists(db_file):
    st.error(f"⚠️ 데이터베이스 파일({db_file})을 찾을 수 없습니다. 파일 위치를 확인해주세요.")
    st.stop()

def run_query(q):
    with sqlite3.connect(db_file) as conn:
        return pd.read_sql(q, conn)

# --- 차트 1: 고령화율과 고용 지표 비교 ---
st.header("1. 고령화율과 지역 경제활동의 상관관계")

# [SQL] 고령화율 계산 및 고용 지표 결합
query1 = """
SELECT 
    CAST(SUBSTR(A.시점, 1, 4) AS INTEGER) as 연도,
    AVG(CAST(A.고령자_65세이상 AS FLOAT) / A.등록인구_소계 * 100) as 고령화율,
    B.평균고용률,
    B.총취업자수
FROM 고령화 A
JOIN (
    SELECT 
        SUBSTR(분기별, 1, 4) as 연도, 
        AVG(고용률) as 평균고용률,
        SUM(취업자) as 총취업자수
    FROM 경제인구
    GROUP BY 연도
) B ON CAST(SUBSTR(A.시점, 1, 4) AS INTEGER) = CAST(B.연도 AS INTEGER)
GROUP BY 연도
ORDER BY 연도
"""

try:
    df1 = run_query(query1)

    # 시각화 (Combo Chart: Bar + Line)
    fig1 = go.Figure()

    # 취업자 수 (막대 그래프)
    fig1.add_trace(go.Bar(
        x=df1['연도'], y=df1['총취업자수'], 
        name='취업자 수', marker_color='lightblue', yaxis='y1'
    ))

    # 고령화율 (선 그래프)
    fig1.add_trace(go.Scatter(
        x=df1['연도'], y=df1['고령화율'], 
        name='고령화율(%)', line=dict(color='red', width=3), yaxis='y2'
    ))

    fig1.update_layout(
        title='연도별 고령화율 및 취업자 수 추이',
        xaxis=dict(title='연도'),
        yaxis=dict(title='취업자 수 (명)', side='left'),
        yaxis2=dict(title='고령화율 (%)', side='right', overlaying='y', tickmode='sync'),
        legend=dict(x=1.1, y=1)
    )

    st.plotly_chart(fig1, use_container_width=True)

    with st.expander("사용한 SQL 및 인사이트 보기"):
        st.code(query1, language='sql')
        st.info("**가설 검증:** 고령화율이 높아짐에 따라 노동 가능 인구가 줄어들 것으로 예상했으나, 그래프상 취업자 수가 유지되거나 증가한다면 이는 고령층의 노동 시장 참여 확대 또는 특정 산업의 인력 유입을 의미할 수 있습니다.")

except Exception as e:
    st.warning(f"차트 1을 생성하는 중 오류가 발생했습니다: {e}")


# --- 차트 2: 고령화 속 관광 산업의 역할 ---
st.header("2. 고령화 시대, 관광/서비스 산업의 보완 가능성")

# [SQL] 고령인구와 관광 관련 GRDP 결합
query2 = """
SELECT 
    CAST(SUBSTR(A.시점, 1, 4) AS INTEGER) as 연도,
    AVG(A.고령자_65세이상) as 고령인구,
    SUM(G.실질) as 관광서비스_생산액
FROM 고령화 A
JOIN GRDP G ON CAST(SUBSTR(A.시점, 1, 4) AS INTEGER) = CAST(SUBSTR(A.시점, 1, 4) AS INTEGER) 
-- 주의: 실제 데이터의 GRDP 시점 형식을 확인해야 함. 여기선 연도 매칭을 가정.
WHERE G.경제활동별 IN ('숙박 및 음식점업', '문화 및 기타 서비스업')
GROUP BY 연도
ORDER BY 연도
"""

try:
    df2 = run_query(query2)

    # 시각화 (Dual Line Chart)
    fig2 = go.Figure()

    fig2.add_trace(go.Scatter(
        x=df2['연도'], y=df2['고령인구'], 
        name='고령 인구수', mode='lines+markers', line=dict(dash='dash')
    ))

    fig2.add_trace(go.Scatter(
        x=df2['연도'], y=df2['관광서비스_생산액'], 
        name='관광/서비스 실질 GRDP', mode='lines+markers', line=dict(width=4)
    ))

    fig2.update_layout(
        title='고령 인구 증가와 관광/서비스 산업 생산액 비교',
        xaxis_title='연도',
        yaxis_title='값 (인구수 / 생산액)',
        hovermode="x unified"
    )

    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("사용한 SQL 및 인사이트 보기"):
        st.code(query2, language='sql')
        st.info("**가설 검증:** 고령인구가 가파르게 증가하는 동안 관광 산업 생산액도 함께 성장한다면, 관광 산업이 강원도의 인구 구조 변화 속에서도 지역 경제의 버팀목 역할을 하고 있음을 시사합니다.")

except Exception as e:
    st.warning(f"차트 2를 생성하는 중 오류가 발생했습니다: {e}")

st.caption("데이터 출처: 강원도 공공데이터 (SQLite DB 활용)")