# GitHub 개발자 행동 패턴 분석기

GitHub API를 활용하여 오픈 소스 프로젝트의 개발자 행동 데이터를 수집, 분석하고 시각화하는 데이터 분석 프로젝트입니다.

![대시보드 이미지](https://github.com/JO-HEEJIN/github-developer-analyzer/raw/main/image.png)


### 🚀 Live Streamlit Dashboard  
**GitHub Developer Behavior Analyzer**  
👉 [Launch the Dashboard](https://jo-heejin-github-developer-analyzer-dashboard-ujxmtk.streamlit.app)

This dashboard visualizes and analyzes open-source developer behavior based on data collected via the GitHub API.

- **Analyzed Repositories**: Flask, pandas, requests, and other major OSS projects  
- **Key Features**:  
  - Commit, PR, and issue statistics  
  - Temporal activity patterns (by hour, day, month)  
  - PR approval prediction model  
  - Message length and code line change analytics



## 주요 기능

- **데이터 수집**:
  - GitHub API를 통한 저장소 데이터 수집 (커밋, PR, 이슈)
  - 개발자 활동 메타데이터 추출

- **개발자 행동 패턴 분석**:
  - 시간대별/요일별 활동 분포
  - 코드 변경 패턴 분석
  - 커밋 메시지 특성 분석
  - 개발자 프로필링 및 클러스터링

- **PR 분석**:
  - PR 승인/거부 패턴
  - 코드 변경량과 처리 시간 관계
  - 리뷰 네트워크 분석

- **인터랙티브 대시보드**:
  - 실시간 필터링 및 탐색
  - 다양한 시각화 차트
  - 개발자 행동 인사이트

- **예측 모델**:
  - PR 승인 예측 머신러닝 모델
  - 개발자 클러스터 분류

## 설치 방법

1. 저장소 클론
```bash
git clone https://github.com/yourusername/github-developer-analyzer.git
cd github-developer-analyzer
```

2. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

3. 환경 변수 설정
`.env` 파일을 생성하고 GitHub 토큰을 추가합니다:
```
GITHUB_TOKEN=your_github_personal_access_token
```

GitHub 토큰은 [GitHub 개인 액세스 토큰](https://github.com/settings/tokens) 페이지에서 생성할 수 있습니다. `repo` 및 `user` 스코프 권한이 필요합니다.

## 사용 방법

### 데이터 수집
```bash
python main.py collect --repos "owner1/repo1" "owner2/repo2" --days 60
```

### 데이터 분석
```bash
python main.py analyze
```

### 대시보드 실행
```bash
python main.py dashboard
```

### 모든 단계 한번에 실행
```bash
python main.py all --repos "owner1/repo1" "owner2/repo2"
```

## 명령줄 옵션

- `action`: 실행할 작업 (`collect`, `analyze`, `dashboard`, 또는 `all`)
- `--repos`: 분석할 GitHub 저장소 목록 (기본값: 'pallets/flask', 'psf/requests', 'pandas-dev/pandas')
- `--days`: 수집할 데이터의 기간(일) (기본값: 30)
- `--max-items`: 저장소당 최대 항목 수 (기본값: 200)

## 프로젝트 구조

```
github-developer-analyzer/
│
├── main.py                   # 메인 실행 스크립트
├── collect_data.py           # 데이터 수집 모듈
├── analyze_data.py           # 데이터 분석 모듈
├── dashboard.py              # 스트림릿 대시보드 
├── requirements.txt          # 필요한 패키지 목록
├── .env                      # 환경 변수 (GitHub 토큰 포함)
│
├── data/                     # 데이터 저장 디렉토리
│   ├── owner_repo/           # 저장소별 디렉토리
│   │   ├── commits.csv       # 커밋 데이터
│   │   ├── pull_requests.csv # PR 데이터
│   │   ├── issues.csv        # 이슈 데이터
│   │   └── metadata.csv      # 저장소 메타데이터
│
├── results/                  # 분석 결과 저장 디렉토리
│   ├── developer_patterns/   # 개발자 패턴 분석 결과
│   ├── pr_patterns/          # PR 패턴 분석 결과
│   ├── clustering/           # 클러스터링 분석 결과
│   ├── time_patterns/        # 시간 패턴 분석 결과
│   └── models/               # 훈련된 모델 저장
```

## 분석 내용 예시

1. **개발자 활동 패턴**:
   - 시간별/요일별 커밋 활동 분포
   - 가장 활발한 시간대 분석
   - 개발자별 활동 패턴 비교

2. **코드 변경 분석**:
   - 커밋 크기 분포
   - 파일 변경 패턴
   - 코드 추가/삭제 비율

3. **협업 패턴**:
   - PR 리뷰 관계 네트워크
   - 코드 리뷰 효율성
   - 팀 구조 분석

4. **개발자 클러스터링**:
   - 유사한 행동 패턴을 가진 개발자 그룹화
   - 개발자 "유형" 식별
   - 클러스터 특성 분석

5. **PR 승인 예측**:
   - PR 승인 가능성 예측
   - 승인에 영향을 미치는 주요 요인
   - 최적의 PR 제출 전략 제안

## 기술 스택

- **데이터 수집**: PyGithub, Python requests
- **데이터 처리 및 분석**: Pandas, NumPy
- **기계 학습**: Scikit-learn
- **시각화**: Matplotlib, Seaborn, Plotly
- **대시보드**: Streamlit

## 개발자 행동 패턴 인사이트

이 프로젝트를 통해 얻을 수 있는 인사이트:

1. **작업 시간 패턴**:
   - 개발자들이 언제 가장 활발히 활동하는지
   - 평일/주말 활동 분포
   - 시간대별 생산성 패턴

2. **코드 기여 스타일**:
   - "추가형" vs "삭제형" 개발자
   - 대규모 변경 vs 작은 변경 선호도
   - 커밋 메시지 패턴

3. **협업 동태학**:
   - 코드 리뷰 네트워크
   - 팀 구조와 상호작용
   - PR 승인 패턴

4. **개발자 유형화**:
   - 유사한 작업 패턴을 가진 개발자 그룹
   - 개발자 "페르소나" 식별
   - 팀 다양성 분석

## 기여 방법

1. 이 저장소를 포크합니다
2. 새 기능 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`)
3. 변경 사항을 커밋합니다 (`git commit -m 'Add some amazing feature'`)
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`)
5. Pull Request를 생성합니다

## 라이센스

MIT 라이센스

## 면책 조항

이 도구는 GitHub의 서비스 약관을 준수하여 사용해야 합니다. 데이터 수집 시 API 속도 제한을 고려하고, 개인 정보 보호 원칙을 준수하세요.
