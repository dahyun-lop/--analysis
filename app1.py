import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import plotly.express as px
import os

# 1. 페이지 설정
st.set_page_config(page_title="강원도 고령화 & 경제 분석 대시보드", layout="wide")
st.title("🌲 강원도 지역 경제 및 고령화 현황 분석")
st.markdown("본 대시보드는 강원도의 인구 구조 변화와 주요 경제 지표를 시각화하여 가설을 검증합니다.")

# 2. 데이터베이스 연결 및 예외 처리
db_file = "강원도분석.db"

if not os.path.exists(db_file):
    st.error(f"⚠️ 데이터베이스 파일({db_file})을 찾을 수 없습니다. 파일 위치를 확인해주세요.")
    st.stop()

def run_query(q):
    with sqlite3.connect(db_file) as conn:
        return pd.read_sql(q, conn)

# --------------------------------------------------------------------------------------------------
# 차트 1: 고령화 추이 및 경제활동 인구 구조 (가설 1 검증)
# --------------------------------------------------------------------------------------------------
st.header("1. 강원도 고령화 추이 및 경제활동 인구 구조")
st.caption("가설: 고령화율이 높을수록 지역 생산성 및 경제 지표가 둔화될 것이다.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1-1. 10년간 고령화율 추이")
    
    # 데이터베이스 내 실제 컬럼명을 유연하게 매칭하기 위해 통째로 가져와 가공합니다.
    try:
        df_aging_raw = run_query("SELECT * FROM [고령화]")
        
        # 컬럼 이름 매칭 자동화 (유연한 예외 처리)
        col_year = [c for c in df_aging_raw.columns if '시점' in c or '년도' in c][0]
        col_pop = [c for c in df_aging_raw.columns if '등록인구' in c or '소계' in c][0]
        col_elder = [c for c in df_aging_raw.columns if '65세' in c or '고령자' in c][0]
        
        # 정제 및 데이터 타입 변환
        df_aging = df_aging_raw[[col_year, col_pop, col_elder]].copy()
        df_aging.columns = ['연도', '등록인구', '고령자']
        
        # 숫자가 아닌 문자열이나 헤더 노이즈 제거
        df_aging = df_aging[df_aging['연도'].str.contains(r'\d+', na=False)].copy()
        df_aging['등록인구'] = pd.to_numeric(df_aging['등록인구'], errors='coerce')
        df_aging['고령자'] = pd.to_numeric(df_aging['고령자'], errors='coerce')
        df_aging['고령화율'] = (df_aging['고령자'] / df_aging['등록인구']) * 100
        df_aging = df_aging.dropna().sort_values('연도')

        # 콤보 차트 생성
        fig1_1 = go.Figure()
        fig1_1.add_trace(go.Bar(
            x=df_aging['연도'], y=df_aging['고령자'], 
            name='고령자 수 (명)', yaxis='y1', marker_color='#FFA07A'
        ))
        fig1_1.add_trace(go.Scatter(
            x=df_aging['연도'], y=df_aging['고령화율'], 
            name='고령화율 (%)', yaxis='y2', mode='lines+markers', line=dict(color='#FF4500', width=3)
        ))
        
        fig1_1.update_layout(
            yaxis=dict(title='고령자 수 (명)', showgrid=False),
            yaxis2=dict(title='고령화율 (%)', overlaying='y', side='right', showgrid=True),
            legend=dict(x=0.01, y=0.99),
            margin=dict(l=40, r=40, t=20, b=40)
        )
        st.plotly_chart(fig1_1, use_container_width=True)
        
        with st.expander("💻 사용한 SQL 보기"):
            st.code("SELECT * FROM [고령화]", language='sql')
            
    except Exception as e:
        st.error(f"차트 1-1 로드 실패: {e}")

with col2:
    st.subheader("1-2. 2023년 강원도 인구 구성 현황")
    
    try:
        # 데이터가 여러 줄 헤더로 인해 꼬인 것을 방지하기 위해 전체 로드 후 인덱스로 접근
        df_ep_raw = run_query("SELECT * FROM [경제인구]")
        
        # '합계'와 '전체'가 포함된 행 필터링
        df_filtered = df_ep_raw[
            (df_ep_raw.iloc[:, 0].str.contains('합계', na=False)) & 
            (df_ep_raw.iloc[:, 1].str.contains('전체', na=False))
        ]
        
        if not df_filtered.empty:
            labels = ['취업자', '실업자', '비경제활동(가사/육아)', '비경제활동(통학)', '비경제활동(기타)']
            
            # 인덱스를 기반으로 순수 데이터 추출 (컬럼명 에러 완벽 회피)
            row = df_filtered.iloc[0]
            values = [
                pd.to_numeric(row.iloc[4], errors='coerce'), # 취업자
                pd.to_numeric(row.iloc[5], errors='coerce'), # 실업자
                pd.to_numeric(row.iloc[7], errors='coerce'), # 가사/육아
                pd.to_numeric(row.iloc[8], errors='coerce'), # 통학
                pd.to_numeric(row.iloc[9], errors='coerce')  # 기타
            ]
            
            fig1_2 = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, marker=dict(colors=px.colors.pastel.Pastel1))])
            fig1_2.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig1_2, use_container_width=True)
        else:
            st.warning("경제인구 테이블에서 '합계' 및 '전체' 기준 데이터를 찾을 수 없습니다.")
            
        with st.expander("💻 사용한 SQL 보기"):
            st.code("SELECT * FROM [경제인구]", language='sql')
            
    except Exception as e:
        st.error(f"차트 1-2 로드 실패: {e}")

st.info("""
**💡 인사이트 (가설 1 검증)**
* 강원도의 고령화율은 지난 10년간 가파르게 상승하여 이미 초고령사회 기준(20%)을 크게 상회하고 있습니다.
* 경제활동 인구 구조 분석 결과, 생산에 직접 기여하지 못하는 비경제활동 인구 비중이 높아 지역 생산성 전반에 부담으로 작용하고 있음을 시사합니다.
""")

# --------------------------------------------------------------------------------------------------
# 차트 2: 주요 산업 구조와 관광 산업의 비중 (가설 2 검증)
# --------------------------------------------------------------------------------------------------
st.write("---")
st.header("2. 강원도 주요 산업 구조와 관광 산업의 비중")
st.caption("가설: 고령화로 인한 생산성 감소를 관광/서비스 산업이 보완할 수 있을 것이다.")

try:
    df_grdp_raw = run_query("SELECT * FROM [GRDP]")
    
    # 컬럼 이름 유연하게 매칭
    col_region = [c for c in df_grdp_raw.columns if '시도' in c][0]
    col_activity = [c for c in df_grdp_raw.columns if '경제활동' in c][0]
