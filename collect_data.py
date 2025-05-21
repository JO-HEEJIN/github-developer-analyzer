#!/usr/bin/env python3
# github_analyzer/collect_data.py

import os
import time
import json
import pandas as pd
from datetime import datetime, timedelta
from github import Github, RateLimitExceededException
from dotenv import load_dotenv
from tqdm import tqdm
import logging


import sys
print("Python Path:", sys.path)
try:
    import numpy
    print("NumPy Path:", numpy.__file__)
except ImportError as e:
    print("NumPy Import Error:", e)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("github_collector.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("GitHubCollector")

# 환경 변수 로드
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
MAX_ITEMS = int(os.getenv("MAX_ITEMS_PER_REQUEST", 100))
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", 0.5))

# 데이터 디렉토리 경로
DATA_DIR = "data"

class GitHubDataCollector:
    def __init__(self, token):
        """GitHub 데이터 수집기 초기화"""
        self.github = Github(token)
        logger.info(f"GitHub API 연결됨 - 속도 제한: {self.github.get_rate_limit().core.remaining}/{self.github.get_rate_limit().core.limit}")
    
    def check_rate_limit(self, min_remaining=10):
        """GitHub API 속도 제한 확인 및 대기"""
        rate_limit = self.github.get_rate_limit()
        remaining = rate_limit.core.remaining
        
        if remaining < min_remaining:
            reset_time = rate_limit.core.reset
            sleep_time = (reset_time - datetime.utcnow()).total_seconds() + 10  # 10초 추가 여유
            logger.warning(f"API 속도 제한 거의 도달: {remaining} 남음. {sleep_time:.0f}초 대기 중...")
            
            if sleep_time > 0:
                time.sleep(sleep_time)
            
            logger.info(f"API 속도 제한 리셋됨. 새로운 제한: {self.github.get_rate_limit().core.remaining}")
    
    def collect_repository_metadata(self, repo_name):
        """저장소의 기본 메타데이터 수집"""
        logger.info(f"저장소 메타데이터 수집 중: {repo_name}")
        
        try:
            repo = self.github.get_repo(repo_name)
            
            metadata = {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "created_at": repo.created_at.isoformat(),
                "updated_at": repo.updated_at.isoformat(),
                "language": repo.language,
                "stargazers_count": repo.stargazers_count,
                "forks_count": repo.forks_count,
                "open_issues_count": repo.open_issues_count,
                "topics": repo.get_topics(),
                "license": repo.license.name if repo.license else None,
                "size": repo.size,
                "default_branch": repo.default_branch,
                "organization": repo.organization.login if repo.organization else None,
                "is_archived": repo.archived,
                "is_fork": repo.fork
            }
            
            time.sleep(REQUEST_DELAY)
            return metadata
            
        except Exception as e:
            logger.error(f"저장소 데이터 수집 중 오류 발생: {e}")
            return None
    
    def collect_commits(self, repo_name, days_back=30, max_commits=1000):
        """저장소의 커밋 데이터 수집"""
        logger.info(f"저장소 커밋 수집 중: {repo_name}, {days_back}일 전부터, 최대 {max_commits}개")
        
        try:
            repo = self.github.get_repo(repo_name)
            since_date = datetime.now() - timedelta(days=days_back)
            
            commits_data = []
            commits = repo.get_commits(since=since_date)
            
            with tqdm(total=min(max_commits, commits.totalCount), desc="커밋 수집") as pbar:
                for i, commit in enumerate(commits):
                    if i >= max_commits:
                        break
                    
                    try:
                        # API 속도 제한 확인
                        if i % 50 == 0:
                            self.check_rate_limit()
                        
                        # 커밋 상세 정보 가져오기
                        commit_data = {
                            "repo": repo_name,
                            "sha": commit.sha,
                            "author_name": commit.commit.author.name if commit.commit.author else None,
                            "author_email": commit.commit.author.email if commit.commit.author else None,
                            "author_login": commit.author.login if commit.author else None,
                            "committer_name": commit.commit.committer.name if commit.commit.committer else None,
                            "committer_email": commit.commit.committer.email if commit.commit.committer else None,
                            "committer_login": commit.committer.login if commit.committer else None,
                            "date": commit.commit.author.date.isoformat() if commit.commit.author else None,
                            "message": commit.commit.message,
                            "url": commit.html_url
                        }
                        
                        # 변경 통계 추가 (API 추가 호출 필요)
                        try:
                            detailed_commit = repo.get_commit(commit.sha)
                            commit_data.update({
                                "additions": detailed_commit.stats.additions,
                                "deletions": detailed_commit.stats.deletions,
                                "total_changes": detailed_commit.stats.total,
                                "files_changed": len(detailed_commit.files)
                            })
                            
                            # 파일 변경 데이터 (선택적으로 수집 가능)
                            # files_data = []
                            # for file in detailed_commit.files:
                            #    files_data.append({
                            #        "filename": file.filename,
                            #        "additions": file.additions,
                            #        "deletions": file.deletions,
                            #        "changes": file.changes,
                            #        "status": file.status
                            #    })
                            # commit_data["files"] = files_data
                            
                        except Exception as e:
                            logger.warning(f"커밋 {commit.sha} 상세 정보 가져오기 실패: {e}")
                            commit_data.update({
                                "additions": None,
                                "deletions": None,
                                "total_changes": None,
                                "files_changed": None
                            })
                        
                        commits_data.append(commit_data)
                        time.sleep(REQUEST_DELAY)
                        pbar.update(1)
                        
                    except RateLimitExceededException:
                        logger.warning("API 속도 제한 도달. 대기 중...")
                        self.check_rate_limit(min_remaining=0)
                        
                    except Exception as e:
                        logger.error(f"커밋 {commit.sha if hasattr(commit, 'sha') else 'unknown'} 처리 중 오류: {e}")
            
            logger.info(f"{len(commits_data)} 커밋 수집됨")
            return commits_data
            
        except Exception as e:
            logger.error(f"커밋 데이터 수집 중 오류 발생: {e}")
            return []

    def collect_pull_requests(self, repo_name, state='all', max_prs=500):
        """저장소의 PR 데이터 수집"""
        logger.info(f"저장소 PR 수집 중: {repo_name}, 상태={state}, 최대 {max_prs}개")
        
        try:
            repo = self.github.get_repo(repo_name)
            prs_data = []
            prs = repo.get_pulls(state=state)
            
            with tqdm(total=min(max_prs, prs.totalCount), desc="PR 수집") as pbar:
                for i, pr in enumerate(prs):
                    if i >= max_prs:
                        break
                    
                    try:
                        # API 속도 제한 확인
                        if i % 30 == 0:
                            self.check_rate_limit()
                        
                        # PR 기본 정보
                        pr_data = {
                            "repo": repo_name,
                            "number": pr.number,
                            "title": pr.title,
                            "body": pr.body,
                            "state": pr.state,
                            "created_at": pr.created_at.isoformat(),
                            "updated_at": pr.updated_at.isoformat(),
                            "closed_at": pr.closed_at.isoformat() if pr.closed_at else None,
                            "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                            "merge_commit_sha": pr.merge_commit_sha,
                            "author_login": pr.user.login if pr.user else None,
                            "additions": pr.additions,
                            "deletions": pr.deletions,
                            "changed_files": pr.changed_files,
                            "comments": pr.comments,
                            "review_comments": pr.review_comments,
                            "commits": pr.commits,
                            "is_merged": pr.merged,
                            "url": pr.html_url
                        }
                        
                        # PR 리뷰어 정보 (선택적)
                        try:
                            reviews = pr.get_reviews()
                            reviewers = {}
                            
                            for review in reviews:
                                reviewer = review.user.login if review.user else "unknown"
                                if reviewer not in reviewers:
                                    reviewers[reviewer] = []
                                
                                reviewers[reviewer].append({
                                    "state": review.state,
                                    "submitted_at": review.submitted_at.isoformat() if review.submitted_at else None
                                })
                            
                            pr_data["reviewers"] = reviewers
                            
                        except Exception as e:
                            logger.warning(f"PR {pr.number} 리뷰 정보 가져오기 실패: {e}")
                        
                        prs_data.append(pr_data)
                        time.sleep(REQUEST_DELAY)
                        pbar.update(1)
                        
                    except RateLimitExceededException:
                        logger.warning("API 속도 제한 도달. 대기 중...")
                        self.check_rate_limit(min_remaining=0)
                        
                    except Exception as e:
                        logger.error(f"PR {pr.number if hasattr(pr, 'number') else 'unknown'} 처리 중 오류: {e}")
            
            logger.info(f"{len(prs_data)} PR 수집됨")
            return prs_data
            
        except Exception as e:
            logger.error(f"PR 데이터 수집 중 오류 발생: {e}")
            return []

    def collect_issues(self, repo_name, state='all', max_issues=500):
        """저장소의 이슈 데이터 수집"""
        logger.info(f"저장소 이슈 수집 중: {repo_name}, 상태={state}, 최대 {max_issues}개")
        
        try:
            repo = self.github.get_repo(repo_name)
            issues_data = []
            issues = repo.get_issues(state=state)
            
            with tqdm(total=min(max_issues, issues.totalCount), desc="이슈 수집") as pbar:
                for i, issue in enumerate(issues):
                    if i >= max_issues:
                        break
                    
                    # PR인 경우 건너뛰기 (PR은 이슈이기도 함)
                    if issue.pull_request:
                        continue
                    
                    try:
                        # API 속도 제한 확인
                        if i % 30 == 0:
                            self.check_rate_limit()
                        
                        # 이슈 기본 정보
                        issue_data = {
                            "repo": repo_name,
                            "number": issue.number,
                            "title": issue.title,
                            "body": issue.body,
                            "state": issue.state,
                            "created_at": issue.created_at.isoformat(),
                            "updated_at": issue.updated_at.isoformat(),
                            "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
                            "author_login": issue.user.login if issue.user else None,
                            "assignees": [assignee.login for assignee in issue.assignees],
                            "comments": issue.comments,
                            "labels": [label.name for label in issue.labels],
                            "milestone": issue.milestone.title if issue.milestone else None,
                            "url": issue.html_url
                        }
                        
                        issues_data.append(issue_data)
                        time.sleep(REQUEST_DELAY)
                        pbar.update(1)
                        
                    except RateLimitExceededException:
                        logger.warning("API 속도 제한 도달. 대기 중...")
                        self.check_rate_limit(min_remaining=0)
                        
                    except Exception as e:
                        logger.error(f"이슈 {issue.number if hasattr(issue, 'number') else 'unknown'} 처리 중 오류: {e}")
            
            logger.info(f"{len(issues_data)} 이슈 수집됨")
            return issues_data
            
        except Exception as e:
            logger.error(f"이슈 데이터 수집 중 오류 발생: {e}")
            return []

    def collect_repository_data(self, repo_name, days_back=30, max_items=None):
        """저장소의 전체 데이터 수집"""
        logger.info(f"저장소 {repo_name} 전체 데이터 수집 시작")
        
        # 기본값 설정
        if max_items is None:
            max_items = {
                "commits": 300,
                "pull_requests": 100,
                "issues": 100
            }
        
        # 저장소 메타데이터 수집
        metadata = self.collect_repository_metadata(repo_name)
        
        # 커밋 데이터 수집
        commits = self.collect_commits(repo_name, days_back=days_back, max_commits=max_items["commits"])
        
        # PR 데이터 수집
        pull_requests = self.collect_pull_requests(repo_name, max_prs=max_items["pull_requests"])
        
        # 이슈 데이터 수집
        issues = self.collect_issues(repo_name, max_issues=max_items["issues"])
        
        # 각 데이터 판다스 DataFrame으로 변환
        metadata_df = pd.DataFrame([metadata]) if metadata else pd.DataFrame()
        commits_df = pd.DataFrame(commits) if commits else pd.DataFrame()
        prs_df = pd.DataFrame(pull_requests) if pull_requests else pd.DataFrame()
        issues_df = pd.DataFrame(issues) if issues else pd.DataFrame()
        
        # JSON 형태로 저장된 열 처리
        for df in [prs_df, issues_df]:
            for col in df.columns:
                if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
                    df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)
        
        # 결과 저장
        repo_dir = os.path.join(DATA_DIR, repo_name.replace("/", "_"))
        os.makedirs(repo_dir, exist_ok=True)
        
        if not metadata_df.empty:
            metadata_df.to_csv(os.path.join(repo_dir, "metadata.csv"), index=False)
        if not commits_df.empty:
            commits_df.to_csv(os.path.join(repo_dir, "commits.csv"), index=False)
        if not prs_df.empty:
            prs_df.to_csv(os.path.join(repo_dir, "pull_requests.csv"), index=False)
        if not issues_df.empty:
            issues_df.to_csv(os.path.join(repo_dir, "issues.csv"), index=False)
        
        logger.info(f"저장소 {repo_name} 데이터 수집 완료")
        logger.info(f"수집된 데이터: {len(commits)} 커밋, {len(pull_requests)} PR, {len(issues)} 이슈")
        
        return {
            "metadata": metadata,
            "commits": commits,
            "pull_requests": pull_requests,
            "issues": issues
        }

def main():
    """메인 함수"""
    # 토큰 유효성 확인
    if not GITHUB_TOKEN or GITHUB_TOKEN == "your_github_token_here":
        logger.error("유효한 GitHub 토큰이 필요합니다. .env 파일에 GITHUB_TOKEN을 설정하세요.")
        sys.exit(1)
    
    # 수집기 초기화
    collector = GitHubDataCollector(GITHUB_TOKEN)
    
    # 분석할 리포지토리 리스트
    repositories = [
        "tensorflow/tensorflow",  # 큰 머신러닝 프레임워크
        "facebook/react",         # 프론트엔드 라이브러리
        "microsoft/vscode",       # 코드 에디터
        "flutter/flutter",        # 모바일 앱 프레임워크
        "django/django"           # 웹 프레임워크
    ]
    
    # 테스트를 위한 더 작은 리포지토리들 (초기 테스트 시 유용)
    small_repositories = [
        "pallets/flask",          # 더 작은 웹 프레임워크
        "psf/requests",           # HTTP 요청 라이브러리
        "pandas-dev/pandas",      # 데이터 분석 라이브러리
    ]
    
    # 사용할 리포지토리 선택 (초기 테스트는 small_repositories로 시작하는 것이 좋음)
    repos_to_collect = small_repositories
    
    # 데이터 수집 옵션
    days_back = 30  # 최근 30일 데이터
    max_items = {
        "commits": 200,      # 저장소당 최대 커밋 수
        "pull_requests": 50, # 저장소당 최대 PR 수
        "issues": 50         # 저장소당 최대 이슈 수
    }
    
    # 모든 저장소에 대한 데이터 수집
    for repo_name in repos_to_collect:
        logger.info(f"===== {repo_name} 데이터 수집 시작 =====")
        
        try:
            collector.collect_repository_data(
                repo_name=repo_name,
                days_back=days_back,
                max_items=max_items
            )
            
        except Exception as e:
            logger.error(f"{repo_name} 처리 중 예상치 못한 오류 발생: {e}")
        
        logger.info(f"===== {repo_name} 데이터 수집 완료 =====\n")
    
    logger.info("모든 데이터 수집 작업 완료!")

if __name__ == "__main__":
    main()
