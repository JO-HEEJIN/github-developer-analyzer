#!/usr/bin/env python3
# realtime_analyzer.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from github import Github
import os
from datetime import datetime, timedelta
import asyncio
import concurrent.futures
import time
from typing import Dict, List, Optional
import json
import re
from collections import Counter
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealtimeGitHubAnalyzer:
    def __init__(self, github_token: str):
        """실시간 GitHub 분석기 초기화"""
        self.github = Github(github_token)
        self.rate_limit_buffer = 100  # API 속도 제한 버퍼
    
    def search_repositories(self, query: str, language: str = None, 
                          min_stars: int = 0, max_results: int = 10) -> List[Dict]:
        """저장소 검색"""
        try:
            # 검색 쿼리 구성
            search_query = f"{query}"
            if language:
                search_query += f" language:{language}"
            if min_stars > 0:
                search_query += f" stars:>={min_stars}"
            
            # 검색 실행
            repositories = self.github.search_repositories(
                query=search_query,
                sort="stars",
                order="desc"
            )
            
            # 결과 파싱
            results = []
            for i, repo in enumerate(repositories):
                if i >= max_results:
                    break
                
                results.append({
                    'name': repo.name,
                    'full_name': repo.full_name,
                    'description': repo.description or "설명 없음",
                    'stars': repo.stargazers_count,
                    'forks': repo.forks_count,
                    'language': repo.language or "Unknown",
                    'created_at': repo.created_at,
                    'updated_at': repo.updated_at,
                    'url': repo.html_url
                })
            
            return results
        
        except Exception as e:
            logger.error(f"저장소 검색 중 오류: {e}")
            return []
    
    def quick_analyze_repository(self, repo_name: str, days_back: int = 30) -> Dict:
        """저장소 빠른 분석"""
        try:
            repo = self.github.get_repo(repo_name)
            since_date = datetime.now() - timedelta(days=days_back)
            
            # 기본 정보
            analysis = {
                'repo_info': {
                    'name': repo.name,
                    'full_name': repo.full_name,
                    'description': repo.description,
                    'stars': repo.stargazers_count,
                    'forks': repo.forks_count,
                    'language': repo.language,
                    'created_at': repo.created_at,
                    'updated_at': repo.updated_at,
                    'open_issues': repo.open_issues_count,
                    'size': repo.size
                },
                'recent_activity': {},
                'contributors': {},
                'languages': {},
                'commit_patterns': {}
            }
            
            # 최근 커밋 분석 (빠른 분석을 위해 최대 100개)
            commits = list(repo.get_commits(since=since_date)[:100])
            
            if commits:
                # 커밋 통계
                commit_data = []
                authors = []
                commit_times = []
                
                for commit in commits:
                    if commit.author:
                        authors.append(commit.author.login)
                    if commit.commit.author:
                        commit_times.append(commit.commit.author.date)
                    
                    commit_data.append({
                        'author': commit.author.login if commit.author else 'Unknown',
                        'date': commit.commit.author.date if commit.commit.author else None,
                        'message': commit.commit.message,
                        'stats': commit.stats if hasattr(commit, 'stats') else None
                    })
                
                # 기여자 분석
                author_counts = Counter(authors)
                analysis['contributors'] = {
                    'total_contributors': len(set(authors)),
                    'top_contributors': dict(author_counts.most_common(5)),
                    'commit_distribution': dict(author_counts)
                }
                
                # 시간 패턴 분석
                if commit_times:
                    hours = [t.hour for t in commit_times if t]
                    days = [t.strftime('%A') for t in commit_times if t]
                    
                    analysis['commit_patterns'] = {
                        'hourly_distribution': dict(Counter(hours)),
                        'daily_distribution': dict(Counter(days)),
                        'most_active_hour': max(set(hours), key=hours.count) if hours else None,
                        'most_active_day': max(set(days), key=days.count) if days else None
                    }
                
                # 최근 활동
                analysis['recent_activity'] = {
                    'commits_last_30_days': len(commits),
                    'avg_commits_per_day': len(commits) / days_back,
                    'last_commit_date': commits[0].commit.author.date if commits[0].commit.author else None
                }
            
            # 언어 정보
            try:
                languages = repo.get_languages()
                total_bytes = sum(languages.values())
                analysis['languages'] = {
                    lang: {
                        'bytes': bytes_count,
                        'percentage': (bytes_count / total_bytes) * 100 if total_bytes > 0 else 0
                    }
                    for lang, bytes_count in languages.items()
                }
            except:
                analysis['languages'] = {}
            
            # PR 및 이슈 정보 (간단한 통계만)
            try:
                recent_prs = list(repo.get_pulls(state='all')[:20])
                recent_issues = list(repo.get_issues(state='all')[:20])
                
                analysis['recent_activity'].update({
                    'open_prs': len([pr for pr in recent_prs if pr.state == 'open']),
                    'closed_prs': len([pr for pr in recent_prs if pr.state == 'closed']),
                    'open_issues': len([issue for issue in recent_issues if issue.state == 'open' and not issue.pull_request]),
                    'closed_issues': len([issue for issue in recent_issues if issue.state == 'closed' and not issue.pull_request])
                })
            except:
                pass
            
            return analysis
        
        except Exception as e:
            logger.error(f"저장소 {repo_name} 분석 중 오류: {e}")
            return None
    
    def check_rate_limit(self) -> Dict:
        """API 속도 제한 확인"""
        rate_limit = self.github.get_rate_limit()
        return {
            'remaining': rate_limit.core.remaining,
            'limit': rate_limit.core.limit,
            'reset_time': rate_limit.core.reset
        }

def create_realtime_dashboard():
    """실시간 분석 대시보드 생성"""
    st.set_page_config(
        page_title="실시간 GitHub 저장소 분석기",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 실시간 GitHub 저장소 분석기")
    st.markdown("GitHub 저장소를 실시간으로 검색하고 분석하는 도구입니다.")
    
    # GitHub 토큰 확인
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        st.error("GitHub 토큰이 설정되지 않았습니다. .env 파일에 GITHUB_TOKEN을 추가하세요.")
        return
    
    # 분석기 초기화
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = RealtimeGitHubAnalyzer(github_token)
    
    analyzer = st.session_state.analyzer
    
    # API 속도 제한 정보 표시
    rate_limit_info = analyzer.check_rate_limit()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("API 요청 남음", rate_limit_info['remaining'])
    with col2:
        st.metric("API 제한", rate_limit_info['limit'])
    with col3:
        reset_time = rate_limit_info['reset_time'].strftime('%H:%M:%S')
        st.metric("리셋 시간", reset_time)
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["저장소 검색", "실시간 분석", "비교 분석"])
    
    with tab1:
        st.header("GitHub 저장소 검색")
        
        # 검색 폼
        with st.form("search_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                search_query = st.text_input("검색어", placeholder="예: machine learning, web framework")
                language = st.selectbox("언어 필터", 
                                      ["모든 언어", "Python", "JavaScript", "Java", "TypeScript", 
                                       "C++", "C#", "Go", "Rust", "Swift", "Kotlin"])
            
            with col2:
                min_stars = st.number_input("최소 스타 수", min_value=0, value=100)
                max_results = st.slider("최대 결과 수", min_value=5, max_value=50, value=10)
            
            search_button = st.form_submit_button("검색", type="primary")
        
        # 검색 실행
        if search_button and search_query:
            with st.spinner("저장소 검색 중..."):
                lang_filter = None if language == "모든 언어" else language
                results = analyzer.search_repositories(
                    query=search_query,
                    language=lang_filter,
                    min_stars=min_stars,
                    max_results=max_results
                )
            
            if results:
                st.success(f"{len(results)}개의 저장소를 찾았습니다!")
                
                # 결과 표시
                for i, repo in enumerate(results):
                    with st.expander(f"⭐ {repo['stars']} | {repo['full_name']} ({repo['language']})"):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"**설명:** {repo['description']}")
                            st.markdown(f"**생성일:** {repo['created_at'].strftime('%Y-%m-%d')}")
                            st.markdown(f"**마지막 업데이트:** {repo['updated_at'].strftime('%Y-%m-%d')}")
                            st.markdown(f"**링크:** [GitHub에서 보기]({repo['url']})")
                        
                        with col2:
                            st.metric("⭐ Stars", f"{repo['stars']:,}")
                            st.metric("🍴 Forks", f"{repo['forks']:,}")
                            
                            # 빠른 분석 버튼
                            if st.button(f"분석하기", key=f"analyze_{i}"):
                                st.session_state[f"analyze_repo_{i}"] = repo['full_name']
                                st.rerun()
            else:
                st.warning("검색 결과가 없습니다. 다른 검색어를 시도해보세요.")
    
    with tab2:
        st.header("실시간 저장소 분석")
        
        # 직접 저장소 입력
        repo_input = st.text_input("저장소 입력", placeholder="owner/repository (예: facebook/react)")
        days_back = st.slider("분석 기간 (일)", min_value=7, max_value=90, value=30)
        
        # 검색 탭에서 선택된 저장소 확인
        selected_repo = None
        for i in range(50):  # 최대 50개 결과 확인
            if f"analyze_repo_{i}" in st.session_state:
                selected_repo = st.session_state[f"analyze_repo_{i}"]
                del st.session_state[f"analyze_repo_{i}"]
                break
        
        repo_to_analyze = selected_repo or repo_input
        
        if repo_to_analyze:
            analyze_button = st.button("분석 시작", type="primary")
            
            if analyze_button:
                with st.spinner(f"{repo_to_analyze} 분석 중..."):
                    analysis = analyzer.quick_analyze_repository(repo_to_analyze, days_back)
                
                if analysis:
                    display_analysis_results(analysis)
                else:
                    st.error("분석에 실패했습니다. 저장소 이름을 확인해주세요.")
    
    with tab3:
        st.header("저장소 비교 분석")
        st.info("여러 저장소를 비교 분석하는 기능입니다. (개발 예정)")
        
        # 비교할 저장소 입력
        col1, col2 = st.columns(2)
        
        with col1:
            repo1 = st.text_input("저장소 1", placeholder="owner/repository")
        
        with col2:
            repo2 = st.text_input("저장소 2", placeholder="owner/repository")
        
        if st.button("비교 분석"):
            if repo1 and repo2:
                st.info("비교 분석 기능은 곧 추가될 예정입니다!")
            else:
                st.warning("두 저장소를 모두 입력해주세요.")

def display_analysis_results(analysis: Dict):
    """분석 결과 표시"""
    repo_info = analysis['repo_info']
    
    # 저장소 기본 정보
    st.markdown(f"## 📊 {repo_info['full_name']} 분석 결과")
    st.markdown(f"**설명:** {repo_info['description'] or '설명 없음'}")
    
    # 기본 메트릭
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("⭐ Stars", f"{repo_info['stars']:,}")
    with col2:
        st.metric("🍴 Forks", f"{repo_info['forks']:,}")
    with col3:
        st.metric("📝 Open Issues", f"{repo_info['open_issues']:,}")
    with col4:
        st.metric("💾 Size (KB)", f"{repo_info['size']:,}")
    
    # 최근 활동
    st.markdown("### 📈 최근 활동")
    recent = analysis['recent_activity']
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("최근 30일 커밋", recent.get('commits_last_30_days', 0))
    with col2:
        st.metric("일평균 커밋", f"{recent.get('avg_commits_per_day', 0):.1f}")
    with col3:
        if recent.get('last_commit_date'):
            days_ago = (datetime.now() - recent['last_commit_date'].replace(tzinfo=None)).days
            st.metric("마지막 커밋", f"{days_ago}일 전")
    
    # 언어 분포
    if analysis['languages']:
        st.markdown("### 💻 언어 분포")
        
        lang_data = []
        for lang, info in analysis['languages'].items():
            lang_data.append({
                'language': lang,
                'percentage': info['percentage']
            })
        
        lang_df = pd.DataFrame(lang_data)
        
        fig = px.pie(lang_df, values='percentage', names='language', 
                    title="언어별 코드 분포")
        st.plotly_chart(fig, use_container_width=True)
    
    # 기여자 정보
    if analysis['contributors']:
        st.markdown("### 👥 주요 기여자")
        contributors = analysis['contributors']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("총 기여자 수", contributors['total_contributors'])
            
            # 상위 기여자
            if contributors['top_contributors']:
                top_contrib_df = pd.DataFrame([
                    {'기여자': k, '커밋 수': v} 
                    for k, v in contributors['top_contributors'].items()
                ])
                st.dataframe(top_contrib_df, use_container_width=True)
        
        with col2:
            # 기여자별 커밋 수 차트
            if contributors['top_contributors']:
                fig = px.bar(
                    x=list(contributors['top_contributors'].keys()),
                    y=list(contributors['top_contributors'].values()),
                    title="상위 기여자별 커밋 수"
                )
                fig.update_layout(xaxis_title="기여자", yaxis_title="커밋 수")
                st.plotly_chart(fig, use_container_width=True)
    
    # 커밋 패턴
    if analysis['commit_patterns']:
        st.markdown("### ⏰ 커밋 패턴")
        patterns = analysis['commit_patterns']
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 시간대별 분포
            if patterns.get('hourly_distribution'):
                hourly_data = patterns['hourly_distribution']
                hours = list(hourly_data.keys())
                counts = list(hourly_data.values())
                
                fig = px.bar(x=hours, y=counts, title="시간대별 커밋 분포")
                fig.update_layout(xaxis_title="시간", yaxis_title="커밋 수")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 요일별 분포
            if patterns.get('daily_distribution'):
                daily_data = patterns['daily_distribution']
                days = list(daily_data.keys())
                counts = list(daily_data.values())
                
                fig = px.bar(x=days, y=counts, title="요일별 커밋 분포")
                fig.update_layout(xaxis_title="요일", yaxis_title="커밋 수")
                st.plotly_chart(fig, use_container_width=True)
        
        # 가장 활발한 시간/요일
        if patterns.get('most_active_hour') is not None and patterns.get('most_active_day'):
            st.info(f"🔥 가장 활발한 시간: {patterns['most_active_hour']}시, 가장 활발한 요일: {patterns['most_active_day']}")

if __name__ == "__main__":
    create_realtime_dashboard()