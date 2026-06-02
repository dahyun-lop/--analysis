import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import os

# 1. 페이지 기본 설정
st.set_page_config(page_title="강원도 고령화 & 산업 분석", layout="wide")

# 2. 데이터베이스 연결 확인
db_path = "강원도분석.db"

if not os.path.exists(db_path):
    st.error("⚠️ 데이터베이스 파일(강원도분석.db)을 찾을 수 없습니다. 파일 위치를 확인해주세요.")
    st.stop()

# 데이터 로드 함수
def run_query(query):
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql(query, conn)

# 헤더 영역
st.title("🌲 강원도 공공데이터 분석 대시보드")
st.markdown("강원도의 고령화 현황과 2023년 경제 구조를 분석하여 지역 경제의 미래를 진단합니다.")
st.divider()

# --- 차트 1: 고령화 추이 및 경제활동 인구 구조 ---
st.header("1. 고령화 추이 및 경제활동 인구 구조")

col1, col2 = st.columns(2)

# 1-1. 고령화 추이 (좌측)
with col1:
    st.subheader("10년간 고령화율 변화 (2014~2023)")
    sql_aging = """
    SELECT 
        시점, 
        (CAST(고령자_65세이상 AS FLOAT) / 등록인구_소계 * 100) AS 고령화율
    FROM aging_population
    ORDER BY 시점 ASC
    """
    df_aging = run_query(sql_aging)
    
    fig_aging = px.line(df_aging, x='시점', y='고령화율', markers=True, 
                        title="연도별 고령화율 추이 (%)",
                        color_discrete_sequence=['#EF553B'])
    st.plotly_chart(fig_aging, use_container_width=True)
    
    with st.expander("사용한 SQL 보기"):
        st.code(sql_aging, language="sql")

# 1-2. 경제활동 인구 구조 (우측)
with col2:
    st.subheader("2023년 경제활동 인구 구성")
    sql_eco = """
    SELECT 
        취업자, 실업자, 비경제활동_가사육아, 비경제활동_통학, 비경제활동_기타
    FROM economic_population
    WHERE 성별 = '합계' AND 분기별 = '전체'
    """
    df_eco = run_query(sql_eco)
    
    # 파이 차트를 위해 데이터 재구성 (Tidy format)
    df_eco_melted = df_eco.melt(var_name="구분", value_name="인원수")
    
    fig_eco = px.pie(df_eco_melted, values='인원수', names='구분', hole=0.4,
                     title="강원도 인구 구조 비중",
                     color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_eco, use_container_width=True)
    
    with st.expander("사용한 SQL 보기"):
        st.code(sql_eco, language="sql")

# 차트 1 인사이트 요약
st.info("""
**가설 1 검증 및 인사이트:**
- **현황:** 강원도의 고령화율은 10년간 지속적으로 상승하여 초고령 사회의 기준을 크게 상회하고 있습니다.
- **인구 구조:** 우측 차트에서 '비경제활동' 인구 중 가사, 통학 외 '기타' 비중이 높게 나타난다면, 이는 고령으로 인한 은퇴 인구가 상당수 포함되어 있음을 시사합니다. 생산 가능 인구의 감소가 실제 경제 지표 둔화로 이어질 우려가 큽니다.
""")
st.divider()

# --- 차트 2: 주요 산업 구조와 관광 산업 비중 ---
st.header("2. 강원도 주요 산업 구조와 관광 산업의 비중 (2023)")

sql_grdp = """
SELECT 경제활동별, 실질
FROM grdp_data
WHERE 시도별 != '전국' AND 경제활동별 != '전체'
ORDER BY 실질 DESC
"""
df_grdp = run_query(sql_grdp)

# 관광 관련 산업 하이라이트 설정
target_industries = ['숙박 및 음식점업', '문화 및 기타 서비스업']
df_grdp['색상'] = df_grdp['경제활동별'].apply(lambda x: '#636EFA' if x in target_industries else '#AB63FA')

fig_grdp = px.bar(df_grdp, x='실질', y='경제활동별', orientation='h',
                  title="강원도 산업별 실질 GRDP 규모",
                  labels={'실질': '생산액 (실질 GRDP)', '경제활동별': '산업군'},
                  color='색상', color_discrete_map="identity")

fig_grdp.update_layout(yaxis={'categoryorder':'total ascending'}) # 높은 순서대로 정렬
st.plotly_chart(fig_grdp, use_container_width=True)

with st.expander("사용한 SQL 보기"):
    st.code(sql_grdp, language="sql")

st.info("""
**가설 2 검증 및 인사이트:**
- **산업 구조:** 강원도 내에서 '숙박 및 음식점업'과 '문화 서비스업'은 주요한 생산 축을 담당하고 있습니다. (하이라이트된 막대 확인)
- **보완 가능성:** 제조업 기반이 취약한 고령화 지역에서 관광/서비스 산업은 고령층의 고용 유지와 외부 자본 유입을 돕는 핵심 보완책입니다. 다만, 해당 산업군이 상위권에 위치하더라도 전체 경제 규모 대비 비중을 지속적으로 확대할 필요가 있습니다.
""")

st.caption("Data Source: 강원도 통계 데이터베이스 (2014-2023)")