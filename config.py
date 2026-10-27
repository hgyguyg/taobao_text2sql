import os
from pathlib import Path

from langchain_qwq import ChatQwen

OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
BASE_URL="https://ws-s00wtjjrfhr26ld0.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"

model = ChatQwen(
    model= "qwen-max",
    api_key= OPENAI_API_KEY,
    base_url= BASE_URL,
    temperature=0
)

CHART_DIR= Path("./charts")
DATA_PATH = "./data/tianchi_mobile_recommend_train_user.csv"
TABLE = f"read_csv_auto('{DATA_PATH}')"