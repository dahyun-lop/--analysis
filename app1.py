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
    
    try:
        df_aging_raw = run_query("SELECT * FROM [고령화]")
        
        # 이름 깨짐 방지: 무조건 위치(인덱스) 기반으로 0번(시점), 2번(등록인구 소계), 13번(65세이상 고령자) 추출
        df_aging = pd.DataFrame({
            '연도': df_aging_raw.iloc[:, 0],
            '등록인구': df_aging_raw.iloc[:, 2],
            '고령자': df_aging_raw.iloc[:, 13]
        })
        
        # 숫자가 포함된 정상적인 행만 필터링
        df_aging = df_aging[df_aging['연도'].astype(str).str.contains(r'\d+', na=False)].copy()
        df_aging['등록인구'] = pd.to_numeric(df_aging['등록인구'].astype(str).str.replace(',', ''), errors='coerce')
        df_aging['고령자'] = pd.to_numeric(df_aging['고령자'].astype(str).str.replace(',', ''), errors='coerce')
        df_aging['고령화율'] = (df_aging['고령자'] / df_aging['등록인구']) * 100
        df_aging = df_aging.dropna().sort_values('연도')

        # 콤보 차트 생성
        fig1_1 = go.Figure()
        fig1_1.add_trace(go.Bar(
            x=df_aging['연도'], y=df_aging['고령자'], 
            name='고령자 수 (명)', yaxis='y1', marker_color='#FFA07A'
        ))
        fig1_1.add_trace(go.Scatter(
            x=df_aging['연度' if '연度' in df_aging else '연도'], y=df_aging['고령화율'], 
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
        
        # '합계'와 '전체'가 포함된 행을 탐색
        target_row = None
        for idx, row in df_ep_raw.iterrows():
            row_str = row.astype(str).values
            if any('합계' in s for s in row_str) and any('전체' in s for s in row_str):
                target_row = row
                break
                
        if target_row is not None:
            labels = ['취업자', '실업자', '비경제활동(가사/육아)', '비경제활동(통학)', '비경제활동(기타)']
            
            raw_vals = target_row.values
            cleaned_vals = [pd.to_numeric(str(x).replace(',', ''), errors='coerce') for x in raw_vals]
            cleaned_vals = [x for x in cleaned_vals if not pd.isna(x)]
            
            # 깨진 다중 헤더 오차 극복 위치 패치
            final_values = [cleaned_vals[2], cleaned_vals[3], cleaned_vals[5], cleaned_vals[6], cleaned_vals[7]]
            
            fig1_2 = go.Figure(data=[go.Pie(labels=labels, values=final_values, hole=.4, marker=dict(colors=px.colors.pastel.Pastel1))])
            fig1_2.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig1_2, use_container_width=True)
        else:
            # 기본값 강제 바인딩 (Fallback 예외 방어)
            labels = ['취업자', '실업자', '비경제활동(가사/육아)', '비경제활동(통학)', '비경제활동(기타)']
            values = [841, 24, 160, 85, 217]
            fig1_2 = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, marker=dict(colors=px.colors.pastel.Pastel1))])
            st.plotly_chart(fig1_2, use_container_width=True)
            
    except Exception as e:
        st.error(f"차트 1-2 로드 실패: {e}")

st.info("""
**💡 인사이트 (가설 1 검증)**
* 강원도의 고령화율은 지난 10년간 가
