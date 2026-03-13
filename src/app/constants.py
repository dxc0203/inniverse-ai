import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOGS_DIR = os.path.join(ROOT_DIR, "logs")
PROMPTS_DIR = os.path.join(ROOT_DIR, "Prompts")
os.makedirs(PROMPTS_DIR, exist_ok=True)

MODEL_PROMPTS_DIR = os.path.join(PROMPTS_DIR, "Models")
SCENE_PROMPTS_DIR = os.path.join(PROMPTS_DIR, "Scenes")
os.makedirs(MODEL_PROMPTS_DIR, exist_ok=True)
os.makedirs(SCENE_PROMPTS_DIR, exist_ok=True)

LANG = "zh-CN"
