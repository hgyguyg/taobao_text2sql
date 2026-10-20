import os
from dotenv import load_dotenv

from langchain_qwq import ChatQwen

load_dotenv()

model = ChatQwen(
    model= "qwen-max",
    api_key= os.getenv("OPENAI_API_KEY"),
    base_url= os.getenv("BASE_URL")
)