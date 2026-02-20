import os
from dotenv import load_dotenv

load_dotenv()
DEEPSEEK_API_KEY =  os.getenv("DEEPSEEK_API_KEY")

API_KEY = os.getenv("HONEYPOT_API_KEY", "SECRET_KEY")
