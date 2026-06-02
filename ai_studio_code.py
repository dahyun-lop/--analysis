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
        query_aging = """
        SELECT 
            시점, 
            등록인구_소계, 
            고령자_65세이상,
            (CAST(고령자_65세이상 AS REAL) / CAST(등록인구_소계 AS REAL)) * 100 AS 고령화율
        FROM 고령화
        WHERE 시점 IS NOT NULL
        ORDER BY 시점
        """
        df_aging = run_query(query_aging)

        if not df_aging.empty:
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
            
            fig1_1.update_layout(
                yaxis=dict(title='고령자 수 (명)', showgrid=False),
                yaxis2=dict(title='고령화율 (%)', overlaying='y', side='right', showgrid=True),
                legend=dict(x=0.01, y=0.99),
                margin=dict(l=40, r=40, t=20, b=40)
            )
            st.plotly_chart(fig1_1, use_container_width=True)
        else:
            st.warning("고령화 테이블에 데이터가 없습니다.")
            
    except Exception as e:
        st.error(f"차트 1-1 로드 실패: {e}")

with col2:
    st.subheader("1-2. 강원도 인구 구성 현황 (2023)")
    
    try:
        query_ep = "SELECT * FROM 경제인구"
        df_ep = run_query(query_ep)
        
        if not df_ep.empty:
            df_ep.columns = df_ep.columns.str.strip()
            
            # 조건부 필터링
            df_target = df_ep[(df_ep['성별'].str.contains('합계|계')) & (df_ep['분기별'].str.contains('전체|계|연평균'))]
            
            if df_target.empty:
                row = df_ep.iloc[0]
            else:
                row = df_target.iloc[0]
            
            household_col = [c for c in df_ep.columns if '가사' in c][0]
            
            v_employ = int(pd.to_numeric(row['취업자'], errors='coerce'))
            v_unemploy = int(pd.to_numeric(row['실업자'], errors='coerce'))
            v_house = int(pd.to_numeric(row[household_col], errors='coerce'))
            v_school = int(pd.to_numeric(row['비경제활동_통학'], errors='coerce'))
            v_etc = int(pd.to_numeric(row['비경제활동_기타'], errors='coerce'))
            
            labels = ['취업자', '실업자', '비경제활동(가사/육아)', '비경제활동(통학)', '비경제활동(기타)']
            values = [v_employ, v_unemploy, v_house, v_school, v_etc]
            
            # [수정] Plotly 색상 모듈 호출 오류 수정
            fig1_2 = go.Figure(data=[go.Pie(
                labels=labels, 
                values=values, 
                hole=.4, 
                marker=dict(colors=px.colors.qualitative.Pastel1)
            )])
            fig1_2.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig1_2, use_container_width=True)
        else:
            st.warning("경제인구 테이블이 비어있습니다.")
            
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
    # [수정] 빈 테이블인 grdp_data 대신 실제 데이터가 들어있는 GRDP 테이블 쿼리
    query_grdp = 'SELECT * FROM "GRDP"'
    df_grdp = run_query(query_grdp)
    
    if not df_grdp.empty:
        df_grdp.columns = df_grdp.columns.str.strip()
        df_grdp['시도별'] = df_grdp['시도별'].astype(str).str.strip()
        df_grdp['경제활동별'] = df_grdp['경제활동별'].astype(str).str.strip()
        
        # 강원 데이터 추출
        df_grdp = df_grdp[df_grdp['시도별'].str.contains('강원')].copy()
        
        # 지능형 수치 컬럼 탐색 구조
        value_col = None
        for col in df_grdp.columns:
            if col in ['실질', '당해년도_가격', '당해년도가격', '값', '금액']:
                value_col = col
                break
                
        if value_col:
            df_grdp['금액'] = pd.to_numeric(df_grdp[value_col], errors='coerce').fillna(0)
        else:
            remain_cols = [c for c in df_grdp.columns if c not in ['시도별', '경제활동별', '시점', '년도']]
            if remain_cols:
                df_grdp['금액'] = pd.to_numeric(df_grdp[remain_cols[0]], errors='coerce').fillna(0)
            else:
                df_grdp['금액'] = pd.to_numeric(df_grdp.iloc[:, -1], errors='coerce').fillna(0)
        
        # 상위 합계 카테고리 필터링
        exclude_cats = ['지역내총생산(시장가격)', '순생산물세', '총부가가치(기초가격)', '총부가가치', '전체', '총합', '계']
        df_grdp_filtered = df_grdp[~df_grdp['경제활동별'].isin(exclude_cats)].sort_values('금액', ascending=True)
        
        if not df_grdp_filtered.empty:
            colors = []
            for cat in df_grdp_filtered['경제활동별']:
                if any(keyword in cat for keyword in ['숙박', '음식점', '문화', '서비스', '도소매', '운수']):
                    colors.append('#008080') 
                else:
                    colors.append('#D3D3D3') 
                    
            fig2 = go.Figure(go.Bar(
                x=df_grdp_filtered['금액'],
                y=df_grdp_filtered['경제활동별'],
                orientation='h',
                marker_color=colors
            ))
            
            fig2.update_layout(
                xaxis_title="GRDP 금액 (백만 원)",
                yaxis=dict(
                    tickfont=dict(size=11),
                    automargin=True
                ),
                margin=dict(l=50, r=40, t=20, b=40),
                height=600
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("필터링된 세부 업종별 GRDP 데이터가 존재하지 않습니다.")
    else:
        st.warning("GRDP 테이블이 비어있거나 데이터를 가져오지 못했습니다.")
        
except Exception as e:
    st.error(f"차트 2 로드 실패: {e}")

st.info("""
**💡 인사이트 (가설 2 검증)**
* 강원도의 산업별 실질 총생산 구조를 살펴보면, 제조업 기반이 취약한 대신 **'숙박 및 음식점업' 및 '문화/기타 서비스업' 등 관광 관련 산업(청록색 표시)**이 매우 상위권에 위치해 있습니다.
* 이는 급격한 고령화로 전통적 생산 인구가 감소하더라도, 지역의 특수성을 살린 관광 마케팅 및 서비스 산업 활성화를 통해 경제의 총부가가치를 유의미하게 방어하고 보완할 수 있음을 입증합니다.
""")

# --------------------------------------------------------------------------------------------------
# 하단 배포 영역
# --------------------------------------------------------------------------------------------------
st.write("---")
st.subheader("🌐 GitHub 업로드 및 Streamlit Cloud 배포 방법")
st.text("1. GitHub 저장소에 app.py, requirements.txt, 강원도분석.db 파일을 업로드합니다.")
st.text("2. share.streamlit.io (Streamlit Cloud)에 접속하여 로그인합니다.")
st.text("3. [New app] 버튼을 누르고 레포지토리와 app.py를 지정한 후 Deploy를 클릭하면 실시간 배포됩니다.")
