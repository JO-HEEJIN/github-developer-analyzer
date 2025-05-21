#!/usr/bin/env python3
# github_analyzer/dashboard.py

import os
import json
import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import networkx as nx
import joblib
from datetime import datetime, timedelta

# 디렉토리 설정
RESULTS_DIR = "results"
# DATA_DIR = "data"

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

MODELS_DIR = os.path.join(RESULTS_DIR, "models")

# 페이지 기본 설정
st.set_page_config(
    page_title="GitHub 개발자 행동 패턴 분석기",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 추가
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 600;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.8rem;
        font-weight: 500;
        color: #0D47A1;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .card {
        background-color: #F5F5F5;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .bold-text {
        font-weight: 600;
    }
    .center-text {
        text-align: center;
    }
    hr {
        margin-top: 2rem;
        margin-bottom: 2rem;
    }
    .highlight {
        background-color: #E3F2FD;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 4px solid #1E88E5;
    }
</style>
""", unsafe_allow_html=True)

# 데이터 로드 함수 - 클래스 외부에 위치
@st.cache_data
def load_dashboard_data():
    """분석 결과 데이터 로드"""
    data = {}
    
    # 사용 가능한 저장소 목록
    data['repositories'] = []
    for repo_dir in os.listdir(DATA_DIR):
        if os.path.isdir(os.path.join(DATA_DIR, repo_dir)):
            data['repositories'].append(repo_dir.replace("_", "/", 1))
    
    # 개발자 패턴 데이터
    dev_patterns_dir = os.path.join(RESULTS_DIR, 'developer_patterns')
    if os.path.exists(dev_patterns_dir):
        # 개발자 통계
        stats_file = os.path.join(dev_patterns_dir, 'dev_stats.csv')
        if os.path.exists(stats_file):
            data['dev_stats'] = pd.read_csv(stats_file)
        
        # 요일 활동
        day_file = os.path.join(dev_patterns_dir, 'day_activity.csv')
        if os.path.exists(day_file):
            data['day_activity'] = pd.read_csv(day_file, index_col=0)
        
        # 시간대 활동
        hour_file = os.path.join(dev_patterns_dir, 'hour_activity.csv')
        if os.path.exists(hour_file):
            data['hour_activity'] = pd.read_csv(hour_file, index_col=0)
        
        # 메시지 패턴
        message_file = os.path.join(dev_patterns_dir, 'message_patterns.json')
        if os.path.exists(message_file):
            with open(message_file, 'r') as f:
                data['message_patterns'] = json.load(f)
    
    # PR 패턴 데이터
    pr_patterns_dir = os.path.join(RESULTS_DIR, 'pr_patterns')
    if os.path.exists(pr_patterns_dir):
        # PR 통계
        pr_stats_file = os.path.join(pr_patterns_dir, 'pr_stats.csv')
        if os.path.exists(pr_stats_file):
            data['pr_stats'] = pd.read_csv(pr_stats_file)
        
        # 크기-시간 상관관계
        corr_file = os.path.join(pr_patterns_dir, 'size_time_corr.json')
        if os.path.exists(corr_file):
            with open(corr_file, 'r') as f:
                data['size_time_corr'] = json.load(f)
        
        # 리뷰 네트워크
        network_file = os.path.join(pr_patterns_dir, 'review_network.json')
        if os.path.exists(network_file):
            with open(network_file, 'r') as f:
                data['review_network'] = json.load(f)
    
    # 클러스터링 데이터
    clustering_dir = os.path.join(RESULTS_DIR, 'clustering')
    if os.path.exists(clustering_dir):
        # 개발자 프로필
        profiles_file = os.path.join(clustering_dir, 'developer_profiles.csv')
        if os.path.exists(profiles_file):
            data['dev_profiles'] = pd.read_csv(profiles_file)
        
        # 클러스터 프로필
        cluster_file = os.path.join(clustering_dir, 'cluster_profiles.csv')
        if os.path.exists(cluster_file):
            data['cluster_profiles'] = pd.read_csv(cluster_file)
    
    # 시간 패턴 데이터
    time_patterns_dir = os.path.join(RESULTS_DIR, 'time_patterns')
    if os.path.exists(time_patterns_dir):
        # 일별 커밋
        daily_file = os.path.join(time_patterns_dir, 'daily_commits.csv')
        if os.path.exists(daily_file):
            data['daily_commits'] = pd.read_csv(daily_file)
            data['daily_commits']['date_only'] = pd.to_datetime(data['daily_commits']['date_only'])
        
        # 요일별 커밋
        day_file = os.path.join(time_patterns_dir, 'day_of_week.csv')
        if os.path.exists(day_file):
            data['day_counts'] = pd.read_csv(day_file)
        
        # 시간대별 커밋
        hour_file = os.path.join(time_patterns_dir, 'hour_of_day.csv')
        if os.path.exists(hour_file):
            data['hour_counts'] = pd.read_csv(hour_file)
        
        # 요일-시간 히트맵
        heatmap_file = os.path.join(time_patterns_dir, 'day_hour_heatmap.csv')
        if os.path.exists(heatmap_file):
            data['day_hour_counts'] = pd.read_csv(heatmap_file, index_col=0)
    
    # 모델 데이터
    if os.path.exists(MODELS_DIR):
        # 모델 평가
        eval_file = os.path.join(MODELS_DIR, 'model_evaluation.json')
        if os.path.exists(eval_file):
            with open(eval_file, 'r') as f:
                data['model_evaluation'] = json.load(f)
    
    return data

class GitHubAnalysisDashboard:
    def __init__(self):
        """대시보드 초기화"""
        # 수정: 전역 함수에서 데이터 로드
        self.data = load_dashboard_data()
    
    def run_dashboard(self):
        """대시보드 실행"""
        # 헤더
        st.markdown('<div class="main-header">GitHub 개발자 행동 패턴 분석기</div>', unsafe_allow_html=True)
        
        # 사이드바
        st.sidebar.image("https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png", width=100)
        st.sidebar.title("탐색 메뉴")
        
        # 페이지 선택
        page = st.sidebar.radio(
            "분석 페이지 선택",
            ["개요", "개발자 행동 패턴", "PR 분석", "시간 패턴", "개발자 클러스터링", "PR 승인 예측"]
        )
        
        # 저장소 선택 (데이터가 있는 경우)
        if 'repositories' in self.data and self.data['repositories']:
            selected_repo = st.sidebar.selectbox(
                "저장소 선택",
                ["모든 저장소"] + self.data['repositories']
            )
        else:
            selected_repo = "모든 저장소"
            st.sidebar.warning("저장소 데이터를 찾을 수 없습니다.")
        
        # 선택된 페이지 표시
        if page == "개요":
            self.show_overview()
        elif page == "개발자 행동 패턴":
            self.show_developer_patterns()
        elif page == "PR 분석":
            self.show_pr_analysis()
        elif page == "시간 패턴":
            self.show_time_patterns()
        elif page == "개발자 클러스터링":
            self.show_clustering()
        elif page == "PR 승인 예측":
            self.show_pr_prediction()
    
    def show_overview(self):
        """개요 페이지"""
        st.markdown('<div class="sub-header">프로젝트 개요</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="card">
        <p>GitHub API를 활용하여 오픈 소스 프로젝트의 개발자 행동 데이터를 수집하고 분석하는 대시보드입니다. 
        개발자 활동 패턴, 코드 변경 특성, PR 처리 방식 등을 시각화하고 분석합니다.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 데이터 요약
        st.markdown('<div class="sub-header">데이터 요약</div>', unsafe_allow_html=True)
        
        # 분석한 저장소 수
        repos_count = len(self.data.get('repositories', []))
        
        # 개발자 수 계산
        if 'dev_stats' in self.data and not self.data['dev_stats'].empty:
            devs_count = len(self.data['dev_stats'])
        else:
            devs_count = 0
        
        # 커밋 수 계산
        commits_count = 0
        if 'daily_commits' in self.data and not self.data['daily_commits'].empty:
            commits_count = self.data['daily_commits']['count'].sum()
        
        # PR 수 계산
        prs_count = 0
        if 'pr_stats' in self.data and not self.data['pr_stats'].empty:
            prs_count = self.data['pr_stats'].get('pr_count', 0).sum() if 'pr_count' in self.data['pr_stats'] else 0
        
        # 요약 통계 표시
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("분석한 저장소", f"{repos_count}")
        
        with col2:
            st.metric("개발자 수", f"{devs_count}")
        
        with col3:
            st.metric("커밋 수", f"{int(commits_count)}")
        
        with col4:
            st.metric("PR 수", f"{int(prs_count)}")
        
        # 시간 추세 차트 (있는 경우)
        st.markdown('<div class="sub-header">활동 추세</div>', unsafe_allow_html=True)
        
        if 'daily_commits' in self.data and not self.data['daily_commits'].empty:
            # 일별 커밋 추세
            fig = px.line(
                self.data['daily_commits'], 
                x='date_only', 
                y='count',
                title='일별 커밋 추세',
                labels={'date_only': '날짜', 'count': '커밋 수'}
            )
            
            fig.update_layout(
                xaxis_title="날짜",
                yaxis_title="커밋 수",
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("활동 추세 데이터를 찾을 수 없습니다.")
        
        # 추가 정보
        st.markdown('<div class="sub-header">주요 발견 사항</div>', unsafe_allow_html=True)
        
        if ('dev_stats' in self.data and not self.data['dev_stats'].empty and
            'day_hour_counts' in self.data and not self.data['day_hour_counts'].empty and
            'pr_stats' in self.data and not self.data['pr_stats'].empty):
            
            # 가장 활발한 개발자
            top_dev = self.data['dev_stats'].sort_values('commit_count', ascending=False).iloc[0]
            top_dev_name = top_dev.name if hasattr(top_dev, 'name') else "알 수 없음"
            
            # 가장 활발한 시간대
            hour_counts = self.data['hour_counts'] if 'hour_counts' in self.data else None
            most_active_hour = hour_counts.iloc[:, 0].idxmax() if hour_counts is not None else "알 수 없음"
            
            # PR 승인율
            if 'is_merged_mean' in self.data['pr_stats'].columns:
                avg_merge_rate = self.data['pr_stats']['is_merged_mean'].mean() * 100
            else:
                avg_merge_rate = 0
            
            st.markdown(f"""
            <div class="card">
                <p>📊 <span class="bold-text">가장 활발한 개발자:</span> {top_dev_name}</p>
                <p>🕒 <span class="bold-text">가장 활발한 시간대:</span> {most_active_hour}시</p>
                <p>📈 <span class="bold-text">평균 PR 승인율:</span> {avg_merge_rate:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("주요 발견 사항 데이터를 찾을 수 없습니다.")
        
        # 추가 안내
        st.markdown("""
        <div class="highlight">
        좌측 사이드바에서 다양한 분석 페이지를 선택하여 더 자세한 정보를 확인하세요.
        </div>
        """, unsafe_allow_html=True)
    
    def show_developer_patterns(self):
        st.write("데이터 구조 확인:")
        st.write("dev_stats 타입:", type(self.data.get('dev_stats')))
        if 'dev_stats' in self.data and not self.data['dev_stats'].empty:
            st.write("dev_stats 열:", self.data['dev_stats'].columns.tolist())
            st.write("dev_stats 인덱스 타입:", type(self.data['dev_stats'].index))
            st.write("dev_stats 샘플:", self.data['dev_stats'].head(2))

        """개발자 행동 패턴 페이지"""
        st.markdown('<div class="sub-header">개발자 행동 패턴 분석</div>', unsafe_allow_html=True)

        if ('dev_stats' not in self.data or self.data['dev_stats'].empty):
            st.warning("개발자 패턴 데이터를 찾을 수 없습니다.")
            return

        # 상위 개발자 표시
        st.markdown('<div class="sub-header">가장 활발한 개발자</div>', unsafe_allow_html=True)

        try:
            # 상위 10명의 개발자 선택
            dev_stats = self.data['dev_stats'].copy()
            
            # 인덱스가 문자열인지 확인하고 필요시 변환
            if not pd.api.types.is_object_dtype(dev_stats.index):
                dev_stats.index = dev_stats.index.astype(str)
            
            # 'commit_count' 열이 있는지 확인
            if 'commit_count' not in dev_stats.columns:
                st.error("커밋 수 정보를 찾을 수 없습니다.")
                return
            
            # 정렬 및 상위 10명 선택
            top_devs = dev_stats.sort_values('commit_count', ascending=False).head(10)
            
            # 인덱스를 열로 변환 (plotly와의 호환성을 위해)
            top_devs_reset = top_devs.reset_index()
            top_devs_reset.rename(columns={'index': 'developer'}, inplace=True)
            
            # Plotly 그래프 생성
            fig = px.bar(
                top_devs_reset, 
                y='developer',  # 인덱스 대신 열 사용
                x='commit_count',
                orientation='h',
                title='커밋 수 기준 상위 개발자',
                labels={'commit_count': '커밋 수', 'developer': '개발자'},
                color='commit_count',
                color_continuous_scale=px.colors.sequential.Blues
            )
            
            fig.update_layout(
                xaxis_title="커밋 수",
                yaxis_title="개발자",
                yaxis={'categoryorder': 'total ascending'}
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"개발자 패턴 차트 생성 중 오류 발생: {str(e)}")
            st.write("개발자 데이터 미리보기:")
            st.write(self.data['dev_stats'].head())
# 개발자 상세 분석
        st.markdown('<div class="sub-header">개발자 상세 분석</div>', unsafe_allow_html=True)
        
        # 개발자 선택
        selected_dev = st.selectbox(
            "개발자 선택",
            top_devs.index.tolist(),
            format_func=lambda x: x if x else "알 수 없음"
        )
        
        if selected_dev:
            # 선택된 개발자 데이터 가져오기
            print("Index type:", self.data['dev_stats'].index.dtype)
            print("Available keys:", self.data['dev_stats'].index.tolist())
            print("Selected key:", selected_dev, "Type:", type(selected_dev))

            dev_data = self.data['dev_stats'].loc[int(selected_dev)]
            
            # 기본 통계
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("총 커밋 수", f"{int(dev_data['commit_count'])}")
                
                if 'active_days' in dev_data:
                    st.metric("활동 기간", f"{int(dev_data['active_days'])}일")
            
            with col2:
                if 'additions_mean' in dev_data:
                    st.metric("평균 추가 라인", f"{dev_data['additions_mean']:.1f}")
                if 'deletions_mean' in dev_data:
                    st.metric("평균 삭제 라인", f"{dev_data['deletions_mean']:.1f}")
            
            with col3:
                if 'message_length_mean' in dev_data:
                    st.metric("평균 메시지 길이", f"{dev_data['message_length_mean']:.1f}")
                if 'commits_per_day' in dev_data:
                    st.metric("일일 평균 커밋", f"{dev_data['commits_per_day']:.2f}")
            
            # 탭으로 다양한 분석 표시
            dev_tabs = st.tabs(["요일별 활동", "시간대별 활동", "커밋 메시지 분석"])
            
            # 요일별 활동 패턴
            with dev_tabs[0]:
                if 'day_activity' in self.data and not self.data['day_activity'].empty:
                    if selected_dev in self.data['day_activity'].index:
                        # 요일별 활동 비율
                        day_data = self.data['day_activity'].loc[selected_dev]
                        
                        # 요일 순서 설정
                        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        valid_days = [day for day in day_order if day in day_data.index]
                        
                        # 데이터프레임 생성
                        day_df = pd.DataFrame({
                            'day': valid_days,
                            'activity': [day_data[day] for day in valid_days]
                        })
                        
                        # 그래프 생성
                        fig = px.bar(
                            day_df,
                            x='day',
                            y='activity',
                            title=f'{selected_dev}의 요일별 활동 패턴',
                            labels={'day': '요일', 'activity': '활동 비율'},
                            color='activity',
                            color_continuous_scale=px.colors.sequential.Viridis
                        )
                        
                        fig.update_layout(
                            xaxis={'categoryorder': 'array', 'categoryarray': valid_days},
                            yaxis_title="활동 비율",
                            xaxis_title="요일"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info(f"{selected_dev}의 요일별 활동 데이터를 찾을 수 없습니다.")
                else:
                    st.info("요일별 활동 데이터를 찾을 수 없습니다.")
            
            # 시간대별 활동 패턴
            with dev_tabs[1]:
                if 'hour_activity' in self.data and not self.data['hour_activity'].empty:
                    if selected_dev in self.data['hour_activity'].index:
                        # 시간대별 활동 비율
                        hour_data = self.data['hour_activity'].loc[selected_dev]
                        
                        # 데이터프레임 생성
                        hour_df = pd.DataFrame({
                            'hour': hour_data.index,
                            'activity': hour_data.values
                        })
                        
                        # 그래프 생성
                        fig = px.line(
                            hour_df,
                            x='hour',
                            y='activity',
                            title=f'{selected_dev}의 시간대별 활동 패턴',
                            labels={'hour': '시간 (24시간)', 'activity': '활동 비율'},
                        )
                        
                        fig.update_layout(
                            xaxis=dict(tickmode='linear', tick0=0, dtick=2),
                            yaxis_title="활동 비율",
                            xaxis_title="시간 (24시간)"
                        )
                        
                        # 영역 채우기 추가
                        fig.add_trace(
                            go.Scatter(
                                x=hour_df['hour'],
                                y=hour_df['activity'],
                                fill='tozeroy',
                                fillcolor='rgba(26, 118, 255, 0.2)',
                                line=dict(color='rgba(26, 118, 255, 0.8)')
                            )
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info(f"{selected_dev}의 시간대별 활동 데이터를 찾을 수 없습니다.")
                else:
                    st.info("시간대별 활동 데이터를 찾을 수 없습니다.")
            
            # 커밋 메시지 분석
            with dev_tabs[2]:
                if ('message_patterns' in self.data and 
                    self.data['message_patterns'] and 
                    selected_dev in self.data['message_patterns']):
                    
                    # 메시지 패턴 데이터
                    message_data = self.data['message_patterns'][selected_dev]
                    
                    # 데이터프레임 생성
                    words = list(message_data.keys())
                    counts = list(message_data.values())
                    
                    words_df = pd.DataFrame({
                        'word': words,
                        'count': counts
                    }).sort_values('count', ascending=False)
                    
                    # 그래프 생성
                    fig = px.bar(
                        words_df,
                        x='count',
                        y='word',
                        orientation='h',
                        title=f'{selected_dev}의 자주 사용하는 단어',
                        labels={'count': '빈도수', 'word': '단어'},
                        color='count',
                        color_continuous_scale=px.colors.sequential.Purples
                    )
                    
                    fig.update_layout(
                        xaxis_title="빈도수",
                        yaxis_title="단어",
                        yaxis={'categoryorder': 'total ascending'}
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"{selected_dev}의 커밋 메시지 분석 데이터를 찾을 수 없습니다.")
        
        # 코드 변경 패턴 분석
        st.markdown('<div class="sub-header">코드 변경 패턴 분석</div>', unsafe_allow_html=True)
        
        # 필요한 열이 있는지 확인
        code_cols = ['additions_mean', 'deletions_mean']
        if all(col in self.data['dev_stats'].columns for col in code_cols):
            # 상위 개발자의 코드 변경 패턴
            top_n = min(15, len(self.data['dev_stats']))
            top_code_devs = self.data['dev_stats'].sort_values('commit_count', ascending=False).head(top_n)
            
            # 그래프 데이터 준비
            add_del_data = []
            
            for dev in top_code_devs.index:
                add_del_data.append({
                    'developer': dev,
                    'type': '추가',
                    'lines': top_code_devs.loc[dev, 'additions_mean']
                })
                add_del_data.append({
                    'developer': dev,
                    'type': '삭제',
                    'lines': top_code_devs.loc[dev, 'deletions_mean']
                })
            
            add_del_df = pd.DataFrame(add_del_data)
            
            # 그래프 생성
            fig = px.bar(
                add_del_df,
                x='developer',
                y='lines',
                color='type',
                barmode='group',
                title='개발자별 평균 코드 추가/삭제 라인',
                labels={'developer': '개발자', 'lines': '라인 수', 'type': '유형'},
                color_discrete_map={'추가': '#4CAF50', '삭제': '#F44336'}
            )
            
            fig.update_layout(
                xaxis_title="개발자",
                yaxis_title="평균 라인 수",
                legend_title="유형"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 추가/삭제 비율 분석
            if 'add_delete_ratio' in self.data['dev_stats'].columns:
                ratio_data = top_code_devs.sort_values('add_delete_ratio')
                
                fig = px.bar(
                    ratio_data,
                    x=ratio_data.index,
                    y='add_delete_ratio',
                    title='개발자별 추가/삭제 라인 비율',
                    labels={'add_delete_ratio': '비율', 'index': '개발자'},
                    color='add_delete_ratio',
                    color_continuous_scale=px.colors.sequential.RdBu
                )
                
                fig.update_layout(
                    xaxis_title="개발자",
                    yaxis_title="추가/삭제 비율"
                )
                
                # 참조선 추가 (1.0 = 균형)
                fig.add_shape(
                    type="line",
                    x0=-0.5,
                    y0=1,
                    x1=len(ratio_data) - 0.5,
                    y1=1,
                    line=dict(color="black", width=1, dash="dash")
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("""
                <div class="card">
                <p><span class="bold-text">추가/삭제 비율 해석:</span></p>
                <ul>
                    <li>비율 = 1: 추가 라인과 삭제 라인이 균형을 이룸</li>
                    <li>비율 > 1: 코드 추가가 삭제보다 많음 (코드베이스 확장)</li>
                    <li>비율 < 1: 코드 삭제가 추가보다 많음 (코드 정리/리팩토링)</li>
                </ul>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("코드 변경 패턴 분석에 필요한 데이터를 찾을 수 없습니다.")
    
    def show_pr_analysis(self):
        """PR 분석 페이지"""
        st.markdown('<div class="sub-header">PR (Pull Request) 분석</div>', unsafe_allow_html=True)
        
        if ('pr_stats' not in self.data or self.data['pr_stats'].empty):
            st.warning("PR 데이터를 찾을 수 없습니다.")
            return
        
        # PR 통계 개요
        st.markdown('<div class="sub-header">PR 통계 개요</div>', unsafe_allow_html=True)
        
        # 기본 통계 계산
        pr_stats = self.data['pr_stats']
        
        # 필요한 열 확인
        if 'pr_count' in pr_stats.columns and 'is_merged_mean' in pr_stats.columns:
            # 전체 PR 수
            total_prs = pr_stats['pr_count'].sum()
            
            # 평균 병합률
            avg_merge_rate = pr_stats['is_merged_mean'].mean() * 100
            
            # 평균 처리 시간 (있는 경우)
            if 'processing_time_mean' in pr_stats.columns:
                avg_processing_time = pr_stats['processing_time_mean'].mean()
            else:
                avg_processing_time = 0
            
            # 통계 표시
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("총 PR 수", f"{int(total_prs)}")
            
            with col2:
                st.metric("평균 병합률", f"{avg_merge_rate:.1f}%")
            
            with col3:
                st.metric("평균 처리 시간", f"{avg_processing_time:.1f} 시간")
        
        # PR 활동이 가장 활발한 개발자
        st.markdown('<div class="sub-header">PR 활동이 가장 활발한 개발자</div>', unsafe_allow_html=True)
        
        if 'pr_count' in pr_stats.columns:
            # 상위 10명의 PR 작성자
            top_pr_authors = pr_stats.sort_values('pr_count', ascending=False).head(10)
            
            # 그래프로 표시
            fig = px.bar(
                top_pr_authors,
                y=top_pr_authors.index,
                x='pr_count',
                orientation='h',
                title='PR 수 기준 상위 개발자',
                labels={'pr_count': 'PR 수', 'index': '개발자'},
                color='pr_count',
                color_continuous_scale=px.colors.sequential.Greens
            )
            
            fig.update_layout(
                xaxis_title="PR 수",
                yaxis_title="개발자",
                yaxis={'categoryorder': 'total ascending'}
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # PR 병합률 분석 (병합률 열이 있는 경우)
            if 'is_merged_mean' in pr_stats.columns:
                # 병합률 기준 정렬 (최소 2개 이상의 PR을 생성한 개발자만)
                min_prs = 2
                merge_rate_devs = pr_stats[pr_stats['pr_count'] >= min_prs].sort_values('is_merged_mean')
                
                if not merge_rate_devs.empty:
                    fig = px.bar(
                        merge_rate_devs,
                        y=merge_rate_devs.index,
                        x=merge_rate_devs['is_merged_mean'] * 100,  # 퍼센트로 변환
                        orientation='h',
                        title=f'개발자별 PR 병합률 (최소 {min_prs}개 PR)',
                        labels={'x': '병합률 (%)', 'index': '개발자'},
                        color=merge_rate_devs['is_merged_mean'] * 100,
                        color_continuous_scale=px.colors.sequential.BuGn,
                        range_color=[0, 100]
                    )
                    
                    fig.update_layout(
                        xaxis_title="병합률 (%)",
                        yaxis_title="개발자",
                        yaxis={'categoryorder': 'total ascending'}
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
        
        # PR 크기와 처리 시간 분석
        st.markdown('<div class="sub-header">PR 크기와 처리 시간의 관계</div>', unsafe_allow_html=True)
        
        # 크기-시간 상관관계 데이터가 있는 경우
        if 'size_time_corr' in self.data and self.data['size_time_corr']:
            corr_data = self.data['size_time_corr']
            
            # 전체 상관관계
            overall_corr = corr_data.get('overall', 0)
            
            # 개발자별 상관관계
            dev_corrs = {k: v for k, v in corr_data.items() if k != 'overall'}
            
            # 전체 상관관계 표시
            st.metric(
                "PR 크기와 처리 시간의 전체 상관관계",
                f"{overall_corr:.3f}",
                delta_color="normal"
            )
            
            # 상관관계 해석
            if abs(overall_corr) < 0.2:
                st.markdown("""
                <div class="card">
                <p><span class="bold-text">해석:</span> PR 크기(추가된 라인 수)와 처리 시간 사이에 약한 상관관계가 있습니다.
                다른 요소들이 PR 처리 시간에 더 큰 영향을 미칠 수 있습니다.</p>
                </div>
                """, unsafe_allow_html=True)
            elif overall_corr >= 0.2:
                st.markdown("""
                <div class="card">
                <p><span class="bold-text">해석:</span> PR 크기(추가된 라인 수)가 커질수록 처리 시간이 증가하는 경향이 있습니다.
                작은 PR이 더 빠르게 검토되고 병합될 가능성이 높습니다.</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="card">
                <p><span class="bold-text">해석:</span> PR 크기(추가된 라인 수)가 커질수록 처리 시간이 오히려 감소하는 특이한 패턴이 있습니다.
                이는 큰 PR이 특정 상황(예: 주요 기능 출시)에서 우선적으로 처리될 수 있음을 시사합니다.</p>
                </div>
                """, unsafe_allow_html=True)
            
            # 개발자별 상관관계 표시 (최소 3명의 개발자 데이터가 있는 경우)
            if len(dev_corrs) >= 3:
                # 데이터프레임 생성
                corr_df = pd.DataFrame({
                    'developer': list(dev_corrs.keys()),
                    'correlation': list(dev_corrs.values())
                }).sort_values('correlation')
                
                # 그래프 생성
                fig = px.bar(
                    corr_df,
                    x='correlation',
                    y='developer',
                    orientation='h',
                    title='개발자별 PR 크기-처리 시간 상관관계',
                    labels={'correlation': '상관관계', 'developer': '개발자'},
                    color='correlation',
                    color_continuous_scale=px.colors.diverging.RdBu,
                    range_color=[-1, 1]
                )
                
                fig.update_layout(
                    xaxis_title="상관관계 계수",
                    yaxis_title="개발자",
                    yaxis={'categoryorder': 'total ascending'}
                )
                
                # 참조선 추가 (0 = 상관관계 없음)
                fig.add_shape(
                    type="line",
                    x0=0,
                    y0=-0.5,
                    x1=0,
                    y1=len(corr_df) - 0.5,
                    line=dict(color="black", width=1, dash="dash")
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("PR 크기와 처리 시간 관계 데이터를 찾을 수 없습니다.")
        
        # PR 리뷰 네트워크 분석
        st.markdown('<div class="sub-header">PR 리뷰 네트워크</div>', unsafe_allow_html=True)
        
        if 'review_network' in self.data and self.data['review_network'] and 'edges' in self.data['review_network']:
            st.markdown("""
            <div class="card">
            <p>PR 리뷰 네트워크는 누가 누구의 코드를 리뷰하는지 보여주는 관계도입니다.
            화살표는 코드 리뷰 방향을 나타내며, 선의 굵기는 리뷰 빈도를 나타냅니다.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # 리뷰 네트워크 시각화
            st.info("이 섹션에서는 네트워크 그래프가 표시됩니다. 실제 구현 시 NetworkX와 Pyvis를 사용하여 인터랙티브 네트워크 그래프를 생성할 수 있습니다.")
        else:
            st.info("PR 리뷰 네트워크 데이터를 찾을 수 없습니다.")
    
    def show_time_patterns(self):
        """시간 패턴 분석 페이지"""
        st.markdown('<div class="sub-header">시간 패턴 분석</div>', unsafe_allow_html=True)
        
        # 필요한 데이터 확인
        time_data_exists = (
            'day_counts' in self.data or
            'hour_counts' in self.data or
            'day_hour_counts' in self.data or
            'daily_commits' in self.data
        )
        
        if not time_data_exists:
            st.warning("시간 패턴 데이터를 찾을 수 없습니다.")
            return
        
        # 일별 커밋 추세
        st.markdown('<div class="sub-header">일별 커밋 추세</div>', unsafe_allow_html=True)
        
        if 'daily_commits' in self.data and not self.data['daily_commits'].empty:
            # 날짜 형식 확인
            date_col = 'date_only'
            count_col = 'count'
            
            if date_col in self.data['daily_commits'].columns and count_col in self.data['daily_commits'].columns:
                # 데이터 준비
                daily_data = self.data['daily_commits'].copy()
                
                # 날짜 열이 datetime 형식이 아니면 변환
                if not pd.api.types.is_datetime64_any_dtype(daily_data[date_col]):
                    daily_data[date_col] = pd.to_datetime(daily_data[date_col])
                
                # 이동 평균 계산 (7일)
                daily_data['moving_avg'] = daily_data[count_col].rolling(window=7, min_periods=1).mean()
                
                # 그래프 생성 - 일별 커밋 및 이동 평균
                fig = go.Figure()
                
                # 일별 커밋 (막대 그래프)
                fig.add_trace(
                    go.Bar(
                        x=daily_data[date_col],
                        y=daily_data[count_col],
                        name='일별 커밋',
                        marker_color='rgba(58, 71, 80, 0.6)'
                    )
                )
                
                # 7일 이동 평균 (선 그래프)
                fig.add_trace(
                    go.Scatter(
                        x=daily_data[date_col],
                        y=daily_data['moving_avg'],
                        name='7일 이동 평균',
                        mode='lines',
                        line=dict(color='rgba(246, 78, 139, 1)')
                    )
                )
                
                fig.update_layout(
                    title='일별 커밋 추세 및 7일 이동 평균',
                    xaxis_title='날짜',
                    yaxis_title='커밋 수',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # 주간 패턴 분석
                st.markdown('<div class="sub-header">주간 패턴 분석</div>', unsafe_allow_html=True)
                
                # 요일 정보 추가
                daily_data['day_of_week'] = daily_data[date_col].dt.dayofweek
                daily_data['day_name'] = daily_data[date_col].dt.day_name()
                
                # 요일별 평균 커밋 수
                day_avg = daily_data.groupby('day_of_week').agg({
                    count_col: ['mean', 'sum', 'count']
                })
                
                day_avg.columns = ['_'.join(col).strip('_') for col in day_avg.columns.values]
                day_avg = day_avg.reset_index()
                
                # 요일 이름 매핑
                day_names = {
                    0: '월요일',
                    1: '화요일',
                    2: '수요일',
                    3: '목요일',
                    4: '금요일',
                    5: '토요일',
                    6: '일요일'
                }
                
                day_avg['day_name'] = day_avg['day_of_week'].map(day_names)
                
                # 그래프 생성 - 요일별 평균 커밋 수
                fig = px.bar(
                    day_avg,
                    x='day_name',
                    y='count_mean',
                    title='요일별 평균 커밋 수',
                    labels={'day_name': '요일', 'count_mean': '평균 커밋 수'},
                    color='count_mean',
                    color_continuous_scale=px.colors.sequential.Viridis,
                    category_orders={"day_name": [day_names[i] for i in range(7)]}
                )
                
                fig.update_layout(
                    xaxis_title='요일',
                    yaxis_title='평균 커밋 수'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("일별 커밋 데이터의 형식이 올바르지 않습니다.")
        else:
            st.info("일별 커밋 데이터를 찾을 수 없습니다.")
        
        # 시간대별 활동 패턴
        st.markdown('<div class="sub-header">시간대별 활동 패턴</div>', unsafe_allow_html=True)
        
        if 'hour_counts' in self.data and not self.data['hour_counts'].empty:
            # 데이터 준비
            hour_data = self.data['hour_counts'].copy()
            
            # 그래프 생성 - 시간대별 커밋 수
            fig = px.bar(
                hour_data,
                x='hour_of_day',
                y='0',
                title='시간대별 커밋 분포',
                labels={'hour_of_day': '시간 (24시간)', '0': '커밋 수'},
                color='0',
                color_continuous_scale=px.colors.sequential.Blues
            )
            
            fig.update_layout(
                xaxis=dict(
                    tickmode='linear',
                    tick0=0,
                    dtick=2,
                    title='시간 (24시간)'
                ),
                yaxis_title='커밋 수'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 피크 시간 찾기
            peak_hour = hour_data.iloc[:, 0].idxmax()
            peak_value = hour_data.iloc[:, 0].max()
            
            # 활동이 많은/적은 시간대 식별
            active_hours = hour_data.sort_values('0', ascending=False).head(3).index.tolist()
            quiet_hours = hour_data.sort_values('0').head(3).index.tolist()
            
            # 인사이트 표시
            st.markdown(f"""
            <div class="card">
                <p><span class="bold-text">시간대 인사이트:</span></p>
                <ul>
                    <li>가장 활발한 시간대: {peak_hour}시 (총 {peak_value}개 커밋)</li>
                    <li>활동이 많은 상위 3개 시간대: {', '.join([f"{h}시" for h in active_hours])}</li>
                    <li>활동이 적은 상위 3개 시간대: {', '.join([f"{h}시" for h in quiet_hours])}</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("시간대별 활동 패턴 데이터를 찾을 수 없습니다.")
        
        # 요일-시간 히트맵
        st.markdown('<div class="sub-header">요일-시간 히트맵</div>', unsafe_allow_html=True)
        
        if 'day_hour_counts' in self.data and not self.data['day_hour_counts'].empty:
            # 데이터 준비
            heatmap_data = self.data['day_hour_counts'].copy()
            
            try:
                # 히트맵 열 확인
                st.write("히트맵 데이터 형태:", heatmap_data.shape)
                
                # Plotly 히트맵 생성
                fig = px.imshow(
                    heatmap_data.values,
                    labels=dict(x="시간 (24시간)", y="요일", color="커밋 수"),
                    x=list(range(heatmap_data.shape[1])),  # 열 수에 맞게 인덱스 생성
                    y=["월", "화", "수", "목", "금", "토", "일"][:heatmap_data.shape[0]],  # 행 수에 맞게 인덱스 생성
                    title="요일-시간대별 커밋 분포 히트맵",
                    color_continuous_scale='YlGnBu'
                )
                
                fig.update_layout(
                    xaxis=dict(
                        tickmode='linear',
                        tick0=0,
                        dtick=2
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # 인사이트 계산
                # 평일/주말 비교
                weekday_data = 0
                weekend_data = 0
                
                # 행 수 확인하여 안전하게 계산
                if heatmap_data.shape[0] >= 5:
                    weekday_data = heatmap_data.iloc[:5].sum().sum()  # 월-금
                
                    if heatmap_data.shape[0] >= 7:
                        weekend_data = heatmap_data.iloc[5:7].sum().sum()  # 토-일
                
                total_commits = weekday_data + weekend_data
                weekday_pct = (weekday_data / total_commits) * 100 if total_commits > 0 else 0
                weekend_pct = (weekend_data / total_commits) * 100 if total_commits > 0 else 0
                
                # 업무 시간/비업무 시간 비교
                work_hours = list(range(9, 18))  # 9시-17시
                work_time_data = 0
                
                # 열 범위 체크하고 안전하게 계산
                valid_work_hours = [h for h in work_hours if h < heatmap_data.shape[1]]
                if valid_work_hours:
                    work_time_data = heatmap_data.iloc[:, valid_work_hours].sum().sum()
                
                non_work_time_data = total_commits - work_time_data
                
                work_time_pct = (work_time_data / total_commits) * 100 if total_commits > 0 else 0
                non_work_time_pct = (non_work_time_data / total_commits) * 100 if total_commits > 0 else 0
                
                # 인사이트 표시
                st.markdown(f"""
                <div class="card">
                    <p><span class="bold-text">활동 패턴 인사이트:</span></p>
                    <ul>
                        <li>평일 활동: {weekday_pct:.1f}% ({int(weekday_data)} 커밋)</li>
                        <li>주말 활동: {weekend_pct:.1f}% ({int(weekend_data)} 커밋)</li>
                        <li>업무 시간 활동 (9-17시): {work_time_pct:.1f}% ({int(work_time_data)} 커밋)</li>
                        <li>비업무 시간 활동: {non_work_time_pct:.1f}% ({int(non_work_time_data)} 커밋)</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                
                # 개발자 행동 패턴 해석
                work_oriented = work_time_pct > 65
                weekend_active = weekend_pct > 25
                
                pattern_description = ""
                
                if work_oriented and not weekend_active:
                    pattern_description = "개발자들이 주로 평일 업무 시간에 활동하는 전통적인 작업 패턴을 보입니다."
                elif work_oriented and weekend_active:
                    pattern_description = "개발자들이 업무 시간에 집중적으로 활동하면서도 주말에도 상당한 활동을 보이는 균형잡힌 패턴입니다."
                elif not work_oriented and weekend_active:
                    pattern_description = "개발자들이 비업무 시간과 주말에 활발하게 활동하는 비전통적인 작업 패턴을 보입니다."
                else:
                    pattern_description = "개발자들이 업무 시간 외에도 많은 활동을 하는 유연한 작업 패턴을 보입니다."
                
                st.markdown(f"""
                <div class="highlight">
                    <p><span class="bold-text">개발 패턴 해석:</span> {pattern_description}</p>
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"히트맵 처리 중 오류 발생: {str(e)}")
                st.write("히트맵 데이터 미리보기:")
                st.write(heatmap_data.head())
        else:
            st.info("요일-시간 히트맵 데이터를 찾을 수 없습니다.")
    
    def show_clustering(self):
        """개발자 클러스터링 페이지"""
        st.markdown('<div class="sub-header">개발자 클러스터링 분석</div>', unsafe_allow_html=True)
        
        if ('dev_profiles' not in self.data or self.data['dev_profiles'].empty or
            'cluster_profiles' not in self.data or self.data['cluster_profiles'].empty):
            st.warning("개발자 클러스터링 데이터를 찾을 수 없습니다.")
            return
        
        # 클러스터링 개요
        st.markdown('<div class="sub-header">클러스터링 개요</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="card">
        <p>개발자 클러스터링은 유사한 행동 패턴과 특성을 가진 개발자들을 그룹화합니다.
        각 클러스터의 특성을 분석하여 개발자 "유형"을 식별하고 이해할 수 있습니다.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 클러스터 수 및 개발자 수
        n_clusters = len(self.data['cluster_profiles'])
        n_developers = len(self.data['dev_profiles'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("클러스터 수", f"{n_clusters}")
        
        with col2:
            st.metric("분석된 개발자 수", f"{n_developers}")
        
        # 클러스터 분포
        cluster_dist = self.data['dev_profiles']['cluster'].value_counts().sort_index()
        
        # 클러스터 분포 차트
        fig = px.pie(
            values=cluster_dist.values,
            names=cluster_dist.index,
            title='클러스터별 개발자 분포',
            labels={'names': '클러스터', 'values': '개발자 수'},
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_traces(textinfo='percent+label')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 클러스터별 특성 분석
        st.markdown('<div class="sub-header">클러스터별 특성 분석</div>', unsafe_allow_html=True)
        
        # 클러스터 프로필
        cluster_profiles = self.data['cluster_profiles']
        
        # 각 클러스터별 주요 특성 표시
        for cluster in range(n_clusters):
            if cluster in cluster_profiles.index:
                cluster_data = cluster_profiles.loc[cluster]
                
                st.markdown(f"""
                <div class="card">
                <h3>클러스터 {cluster} 특성</h3>
                """, unsafe_allow_html=True)
                
                # 주요 특성 선택
                key_features = [
                    ('commit_count', '평균 커밋 수'),
                    ('message_length', '평균 메시지 길이'),
                    ('hour_of_day', '주요 활동 시간대'),
                    ('commit_count', '평균 커밋 수')
                ]
                
                # 코드 변경 특성 추가
                for col in ['additions', 'deletions', 'total_changes', 'files_changed']:
                    if col in cluster_data:
                        key_features.append((col, f'평균 {col}'))
                
                # PR 관련 특성 추가
                for col in ['pr_count', 'merge_rate', 'pr_processing_time']:
                    if col in cluster_data:
                        key_features.append((col, f'평균 {col}'))
                
                # 클러스터 특성 테이블 생성
                feature_data = []
                
                for feature_name, feature_label in key_features:
                    if feature_name in cluster_data:
                        feature_data.append({
                            '특성': feature_label,
                            '값': round(cluster_data[feature_name], 2)
                        })
                
                # 테이블 표시
                if feature_data:
                    st.dataframe(pd.DataFrame(feature_data), use_container_width=True, hide_index=True)
                
                # 클러스터에 속한 대표적인 개발자
                cluster_devs = self.data['dev_profiles'][self.data['dev_profiles']['cluster'] == cluster]
                
                if not cluster_devs.empty:
                    # 커밋 수 기준 상위 5명
                    top_cluster_devs = cluster_devs.sort_values('commit_count', ascending=False).head(5)
                    
                    st.markdown(f"""
                    <p><span class="bold-text">대표 개발자:</span> {', '.join(top_cluster_devs.index)}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("</div>", unsafe_allow_html=True)
        
        # 클러스터 시각화
        st.markdown('<div class="sub-header">클러스터 시각화</div>', unsafe_allow_html=True)
        
        # PCA 결과가 있는지 확인
        if 'pca_x' in self.data['dev_profiles'].columns and 'pca_y' in self.data['dev_profiles'].columns:
            # 데이터 준비
            vis_data = self.data['dev_profiles'].copy()
            
            # 그래프 생성
            fig = px.scatter(
                vis_data,
                x='pca_x',
                y='pca_y',
                color='cluster',
                size='commit_count',
                hover_name=vis_data.index,
                title='개발자 클러스터 시각화 (PCA)',
                labels={'pca_x': '주성분 1', 'pca_y': '주성분 2', 'cluster': '클러스터'},
                color_discrete_sequence=px.colors.qualitative.Set1
            )
            
            fig.update_layout(
                xaxis_title='주성분 1',
                yaxis_title='주성분 2',
                legend_title='클러스터'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 클러스터 해석
            st.markdown('<div class="sub-header">클러스터 해석</div>', unsafe_allow_html=True)
            
            # 클러스터 특성 기반 개발자 유형 해석
            cluster_interpretations = {}
            
            for cluster in range(n_clusters):
                if cluster in cluster_profiles.index:
                    data = cluster_profiles.loc[cluster]
                    
                    # 클러스터 특성 분석
                    commit_freq = data.get('commit_count', 0)
                    
                    # 커밋 빈도 기준 해석
                    if commit_freq > 50:
                        activity_level = "매우 활발한"
                    elif commit_freq > 20:
                        activity_level = "활발한"
                    else:
                        activity_level = "간헐적인"
                    
                    # 시간대 기준 해석
                    hour = data.get('hour_of_day', 12)
                    if 9 <= hour <= 17:
                        time_pattern = "업무 시간"
                    elif hour < 6 or hour > 21:
                        time_pattern = "야간"
                    else:
                        time_pattern = "일반적인"
                    
                    # 코드 변경 패턴 해석
                    if 'additions' in data and 'deletions' in data:
                        ratio = data['additions'] / (data['deletions'] + 1)  # 0으로 나누기 방지
                        
                        if ratio > 3:
                            code_pattern = "새 코드 작성 중심"
                        elif ratio < 0.5:
                            code_pattern = "리팩토링/정리 중심"
                        else:
                            code_pattern = "균형잡힌 코드 작성"
                    else:
                        code_pattern = "일반적인 코드 작성"
                    
                    # PR 패턴 해석
                    pr_pattern = ""
                    if 'merge_rate' in data:
                        if data['merge_rate'] > 0.8:
                            pr_pattern = "높은 PR 승인율"
                        elif data['merge_rate'] < 0.5:
                            pr_pattern = "낮은 PR 승인율"
                    
                    # 조합하여 클러스터 해석
                    interpretation = f"{activity_level} 활동, {time_pattern} 작업, {code_pattern}"
                    if pr_pattern:
                        interpretation += f", {pr_pattern}"
                    
                    cluster_interpretations[cluster] = interpretation
            
            # 해석 표시
            for cluster, interpretation in cluster_interpretations.items():
                st.markdown(f"""
                <div class="highlight">
                <p><span class="bold-text">클러스터 {cluster} 개발자 유형:</span> {interpretation}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("클러스터 시각화에 필요한 PCA 데이터를 찾을 수 없습니다.")
    
    def show_pr_prediction(self):
        """PR 승인 예측 페이지"""
        st.markdown('<div class="sub-header">PR 승인 예측 모델</div>', unsafe_allow_html=True)
        
        # 모델 평가 데이터 확인
        if 'model_evaluation' not in self.data:
            st.warning("PR 승인 예측 모델 데이터를 찾을 수 없습니다.")
            return
        
        # 모델 개요
        st.markdown("""
        <div class="card">
        <p>이 모델은 PR의 다양한 특성을 기반으로 PR이 승인(병합)될 확률을 예측합니다.
        코드 변경 크기, 파일 수, 코멘트 수, 제출 시간 등의 특성을 사용합니다.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 모델 성능 지표
        eval_data = self.data['model_evaluation']
        
        accuracy = eval_data.get('accuracy', 0)
        report = eval_data.get('report', {})
        
        # 성능 지표 표시
        st.markdown('<div class="sub-header">모델 성능</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("정확도", f"{accuracy:.2%}")
        
        with col2:
            if 'weighted avg' in report and 'precision' in report['weighted avg']:
                st.metric("정밀도", f"{report['weighted avg']['precision']:.2%}")
            else:
                st.metric("정밀도", "N/A")
        
        with col3:
            if 'weighted avg' in report and 'recall' in report['weighted avg']:
                st.metric("재현율", f"{report['weighted avg']['recall']:.2%}")
            else:
                st.metric("재현율", "N/A")
        
        # 모델 사용해보기
        st.markdown('<div class="sub-header">PR 승인 확률 예측하기</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="card">
        <p>아래 양식에 PR 정보를 입력하여 승인 확률을 예측해 볼 수 있습니다.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 입력 폼
        with st.form("pr_prediction_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                additions = st.number_input("추가된 라인 수", min_value=0, value=100)
                deletions = st.number_input("삭제된 라인 수", min_value=0, value=20)
                changed_files = st.number_input("변경된 파일 수", min_value=1, value=3)
            
            with col2:
                comments = st.number_input("코멘트 수", min_value=0, value=2)
                title_length = st.slider("제목 길이", min_value=10, max_value=100, value=50)
                day_of_week = st.selectbox("요일", options=[
                    ("월요일", 0), 
                    ("화요일", 1), 
                    ("수요일", 2), 
                    ("목요일", 3), 
                    ("금요일", 4), 
                    ("토요일", 5), 
                    ("일요일", 6)
                ], format_func=lambda x: x[0])
                hour_of_day = st.slider("시간대 (24시간)", min_value=0, max_value=23, value=14)
            
            submit_button = st.form_submit_button("예측하기")
        
        # 예측 버튼이 클릭되면
        if submit_button:
            st.markdown("### 예측 결과")
            
            # 실제 모델이 있는 경우 사용, 없으면 데모 결과 표시
            if os.path.exists(os.path.join(MODELS_DIR, 'pr_approval_model.pkl')):
                # 모델 로드
                model = joblib.load(os.path.join(MODELS_DIR, 'pr_approval_model.pkl'))
                
                # 입력 데이터 준비
                input_data = np.array([[
                    additions, deletions, changed_files, comments, 
                    title_length, day_of_week[1], hour_of_day
                ]])
                
                # 예측
                prediction = model.predict(input_data)[0]
                probability = model.predict_proba(input_data)[0][1]
                
                # 결과 표시
                if prediction:
                    st.success(f"이 PR은 승인될 가능성이 높습니다! (확률: {probability:.2%})")
                else:
                    st.error(f"이 PR은 거부될 가능성이 있습니다. (확률: {1-probability:.2%})")
            else:
                # 데모 결과 (모델이 없는 경우)
                import random
                probability = random.uniform(0.6, 0.95)
                st.success(f"이 PR은 승인될 가능성이 높습니다! (확률: {probability:.2%})")
                
                st.info("참고: 이것은 데모 결과입니다. 실제 모델 파일을 찾을 수 없습니다.")
            
            # 입력값 기반 제안
            st.markdown('<div class="sub-header">PR 개선 제안</div>', unsafe_allow_html=True)
            
            suggestions = []
            
            if additions + deletions > 300:
                suggestions.append("PR 크기가 큽니다. 가능하면 더 작은 단위로 분할하는 것이 좋습니다.")
            
            if changed_files > 10:
                suggestions.append("변경된 파일 수가 많습니다. 관련 변경사항끼리 그룹화하여 여러 PR로 나누는 것을 고려하세요.")
            
            if comments < 1:
                suggestions.append("코멘트가 없습니다. PR 설명에 충분한 정보를 추가하여 리뷰어의 이해를 돕는 것이 좋습니다.")
            
            if day_of_week[1] >= 5:  # 주말
                suggestions.append("주말에 제출된 PR은 리뷰 시간이 더 오래 걸릴 수 있습니다.")
            
            if hour_of_day < 9 or hour_of_day > 17:
                suggestions.append("업무 시간 외에 제출된 PR은 리뷰 시간이 더 오래 걸릴 수 있습니다.")
            
            if suggestions:
                st.markdown("""
                <div class="highlight">
                <p><span class="bold-text">PR 개선 제안:</span></p>
                <ul>
                """ + "".join([f"<li>{s}</li>" for s in suggestions]) + """
                </ul>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="highlight">
                <p>이 PR은 이미 좋은 구조를 가지고 있습니다. 특별한 개선 제안이 없습니다.</p>
                </div>
                """, unsafe_allow_html=True)
            
        # 특성 중요도
        st.markdown('<div class="sub-header">특성 중요도</div>', unsafe_allow_html=True)
        
        # 특성 중요도 이미지 표시 (이미지가 있는 경우)
        importance_img_path = os.path.join(MODELS_DIR, 'feature_importance.png')
        
        if os.path.exists(importance_img_path):
            st.image(importance_img_path, caption="PR 승인 예측에 영향을 미치는 특성들의 중요도", use_column_width=True)
        else:
            # 데모 특성 중요도 (이미지가 없는 경우)
            st.info("특성 중요도 이미지를 찾을 수 없습니다. 대신 샘플 데이터를 표시합니다.")
            
            # 샘플 특성 중요도 데이터
            importance_data = {
                'feature': ['additions', 'deletions', 'changed_files', 'comments', 'title_length', 'day_of_week', 'hour_of_day'],
                'importance': [0.35, 0.25, 0.18, 0.12, 0.05, 0.03, 0.02]
            }
            
            # 데이터프레임 생성
            importance_df = pd.DataFrame(importance_data).sort_values('importance', ascending=False)
            
            # 그래프 생성
            fig = px.bar(
                importance_df,
                x='importance',
                y='feature',
                orientation='h',
                title='PR 승인 예측에 대한 특성 중요도',
                labels={'importance': '중요도', 'feature': '특성'},
                color='importance',
                color_continuous_scale=px.colors.sequential.Viridis
            )
            
            fig.update_layout(
                xaxis_title='중요도',
                yaxis_title='특성',
                yaxis={'categoryorder': 'total ascending'}
            )
            
            st.plotly_chart(fig, use_container_width=True)

def main():
    """대시보드 메인 함수"""
    # 대시보드 인스턴스 생성
    dashboard = GitHubAnalysisDashboard()
    
    # 대시보드 실행
    dashboard.run_dashboard()

if __name__ == "__main__":
    main()
