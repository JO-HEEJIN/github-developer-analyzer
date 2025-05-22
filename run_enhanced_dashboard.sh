#!/bin/bash
# run_enhanced_dashboard.sh

echo "🚀 GitHub 개발자 행동 패턴 분석기 Pro 시작 중..."

# 가상환경 활성화 확인 (conda와 일반 venv 모두 지원)
if [[ "$VIRTUAL_ENV" != "" ]] || [[ "$CONDA_DEFAULT_ENV" != "" ]]; then
    if [[ "$CONDA_DEFAULT_ENV" != "" ]]; then
        echo "✅ Conda 환경 활성화됨: $CONDA_DEFAULT_ENV"
    else
        echo "✅ 가상환경 활성화됨: $VIRTUAL_ENV"
    fi
else
    echo "⚠️  가상환경이 활성화되지 않았습니다."
    echo "다음 명령어로 가상환경을 활성화하세요:"
    echo "conda activate github_env"
    echo "또는"
    echo "source your_venv/bin/activate"
fi

# GitHub 토큰 확인
if [ -f ".env" ]; then
    echo "✅ .env 파일 발견"
    if grep -q "GITHUB_TOKEN=" .env; then
        echo "✅ GitHub 토큰 설정 확인됨"
    else
        echo "❌ .env 파일에 GitHub 토큰이 없습니다."
        echo "GITHUB_TOKEN=your_token_here 형식으로 추가하세요."
    fi
else
    echo "❌ .env 파일이 없습니다."
    echo "GitHub 토큰을 포함한 .env 파일을 생성하세요."
fi

# 필요한 디렉토리 생성
mkdir -p data results models

echo "📁 필요한 디렉토리 확인 완료"

# Streamlit 대시보드 실행
echo "🌐 향상된 대시보드를 실행합니다..."
echo "브라우저에서 http://localhost:8502 를 열어 확인하세요."

# 포트 8502로 실행 (기본 대시보드와 구분)
streamlit run enhanced_dashboard.py --server.port 8502