#!/usr/bin/env python3
# enhanced_dashboard.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import json
from datetime import datetime, timedelta
from github import Github
import asyncio
import time
from typing import Dict, List, Optional
from collections import Counter
import logging

# 기존 코드에서 필요한 함수들 import
from realtime_analyzer import RealtimeGitHubAnalyzer, display_analysis_results

# 디렉토리 설정
RESULTS_DIR = "results"
DATA_DIR = "data"
MODELS_DIR = os.path.join(RESULTS_DIR, "models")

# 페이지 설정
st.set_page_config(
    page_title="GitHub 개발자 행동 패턴 분석기 Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

from dotenv import load_dotenv

# 명시적으로 .env 파일 로드
load_dotenv()

print("현재 작업 디렉토리:", os.getcwd())
print(".env 파일 존재:", os.path.exists('.env'))
github_token = os.getenv("GITHUB_TOKEN")
print("토큰 로드됨:", "예" if github_token else "아니오")
if github_token:
    print("토큰 길이:", len(github_token))
    print("토큰 시작:", github_token[:8] + "...")

# CSS 스타일링
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 600;
        color: #1E88E5;
        margin-bottom: 1rem;
        text-align: center;
    }
    .feature-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem;
        border-left: 4px solid #1E88E5;
    }
    .status-good { color: #28a745; }
    .status-warning { color: #ffc107; }
    .status-danger { color: #dc3545; }
</style>
""", unsafe_allow_html=True)

# 메인 함수
def main():
    # 헤더
    st.markdown('<div class="main-header">🚀 GitHub 개발자 행동 패턴 분석기 Pro</div>', unsafe_allow_html=True)
    
    # GitHub 토큰 확인
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        st.error("❌ GitHub 토큰이 설정되지 않았습니다. .env 파일에 GITHUB_TOKEN을 추가하세요.")
        st.info("💡 GitHub Personal Access Token이 필요합니다. [여기서 생성](https://github.com/settings/tokens)")
        return
    
    # 실시간 분석기 초기화
    if 'realtime_analyzer' not in st.session_state:
        st.session_state.realtime_analyzer = RealtimeGitHubAnalyzer(github_token)
    
    analyzer = st.session_state.realtime_analyzer
    
    # 사이드바 메뉴
    st.sidebar.image("https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png", width=80)
    st.sidebar.title("📋 분석 메뉴")
    
    # API 상태 확인
    rate_limit_info = analyzer.check_rate_limit()
    remaining_pct = (rate_limit_info['remaining'] / rate_limit_info['limit']) * 100
    
    if remaining_pct > 50:
        status_color = "status-good"
        status_icon = "🟢"
    elif remaining_pct > 20:
        status_color = "status-warning"
        status_icon = "🟡"
    else:
        status_color = "status-danger"
        status_icon = "🔴"
    
    st.sidebar.markdown(f"""
    **API 상태** {status_icon}
    <div class="{status_color}">
    남은 요청: {rate_limit_info['remaining']}/{rate_limit_info['limit']} ({remaining_pct:.1f}%)
    </div>
    """, unsafe_allow_html=True)
    
    # 페이지 선택
    page_options = [
        "🏠 홈",
        "🔍 실시간 저장소 검색",
        "⚡ 빠른 분석",
        "📊 기존 분석 결과",
        "🎯 저장소 비교",
        "🤖 AI 인사이트",
        "⚙️ 설정"
    ]
    
    selected_page = st.sidebar.radio("페이지 선택", page_options)
    
    # 페이지별 라우팅
    if selected_page == "🏠 홈":
        show_home_page()
    elif selected_page == "🔍 실시간 저장소 검색":
        show_realtime_search()
    elif selected_page == "⚡ 빠른 분석":
        show_quick_analysis()
    elif selected_page == "📊 기존 분석 결과":
        show_existing_results()
    elif selected_page == "🎯 저장소 비교":
        show_comparison_analysis()
    elif selected_page == "🤖 AI 인사이트":
        show_ai_insights()
    elif selected_page == "⚙️ 설정":
        show_settings()

def show_home_page():
    """홈 페이지"""
    st.markdown("## 🎯 분석 대시보드 개요")
    
    # 주요 기능 소개
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
        <h3>🔍 실시간 검색</h3>
        <p>GitHub 저장소를 실시간으로 검색하고 즉시 분석할 수 있습니다.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
        <h3>⚡ 빠른 분석</h3>
        <p>저장소 URL만 입력하면 몇 초 내에 종합 분석 결과를 확인할 수 있습니다.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
        <h3>🎯 비교 분석</h3>
        <p>여러 저장소를 동시에 비교하여 인사이트를 도출할 수 있습니다.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 최근 활동 요약
    st.markdown("## 📈 최근 분석 활동")
    
    # 기존 분석 결과 요약
    if os.path.exists(DATA_DIR):
        repos = [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("분석된 저장소", len(repos))
        
        with col2:
            # 개발자 수 계산
            dev_stats_file = os.path.join(RESULTS_DIR, 'developer_patterns', 'dev_stats.csv')
            dev_count = 0
            if os.path.exists(dev_stats_file):
                try:
                    dev_df = pd.read_csv(dev_stats_file)
                    dev_count = len(dev_df)
                except:
                    pass
            st.metric("분석된 개발자", dev_count)
        
        with col3:
            # 커밋 수 계산
            daily_file = os.path.join(RESULTS_DIR, 'time_patterns', 'daily_commits.csv')
            commit_count = 0
            if os.path.exists(daily_file):
                try:
                    daily_df = pd.read_csv(daily_file)
                    commit_count = daily_df['count'].sum()
                except:
                    pass
            st.metric("분석된 커밋", f"{int(commit_count):,}")
        
        with col4:
            # 마지막 분석 시간
            latest_time = "없음"
            try:
                results_files = []
                for root, dirs, files in os.walk(RESULTS_DIR):
                    for file in files:
                        if file.endswith('.csv'):
                            results_files.append(os.path.join(root, file))
                
                if results_files:
                    latest_file = max(results_files, key=os.path.getctime)
                    latest_time = datetime.fromtimestamp(os.path.getctime(latest_file)).strftime('%m-%d %H:%M')
            except:
                pass
            st.metric("마지막 분석", latest_time)
        
        # 저장소 목록
        if repos:
            st.markdown("### 📁 분석된 저장소")
            for repo in repos[:5]:  # 상위 5개만 표시
                repo_name = repo.replace("_", "/", 1)
                st.markdown(f"- {repo_name}")
            
            if len(repos) > 5:
                st.info(f"총 {len(repos)}개 저장소 중 5개만 표시됩니다. 전체 결과는 '기존 분석 결과' 페이지에서 확인하세요.")
    else:
        st.info("아직 분석된 저장소가 없습니다. 실시간 검색이나 빠른 분석을 시작해보세요!")
    
    # 빠른 시작 가이드
    st.markdown("## 🚀 빠른 시작")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **1단계: 저장소 검색**
        - 좌측 메뉴에서 '실시간 저장소 검색' 선택
        - 관심 있는 키워드로 검색
        - 결과에서 분석할 저장소 선택
        """)
    
    with col2:
        st.markdown("""
        **2단계: 빠른 분석**
        - '빠른 분석' 페이지로 이동
        - 저장소 URL 입력 (예: owner/repository)
        - 분석 결과 확인 및 인사이트 도출
        """)

def show_realtime_search():
    """실시간 저장소 검색 페이지"""
    st.markdown("## 🔍 실시간 GitHub 저장소 검색")
    
    analyzer = st.session_state.realtime_analyzer
    
    # 검색 폼
    with st.form("advanced_search"):
        st.markdown("### 검색 조건 설정")
        
        col1, col2 = st.columns(2)
        
        with col1:
            search_query = st.text_input("🔎 검색어", placeholder="예: machine learning, react components")
            language = st.selectbox("💻 프로그래밍 언어", 
                                  ["모든 언어", "Python", "JavaScript", "TypeScript", "Java", 
                                   "C++", "C#", "Go", "Rust", "Swift", "Kotlin", "PHP", "Ruby"])
            
        with col2:
            min_stars = st.number_input("⭐ 최소 스타 수", min_value=0, value=500, step=100)
            max_results = st.slider("📋 최대 결과 수", min_value=5, max_value=30, value=15)
            sort_option = st.selectbox("🔢 정렬 기준", ["Stars (높은 순)", "최근 업데이트", "생성일"])
        
        # 고급 필터
        with st.expander("🔧 고급 필터 (선택사항)"):
            col3, col4 = st.columns(2)
            
            with col3:
                min_forks = st.number_input("🍴 최소 포크 수", min_value=0, value=0)
                topic_filter = st.text_input("🏷️ 토픽", placeholder="예: web, api, framework")
            
            with col4:
                created_after = st.date_input("📅 생성일 이후", 
                                            value=datetime.now() - timedelta(days=365*3))
                exclude_forks = st.checkbox("🚫 포크된 저장소 제외", value=True)
        
        search_button = st.form_submit_button("🔍 검색 시작", type="primary")
    
    # 검색 실행
    if search_button and search_query:
        with st.spinner("🔄 GitHub에서 저장소 검색 중..."):
            # 검색 쿼리 구성
            lang_filter = None if language == "모든 언어" else language
            
            try:
                results = analyzer.search_repositories(
                    query=search_query,
                    language=lang_filter,
                    min_stars=min_stars,
                    max_results=max_results
                )
                
                if results:
                    st.success(f"✅ {len(results)}개의 저장소를 찾았습니다!")
                    
                    # 필터링 옵션
                    col1, col2 = st.columns([3, 1])
                    
                    with col2:
                        view_mode = st.radio("표시 방식", ["카드뷰", "테이블뷰"])
                    
                    # 결과 표시
                    if view_mode == "카드뷰":
                        display_card_view(results, analyzer)
                    else:
                        display_table_view(results, analyzer)
                
                else:
                    st.warning("🤷 검색 결과가 없습니다. 다른 검색어나 조건을 시도해보세요.")
                    
            except Exception as e:
                st.error(f"❌ 검색 중 오류가 발생했습니다: {str(e)}")
    
    # 인기 검색어 제안
    st.markdown("### 💡 추천 검색어")
    
    popular_searches = [
        "machine learning", "web framework", "data visualization", 
        "mobile app", "cryptocurrency", "automation", "testing", "api"
    ]
    
    cols = st.columns(4)
    for i, search_term in enumerate(popular_searches):
        with cols[i % 4]:
            if st.button(f"🔎 {search_term}", key=f"popular_{i}"):
                st.experimental_set_query_params(search=search_term)
                st.rerun()

def display_card_view(results, analyzer):
    """카드 형태로 검색 결과 표시"""
    for i, repo in enumerate(results):
        with st.container():
            # 저장소 헤더
            col1, col2, col3 = st.columns([6, 2, 2])
            
            with col1:
                st.markdown(f"### 📦 {repo['full_name']}")
                st.markdown(f"**{repo['language']}** | ⭐ {repo['stars']:,} | 🍴 {repo['forks']:,}")
            
            with col2:
                freshness_days = (datetime.now() - repo['updated_at'].replace(tzinfo=None)).days
                if freshness_days < 7:
                    freshness_color = "🟢"
                elif freshness_days < 30:
                    freshness_color = "🟡"
                else:
                    freshness_color = "🔴"
                
                st.markdown(f"**업데이트** {freshness_color}")
                st.markdown(f"{freshness_days}일 전")
            
            with col3:
                if st.button(f"⚡ 빠른 분석", key=f"quick_analyze_{i}"):
                    st.session_state.selected_repo_for_analysis = repo['full_name']
                    st.switch_page("pages/quick_analysis.py")
            
            # 저장소 설명
            st.markdown(f"📝 {repo['description']}")
            
            # 추가 정보
            col4, col5, col6 = st.columns(3)
            
            with col4:
                st.markdown(f"**생성일:** {repo['created_at'].strftime('%Y-%m-%d')}")
            
            with col5:
                st.markdown(f"**[GitHub에서 보기]({repo['url']})**")
            
            with col6:
                if st.button(f"📊 상세 분석", key=f"detailed_analyze_{i}"):
                    with st.spinner("분석 중..."):
                        analysis = analyzer.quick_analyze_repository(repo['full_name'])
                        if analysis:
                            st.session_state[f"analysis_result_{i}"] = analysis
                            st.rerun()
            
            # 분석 결과 표시 (있는 경우)
            if f"analysis_result_{i}" in st.session_state:
                with st.expander("📈 분석 결과", expanded=True):
                    display_analysis_results(st.session_state[f"analysis_result_{i}"])
                    del st.session_state[f"analysis_result_{i}"]
            
            st.divider()

def display_table_view(results, analyzer):
    """테이블 형태로 검색 결과 표시"""
    # 데이터프레임 생성
    df_data = []
    for repo in results:
        freshness_days = (datetime.now() - repo['updated_at'].replace(tzinfo=None)).days
        df_data.append({
            '저장소': repo['full_name'],
            '설명': repo['description'][:100] + '...' if len(repo['description']) > 100 else repo['description'],
            '언어': repo['language'],
            'Stars': repo['stars'],
            'Forks': repo['forks'],
            '마지막 업데이트': f"{freshness_days}일 전",
            'URL': repo['url']
        })
    
    df = pd.DataFrame(df_data)
    
    # 선택 가능한 테이블
    selected_repos = st.multiselect(
        "분석할 저장소 선택",
        options=df['저장소'].tolist(),
        default=[]
    )
    
    # 테이블 표시
    st.dataframe(df, use_container_width=True)
    
    # 선택된 저장소 분석
    if selected_repos and st.button("선택된 저장소 분석"):
        for repo_name in selected_repos:
            with st.expander(f"📊 {repo_name} 분석 결과"):
                with st.spinner("분석 중..."):
                    analysis = analyzer.quick_analyze_repository(repo_name)
                    if analysis:
                        display_analysis_results(analysis)

def show_quick_analysis():
    """빠른 분석 페이지"""
    st.markdown("## ⚡ 빠른 저장소 분석")
    
    analyzer = st.session_state.realtime_analyzer
    
    # 저장소 입력
    col1, col2 = st.columns([3, 1])
    
    with col1:
        repo_input = st.text_input(
            "🔗 저장소 URL 또는 이름",
            placeholder="owner/repository (예: facebook/react, microsoft/vscode)",
            help="GitHub 저장소의 full name을 입력하세요"
        )
    
    with col2:
        days_back = st.selectbox("📅 분석 기간", [7, 14, 30, 60, 90], index=2)
    
    # 검색 페이지에서 선택된 저장소 확인
    if 'selected_repo_for_analysis' in st.session_state:
        repo_input = st.session_state.selected_repo_for_analysis
        del st.session_state.selected_repo_for_analysis
        st.info(f"선택된 저장소: {repo_input}")
    
    # 분석 옵션
    with st.expander("🔧 분석 옵션"):
        col3, col4 = st.columns(2)
        
        with col3:
            include_contributors = st.checkbox("👥 기여자 분석 포함", value=True)
            include_languages = st.checkbox("💻 언어 분석 포함", value=True)
        
        with col4:
            include_activity = st.checkbox("📈 활동 패턴 분석 포함", value=True)
            include_issues = st.checkbox("🐛 이슈/PR 분석 포함", value=True)
    
    # 분석 실행
    if st.button("🚀 분석 시작", type="primary") and repo_input:
        try:
            with st.spinner(f"🔄 {repo_input} 분석 중... (최대 30초 소요)"):
                # 진행률 표시
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("저장소 정보 가져오는 중...")
                progress_bar.progress(20)
                
                analysis = analyzer.quick_analyze_repository(repo_input, days_back)
                
                if analysis:
                    progress_bar.progress(100)
                    status_text.text("분석 완료!")
                    
                    time.sleep(0.5)  # 잠시 완료 메시지 표시
                    progress_bar.empty()
                    status_text.empty()
                    
                    # 분석 결과 표시
                    display_enhanced_analysis_results(analysis, include_contributors, 
                                                    include_languages, include_activity, include_issues)
                    
                    # 분석 결과 저장 옵션
                    if st.button("💾 분석 결과 저장"):
                        save_analysis_result(repo_input, analysis)
                        st.success("분석 결과가 저장되었습니다!")
                
                else:
                    st.error("❌ 분석에 실패했습니다. 저장소 이름을 확인해주세요.")
        
        except Exception as e:
            st.error(f"❌ 분석 중 오류가 발생했습니다: {str(e)}")
    
    # 최근 분석 히스토리
    show_recent_analysis_history()

def display_enhanced_analysis_results(analysis, include_contributors=True, 
                                    include_languages=True, include_activity=True, include_issues=True):
    """향상된 분석 결과 표시"""
    repo_info = analysis['repo_info']
    
    # 저장소 헤더
    st.markdown(f"# 📊 {repo_info['full_name']} 종합 분석")
    
    # 건강도 스코어 계산
    health_score = calculate_repo_health_score(analysis)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"**📝 설명:** {repo_info['description'] or '설명 없음'}")
        st.markdown(f"**🔗 링크:** [GitHub에서 보기](https://github.com/{repo_info['full_name']})")
    
    with col2:
        # 건강도 스코어 표시
        score_color = "🟢" if health_score >= 70 else "🟡" if health_score >= 40 else "🔴"
        st.metric("💊 저장소 건강도", f"{health_score}/100 {score_color}")
    
    with col3:
        # 인기도 표시
        popularity = min(100, (repo_info['stars'] / 1000) * 10)
        st.metric("🔥 인기도", f"{popularity:.1f}/100")
    
    # 기본 메트릭 (개선된 버전)
    st.markdown("### 📈 핵심 지표")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("⭐ Stars", f"{repo_info['stars']:,}")
    
    with col2:
        st.metric("🍴 Forks", f"{repo_info['forks']:,}")
    
    with col3:
        st.metric("📝 Open Issues", f"{repo_info['open_issues']:,}")
    
    with col4:
        days_since_creation = (datetime.now() - repo_info['created_at'].replace(tzinfo=None)).days
        st.metric("📅 개발 기간", f"{days_since_creation}일")
    
    with col5:
        days_since_update = (datetime.now() - repo_info['updated_at'].replace(tzinfo=None)).days
        freshness = "🟢 활발함" if days_since_update < 7 else "🟡 보통" if days_since_update < 30 else "🔴 비활성"
        st.metric("🔄 활성도", freshness)
    
    # 탭으로 구성된 상세 분석
    tabs = []
    tab_names = ["📊 개요"]
    
    if include_activity and analysis['recent_activity']:
        tab_names.append("📈 활동 패턴")
    
    if include_contributors and analysis['contributors']:
        tab_names.append("👥 기여자")
    
    if include_languages and analysis['languages']:
        tab_names.append("💻 언어")
    
    if include_issues:
        tab_names.append("🐛 이슈/PR")
    
    tab_names.append("🎯 권장사항")
    
    tabs = st.tabs(tab_names)
    
    tab_idx = 0
    
    # 개요 탭
    with tabs[tab_idx]:
        display_overview_tab(analysis)
        tab_idx += 1
    
    # 활동 패턴 탭
    if include_activity and analysis['recent_activity']:
        with tabs[tab_idx]:
            display_activity_tab(analysis)
            tab_idx += 1
    
    # 기여자 탭
    if include_contributors and analysis['contributors']:
        with tabs[tab_idx]:
            display_contributors_tab(analysis)
            tab_idx += 1
    
    # 언어 탭
    if include_languages and analysis['languages']:
        with tabs[tab_idx]:
            display_languages_tab(analysis)
            tab_idx += 1
    
    # 이슈/PR 탭
    if include_issues:
        with tabs[tab_idx]:
            display_issues_tab(analysis)
            tab_idx += 1
    
    # 권장사항 탭
    with tabs[tab_idx]:
        display_recommendations_tab(analysis)

def calculate_repo_health_score(analysis):
    """저장소 건강도 스코어 계산"""
    score = 0
    repo_info = analysis['repo_info']
    recent = analysis['recent_activity']
    
    # 최근 활동 (30점)
    if recent.get('commits_last_30_days', 0) > 0:
        score += min(30, recent['commits_last_30_days'] * 2)
    
    # 인기도 (25점)
    stars_score = min(25, (repo_info['stars'] / 1000) * 25)
    score += stars_score
    
    # 업데이트 빈도 (20점)
    if recent.get('last_commit_date'):
        days_ago = (datetime.now() - recent['last_commit_date'].replace(tzinfo=None)).days
        if days_ago < 7:
            score += 20
        elif days_ago < 30:
            score += 15
        elif days_ago < 90:
            score += 10
    
    # 커뮤니티 참여 (15점)
    if repo_info['forks'] > 10:
        score += min(15, (repo_info['forks'] / 100) * 15)
    
    # 문서화 및 이슈 관리 (10점)
    if repo_info['description']:
        score += 5
    
    if analysis['contributors'].get('total_contributors', 0) > 1:
        score += 5
    
    return min(100, int(score))

def display_overview_tab(analysis):
    """개요 탭 내용"""
    repo_info = analysis['repo_info']
    recent = analysis['recent_activity']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 프로젝트 정보")
        
        info_data = {
            "속성": ["생성일", "마지막 업데이트", "크기", "라이선스", "주 언어"],
            "값": [
                repo_info['created_at'].strftime('%Y-%m-%d'),
                repo_info['updated_at'].strftime('%Y-%m-%d'),
                f"{repo_info['size']:,} KB",
                "정보 없음",  # 라이선스 정보는 별도 API 호출 필요
                repo_info['language'] or "정보 없음"
            ]
        }
        
        st.dataframe(pd.DataFrame(info_data), use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("#### 📈 최근 30일 활동")
        
        if recent:
            activity_data = {
                "지표": ["커밋 수", "일평균 커밋", "기여자 수"],
                "값": [
                    recent.get('commits_last_30_days', 0),
                    f"{recent.get('avg_commits_per_day', 0):.1f}",
                    analysis['contributors'].get('total_contributors', 0)
                ]
            }
            
            st.dataframe(pd.DataFrame(activity_data), use_container_width=True, hide_index=True)
        else:
            st.info("최근 활동 데이터가 없습니다.")

def display_activity_tab(analysis):
    """활동 패턴 탭 내용"""
    patterns = analysis.get('commit_patterns', {})
    
    if not patterns:
        st.info("커밋 패턴 데이터가 없습니다.")
        return
    
    col1, col2 = st.columns(2)
    
    # 시간대별 활동
    with col1:
        if patterns.get('hourly_distribution'):
            hourly_data = patterns['hourly_distribution']
            
            fig = px.bar(
                x=list(hourly_data.keys()),
                y=list(hourly_data.values()),
                title="⏰ 시간대별 커밋 분포",
                labels={'x': '시간', 'y': '커밋 수'}
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    # 요일별 활동
    with col2:
        if patterns.get('daily_distribution'):
            daily_data = patterns['daily_distribution']
            
            # 요일 순서 정렬
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            sorted_daily = {day: daily_data.get(day, 0) for day in day_order}
            
            fig = px.bar(
                x=list(sorted_daily.keys()),
                y=list(sorted_daily.values()),
                title="📅 요일별 커밋 분포",
                labels={'x': '요일', 'y': '커밋 수'}
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    # 활동 인사이트
    if patterns.get('most_active_hour') is not None and patterns.get('most_active_day'):
        st.info(f"""
        🔥 **가장 활발한 개발 시간**: {patterns['most_active_hour']}시  
        📅 **가장 활발한 요일**: {patterns['most_active_day']}
        """)

def display_contributors_tab(analysis):
    """기여자 탭 내용"""
    contributors = analysis.get('contributors', {})
    
    if not contributors:
        st.info("기여자 데이터가 없습니다.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 👥 기여자 통계")
        st.metric("총 기여자 수", contributors['total_contributors'])
        
        # 상위 기여자 테이블
        if contributors.get('top_contributors'):
            contrib_df = pd.DataFrame([
                {'기여자': k, '커밋 수': v, '기여도': f"{(v/sum(contributors['top_contributors'].values()))*100:.1f}%"}
                for k, v in contributors['top_contributors'].items()
            ])
            
            st.markdown("#### 🏆 상위 기여자")
            st.dataframe(contrib_df, use_container_width=True, hide_index=True)
    
    with col2:
        # 기여자 분포 차트
        if contributors.get('top_contributors'):
            fig = px.pie(
                values=list(contributors['top_contributors'].values()),
                names=list(contributors['top_contributors'].keys()),
                title="기여자별 커밋 분포"
            )
            st.plotly_chart(fig, use_container_width=True)

def display_languages_tab(analysis):
    """언어 탭 내용"""
    languages = analysis.get('languages', {})
    
    if not languages:
        st.info("언어 정보가 없습니다.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 언어별 코드 비율
        lang_df = pd.DataFrame([
            {
                '언어': lang,
                '코드량 (bytes)': f"{info['bytes']:,}",
                '비율': f"{info['percentage']:.1f}%"
            }
            for lang, info in languages.items()
        ])
        
        st.markdown("#### 💻 언어별 통계")
        st.dataframe(lang_df, use_container_width=True, hide_index=True)
    
    with col2:
        # 언어 분포 파이 차트
        percentages = [info['percentage'] for info in languages.values()]
        lang_names = list(languages.keys())
        
        fig = px.pie(
            values=percentages,
            names=lang_names,
            title="언어별 코드 분포"
        )
        st.plotly_chart(fig, use_container_width=True)

def display_issues_tab(analysis):
    """이슈/PR 탭 내용"""
    recent = analysis.get('recent_activity', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🐛 이슈 현황")
        if 'open_issues' in recent:
            st.metric("열린 이슈", recent['open_issues'])
        if 'closed_issues' in recent:
            st.metric("닫힌 이슈", recent['closed_issues'])
    
    with col2:
        st.markdown("#### 🔄 PR 현황")
        if 'open_prs' in recent:
            st.metric("열린 PR", recent['open_prs'])
        if 'closed_prs' in recent:
            st.metric("닫힌 PR", recent['closed_prs'])

def display_recommendations_tab(analysis):
    """권장사항 탭 내용"""
    repo_info = analysis['repo_info']
    recent = analysis['recent_activity']
    contributors = analysis.get('contributors', {})
    
    recommendations = []
    
    # 활동성 관련 권장사항
    if recent.get('commits_last_30_days', 0) == 0:
        recommendations.append("🔴 최근 30일간 커밋이 없습니다. 프로젝트가 비활성 상태일 수 있습니다.")
    elif recent.get('commits_last_30_days', 0) < 5:
        recommendations.append("🟡 커밋 활동이 저조합니다. 정기적인 업데이트를 고려해보세요.")
    else:
        recommendations.append("🟢 활발한 개발 활동을 보이고 있습니다!")
    
    # 커뮤니티 관련 권장사항
    if repo_info['stars'] < 10:
        recommendations.append("📣 프로젝트 홍보를 통해 더 많은 관심을 받아보세요.")
    
    if contributors.get('total_contributors', 0) == 1:
        recommendations.append("👥 다른 개발자들의 기여를 유도해보세요. 이슈 레이블링이나 기여 가이드 작성을 고려해보세요.")
    
    # 문서화 관련 권장사항
    if not repo_info['description']:
        recommendations.append("📝 프로젝트 설명을 추가하여 다른 개발자들이 이해하기 쉽게 만드세요.")
    
    # 이슈 관리 관련 권장사항
    if repo_info['open_issues'] > 50:
        recommendations.append("🐛 열린 이슈가 많습니다. 이슈 정리나 우선순위 관리를 고려해보세요.")
    
    # 권장사항 표시
    st.markdown("### 🎯 맞춤 권장사항")
    
    for i, rec in enumerate(recommendations):
        st.markdown(f"{i+1}. {rec}")
    
    # 벤치마킹 정보
    st.markdown("### 📊 유사 프로젝트 벤치마킹")
    
    if repo_info['language']:
        similar_metrics = get_language_benchmarks(repo_info['language'])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            current_stars = repo_info['stars']
            avg_stars = similar_metrics.get('avg_stars', 0)
            stars_status = "🟢 평균 이상" if current_stars > avg_stars else "🟡 평균 이하"
            st.metric("Stars 비교", stars_status, f"평균: {avg_stars:,}")
        
        with col2:
            current_forks = repo_info['forks']
            avg_forks = similar_metrics.get('avg_forks', 0)
            forks_status = "🟢 평균 이상" if current_forks > avg_forks else "🟡 평균 이하"
            st.metric("Forks 비교", forks_status, f"평균: {avg_forks:,}")
        
        with col3:
            current_issues = repo_info['open_issues']
            avg_issues = similar_metrics.get('avg_issues', 0)
            issues_status = "🟢 잘 관리됨" if current_issues < avg_issues else "🟡 관리 필요"
            st.metric("Issues 비교", issues_status, f"평균: {avg_issues:,}")

def get_language_benchmarks(language):
    """언어별 벤치마크 데이터 (예시)"""
    benchmarks = {
        'Python': {'avg_stars': 500, 'avg_forks': 100, 'avg_issues': 20},
        'JavaScript': {'avg_stars': 800, 'avg_forks': 150, 'avg_issues': 25},
        'TypeScript': {'avg_stars': 600, 'avg_forks': 120, 'avg_issues': 18},
        'Java': {'avg_stars': 400, 'avg_forks': 80, 'avg_issues': 15},
        'Go': {'avg_stars': 300, 'avg_forks': 60, 'avg_issues': 12},
        'Rust': {'avg_stars': 350, 'avg_forks': 70, 'avg_issues': 10},
    }
    
    return benchmarks.get(language, {'avg_stars': 100, 'avg_forks': 20, 'avg_issues': 10})

def show_recent_analysis_history():
    """최근 분석 히스토리 표시"""
    st.markdown("### 📚 최근 분석 히스토리")
    
    if 'analysis_history' not in st.session_state:
        st.session_state.analysis_history = []
    
    history = st.session_state.analysis_history
    
    if history:
        for i, item in enumerate(history[-5:]):  # 최근 5개만 표시
            with st.expander(f"📊 {item['repo']} - {item['timestamp']}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Stars", f"{item['stars']:,}")
                
                with col2:
                    st.metric("Commits", item['commits'])
                
                with col3:
                    st.metric("Contributors", item['contributors'])
                
                if st.button(f"다시 분석", key=f"reanalyze_{i}"):
                    st.session_state.selected_repo_for_analysis = item['repo']
                    st.rerun()
    else:
        st.info("아직 분석 히스토리가 없습니다. 저장소를 분석해보세요!")

def save_analysis_result(repo_name, analysis):
    """분석 결과 저장"""
    if 'analysis_history' not in st.session_state:
        st.session_state.analysis_history = []
    
    # 히스토리에 추가
    history_item = {
        'repo': repo_name,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'stars': analysis['repo_info']['stars'],
        'commits': analysis['recent_activity'].get('commits_last_30_days', 0),
        'contributors': analysis['contributors'].get('total_contributors', 0)
    }
    
    st.session_state.analysis_history.append(history_item)
    
    # 최대 50개까지만 저장
    if len(st.session_state.analysis_history) > 50:
        st.session_state.analysis_history = st.session_state.analysis_history[-50:]

def show_existing_results():
    """기존 분석 결과 페이지"""
    st.markdown("## 📊 기존 분석 결과")
    
    # 기존 분석 결과 로드 및 표시
    if not os.path.exists(DATA_DIR):
        st.info("아직 분석된 데이터가 없습니다.")
        return
    
    # 분석된 저장소 목록
    repos = [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]
    
    if not repos:
        st.info("분석된 저장소가 없습니다.")
        return
    
    st.markdown(f"### 📁 분석된 저장소 ({len(repos)}개)")
    
    # 저장소 선택
    selected_repo = st.selectbox("저장소 선택", repos, format_func=lambda x: x.replace("_", "/", 1))
    
    if selected_repo:
        repo_path = os.path.join(DATA_DIR, selected_repo)
        
        # 사용 가능한 분석 데이터 확인
        available_data = []
        
        if os.path.exists(os.path.join(repo_path, "commits.csv")):
            available_data.append("커밋 데이터")
        
        if os.path.exists(os.path.join(repo_path, "pull_requests.csv")):
            available_data.append("PR 데이터")
        
        if os.path.exists(os.path.join(repo_path, "issues.csv")):
            available_data.append("이슈 데이터")
        
        if available_data:
            st.success(f"사용 가능한 데이터: {', '.join(available_data)}")
            
            # 기존 대시보드 기능 통합
            display_legacy_dashboard(selected_repo)
        else:
            st.warning("선택된 저장소에 분석 데이터가 없습니다.")

def display_legacy_dashboard(repo_dir):
    """기존 분석 결과 대시보드"""
    st.markdown("### 📈 상세 분석 결과")
    
    # 여기에 기존 dashboard.py의 기능들을 통합
    # 간단한 버전으로 구현
    
    repo_path = os.path.join(DATA_DIR, repo_dir)
    
    # 커밋 데이터 분석
    commits_file = os.path.join(repo_path, "commits.csv")
    if os.path.exists(commits_file):
        try:
            commits_df = pd.read_csv(commits_file)
            
            st.markdown("#### 📊 커밋 분석")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("총 커밋 수", len(commits_df))
            
            with col2:
                unique_authors = commits_df['author_login'].nunique() if 'author_login' in commits_df.columns else 0
                st.metric("개발자 수", unique_authors)
            
            with col3:
                if 'date' in commits_df.columns:
                    commits_df['date'] = pd.to_datetime(commits_df['date'])
                    date_range = (commits_df['date'].max() - commits_df['date'].min()).days
                    st.metric("분석 기간", f"{date_range}일")
            
            # 시간별 커밋 분포
            if 'date' in commits_df.columns:
                commits_df['date'] = pd.to_datetime(commits_df['date'])
                daily_commits = commits_df.groupby(commits_df['date'].dt.date).size()
                
                fig = px.line(x=daily_commits.index, y=daily_commits.values, 
                            title="일별 커밋 추세")
                fig.update_layout(xaxis_title="날짜", yaxis_title="커밋 수")
                st.plotly_chart(fig, use_container_width=True)
        
        except Exception as e:
            st.error(f"커밋 데이터 로드 중 오류: {e}")

def show_comparison_analysis():
    """저장소 비교 분석 페이지"""
    st.markdown("## 🎯 저장소 비교 분석")
    
    analyzer = st.session_state.realtime_analyzer
    
    st.info("💡 두 개 이상의 저장소를 비교하여 인사이트를 도출할 수 있습니다.")
    
    # 비교할 저장소 입력
    with st.form("comparison_form"):
        st.markdown("### 비교할 저장소 입력")
        
        col1, col2 = st.columns(2)
        
        with col1:
            repo1 = st.text_input("저장소 1", placeholder="owner/repository")
            repo3 = st.text_input("저장소 3 (선택)", placeholder="owner/repository")
        
        with col2:
            repo2 = st.text_input("저장소 2", placeholder="owner/repository")
            repo4 = st.text_input("저장소 4 (선택)", placeholder="owner/repository")
        
        analysis_period = st.selectbox("분석 기간", [7, 14, 30, 60], index=2)
        
        compare_button = st.form_submit_button("🔄 비교 분석 시작", type="primary")
    
    if compare_button:
        repos_to_compare = [repo for repo in [repo1, repo2, repo3, repo4] if repo.strip()]
        
        if len(repos_to_compare) < 2:
            st.error("최소 2개의 저장소를 입력해주세요.")
            return
        
        # 각 저장소 분석
        comparison_results = {}
        
        for repo in repos_to_compare:
            with st.spinner(f"📊 {repo} 분석 중..."):
                analysis = analyzer.quick_analyze_repository(repo, analysis_period)
                if analysis:
                    comparison_results[repo] = analysis
                else:
                    st.error(f"❌ {repo} 분석에 실패했습니다.")
        
        if len(comparison_results) >= 2:
            display_comparison_results(comparison_results)
        else:
            st.error("비교할 수 있는 유효한 분석 결과가 부족합니다.")

def display_comparison_results(comparison_results):
    """비교 분석 결과 표시"""
    st.markdown("## 📊 비교 분석 결과")
    
    # 기본 메트릭 비교
    st.markdown("### ⚖️ 핵심 지표 비교")
    
    comparison_data = []
    
    for repo_name, analysis in comparison_results.items():
        repo_info = analysis['repo_info']
        recent = analysis['recent_activity']
        contributors = analysis.get('contributors', {})
        
        comparison_data.append({
            '저장소': repo_name,
            'Stars': repo_info['stars'],
            'Forks': repo_info['forks'],
            '언어': repo_info['language'] or 'Unknown',
            '최근 30일 커밋': recent.get('commits_last_30_days', 0),
            '기여자 수': contributors.get('total_contributors', 0),
            '열린 이슈': repo_info['open_issues']
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True)
    
    # 시각적 비교
    col1, col2 = st.columns(2)
    
    with col1:
        # Stars 비교
        fig = px.bar(comparison_df, x='저장소', y='Stars', 
                    title="⭐ Stars 비교", color='Stars')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 최근 활동 비교
        fig = px.bar(comparison_df, x='저장소', y='최근 30일 커밋', 
                    title="📈 최근 활동 비교", color='최근 30일 커밋')
        st.plotly_chart(fig, use_container_width=True)
    
    # 레이더 차트로 종합 비교
    st.markdown("### 🎯 종합 비교 (레이더 차트)")
    
    # 정규화된 점수 계산
    metrics = ['Stars', 'Forks', '최근 30일 커밋', '기여자 수']
    
    fig = go.Figure()
    
    for _, row in comparison_df.iterrows():
        # 각 메트릭을 0-100 스케일로 정규화
        normalized_values = []
        for metric in metrics:
            max_val = comparison_df[metric].max()
            if max_val > 0:
                normalized_values.append((row[metric] / max_val) * 100)
            else:
                normalized_values.append(0)
        
        fig.add_trace(go.Scatterpolar(
            r=normalized_values + [normalized_values[0]],  # 닫힌 도형을 위해 첫 값 반복
            theta=metrics + [metrics[0]],
            fill='toself',
            name=row['저장소']
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        title="저장소별 종합 성능 비교"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 승자 결정
    st.markdown("### 🏆 카테고리별 우승자")
    
    winners = {}
    for metric in ['Stars', 'Forks', '최근 30일 커밋', '기여자 수']:
        winner = comparison_df.loc[comparison_df[metric].idxmax(), '저장소']
        winners[metric] = winner
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**⭐ 인기도 (Stars):** {winners['Stars']}")
        st.markdown(f"**🍴 커뮤니티 (Forks):** {winners['Forks']}")
    
    with col2:
        st.markdown(f"**📈 활동성:** {winners['최근 30일 커밋']}")
        st.markdown(f"**👥 협업 (기여자):** {winners['기여자 수']}")

def show_ai_insights():
    """AI 인사이트 페이지"""
    st.markdown("## 🤖 AI 기반 인사이트")
    
    st.info("🚧 이 기능은 개발 중입니다. AI 모델을 통한 고급 분석 기능이 곧 추가될 예정입니다.")
    
    # 미래 기능 미리보기
    with st.expander("🔮 예정된 AI 기능들"):
        st.markdown("""
        ### 🎯 개발 예정 기능
        
        1. **📈 트렌드 예측**
           - 저장소의 미래 성장 예측
           - 기술 스택 트렌드 분석
        
        2. **🔍 코드 품질 분석**
           - AI 기반 코드 리뷰
           - 버그 예측 모델
        
        3. **💡 개선 제안**
           - 맞춤형 개발 전략 제안
           - 커뮤니티 성장 방안
        
        4. **🎨 자동 리포트 생성**
           - 주간/월간 프로젝트 리포트
           - 투자자용 분석 보고서
        """)

def show_settings():
    """설정 페이지"""
    st.markdown("## ⚙️ 설정")
    
    # API 설정
    st.markdown("### 🔑 API 설정")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # GitHub 토큰 상태 확인
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            masked_token = github_token[:8] + "..." + github_token[-4:]
            st.success(f"✅ GitHub 토큰 설정됨: {masked_token}")
        else:
            st.error("❌ GitHub 토큰이 설정되지 않았습니다.")
        
        # API 사용량 표시
        if 'realtime_analyzer' in st.session_state:
            rate_info = st.session_state.realtime_analyzer.check_rate_limit()
            st.info(f"남은 API 요청: {rate_info['remaining']}/{rate_info['limit']}")
    
    with col2:
        # 분석 기본값 설정
        st.markdown("#### 📊 분석 기본값")
        
        default_days = st.selectbox("기본 분석 기간", [7, 14, 30, 60, 90], index=2)
        default_max_results = st.slider("기본 검색 결과 수", 5, 50, 15)
        
        if st.button("💾 설정 저장"):
            st.session_state.default_days = default_days
            st.session_state.default_max_results = default_max_results
            st.success("설정이 저장되었습니다!")
    
    # 데이터 관리
    st.markdown("### 🗂️ 데이터 관리")
    
    col3, col4 = st.columns(2)
    
    with col3:
        if st.button("🗑️ 분석 히스토리 삭제"):
            if 'analysis_history' in st.session_state:
                del st.session_state.analysis_history
                st.success("분석 히스토리가 삭제되었습니다.")
    
    with col4:
        if st.button("📤 데이터 내보내기"):
            st.info("데이터 내보내기 기능은 곧 추가될 예정입니다.")
    
    # 정보
    st.markdown("### ℹ️ 시스템 정보")
    
    system_info = {
        "항목": ["Streamlit 버전", "Python 버전", "설치된 패키지"],
        "정보": ["1.45.1", "3.9+", "pandas, plotly, PyGithub 등"]
    }
    
    st.dataframe(pd.DataFrame(system_info), use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()