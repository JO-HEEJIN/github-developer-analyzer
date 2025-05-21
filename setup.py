# github_analyzer/setup.py

import os
import sys

# 필요한 디렉토리 생성
directories = ['data', 'models', 'visualizations']

for directory in directories:
    os.makedirs(directory, exist_ok=True)
    print(f"디렉토리 생성됨: {directory}")

# .env 파일 생성 (GitHub 토큰 저장용)
env_content = """# GitHub API 토큰
GITHUB_TOKEN=your_github_token_here

# 기타 설정
MAX_ITEMS_PER_REQUEST=100
REQUEST_DELAY=0.5
"""

with open('.env', 'w') as f:
    f.write(env_content)
print(".env 파일 생성됨 - GitHub 토큰을 추가해주세요")

# requirements.txt 생성
requirements = """pandas>=1.3.0
numpy>=1.20.0
matplotlib>=3.4.0
seaborn>=0.11.0
plotly>=5.3.0
scikit-learn>=1.0.0
streamlit>=1.10.0
PyGithub>=1.55.0
python-dotenv>=0.19.0
networkx>=2.6.0
joblib>=1.1.0
tqdm>=4.62.0
"""

with open('requirements.txt', 'w') as f:
    f.write(requirements)
print("requirements.txt 파일 생성됨")

print("\n셋업 완료! 다음 단계를 진행하세요:")
print("1. .env 파일에 GitHub 토큰을 추가하세요")
print("2. 'pip install -r requirements.txt' 명령으로 필요한 패키지를 설치하세요")
