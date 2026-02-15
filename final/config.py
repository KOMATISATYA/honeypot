import os
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY1 = os.getenv("GROQ_API_KEY1")
GROQ_API_KEY2 = os.getenv("GROQ_API_KEY2")

API_KEY = os.getenv("HONEYPOT_API_KEY", "SECRET_KEY")
