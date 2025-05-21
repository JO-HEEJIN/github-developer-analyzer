#!/usr/bin/env python3
# github_analyzer/main.py

import os
import argparse
import logging
from dotenv import load_dotenv

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

def setup_directories():
    """필요한 디렉토리 생성"""
    directories = ['data', 'results', 'results/developer_patterns', 
                   'results/pr_patterns', 'results/clustering', 
                   'results/time_patterns', 'results/models']
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.debug(f"디렉토리 확인: {directory}")

def parse_arguments():
    """명령줄 인자 파싱"""
    parser = argparse.ArgumentParser(description="GitHub 개발자 행동 패턴 분석기")
    
    parser.add_argument(
        "action", 
        choices=["collect", "analyze", "dashboard", "all"],
        help="실행할 작업 (collect: 데이터 수집, analyze: 데이터 분석, dashboard: 대시보드 실행, all: 모두 실행)"
    )
    
    parser.add_argument(
        "--repos", 
        nargs="+", 
        help="분석할 GitHub 저장소 (예: 'owner/repo')"
    )
    
    parser.add_argument(
        "--days", 
        type=int, 
        default=30,
        help="수집할 데이터의 기간(일) (기본값: 30)"
    )
    
    parser.add_argument(
        "--max-items", 
        type=int, 
        default=200,
        help="저장소당 최대 항목 수 (기본값: 200)"
    )
    
    return parser.parse_args()

def main():
    """메인 함수"""
    # 환경 변수 로드
    load_dotenv()
    
    # 디렉토리 설정
    setup_directories()
    
    # 명령줄 인자 파싱
    args = parse_arguments()
    
    # GitHub 토큰 확인
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        logger.error("GitHub 토큰이 설정되지 않았습니다. .env 파일에 GITHUB_TOKEN을 추가하세요.")
        return
    
    # 기본 저장소 설정 (인자로 제공되지 않은 경우)
    default_repos = [
        "pallets/flask",
        "psf/requests",
        "pandas-dev/pandas"
    ]
    
    repositories = args.repos if args.repos else default_repos
    
    # 선택된 작업 실행
    if args.action in ["collect", "all"]:
        logger.info("데이터 수집 시작...")
        from collect_data import GitHubDataCollector
        
        collector = GitHubDataCollector(github_token)
        
        for repo_name in repositories:
            logger.info(f"저장소 {repo_name} 데이터 수집 중...")
            collector.collect_repository_data(
                repo_name=repo_name,
                days_back=args.days,
                max_items={
                    "commits": args.max_items,
                    "pull_requests": args.max_items // 2,
                    "issues": args.max_items // 2
                }
            )
        
        logger.info("데이터 수집 완료!")
    
    if args.action in ["analyze", "all"]:
        logger.info("데이터 분석 시작...")
        from analyze_data import GitHubDataAnalyzer
        
        analyzer = GitHubDataAnalyzer()
        analyzer.run_analysis(repositories)
        
        logger.info("데이터 분석 완료!")
    
    if args.action in ["dashboard", "all"]:
        logger.info("대시보드 실행...")
        import subprocess
        import os
        
        subprocess.run(["streamlit", "run", "dashboard.py"], env=os.environ)

    logger.info("작업 완료!")

if __name__ == "__main__":
    main()
