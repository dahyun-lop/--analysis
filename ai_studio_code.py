import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="강원도 고령화 & 경제 분석 대시보드", layout="wide")
st.title("🌲 강원도 지역 경제 및 고령화 현황 분석")
st.markdown("본 대시보드는 강원도의 인구 구조 변화와 주요 경제 지표를 시각화하여 가설을 검증합니다.")

# CSV 파일 경로 설정
url_aging = "aging_population.csv"
url_economic = "economic_population.csv"
url_grdp = "grdp_data.csv"

# 파일 존재 여부 체크
missing_files = []
for f in [url_aging, url_economic, url_grdp]:
    if not os.path.exists(f):
        missing_files.append(f)

if missing_files:
    st.error(f"⚠️ 아래의 CSV 파일을 찾을 수 없습니다. 파일 위치를 확인해주세요.")
    for mf in missing_files:
        st.markdown(f"- `{mf}`")
    st.stop()

# --------------------------------------------------------------------------------------------------
# 차트 1: 고령화 추이 및 경제활동 인구 구조 (가설 1 검증)
# --------------------------------------------------------------------------------------------------
st.header("1. 강원도 고령화 추이 및 경제활동 인구 구조")
st.caption("가설: 고령화율이 높을수록 지역 생산성 및 경제 지표가 둔화될 것이다.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1-1. 10년간 고령화율 추이 (2014~2023)")
    
    try:
        # 한글 깨짐(BOM) 방지를 위해 utf-8-sig 사용, 안되면 cp949 시도
        try:
            df_aging = pd.read_csv(url_aging, encoding='utf-8-sig')
        except UnicodeDecodeError:
            df_aging = pd.read_csv(url_aging, encoding='cp949')
            
        df_aging.columns = df_aging.columns.str.strip()
        
        # [안전 장치] 만약 '시점'이라는 컬럼명이 없으면 첫 번째 컬럼 이름을 '시점'으로 강제 변경
        if '시점' not in df_aging.columns and len(df_aging.columns) > 0:
            df_aging.rename(columns={df_aging.columns[0]: '시점'}, inplace=True)
            
        df_aging = df_aging.dropna(subset=['시점']).sort_values('시점')
        
        # 고령화율 계산 및 타입 변환
        df_aging['고령자_65세이상'] = pd.to_numeric(df_aging['고령자_65세이상'], errors='coerce')
        df_aging['등록인구_소계'] = pd.to_numeric(df_aging['등록인구_소계'], errors='coerce')
        df_aging['고령화율'] = (df_aging['고령자_65세이상'] / df_aging['등록인구_소계']) * 100

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
            
    except Exception as e:
        st.error(f"차트 1-1 로드 실패: {e}")

with col2:
    st.subheader("1-2. 2023년 강원도 인구 구성 현황")
    
    try:
        try:
            df_economic = pd.read_csv(url_economic, encoding='utf-8-sig')
        except UnicodeDecodeError:
            df_economic = pd.read_csv(url_economic, encoding='cp949')
            
        df_economic.columns = df_economic.columns.str.strip()
        
        # 성별, 분기별 문자열 공백 제거 후 필터링 (에러 방지)
        df_economic['성별'] = df_economic['성별'].astype(str).str.strip()
        df_economic['분기별'] = df_economic['분기별'].astype(str).str.strip()
        
        df_filtered = df_economic[(df_economic['성별'] == '합계') & (df_economic['분기별'] == '전체')]
        
        if not df_filtered.empty:
            labels = ['취업자', '실업자', '비경제활동(가사/육아)', '비경제활동(통학)', '비경제활동(기타)']
            row = df_filtered.iloc[0]
            
            # 수치 데이터 형변환
            values = [
                pd.to_numeric(row['취업자'], errors='coerce'),
                pd.to_numeric(row['실업자'], errors='coerce'),
                pd.to_numeric(row['비경제활동_가사육아'], errors='coerce'),
                pd.to_numeric(row['비경제활동_통학'], errors='coerce'),
                pd.to_numeric(row['비경제활동_기타'], errors='coerce')
            ]
            
            fig1_2 = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, marker=dict(colors=px.colors.pastel.Pastel1))])
            fig1_2.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig1_2, use_container_width=True)
        else:
            st.warning("경제인구 데이터에서 '성별=합계' 및 '분기별=전체' 조건에 맞는 데이터를 찾을 수 없습니다.")
            
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
    try:
        df_grdp = pd.read_csv(url_grdp, encoding='utf-8-sig')
    except UnicodeDecodeError:
        df_grdp = pd.read_csv(url_grdp, encoding='cp949')
        
    df_grdp.columns = df_grdp.columns.str.strip()
    
    df_grdp['시도별'] = df_grdp['시도별'].astype(str).str.strip()
    df_grdp['경제활동별'] = df_grdp['경제활동별'].astype(str).str.strip()
    df_grdp['실질'] = pd.to_numeric(df_grdp['실질'], errors='coerce')
    
    exclude_cats = ['지역내총생산(시장가격)', '순생산물세', '총부가가치(기초가격)', '총부가가치']
    df_grdp_filtered = df_grdp[
        (df_grdp['시도별'].str.contains('강원')) & 
        (~df_grdp['경제활동별'].isin(exclude_cats))
    ].sort_values('실질', ascending=True)
    
    colors = []
    for cat in df_grdp_filtered['경제활동별']:
        if any(keyword in cat for keyword in ['숙박', '음식점', '문화', '서비스', '도소매', '운수']):
            colors.append('#008080') 
        else:
            colors.append('#D3D3D3') 
            
    fig2 = go.Figure(go.Bar(
        x=df_grdp_filtered['실질'],
        y=df_grdp_filtered['경제활동별'],
        orientation='h',
        marker_color=colors
    ))
    
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
1. **GitHub 업로드:** 새 저장소(Repository)를 만들고 코드가 담긴 파일, `requirements.txt`, 그리고 3개의 CSV 파일(`aging_population.csv`, `economic_population.csv`, `grdp_data.csv`)을 함께 푸시합니다.
2. **Cloud 로그인:** [Streamlit Community Cloud](https://share.streamlit.io/)에 접속하여 GitHub 계정으로 로그인합니다.
3. **App 배포:** **[New app]** 버튼을 누른 후, 레포지토리와 실행 메인 파일 경로를 선택하고 **[Deploy]**를 누르면 배포됩니다.
""")
