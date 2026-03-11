import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), \"..\", \"..\"))
LOGS_DIR = os.path.join(ROOT_DIR, \"logs\")
PROMPTS_DIR = os.path.join(ROOT_DIR, \"Prompts\")
os.makedirs(PROMPTS_DIR, exist_ok=True)

LANG = \"zh-CN\"
