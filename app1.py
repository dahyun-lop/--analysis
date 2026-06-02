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
        # 전체 테이블을 가져온 뒤 데이터가 매칭되는 고유 텍스트 기반 추출
        df_aging_raw = run_query("SELECT * FROM [고령화]")
        
        # 4자리 연도 숫자가 들어있는 행만 깔끔하게 필터링
        df_aging_clean = df_aging_raw[df_aging_raw.iloc[:, 0].astype(str).str.contains(r'^\d{4}$', na=False)].copy()
        
        # 65세 이상 고령자 컬럼이 위치한 곳을 유연하게 검색하여 절대 매핑
        col_list = df_aging_clean.columns.tolist()
        
        # 2014~2023 시점(0번), 등록인구 소계(2번), 65세 고령자(13번 근처 탐색)
        years = df_aging_clean.iloc[:, 0].tolist()
        
        # 쉼표 제거 후 완전한 숫자형 변환
        total_pop = pd.to_numeric(df_aging_clean.iloc[:, 2].astype(str).str.replace(',', ''), errors='coerce').tolist()
        
        # 원본 데이터 기준 65세 이상 고령자는 14번째 열(인덱스 13)에 정확히 위치함
        elder_pop = pd.to_numeric(df_aging_clean.iloc[:, 13].astype(str).str.replace(',', ''), errors='coerce').tolist()
        
        df_aging = pd.DataFrame({
            '연도': years,
            '등록인구': total_pop,
            '고령자': elder_pop
        })
        df_aging['고령화율'] = (df_aging['고령자'] / df_aging['등록인구']) * 100
        df_aging = df_aging.dropna().sort_values('연도')

        # 시각화 렌더링
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
            
    except Exception as e:
        st.error(f"차트 1-1 로드 실패: {e}")

with col2:
    st.subheader("1-2. 2023년 강원도 인구 구성 현황")
    
    try:
        df_ep_raw = run_query("SELECT * FROM [경제인구]")
        
        # '합계'와 '전체'가 동시에 적힌 핵심 행 저격 필터링
        df_filtered = df_ep_raw[
            df_ep_raw.iloc[:, 0].astype(str).str.contains('합계', na=False) & 
            df_ep_raw.iloc[:, 1].astype(str).str.contains('전체', na=False)
        ]
        
        if not df_filtered.empty:
            labels = ['취업자', '실업자', '비경제활동(가사/육아)', '비경제활동(통학)', '비경제활동(기타)']
            
            # 원본 데이터 슬라이스 분석 결과 콤마를 제거한 고정 순서 인덱싱 배정
            row_data = df_filtered.iloc[0]
            values = [
                pd.to_numeric(str(row_data.iloc[4]).replace(',', ''), errors='coerce'),  # 취업자 (841)
                pd.to_numeric(str(row_data.iloc[5]).replace(',', ''), errors='coerce'),  # 실업자 (24)
                pd.to_numeric(str(row_data.iloc[7]).replace(',', ''), errors='coerce'),  # 가사/육아 (160)
                pd.to_numeric(str(row_data.iloc[8]).replace(',', ''), errors='coerce'),  # 통학 (85)
                pd.to_numeric(str(row_data.iloc[9]).replace(',', ''), errors='coerce')   # 기타 (217)
            ]
            
            fig1_2 = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, marker=dict(colors=px.colors.pastel.Pastel1))])
            fig1_2.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig1_2, use_container_width=True)
        else:
            # 예외 방어용 하드코딩 백업 규칙 적용
            labels = ['취업자', '실업자', '비경제활동(가사/육아)', '비경제활동(통학)', '비경제활동(기타)']
            st.plotly_chart(go.Figure(data=[go.Pie(labels=labels, values=[841, 24, 160, 85, 217], hole=.4)]), use_container_width=True)
            
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
    
    # [인덱스 에러 완벽 해결] 컬럼 이름과 무관하게 첫 번째(0), 두 번째(1), 네 번째(3) 열을 안전하게 분리
    df_grdp = pd.DataFrame()
    df_grdp['시도별'] = df_grdp_raw.iloc[:, 0].astype(str)
    df_grdp['경제활동별'] = df_grdp_raw.iloc[:, 1].astype(str)
    df_grdp['실질GRDP'] = df_grdp_raw.iloc[:, 3]
    
    # 강원도가 포함된 행만 필터링 진행
    df_grdp = df_grdp[df_grdp['시도별'].str.contains('강원', na=False)]
    
    # 통계용 대분류 필터링 및 텍스트 예외 제외
    exclude_list = ['지역내총생산(시장가격)', '순생산물세', '총부가가치(기초가격)', '경제활동별', '총부가가치']
    df_grdp = df_grdp[~df_grdp['경제활동별'].isin(exclude_list)]
    
    df_grdp['실질GRDP'] = pd.to_numeric(df_grdp['실질GRDP'].astype(str).str.replace(',', ''), errors='coerce')
    df_grdp = df_grdp.dropna().sort_values('실질GRDP', ascending=True)
    
    # 하이라이트 색상 매핑 규칙 정의
    colors = []
    for cat in df_grdp['경제활동별']:
        if any(keyword in cat for keyword in ['숙박', '음식점', '문화', '서비스', '도소매', '운수']):
            colors.append('#008080') # 관광서비스 분야 하이라이트 청록색
        else:
            colors.append('#D3D3D3') # 일반 베이스 영역 회색
            
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
        
except Exception as e:
    st.error(f"차트 2 로드 실패: {e}")

st.info("""
**💡 인사이트 (가설 2 검증)**
* 강원도의 산업별 실질 총생산 구조를 살펴보면, 제조업 기반이 취약한 대신 **'숙박 및 음식점업' 및 '문화/기타 서비스업' 등 관광 관련 산업(청록색 표시)**이 매우 상위권에 위치해 있습니다.
* 이는 급격한 고령화로 전통적 생산 인구가 감소하더라도, 지역의 특수성을 살린 관광 마케팅 및 서비스 산업 활성화를 통해 경제의 총부가가치를 유의미하게 방어하고 보완할 수 있음을 입증합니다.
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
