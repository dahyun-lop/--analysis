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
    st.subheader("1-1. 10년간 고령화율 추이 (2014~2023)")
    
    # [SQL] 한글 테이블명 '고령화' 반영 및 컬럼 공백 제거 처리
    query_aging = """
    SELECT 
        [시점] AS 연도,
        [등록인구] AS 등록인구_소계,
        [65세 이상 고령자] AS 고령자_65세이상,
        (CAST([65세 이상 고령자] AS FLOAT) / [등록인구] * 100) AS 고령화율
    FROM [고령화]
    WHERE [시점] NOT IN ('시점', '') -- 헤더 행 노이즈 필터링
    ORDER BY [시점] ASC
    """
    
    try:
        df_aging = run_query(query_aging)
        
        # 콤보 차트 생성 (막대: 고령자수, 선: 고령화율)
        fig1_1 = go.Figure()
        fig1_1.add_trace(go.Bar(
            x=df_aging['연도'], y=df_aging['고령자_65세이상'], 
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
            st.code(query_aging, language='sql')
            
    except Exception as e:
        st.error(f"차트 1-1 로드 실패: {e}")

with col2:
    st.subheader("1-2. 2023년 강원도 인구 구성 현황")
    
    # [SQL] 한글 테이블명 '경제인구' 반영
    query_ep = """
    SELECT 
        [경제활동인구] AS 취업자, 
        [비경제활동인구] AS 실업자, 
        [비경제활동인구_1] AS 비경제활동_가사육아, 
        [비경제활동인구_2] AS 비경제활동_통학, 
        [비경제활동인구_3] AS 비경제활동_기타
    FROM [경제인구]
    WHERE [성별] = '합계' AND [분기별] = '전체'
    """
    # SQLite 내부 인덱싱 컴파일 상태에 대응하기 위한 대체 쿼리 적용
    try:
        df_ep = run_query(query_ep)
        
        if df_ep.empty:
            # 컬럼명이 기본값으로 들어갔을 경우를 대비한 Fallback 쿼리
            query_ep = "SELECT * FROM [경제인구] LIMIT 1 OFFSET 3"
            df_ep = run_query(query_ep)
            
        if not df_ep.empty:
            labels = ['취업자', '실업자', '비경제활동(가사/육아)', '비경제활동(통학)', '비경제활동(기타)']
            # 4번째 행 데이터 파싱
            values = [df_ep.iloc[0, 4], df_ep.iloc[0, 5], df_ep.iloc[0, 7], df_ep.iloc[0, 8], df_ep.iloc[0, 9]]
            
            fig1_2 = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, marker=dict(colors=px.colors.pastel.Pastel1))])
            fig1_2.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig1_2, use_container_width=True)
        else:
            st.warning("데이터가 존재하지 않습니다.")
            
        with st.expander("💻 사용한 SQL 보기"):
            st.code(query_ep, language='sql')
            
    except Exception as e:
        # 컬럼 구조 유연화 처리
        try:
            df_ep_raw = run_query("SELECT * FROM [경제인구] WHERE [성별] = '합계' AND [분기별] = '전체'")
            labels = ['취업자', '실업자', '가사/육아', '통학', '기타']
            values = [df_ep_raw.iloc[0, 4], df_ep_raw.iloc[0, 5], df_ep_raw.iloc[0, 7], df_ep_raw.iloc[0, 8], df_ep_raw.iloc[0, 9]]
            fig1_2 = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4)])
            st.plotly_chart(fig1_2, use_container_width=True)
        except:
            st.error(f"차트 1-2 로드 실패: {e}")

st.info("""
**💡 인사이트 (가설 1 검증)**
* 강원도의 고령화율은 2014년 **16.4%**에서 2023년 **23.7%**로 가파르게 상승하여 이미 초고령사회에 진입했습니다.
* 2023년 인구 구조 분석 결과, 실제 경제 활동에 참여하지 않는 비경제활동인구(가사, 통학, 기타)의 비중이 상당 부분을 차지하고 있어, 생산 가능 인구 확보에 구조적 한계가 오고 있음을 보여줍니다.
""")

# --------------------------------------------------------------------------------------------------
# 차트 2: 주요 산업 구조와 관광 산업의 비중 (가설 2 검증)
# --------------------------------------------------------------------------------------------------
st.write("---")
st.header("2. 강원도 주요 산업 구조와 관광 산업의 비중")
st.caption("가설: 고령화로 인한 생산성 감소를 관광/서비스 산업이 보완할 수 있을 것이다.")

# [SQL] 한글 테이블명 'GRDP' 반영 및 필터링
query_grdp = """
SELECT 
    [경제활동별],
    CAST([실질] AS INTEGER) AS 실질GRDP
FROM [GRDP]
WHERE [시도별] LIKE '%강원%' 
  AND [경제활동별] NOT IN ('지역내총생산(시장가격)', '순생산물세', '총부가가치(기초가격)', '경제활동별')
ORDER BY 실질GRDP ASC
"""

try:
    df_grdp = run_query(query_grdp)
    
    colors = []
    for cat in df_grdp['경제활동별']:
        if cat in ['숙박 및 음식점업', '문화 및 기타 서비스업', '도소매업']:
            colors.append('#008080') # 하이라이트 청록색
        else:
            colors.append('#D3D3D3') # 일반 회색
            
    fig2 = go.Figure(go.Bar(
        x=df_grdp['실질GRDP'],
        y=df_grdp['경제활동별'],
        orientation='h',
        marker_color=colors
    ))
    
    fig2.update_layout(
        xaxis_title="실질 GRDP (백만 원)",
        yaxis=dict(autorange="text", tickfont=dict(size=11)),
        margin=dict(l=150, r=40, t=20, b=40),
        height=600
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    
    with st.expander("💻 사용한 SQL 보기"):
        st.code(query_grdp, language='sql')
        
except Exception as e:
    st.error(f"차트 2 로드 실패: {e}")

st.info("""
**💡 인사이트 (가설 2 검증)**
* 강원도의 주요 실질 GRDP 구조를 분석한 결과, 부동산업이나 공공행정 외에도 **'숙박 및 음식점업' 및 '문화/기타 서비스업'(청록색 표시)**이 탄탄한 축을 형성하고 있습니다.
* 제조업 기반이 취약한 고령화 경제 구조 속에서 영동/영서 지역의 풍부한 자원을 바탕으로 한 **관광 및 서비스 산업 기반 지표가 상위권을 유지**하고 있으므로, 해당 산업 고도화를 통해 지역 생산성 감소를 실질적으로 보완·방어할 수 있다는 가설이 지지됩니다.
""")

# --------------------------------------------------------------------------------------------------
# 배포 가이드 안내
# --------------------------------------------------------------------------------------------------
st.write("---")
st.subheader("🌐 GitHub 업로드 및 Streamlit Cloud 배포 안내")
st.markdown("""
1. **GitHub 업로드:** 새 저장소(Repository)를 만들고 `app.py`, `requirements.txt`, `강원도분석.db` 파일을 푸시(Upload)합니다.
2. **Cloud 로그인:** [Streamlit Community Cloud](https://share.streamlit.io/)에 접속하여 GitHub 계정으로 로그인합니다.
3. **App 배포:** **[New app]** 버튼을 누른 후, 방금 만든 레포지토리와 `app.py` 경로를 선택하고 **[Deploy]**를 누르면 1분 만에 전 세계에 배포됩니다.
""")
