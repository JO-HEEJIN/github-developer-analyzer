cd ~
mkdir github-developer-analyzer
cd github-developer-analyzer
conda create -n github_env python=3.9 -y
conda activate github_env
conda install numpy pandas matplotlib scikit-learn -y
pip install streamlit PyGithub python-dotenv plotly networkx tqdm joblib seaborn
mkdir data models results visualizations
echo "GITHUB_TOKEN=your_token_here" > .env
cp /Users/momo/github_analyzer/*.py .
python main.py all