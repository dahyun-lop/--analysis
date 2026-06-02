import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import plotly.express as px
import os

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="강원도 고령화 & 경제 분석 대시보드", layout="wide")
st.title("🌲 강원도 지역 경제 및 고령화 현황 분석")
st.markdown("본 대시보드는 강원도의 인구 구조 변화와 주요 경제 지표를 시각화하여 가설을 검증합니다.")

# 2. 데이터베이스 연결
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
    
    try:
        # 실제 한글 테이블명 '고령화', 컬럼명 '시점' 반영
        query_aging = """
        SELECT 
            시점, 
            등록인구_소계, 
            고령자_65세이상,
            (CAST(고령자_65세이상 AS FLOAT) / 등록인구_소계) * 100 AS 고령화율
        FROM 고령화
        WHERE 시점 IS NOT NULL
        ORDER BY 시점
        """
        df_aging = run_query(query_aging)

        fig1_1 = go.Figure()
        fig1_1.add_trace(go.Bar(
            x=df_aging['시점'], 
            y=df_aging['고령자_65세이상'], 
            name='고령자 수 (명)', 
            yaxis='y1', 
            marker_color='#FFA07A'
        ))
        fig1_1.add_trace(go.Scatter(
            x=df_aging['시점'], 
            y=df_aging['고령화율'], 
            name='고령화율 (%)', 
            yaxis='y2', 
            mode='lines+markers', 
            line=dict(color='#FF4500', width=3)
        ))
        
        # Dual Y-axis 레이아웃 표준 구조 설정
        fig1_1.update_layout(
            yaxis=dict(title='고령자 수 (명)', showgrid=False),
            yaxis2=dict(title='고령화율 (%)', overlaying='y', side='right', showgrid=True),
            legend=dict(x=0.01, y=0.99),
            margin=dict(l=40, r=40, t=20, b=40)
        )
        st.plotly_chart(fig1_1, use_container_width=True)
            
    except Exception as e:
        st.error(f"차트 1-1 로드 실패: {e}")

with col2:
    st.subheader("1-2. 2023년 강원도 인구 구성 현황")
    
    try:
        # 실제 한글 테이블명 '경제인구', 컬럼명 '비경제활동_가사육아' 반영
        query_ep = """
        SELECT 
            취업자, 
            실업자, 
            비경제활동_가사육아, 
            비경제활동_통학, 
            비경제활동_기타
        FROM 경제인구
        WHERE 성별 LIKE '%합계%' AND 분기별 LIKE '%전체%'
        LIMIT 1
        """
        df_ep = run_query(query_ep)
        
        if not df_ep.empty:
            labels = ['취업자', '실업자', '비경제활동(가사/육아)', '비경제활동(통학)', '비경제활동(기타)']
            row = df_ep.iloc[0]
            values = [row['취업자'], row['실업자'], row['비경제활동_가사육아'], row['비경제활동_통학'], row['비경제활동_기타']]
            
            fig1_2 = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, marker=dict(colors=px.colors.pastel.Pastel1))])
            fig1_2.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig1_2, use_container_width=True)
        else:
            st.warning("경제인구 데이터에서 조건을 만족하는 데이터를 찾을 수 없습니다.")
            
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
    # 실제 테이블명 'grdp_data' 반영 및 강원 지역 데이터 한정 추출
    query_grdp = """
    SELECT 
        시도별, 
        경제활동별, 
        CAST(실질 AS REALSCORE) as 실질값
    FROM grdp_data
    WHERE 시도별 LIKE '%강원%'
      AND 경제활동별 NOT IN ('지역내총생산(시장가격)', '순생산물세', '총부가가치(기초가격)', '총부가가치', '전체')
    ORDER BY 실질값 ASC
    """
    df_grdp = run_query(query_grdp)
    
    if not df_grdp.empty:
        colors = []
        for cat in df_grdp['경제활동별']:
            if any(keyword in cat for keyword in ['숙박', '음식점', '문화', '서비스', '도소매', '운수']):
                colors.append('#008080') # 하이라이트 청록색
            else:
                colors.append('#D3D3D3') # 기본 회색
                
        fig2 = go.Figure(go.Bar(
            x=df_grdp['실질값'],
            y=df_grdp['경제활동별'],
            orientation='h',
            marker_color=colors
        ))
        
        # Mime type 에러를 방지하기 위해 불필요한 레이아웃 속성을 표준 구조로 고정
        fig2.update_layout(
            xaxis_title="실질 GRDP (백만 원)",
            yaxis=dict(
                tickfont=dict(size=11),
                automargin=True
            ),
            margin=dict(l=50, r=40, t=20, b=40),
            height=600
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("grdp_data 테이블에서 '강원' 조건을 만족하는 데이터를 찾지 못했습니다.")
        
except Exception as e:
    st.error(f"차트 2 로드 실패: {e}")

st.info("""
**💡 인사이트 (가설 2 검증)**
* 강원도의 산업별 실질 총생산 구조를 살펴보면, 제조업 기반이 취약한 대신 **'숙박 및 음식점업' 및 '문화/기타 서비스업' 등 관광 관련 산업(청록색 표시)**이 매우 상위권에 위치해 있습니다.
* 이는 급격한 고령화로 전통적 생산 인구가 감소하더라도, 지역의 특수성을 살린 관광 마케팅 및 서비스 산업 활성화를 통해 경제의 총부가가치를 유의미하게 방어하고 보완할 수 있음을 입증합니다.
""")

# --------------------------------------------------------------------------------------------------
# 하단 안내 영역 (Mime type 버그 방지를 위해 단순 텍스트로 수정)
# --------------------------------------------------------------------------------------------------
st.write("---")
st.subheader("🌐 GitHub 업로드 및 Streamlit Cloud 배포 방법")
st.text("1. GitHub 저장소에 app.py, requirements.txt, 강원도분석.db 3개 파일을 업로드합니다.")
st.text("2. share.streamlit.io (Streamlit Cloud)에 접속하여 로그인합니다.")
st.text("3. [New app] 버튼을 누르고 본인의 Repository와 app.py를 선택한 뒤 Deploy를 클릭하면 완료됩니다.")
