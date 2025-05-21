#!/usr/bin/env python3
# github_analyzer/analyze_data.py

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import logging
import glob
import re
from collections import Counter

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("github_analyzer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("GitHubAnalyzer")

# 데이터 및 결과 디렉토리
DATA_DIR = "data"
RESULTS_DIR = "results"
os.makedirs(RESULTS_DIR, exist_ok=True)

class GitHubDataAnalyzer:
    def __init__(self):
        """GitHub 데이터 분석기 초기화"""
        logger.info("GitHub 데이터 분석기 초기화")
        
        # 그래프 스타일 설정
        plt.style.use('ggplot')
        sns.set(style="whitegrid")
    
    def load_data(self, repositories=None):
        """지정된 저장소들 또는 모든 저장소의 데이터 로드"""
        all_commits = []
        all_prs = []
        all_issues = []
        repo_metadata = {}
        
        # 분석할 저장소 목록 결정
        if repositories is None:
            # 데이터 디렉토리의 모든 저장소 디렉토리 검색
            repo_dirs = [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]
            repositories = [d.replace("_", "/", 1) for d in repo_dirs]
        
        logger.info(f"{len(repositories)} 저장소의 데이터 로드 중")
        
        for repo_name in repositories:
            repo_dir = os.path.join(DATA_DIR, repo_name.replace("/", "_"))
            
            # 각 데이터 파일 로드
            try:
                # 메타데이터
                metadata_file = os.path.join(repo_dir, "metadata.csv")
                if os.path.exists(metadata_file):
                    metadata_df = pd.read_csv(metadata_file)
                    if not metadata_df.empty:
                        repo_metadata[repo_name] = metadata_df.iloc[0].to_dict()
                
                # 커밋 데이터
                commits_file = os.path.join(repo_dir, "commits.csv")
                if os.path.exists(commits_file):
                    commits_df = pd.read_csv(commits_file)
                    if not commits_df.empty:
                        # 저장소 이름 추가 (파일에 없는 경우)
                        if 'repo' not in commits_df.columns:
                            commits_df['repo'] = repo_name
                        all_commits.append(commits_df)
                
                # PR 데이터
                prs_file = os.path.join(repo_dir, "pull_requests.csv")
                if os.path.exists(prs_file):
                    prs_df = pd.read_csv(prs_file)
                    if not prs_df.empty:
                        # 저장소 이름 추가
                        if 'repo' not in prs_df.columns:
                            prs_df['repo'] = repo_name
                        all_prs.append(prs_df)
                
                # 이슈 데이터
                issues_file = os.path.join(repo_dir, "issues.csv")
                if os.path.exists(issues_file):
                    issues_df = pd.read_csv(issues_file)
                    if not issues_df.empty:
                        # 저장소 이름 추가
                        if 'repo' not in issues_df.columns:
                            issues_df['repo'] = repo_name
                        all_issues.append(issues_df)
                
            except Exception as e:
                logger.error(f"저장소 {repo_name} 데이터 로드 중 오류: {e}")
        
        # 모든 데이터 결합
        commits_df = pd.concat(all_commits, ignore_index=True) if all_commits else pd.DataFrame()
        prs_df = pd.concat(all_prs, ignore_index=True) if all_prs else pd.DataFrame()
        issues_df = pd.concat(all_issues, ignore_index=True) if all_issues else pd.DataFrame()
        
        # 날짜 열 변환
        for df, date_cols in [
            (commits_df, ['date']),
            (prs_df, ['created_at', 'updated_at', 'closed_at', 'merged_at']),
            (issues_df, ['created_at', 'updated_at', 'closed_at'])
        ]:
            if not df.empty:
                for col in date_cols:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # PR 데이터 - reviewers 열이 JSON 문자열인 경우 파싱
        if not prs_df.empty and 'reviewers' in prs_df.columns:
            try:
                prs_df['reviewers'] = prs_df['reviewers'].apply(
                    lambda x: json.loads(x) if isinstance(x, str) else x
                )
            except Exception as e:
                logger.warning(f"'reviewers' 열 파싱 중 오류: {e}")
        
        # 이슈 데이터 - JSON 문자열로 저장된 열 파싱
        for col in ['assignees', 'labels']:
            if not issues_df.empty and col in issues_df.columns:
                try:
                    issues_df[col] = issues_df[col].apply(
                        lambda x: json.loads(x) if isinstance(x, str) else x
                    )
                except Exception as e:
                    logger.warning(f"'{col}' 열 파싱 중 오류: {e}")
        
        logger.info(f"데이터 로드 완료: {len(commits_df)} 커밋, {len(prs_df)} PR, {len(issues_df)} 이슈")
        
        return {
            "commits": commits_df,
            "pull_requests": prs_df,
            "issues": issues_df,
            "metadata": repo_metadata
        }
    
    def clean_data(self, data):
        """데이터 정제 및 전처리"""
        commits_df = data["commits"].copy()
        prs_df = data["pull_requests"].copy()
        issues_df = data["issues"].copy()
        
        logger.info("데이터 정제 및 전처리 중...")
        
        # 커밋 데이터 정제
        if not commits_df.empty:
            # 날짜 관련 특성 추가
            commits_df['date'] = pd.to_datetime(commits_df['date'], errors='coerce')
            commits_df = commits_df.dropna(subset=['date'])  # 날짜가 없는 행 제거
            
            # 요일 및 시간 추출
            commits_df['day_of_week'] = commits_df['date'].dt.dayofweek  # 0=월요일, 6=일요일
            commits_df['day_name'] = commits_df['date'].dt.day_name()
            commits_df['hour_of_day'] = commits_df['date'].dt.hour
            commits_df['month'] = commits_df['date'].dt.month
            commits_df['year'] = commits_df['date'].dt.year
            
            # 커밋 메시지 분석
            commits_df['message_length'] = commits_df['message'].apply(lambda x: len(str(x)) if pd.notna(x) else 0)
            
            # 이상치 처리
            for col in ['additions', 'deletions', 'total_changes', 'files_changed']:
                if col in commits_df.columns:
                    # 0 이상의 값 확인
                    commits_df[col] = commits_df[col].apply(lambda x: max(0, x) if pd.notna(x) else 0)
                    
                    # 상위 1% 이상치 제한
                    upper_limit = commits_df[col].quantile(0.99)
                    commits_df[col] = commits_df[col].apply(lambda x: min(x, upper_limit))
        
        # PR 데이터 정제
        if not prs_df.empty:
            # 날짜 변환
            for col in ['created_at', 'updated_at', 'closed_at', 'merged_at']:
                if col in prs_df.columns:
                    prs_df[col] = pd.to_datetime(prs_df[col], errors='coerce')
            
            # PR 처리 시간 계산 (시간 단위)
            prs_df['processing_time'] = None
            mask = ~prs_df['closed_at'].isna()
            prs_df.loc[mask, 'processing_time'] = (
                prs_df.loc[mask, 'closed_at'] - prs_df.loc[mask, 'created_at']
            ).dt.total_seconds() / 3600
            
            # 이상치 처리
            for col in ['additions', 'deletions', 'changed_files', 'comments', 'review_comments', 'commits']:
                if col in prs_df.columns:
                    # 0 이상의 값 확인
                    prs_df[col] = prs_df[col].apply(lambda x: max(0, x) if pd.notna(x) else 0)
                    
                    # 상위 1% 이상치 제한
                    upper_limit = prs_df[col].quantile(0.99)
                    prs_df[col] = prs_df[col].apply(lambda x: min(x, upper_limit))
            
            # PR 제목 길이
            if 'title' in prs_df.columns:
                prs_df['title_length'] = prs_df['title'].apply(lambda x: len(str(x)) if pd.notna(x) else 0)
            
            # 병합 여부 플래그
            if 'is_merged' not in prs_df.columns and 'merged_at' in prs_df.columns:
                prs_df['is_merged'] = ~prs_df['merged_at'].isna()
        
        # 이슈 데이터 정제
        if not issues_df.empty:
            # 날짜 변환
            for col in ['created_at', 'updated_at', 'closed_at']:
                if col in issues_df.columns:
                    issues_df[col] = pd.to_datetime(issues_df[col], errors='coerce')
            
            # 이슈 처리 시간 계산 (시간 단위)
            issues_df['resolution_time'] = None
            mask = ~issues_df['closed_at'].isna()
            issues_df.loc[mask, 'resolution_time'] = (
                issues_df.loc[mask, 'closed_at'] - issues_df.loc[mask, 'created_at']
            ).dt.total_seconds() / 3600
            
            # 이슈 제목 및 본문 길이
            if 'title' in issues_df.columns:
                issues_df['title_length'] = issues_df['title'].apply(lambda x: len(str(x)) if pd.notna(x) else 0)
            
            if 'body' in issues_df.columns:
                issues_df['body_length'] = issues_df['body'].apply(
                    lambda x: len(str(x)) if pd.notna(x) and x is not None else 0
                )
        
        logger.info("데이터 정제 완료")
        
        return {
            "commits": commits_df,
            "pull_requests": prs_df,
            "issues": issues_df
        }
    
    def analyze_developer_patterns(self, commits_df):
        """개발자 활동 패턴 분석"""
        logger.info("개발자 활동 패턴 분석 중...")
        
        if commits_df.empty:
            logger.warning("커밋 데이터가 없습니다. 개발자 패턴 분석을 건너뜁니다.")
            return None
        
        # 저자 기준으로 사용 (author_login 또는 author_name)
        author_col = 'author_login' if 'author_login' in commits_df.columns else 'author_name'
        
        # 유효한 저자 이름만 사용
        valid_authors = commits_df[author_col].dropna().unique()
        logger.info(f"고유한 개발자 수: {len(valid_authors)}")
        
        # 상위 개발자만 상세 분석 (너무 많으면 분석이 어려움)
        top_authors = commits_df[author_col].value_counts().head(30).index
        
        # 개발자별 기본 통계
        dev_stats = commits_df.groupby(author_col).agg({
            'sha': 'count',  # 커밋 수
            'message_length': ['mean', 'median'],  # 커밋 메시지 길이
            'date': ['min', 'max']  # 첫/마지막 커밋 날짜
        })
        
        # 멀티인덱스 컬럼 이름 정리
        dev_stats.columns = ['_'.join(col).strip('_') for col in dev_stats.columns.values]
        dev_stats = dev_stats.rename(columns={'sha_count': 'commit_count'})
        
        # 활동 기간 계산 (일 단위)
        dev_stats['active_days'] = (dev_stats['date_max'] - dev_stats['date_min']).dt.days + 1
        
        # 일일 평균 커밋 수 계산
        dev_stats['commits_per_day'] = dev_stats['commit_count'] / dev_stats['active_days']
        
        # 코드 변경 패턴 (있는 경우만)
        code_cols = [col for col in ['additions', 'deletions', 'total_changes', 'files_changed'] 
                    if col in commits_df.columns]
        
        if code_cols:
            code_stats = commits_df.groupby(author_col)[code_cols].agg(['mean', 'median', 'sum'])
            code_stats.columns = ['_'.join(col).strip('_') for col in code_stats.columns.values]
            
            # 개발자 통계에 코드 변경 패턴 병합
            dev_stats = pd.concat([dev_stats, code_stats], axis=1)
            
            # 추가/삭제 비율 계산 (있는 경우)
            if 'additions_sum' in dev_stats.columns and 'deletions_sum' in dev_stats.columns:
                dev_stats['add_delete_ratio'] = dev_stats['additions_sum'] / (dev_stats['deletions_sum'] + 1)  # 0으로 나누기 방지
        
        # 요일별 활동 패턴
        day_activity = pd.crosstab(
            commits_df[author_col], 
            commits_df['day_name'],
            normalize='index'  # 각 개발자별로 정규화
        )
        
        # 요일 순서 조정
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        if set(day_order).issubset(day_activity.columns):
            day_activity = day_activity.reindex(columns=day_order)
        
        # 시간대별 활동 패턴
        hour_activity = pd.crosstab(
            commits_df[author_col], 
            commits_df['hour_of_day'],
            normalize='index'  # 각 개발자별로 정규화
        )
        
        # 커밋 메시지 분석
        message_patterns = {}
        
        # 상위 개발자에 대해서만 상세 메시지 분석 수행
        for author in top_authors:
            author_commits = commits_df[commits_df[author_col] == author]
            
            # 메시지가 있는 커밋만 분석
            messages = author_commits['message'].dropna().astype(str).tolist()
            
            if messages:
                # 모든 메시지 합치기
                all_text = ' '.join(messages).lower()
                
                # 일반적인 단어, 기호 제거
                all_text = re.sub(r'[^\w\s]', ' ', all_text)
                
                # 단어 빈도 계산
                words = all_text.split()
                word_freq = Counter(words)
                
                # 일반적인 불용어 제거
                stopwords = {'the', 'and', 'to', 'of', 'a', 'in', 'for', 'is', 'on', 'that', 'by', 'this', 'with', 'i', 'you', 'it'}
                for word in stopwords:
                    if word in word_freq:
                        del word_freq[word]
                
                # 상위 10개 단어 저장
                top_words = {word: count for word, count in word_freq.most_common(10)}
                message_patterns[author] = top_words
        
        # 결과 저장
        dev_patterns = {
            'stats': dev_stats,
            'day_activity': day_activity,
            'hour_activity': hour_activity,
            'message_patterns': message_patterns
        }
        
        # 파일로 저장
        os.makedirs(os.path.join(RESULTS_DIR, 'developer_patterns'), exist_ok=True)
        
        # 기본 통계
        dev_stats.to_csv(os.path.join(RESULTS_DIR, 'developer_patterns', 'dev_stats.csv'))
        
        # 요일 활동
        day_activity.to_csv(os.path.join(RESULTS_DIR, 'developer_patterns', 'day_activity.csv'))
        
        # 시간대 활동
        hour_activity.to_csv(os.path.join(RESULTS_DIR, 'developer_patterns', 'hour_activity.csv'))
        
        # 메시지 패턴
        with open(os.path.join(RESULTS_DIR, 'developer_patterns', 'message_patterns.json'), 'w') as f:
            json.dump(message_patterns, f, indent=2)
        
        logger.info("개발자 패턴 분석 완료")
        
        return dev_patterns
    
    def analyze_pr_patterns(self, prs_df):
        """PR 패턴 분석"""
        logger.info("PR 패턴 분석 중...")
        
        if prs_df.empty:
            logger.warning("PR 데이터가 없습니다. PR 패턴 분석을 건너뜁니다.")
            return None
        
        # 저자 컬럼
        author_col = 'author_login'
        if author_col not in prs_df.columns:
            logger.warning(f"'{author_col}' 열을 찾을 수 없습니다. PR 패턴 분석을 건너뜁니다.")
            return None
        
        # 상위 개발자만 분석
        top_authors = prs_df[author_col].value_counts().head(30).index
        
        # 개발자별 PR 통계
        pr_stats = prs_df.groupby(author_col).agg({
            'number': 'count',  # PR 수
            'processing_time': ['mean', 'median', 'std'],  # 처리 시간
            'is_merged': 'mean',  # 병합률
            'comments': ['mean', 'sum'],  # 코멘트
            'commits': ['mean', 'max']  # 커밋 수
        })
        
        # 멀티인덱스 컬럼 이름 정리
        pr_stats.columns = ['_'.join(col).strip('_') for col in pr_stats.columns.values]
        pr_stats = pr_stats.rename(columns={'number_count': 'pr_count'})
        
        # 코드 변경 패턴
        code_cols = [col for col in ['additions', 'deletions', 'changed_files'] 
                    if col in prs_df.columns]
        
        if code_cols:
            code_stats = prs_df.groupby(author_col)[code_cols].agg(['mean', 'median', 'sum'])
            code_stats.columns = ['_'.join(col).strip('_') for col in code_stats.columns.values]
            
            # PR 통계에 코드 변경 패턴 병합
            pr_stats = pd.concat([pr_stats, code_stats], axis=1)
        
        # PR 크기 대 처리 시간 분석
        size_time_corr = {}
        
        if 'additions' in prs_df.columns and 'processing_time' in prs_df.columns:
            # 전체 상관관계
            corr = prs_df[['additions', 'processing_time']].corr().iloc[0, 1]
            size_time_corr['overall'] = corr
            
            # 개발자별 상관관계 (상위 개발자만)
            for author in top_authors:
                author_prs = prs_df[prs_df[author_col] == author]
                if len(author_prs) >= 10:  # 충분한 데이터가 있는 경우만
                    author_corr = author_prs[['additions', 'processing_time']].corr().iloc[0, 1]
                    size_time_corr[author] = author_corr
        
        # 리뷰 패턴 분석 (reviewers 열이 있는 경우)
        review_network = None
        
        if 'reviewers' in prs_df.columns and prs_df['reviewers'].notna().any():
            # 리뷰 네트워크 구성 (누가 누구의 코드를 리뷰하는지)
            review_edges = []
            
            for _, row in prs_df[prs_df['reviewers'].notna()].iterrows():
                author = row[author_col]
                reviewers_data = row['reviewers']
                
                if isinstance(reviewers_data, dict):
                    for reviewer in reviewers_data.keys():
                        if reviewer != author:  # 자기 자신은 제외
                            review_edges.append((reviewer, author))
            
            # 리뷰 횟수 계산
            review_counts = Counter(review_edges)
            
            # 네트워크 데이터 구성
            review_network = {
                'edges': [{'source': src, 'target': tgt, 'weight': cnt} 
                         for (src, tgt), cnt in review_counts.items()]
            }
            
            # 리뷰 네트워크 저장
            with open(os.path.join(RESULTS_DIR, 'pr_patterns', 'review_network.json'), 'w') as f:
                json.dump(review_network, f, indent=2)
        
        # 결과 저장
        pr_patterns = {
            'stats': pr_stats,
            'size_time_corr': size_time_corr,
            'review_network': review_network
        }
        
        # 파일로 저장
        os.makedirs(os.path.join(RESULTS_DIR, 'pr_patterns'), exist_ok=True)
        
        # PR 통계
        pr_stats.to_csv(os.path.join(RESULTS_DIR, 'pr_patterns', 'pr_stats.csv'))
        
        # 크기-시간 상관관계
        with open(os.path.join(RESULTS_DIR, 'pr_patterns', 'size_time_corr.json'), 'w') as f:
            json.dump(size_time_corr, f, indent=2)
        
        logger.info("PR 패턴 분석 완료")
        
        return pr_patterns
    
    def cluster_developers(self, commits_df, prs_df):
        """개발자 클러스터링"""
        logger.info("개발자 클러스터링 시작...")
        
        if commits_df.empty:
            logger.warning("커밋 데이터가 없습니다. 개발자 클러스터링을 건너뜁니다.")
            return None
        
        # 저자 컬럼
        author_col = 'author_login' if 'author_login' in commits_df.columns else 'author_name'
        
        # 커밋 기반 개발자 프로필 생성
        commit_profiles = commits_df.groupby(author_col).agg({
            'sha': 'count',  # 커밋 수
            'message_length': 'mean',  # 평균 메시지 길이
            'day_of_week': 'mean',  # 평균 요일 (숫자 값)
            'hour_of_day': 'mean'  # 평균 시간
        }).rename(columns={'sha': 'commit_count'})
        
        # 코드 변경 통계 (있는 경우만)
        code_cols = [col for col in ['additions', 'deletions', 'total_changes', 'files_changed'] 
                    if col in commits_df.columns]
        
        if code_cols:
            code_stats = commits_df.groupby(author_col)[code_cols].agg('mean')
            commit_profiles = pd.concat([commit_profiles, code_stats], axis=1)
        
        # 요일 활동 패턴 (선택적)
        days = range(7)  # 0=월요일, 6=일요일
        for day in days:
            day_filter = commits_df['day_of_week'] == day
            day_counts = commits_df[day_filter].groupby(author_col).size()
            commit_profiles[f'day_{day}_pct'] = day_counts / commit_profiles['commit_count']
            commit_profiles[f'day_{day}_pct'] = commit_profiles[f'day_{day}_pct'].fillna(0)
        
        # PR 데이터 병합 (있는 경우)
        if not prs_df.empty and author_col in prs_df.columns:
            pr_profiles = prs_df.groupby(author_col).agg({
                'number': 'count',  # PR 수
                'is_merged': 'mean',  # 병합률
                'processing_time': 'mean',  # 평균 처리 시간
                'comments': 'mean'  # 평균 코멘트 수
            }).rename(columns={'number': 'pr_count'})
            
            # PR 코드 변경 통계 (있는 경우만)
            pr_code_cols = [col for col in ['additions', 'deletions', 'changed_files'] 
                           if col in prs_df.columns]
            
            if pr_code_cols:
                pr_code_stats = prs_df.groupby(author_col)[pr_code_cols].agg('mean')
                pr_profiles = pd.concat([pr_profiles, pr_code_stats], axis=1)
                
                # PR 열 이름 구분을 위해 접두사 추가
                pr_profiles = pr_profiles.add_prefix('pr_')
                # 원래 이름 복원
                pr_profiles = pr_profiles.rename(columns={
                    'pr_pr_count': 'pr_count',
                    'pr_is_merged': 'merge_rate'
                })
            
            # 개발자 프로필에 PR 정보 병합
            dev_profiles = pd.merge(
                commit_profiles, 
                pr_profiles, 
                left_index=True, 
                right_index=True, 
                how='left'
            )
        else:
            dev_profiles = commit_profiles
        
        # 최소 커밋 수 필터링 (노이즈 제거)
        min_commits = 5
        dev_profiles = dev_profiles[dev_profiles['commit_count'] >= min_commits]
        
        if len(dev_profiles) < 5:
            logger.warning(f"클러스터링에 충분한 개발자가 없습니다 (최소 커밋 {min_commits}개 이상): {len(dev_profiles)} 명")
            return None
        
        # 클러스터링을 위한 특성 선택
        feature_cols = ['commit_count', 'message_length', 'hour_of_day']
        
        # 코드 변경 특성 추가 (있는 경우)
        for col in ['additions', 'deletions', 'total_changes', 'files_changed']:
            if col in dev_profiles.columns:
                feature_cols.append(col)
        
        # PR 관련 특성 추가 (있는 경우)
        for col in ['pr_count', 'merge_rate', 'pr_processing_time', 'pr_comments']:
            if col in dev_profiles.columns:
                feature_cols.append(col)
        
        # 클러스터링을 위한 데이터 준비
        X = dev_profiles[feature_cols].fillna(0)
        
        # 스케일링
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # 최적의 클러스터 수 결정 (실루엣 스코어 사용 또는 다른 방법)
        n_clusters = min(4, len(X) - 1)  # 데이터 크기에 따라 조정
        
        # K-means 클러스터링
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_scaled)
        
        # 클러스터 할당
        dev_profiles['cluster'] = clusters
        
        # 시각화를 위한 차원 축소 (PCA)
        if len(X) >= 3:  # 최소 3개 이상의 데이터 포인트 필요
            pca = PCA(n_components=2)
            X_pca = pca.fit_transform(X_scaled)
            
            # PCA 결과 추가
            dev_profiles['pca_x'] = X_pca[:, 0]
            dev_profiles['pca_y'] = X_pca[:, 1]
            
            # 클러스터링 시각화
            plt.figure(figsize=(10, 8))
            
            # 각 클러스터별로 산점도
            for cluster_id in range(n_clusters):
                cluster_data = dev_profiles[dev_profiles['cluster'] == cluster_id]
                plt.scatter(
                    cluster_data['pca_x'], 
                    cluster_data['pca_y'],
                    s=cluster_data['commit_count'] / 5,  # 크기는 커밋 수에 비례
                    alpha=0.7,
                    label=f'Cluster {cluster_id}'
                )
            
            # 개발자 이름 레이블 (상위 개발자만)
            top_devs = dev_profiles.sort_values('commit_count', ascending=False).head(10).index
            for dev in top_devs:
                if dev in dev_profiles.index:
                    x = dev_profiles.loc[dev, 'pca_x']
                    y = dev_profiles.loc[dev, 'pca_y']
                    plt.annotate(dev, (x, y), fontsize=9)
            
            plt.title('개발자 클러스터링 (PCA 차원 축소)')
            plt.xlabel('주성분 1')
            plt.ylabel('주성분 2')
            plt.legend()
            plt.grid(True)
            
            # 결과 저장
            os.makedirs(os.path.join(RESULTS_DIR, 'clustering'), exist_ok=True)
            plt.savefig(os.path.join(RESULTS_DIR, 'clustering', 'developer_clusters.png'), dpi=300)
            plt.close()
        
        # 클러스터별 특성 분석
        cluster_profiles = dev_profiles.groupby('cluster').mean()
        
        # 개발자 프로필 및 클러스터 정보 저장
        dev_profiles.to_csv(os.path.join(RESULTS_DIR, 'clustering', 'developer_profiles.csv'))
        cluster_profiles.to_csv(os.path.join(RESULTS_DIR, 'clustering', 'cluster_profiles.csv'))
        
        logger.info(f"개발자 클러스터링 완료: {n_clusters} 클러스터, {len(dev_profiles)} 개발자")
        
        return {
            'dev_profiles': dev_profiles,
            'cluster_profiles': cluster_profiles,
            'n_clusters': n_clusters
        }
    
    def analyze_time_patterns(self, commits_df):
        """시간 패턴 분석"""
        logger.info("시간 패턴 분석 중...")
        
        if commits_df.empty:
            logger.warning("커밋 데이터가 없습니다. 시간 패턴 분석을 건너뜁니다.")
            return None
        
        # 시간 관련 데이터 확인
        if 'date' not in commits_df.columns:
            logger.warning("'date' 열을 찾을 수 없습니다. 시간 패턴 분석을 건너뜁니다.")
            return None
        
        # 날짜 포맷 확인
        commits_df['date'] = pd.to_datetime(commits_df['date'], errors='coerce')
        commits_df = commits_df.dropna(subset=['date'])
        
        # 날짜 특성 추가
        commits_df['day_of_week'] = commits_df['date'].dt.dayofweek
        commits_df['day_name'] = commits_df['date'].dt.day_name()
        commits_df['hour_of_day'] = commits_df['date'].dt.hour
        commits_df['date_only'] = commits_df['date'].dt.date
        
        # 결과 저장 디렉토리
        os.makedirs(os.path.join(RESULTS_DIR, 'time_patterns'), exist_ok=True)
        
        # 일별 커밋 수
        daily_commits = commits_df.groupby('date_only').size().reset_index(name='count')
        daily_commits.to_csv(os.path.join(RESULTS_DIR, 'time_patterns', 'daily_commits.csv'), index=False)
        
        # 요일별 커밋 분포
        day_counts = commits_df.groupby('day_name').size()
        
        # 요일 순서 조정
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        if set(day_counts.index).issubset(day_order):
            day_counts = day_counts.reindex(day_order)
        
        day_counts.to_csv(os.path.join(RESULTS_DIR, 'time_patterns', 'day_of_week.csv'))
        
        # 시간대별 커밋 분포
        hour_counts = commits_df.groupby('hour_of_day').size()
        hour_counts.to_csv(os.path.join(RESULTS_DIR, 'time_patterns', 'hour_of_day.csv'))
        
        # 요일-시간 히트맵 데이터
        day_hour_counts = pd.crosstab(
            commits_df['day_of_week'], 
            commits_df['hour_of_day']
        )
        day_hour_counts.to_csv(os.path.join(RESULTS_DIR, 'time_patterns', 'day_hour_heatmap.csv'))
        
        # 시각화: 요일별 커밋 분포
        plt.figure(figsize=(10, 6))
        ax = sns.barplot(x=day_counts.index, y=day_counts.values)
        plt.title('요일별 커밋 분포')
        plt.xlabel('요일')
        plt.ylabel('커밋 수')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(RESULTS_DIR, 'time_patterns', 'day_of_week.png'), dpi=300)
        plt.close()
        
        # 시각화: 시간대별 커밋 분포
        plt.figure(figsize=(12, 6))
        ax = sns.barplot(x=hour_counts.index, y=hour_counts.values)
        plt.title('시간대별 커밋 분포')
        plt.xlabel('시간 (24시간)')
        plt.ylabel('커밋 수')
        plt.xticks(range(0, 24, 2))
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(os.path.join(RESULTS_DIR, 'time_patterns', 'hour_of_day.png'), dpi=300)
        plt.close()
        
        # 시각화: 요일-시간 히트맵
        plt.figure(figsize=(14, 8))
        ax = sns.heatmap(day_hour_counts, cmap="YlGnBu", annot=False, fmt="d")
        plt.title('요일-시간대별 커밋 분포')
        plt.xlabel('시간 (24시간)')
        plt.ylabel('요일')
        plt.yticks(ticks=np.arange(0.5, 7.5), labels=day_order)
        plt.tight_layout()
        plt.savefig(os.path.join(RESULTS_DIR, 'time_patterns', 'day_hour_heatmap.png'), dpi=300)
        plt.close()
        
        # 월별/연도별 추세 (충분한 데이터가 있는 경우)
        commits_df['year_month'] = commits_df['date'].dt.to_period('M')
        monthly_counts = commits_df.groupby('year_month').size()
        
        if len(monthly_counts) > 1:
            monthly_counts.to_csv(os.path.join(RESULTS_DIR, 'time_patterns', 'monthly_commits.csv'))
            
            # 월별 추세 시각화
            plt.figure(figsize=(12, 6))
            monthly_counts.plot(kind='line', marker='o')
            plt.title('월별 커밋 추세')
            plt.xlabel('년-월')
            plt.ylabel('커밋 수')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(RESULTS_DIR, 'time_patterns', 'monthly_trend.png'), dpi=300)
            plt.close()
        
        logger.info("시간 패턴 분석 완료")
        
        return {
            'daily_commits': daily_commits,
            'day_counts': day_counts,
            'hour_counts': hour_counts,
            'day_hour_counts': day_hour_counts
        }
    
    def train_pr_approval_model(self, prs_df):
        """PR 승인 예측 모델 훈련"""
        logger.info("PR 승인 예측 모델 훈련 중...")
        
        if prs_df.empty:
            logger.warning("PR 데이터가 없습니다. 모델 훈련을 건너뜁니다.")
            return None
        
        # 목표 변수 확인
        if 'is_merged' not in prs_df.columns:
            logger.warning("'is_merged' 열을 찾을 수 없습니다. 모델 훈련을 건너뜁니다.")
            return None
        
        # 특성 선택
        features = []
        
        # 기본 특성
        basic_features = ['additions', 'deletions', 'changed_files', 'comments']
        features.extend([f for f in basic_features if f in prs_df.columns])
        
        # 추가 특성
        if 'title_length' in prs_df.columns:
            features.append('title_length')
        
        if 'commits' in prs_df.columns:
            features.append('commits')
        
        # 파생 특성 생성
        if 'created_at' in prs_df.columns:
            prs_df['day_of_week'] = pd.to_datetime(prs_df['created_at']).dt.dayofweek
            prs_df['hour_of_day'] = pd.to_datetime(prs_df['created_at']).dt.hour
            features.extend(['day_of_week', 'hour_of_day'])
        
        # 특성 및 목표 변수 추출
        X = prs_df[features].fillna(0)
        y = prs_df['is_merged']
        
        # 모델 생성 및 훈련
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
        import joblib
        
        # 학습/테스트 세트 분할
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42
        )
        
        # 모델 훈련
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # 예측 및 평가
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        # 분류 보고서
        report = classification_report(y_test, y_pred, output_dict=True)
        
        # 혼동 행렬
        cm = confusion_matrix(y_test, y_pred)
        
        # 특성 중요도
        importance = pd.DataFrame({
            'feature': features,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        # 결과 저장 디렉토리
        os.makedirs(os.path.join(RESULTS_DIR, 'models'), exist_ok=True)
        
        # 모델 저장
        joblib.dump(model, os.path.join(RESULTS_DIR, 'models', 'pr_approval_model.pkl'))
        
        # 평가 결과 저장
        with open(os.path.join(RESULTS_DIR, 'models', 'model_evaluation.json'), 'w') as f:
            json.dump({
                'accuracy': accuracy,
                'report': report
            }, f, indent=2)
        
        # 혼동 행렬 시각화
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
        plt.title('PR 승인 예측 모델 혼동 행렬')
        plt.ylabel('실제 레이블')
        plt.xlabel('예측 레이블')
        plt.tight_layout()
        plt.savefig(os.path.join(RESULTS_DIR, 'models', 'confusion_matrix.png'), dpi=300)
        plt.close()
        
        # 특성 중요도 시각화
        plt.figure(figsize=(10, 6))
        sns.barplot(x='importance', y='feature', data=importance)
        plt.title('PR 승인 예측에 대한 특성 중요도')
        plt.tight_layout()
        plt.savefig(os.path.join(RESULTS_DIR, 'models', 'feature_importance.png'), dpi=300)
        plt.close()
        
        logger.info(f"모델 훈련 완료. 정확도: {accuracy:.4f}")
        
        return {
            'model': model,
            'accuracy': accuracy,
            'report': report,
            'importance': importance
        }
    
    def run_analysis(self, repositories=None):
        """모든 분석 실행"""
        # 1. 데이터 로드
        data = self.load_data(repositories)
        
        # 2. 데이터 정제
        clean_data = self.clean_data(data)
        
        # 3. 개발자 활동 패턴 분석
        dev_patterns = self.analyze_developer_patterns(clean_data["commits"])
        
        # 4. PR 패턴 분석
        pr_patterns = self.analyze_pr_patterns(clean_data["pull_requests"])
        
        # 5. 개발자 클러스터링
        clustering = self.cluster_developers(
            clean_data["commits"], 
            clean_data["pull_requests"]
        )
        
        # 6. 시간 패턴 분석
        time_patterns = self.analyze_time_patterns(clean_data["commits"])
        
        # 7. PR 승인 예측 모델 훈련
        pr_model = self.train_pr_approval_model(clean_data["pull_requests"])
        
        # 결과 요약
        summary = {
            'repositories': repositories,
            'data_counts': {
                'commits': len(clean_data["commits"]),
                'pull_requests': len(clean_data["pull_requests"]),
                'issues': len(clean_data["issues"])
            },
            'dev_count': len(clean_data["commits"][clean_data["commits"]["author_login"].notna()]["author_login"].unique()) if 'author_login' in clean_data["commits"].columns else 0,
            'clusters': clustering['n_clusters'] if clustering else 0,
            'model_accuracy': pr_model['accuracy'] if pr_model else None
        }
        
        # 요약 저장
        with open(os.path.join(RESULTS_DIR, 'analysis_summary.json'), 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info("모든 분석 완료!")
        
        return {
            'dev_patterns': dev_patterns,
            'pr_patterns': pr_patterns,
            'clustering': clustering,
            'time_patterns': time_patterns,
            'pr_model': pr_model,
            'summary': summary
        }

def main():
    """메인 함수"""
    # 분석기 초기화
    analyzer = GitHubDataAnalyzer()
    
    # 분석할 저장소 목록 (비워두면 data 디렉토리의 모든 저장소 분석)
    repositories = [
        "pallets/flask",
        "psf/requests",
        "pandas-dev/pandas"
    ]
    
    # 모든 분석 실행
    results = analyzer.run_analysis(repositories)
    
    logger.info("분석 완료!")
    logger.info(f"분석 결과는 '{RESULTS_DIR}' 디렉토리에 저장되었습니다.")

if __name__ == "__main__":
    main()
