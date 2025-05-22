# GitHub 개발자 행동 패턴 분석기 v2.0

GitHub API를 활용하여 오픈 소스 프로젝트의 개발자 행동 데이터를 실시간으로 수집, 분석하고 시각화하는 고도화된 데이터 분석 프로젝트입니다.

![GitHub](https://img.shields.io/badge/GitHub-API-181717?style=for-the-badge&logo=github)
![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

## 🆕 새로운 기능 (v2.0)

### 🔍 실시간 분석 엔진
- **실시간 저장소 검색**: GitHub API를 통한 즉석 검색
- **고급 필터링**: 언어, 인기도, 생성일, 토픽별 필터
- **즉석 분석**: 저장소 URL 입력만으로 몇 초 내 종합 분석
- **API 모니터링**: 실시간 API 제한 상태 확인

### 📊 향상된 분석 기능
- **저장소 건강도 스코어**: 0-100점 종합 평가 시스템
- **벤치마킹**: 동일 언어 프로젝트와의 비교 분석
- **다중 저장소 비교**: 레이더 차트를 통한 시각적 비교
- **AI 기반 권장사항**: 맞춤형 개선 제안

### 🎯 사용자 경험 개선
- **카드뷰/테이블뷰**: 선택 가능한 표시 방식
- **분석 히스토리**: 최근 분석한 저장소 기록 관리
- **진행률 표시**: 실시간 분석 진행 상황
- **반응형 디자인**: 모바일 친화적 인터페이스

### 🤖 지능형 기능
- **자동 카테고리 분류**: 프로젝트 유형 자동 감지
- **트렌드 분석**: 시간대별 활동 패턴 분석
- **기여자 네트워크**: 협업 관계 시각화
- **예측 모델**: PR 승인 확률 예측

## 🚀 빠른 시작

### 1. 환경 설정

#### 필수 요구사항
- Python 3.9 이상
- GitHub Personal Access Token
- 안정적인 인터넷 연결

#### 설치 방법

```bash
# 저장소 클론
git clone https://github.com/yourusername/github-developer-analyzer.git
cd github-developer-analyzer

# 가상환경 생성 (Conda 사용)
conda create -n github_env python=3.9
conda activate github_env

# 또는 venv 사용
python -m venv github_env
source github_env/bin/activate  # Linux/Mac
# github_env\Scripts\activate   # Windows

# 필요한 패키지 설치
pip install -r requirements.txt
```

### 2. GitHub 토큰 설정

#### 토큰 생성
1. [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. "Generate new token (classic)" 클릭
3. 필요한 권한 선택:
   - `repo` (전체 선택)
   - `user` (사용자 정보)
4. 토큰 생성 후 복사

#### 환경 변수 설정
```bash
# .env 파일 생성
echo "GITHUB_TOKEN=your_github_token_here" > .env

# 기타 설정 (선택사항)
echo "MAX_ITEMS_PER_REQUEST=100" >> .env
echo "REQUEST_DELAY=0.5" >> .env
```

### 3. 실행 방법

#### v2.0 실시간 분석 대시보드
```bash
# 향상된 대시보드 실행 (포트 8502)
streamlit run enhanced_dashboard.py --server.port 8502

# 또는 실행 스크립트 사용
chmod +x run_enhanced_dashboard.sh
./run_enhanced_dashboard.sh
```

#### v1.0 기본 분석 (배치 처리)
```bash
# 데이터 수집 및 분석
python main.py all

# 또는 단계별 실행
python main.py collect --repos "owner/repo1" "owner/repo2"
python main.py analyze
python main.py dashboard
```

## 📁 프로젝트 구조

```
github-developer-analyzer/
│
├── 📊 v2.0 (실시간 분석)
│   ├── enhanced_dashboard.py      # 향상된 Streamlit 대시보드
│   ├── realtime_analyzer.py       # 실시간 분석 엔진
│   └── run_enhanced_dashboard.sh   # 실행 스크립트
│
├── 📈 v1.0 (배치 분석)
│   ├── main.py                    # 메인 실행 스크립트
│   ├── collect_data.py            # 데이터 수집 모듈
│   ├── analyze_data.py            # 데이터 분석 모듈
│   └── dashboard.py               # 기본 대시보드
│
├── 📂 데이터 및 결과
│   ├── data/                      # 수집된 원시 데이터
│   ├── results/                   # 분석 결과
│   │   ├── developer_patterns/    # 개발자 패턴 분석
│   │   ├── pr_patterns/          # PR 패턴 분석
│   │   ├── clustering/           # 클러스터링 결과
│   │   ├── time_patterns/        # 시간 패턴 분석
│   │   └── models/               # 훈련된 ML 모델
│   └── visualizations/           # 생성된 시각화
│
├── 📋 설정 및 문서
│   ├── requirements.txt          # Python 패키지 목록
│   ├── .env                      # 환경 변수 (GitHub 토큰)
│   ├── .gitignore               # Git 무시 파일
│   └── README.md                # 프로젝트 설명서
│
└── 🧪 유틸리티
    ├── setup.py                 # 프로젝트 초기 설정
    └── setup.sh                 # 환경 설정 스크립트
```

## 🌿 브랜치 구조 및 버전 관리

### 브랜치 전략
```
main                           # 안정 버전 (v1.0)
├── feature/realtime-dashboard # 실시간 기능 (v2.0)
├── feature/ai-insights       # AI 기능 개발 중 (v3.0 예정)
├── feature/api-integration   # 외부 API 연동 (v3.1 예정)
└── hotfix/*                  # 긴급 버그 수정
```

### 버전 히스토리
- **v1.0.0**: 기본 GitHub 분석 기능
  - 배치 데이터 수집 및 분석
  - 기본 Streamlit 대시보드
  - 개발자 패턴 분석
  - PR 승인 예측 모델

- **v2.0.0**: 실시간 분석 엔진 (현재)
  - 실시간 저장소 검색
  - 향상된 UI/UX
  - 저장소 건강도 스코어
  - 다중 저장소 비교

- **v3.0.0**: AI 인사이트 (계획)
  - 트렌드 예측 모델
  - 자동 리포트 생성
  - 코드 품질 분석

## 🎯 주요 기능 상세

### 실시간 저장소 검색
- **고급 검색 필터**: 언어, 스타 수, 포크 수, 생성일
- **인기 검색어**: 미리 정의된 트렌드 키워드
- **결과 정렬**: Stars, 최근 업데이트, 생성일 기준
- **빠른 액션**: 검색 결과에서 즉시 분석 시작

### 종합 분석 대시보드
#### 📊 핵심 지표
- **저장소 건강도**: 활동성, 인기도, 관리 수준 종합 평가
- **벤치마킹**: 동일 언어 프로젝트 대비 순위
- **성장 트렌드**: 스타, 포크, 이슈 증가 패턴

#### 👥 기여자 분석
- **기여자 분포**: 상위 기여자 및 기여도 분석
- **활동 패턴**: 시간대별, 요일별 커밋 패턴
- **협업 네트워크**: 리뷰 관계 시각화

#### 💻 기술 스택 분석
- **언어 분포**: 코드베이스 언어 구성
- **의존성 분석**: 주요 라이브러리 및 프레임워크
- **코드 품질**: 평균 커밋 크기, 파일 변경 패턴

#### 🎯 맞춤형 권장사항
- **개발 전략**: 프로젝트 특성에 맞는 개선 방안
- **커뮤니티 성장**: 기여자 유치 및 참여 증대 방안
- **기술 로드맵**: 기술 스택 개선 제안

### 다중 저장소 비교
- **레이더 차트**: 다차원 성능 비교
- **지표별 순위**: 카테고리별 우승자 선정
- **상대적 분석**: 선택한 저장소들 간의 상대적 위치

## 🛠️ 기술 스택

### 🐍 백엔드
- **Python 3.9+**: 메인 개발 언어
- **PyGithub**: GitHub API 클라이언트
- **Pandas**: 데이터 처리 및 분석
- **NumPy**: 수치 계산
- **Scikit-learn**: 머신러닝 모델

### 🎨 프론트엔드
- **Streamlit**: 웹 애플리케이션 프레임워크
- **Plotly**: 인터랙티브 시각화
- **Matplotlib/Seaborn**: 정적 차트 생성

### 📊 데이터 처리
- **asyncio**: 비동기 데이터 수집
- **concurrent.futures**: 병렬 처리
- **python-dotenv**: 환경 변수 관리

### 🔧 개발 도구
- **Git**: 버전 관리
- **GitHub Actions**: CI/CD (예정)
- **pytest**: 테스트 프레임워크 (예정)

## 📊 분석 예시

### 예시 1: 인기 머신러닝 프레임워크 비교
```python
# 실시간 검색으로 다음 저장소들을 비교 분석
repositories = [
    "tensorflow/tensorflow",
    "pytorch/pytorch", 
    "scikit-learn/scikit-learn",
    "keras-team/keras"
]

# 각 저장소의 건강도 스코어, 기여자 수, 활동 패턴을 
# 레이더 차트로 비교하여 인사이트 도출
```

### 예시 2: 스타트업을 위한 웹 프레임워크 선택
```python
# 검색어: "web framework"
# 필터: Python, 최소 1000 stars
# 결과: Django, Flask, FastAPI 등을 비교하여
# 프로젝트 규모와 팀 크기에 맞는 최적 선택 제안
```

## 🔮 향후 개발 계획

### v3.0: AI 인사이트 엔진
- **트렌드 예측**: 저장소의 미래 성장 예측
- **코드 품질 분석**: AI 기반 코드 리뷰
- **자동 리포트**: 주간/월간 프로젝트 리포트 생성

### v3.1: 외부 통합
- **Slack/Discord 봇**: 실시간 알림 및 분석
- **GitHub 앱**: 저장소에 직접 설치 가능한 앱
- **REST API**: 다른 서비스에서 활용 가능한 API

### v3.2: 엔터프라이즈 기능
- **팀 대시보드**: 조직 내 여러 저장소 통합 관리
- **권한 관리**: 사용자별 접근 권한 설정
- **데이터 내보내기**: PDF, Excel 리포트 생성

## 🤝 기여 방법

### 개발 환경 설정
```bash
# 포크한 저장소 클론
git clone https://github.com/your-username/github-developer-analyzer.git
cd github-developer-analyzer

# 개발용 브랜치 생성
git checkout -b feature/your-feature-name

# 개발 의존성 설치
pip install -r requirements-dev.txt

# 코드 스타일 검사
black . && flake8 .

# 테스트 실행
pytest tests/
```

### 커밋 컨벤션
- `feat:` 새로운 기능 추가
- `fix:` 버그 수정
- `docs:` 문서 변경
- `style:` 코드 포맷팅
- `refactor:` 코드 리팩토링
- `test:` 테스트 추가/수정

### Pull Request 가이드라인
1. 기능별로 별도 브랜치 생성
2. 의미 있는 커밋 메시지 작성
3. 테스트 코드 포함
4. 문서 업데이트
5. 코드 리뷰 요청

## 📄 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🙏 감사의 말

- **GitHub API**: 풍부한 데이터 제공
- **Streamlit**: 빠른 웹 앱 개발 지원
- **Plotly**: 아름다운 시각화 도구
- **오픈소스 커뮤니티**: 영감과 학습 기회 제공

## 📞 문의 및 지원

- **Issues**: [GitHub Issues](https://github.com/yourusername/github-developer-analyzer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/github-developer-analyzer/discussions)
- **Email**: your.email@example.com

---

⭐ **이 프로젝트가 도움이 되었다면 별표를 눌러주세요!**

🚀 **기여하고 싶으시다면 언제든 Pull Request를 보내주세요!**

📊 **데이터 기반 의사결정으로 더 나은 오픈소스 생태계를 만들어가요!**