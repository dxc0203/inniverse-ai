import streamlit as st
import os
from dotenv import load_dotenv

# Import local modules
from constants import LOGS_DIR, MODEL_PROMPTS_DIR, SCENE_PROMPTS_DIR, LANG
from pages_ui import render_new_project, render_prompt_management, render_history, render_prompt_gallery

load_dotenv()

st.set_page_config(page_title="Inniverse AI 实验室", layout="wide")

# --- Session State ---
if "uploaded_files" not in st.session_state:
    st.session_state["uploaded_files"] = []
if "input_prompt" not in st.session_state:
    st.session_state["input_prompt"] = "A beautiful landscape painting."
if "selected_prompt_name" not in st.session_state:
    st.session_state["selected_prompt_name"] = ""
if "navigate_to" not in st.session_state:
    st.session_state["navigate_to"] = None

st.title("Inniverse AI")

# --- Sidebar ---
with st.sidebar:
    if st.session_state["navigate_to"]:
        st.session_state["page_nav"] = st.session_state["navigate_to"]
        st.session_state["navigate_to"] = None
    
    page = st.radio(
        "菜单",
        [
            "新项目",
            "提示词库",
            "模特提示词管理",
            "场景提示词管理",
            "历史记录",
            
        ],
        key="page_nav",
    )
    st.divider()
    st.header("开发者工具")
    
    api_key = st.text_input(
        "Gemini API 密鑰",
        type="password",
        key="api_key_input",
        help="请输入您的 API 密鑰。如果未提供，应用程序将尝试使用环境变量。"
    )
    
    test_mode = st.checkbox("测试模式", value=False)
    if test_mode:
        st.warning("测试模式已开启。不会进行 API 调用。")
    st.divider()

# --- Main Interface ---
if page == "新项目":
    render_new_project(LOGS_DIR, MODEL_PROMPTS_DIR, SCENE_PROMPTS_DIR, test_mode)
elif page == "提示词库":
    render_prompt_gallery(MODEL_PROMPTS_DIR, SCENE_PROMPTS_DIR)
elif page == "模特提示词管理":
    render_prompt_management(MODEL_PROMPTS_DIR, "模特")
elif page == "场景提示词管理":
    render_prompt_management(SCENE_PROMPTS_DIR, "场景")
elif page == "历史记录":
    render_history(LOGS_DIR)
