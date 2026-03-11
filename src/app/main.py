import streamlit as st
import os
import shutil
from dotenv import load_dotenv
from PIL import Image

# Import local modules
from constants import LOGS_DIR, PROMPTS_DIR, LANG
from models import generate_image_from_text, generate_image_from_image_and_text
from ui_components import prompt_builder_ui

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

# 2. 設定中心 (側邊欄)
with st.sidebar:
    if st.session_state["navigate_to"]:
        st.session_state["page_nav"] = st.session_state["navigate_to"]
        st.session_state["navigate_to"] = None
    
    page = st.radio(
        "菜单",
        [
            "新项目",
            "提示词管理",
            "历史记录",
        ],
        key="page_nav",
    )
    st.divider()
    st.header("开发者工具")
    
    # API Key 設定
    api_key = st.text_input(
        "Gemini API 密钥",
        type="password",
        key="api_key_input",
        help="请输入您的 API 密钥。如果未提供，应用程序将尝试使用环境变量。"
    )
    
    # 🌟 加入 Test Mode 開關
    test_mode = st.checkbox("测试模式", value=True)
    if test_mode:
        st.warning("测试模式已开启。不会进行 API 调用。")
    st.divider()

# 4. 主介面：上傳與執行
if page == "新项目":
    project_name = st.text_input("项目名称", value="我的项目_001", key="input_project_name")
    
    # Use Prompt Builder
    new_prompt = prompt_builder_ui("new_project")
    if new_prompt:
        st.session_state["input_prompt"] = new_prompt
        st.success("已生成英文提示。")
        
    user_prompt = st.text_area("提示", key="input_prompt", height=150)
    
    task_type = st.selectbox("选择任务类型", ["从文本生成图像", "从图像和文本生成图像"], key="task_type_selector")
    
    if task_type == "从图像和文本生成图像":
        newly_uploaded_files = st.file_uploader("上传图片", type=["jpg", "jpeg", "png"], accept_multiple_files=False)
        if newly_uploaded_files:
            st.session_state["uploaded_files"] = [newly_uploaded_files]
            
    if task_type == "从图像和文本生成图像" and st.session_state["uploaded_files"]:
        if len(st.session_state["uploaded_files"]) > 5:
            st.error(f"您上传了 {len(st.session_state['uploaded_files'])} 个文件。最多 5 个。")
        else:
            processed_imgs = []
            cols = st.columns(len(st.session_state["uploaded_files"]))
            for idx, up_file in enumerate(st.session_state["uploaded_files"]):
                img = Image.open(up_file)
                img.thumbnail((1024, 1024))
                processed_imgs.append(img)
                with cols[idx]:
                    st.image(img, caption=f"预览 {idx + 1}", use_container_width=True)
                if st.button("删除", key=f"delete_{idx}"):
                    st.session_state["uploaded_files"].pop(idx)
                    st.rerun()
                    
    if st.button("运行 AI"):
        log_dir = os.path.join(LOGS_DIR, project_name)
        os.makedirs(os.path.join(log_dir, "inputs"), exist_ok=True)
        os.makedirs(os.path.join(log_dir, "outputs"), exist_ok=True)
        
        with open(os.path.join(log_dir, "prompt.txt"), "w", encoding="utf-8") as f:
            f.write(user_prompt)
            
        with st.spinner("处理中..."):
            if task_type == "从文本生成图像":
                image_results = generate_image_from_text(user_prompt, test_mode)
                if image_results:
                    st.subheader("生成的图像")
                    cols = st.columns(len(image_results))
                    for i, img_data in enumerate(image_results):
                        img_path = img_data if test_mode else os.path.join(log_dir, "outputs", f"generated_image_{i+1}.png")
                        if not test_mode:
                            with open(img_path, "wb") as f:
                                f.write(img_data)
                        with cols[i]:
                            st.image(img_path, caption=f"生成的图像 {i+1}", use_container_width=True)
                    st.success("图像 generation 完成！")
                    
            elif task_type == "从图像和文本生成图像":
                if 'processed_imgs' in locals() and processed_imgs:
                    input_image = processed_imgs[0]
                    input_image.save(os.path.join(log_dir, "inputs", "input_image.png"))
                    image_results = generate_image_from_image_and_text(input_image, user_prompt, test_mode)
                    if image_results:
                        st.subheader("生成的图像")
                        cols = st.columns(len(image_results))
                        for i, img_data in enumerate(image_results):
                            img_path = img_data if test_mode else os.path.join(log_dir, "outputs", f"generated_image_{i+1}.png")
                            if not test_mode:
                                with open(img_path, "wb") as f:
                                    f.write(img_data)
                            with cols[i]:
                                st.image(img_path, caption=f"生成的图像 {i+1}", use_container_width=True)
                        st.success("图像 generation 完成！")
                else:
                    st.warning("请为此任务上传图片。")

elif page == "提示词管理":
    st.header("提示词管理")
    prompt_files = [f for f in os.listdir(PROMPTS_DIR) if f.endswith(".txt")]
    selected_prompt = st.selectbox("选择提示", ["创建新提示"] + prompt_files)
    
    # Injected Prompt Builder for Management
    manage_prompt = prompt_builder_ui("manage")
    
    prompt_content = ""
    if selected_prompt != "创建新提示":
        try:
            with open(os.path.join(PROMPTS_DIR, selected_prompt), "r", encoding="utf-8") as f:
                prompt_content = f.read()
            st.session_state["selected_prompt_name"] = selected_prompt
        except Exception as e:
            st.error(f"读取提示文件时出错：{e}")
            
    # If builder was used, update content
    if manage_prompt:
        prompt_content = manage_prompt
        st.success("已生成英文提示。")
        
    new_prompt_name = st.text_input("提示名称（例如 'my_prompt.txt'）", value=selected_prompt if selected_prompt != "创建新提示" else "")
    prompt_text = st.text_area("提示内容", value=prompt_content, height=300)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("保存提示", use_container_width=True):
            if new_prompt_name and prompt_text:
                if not new_prompt_name.endswith(".txt"):
                    new_prompt_name += ".txt"
                try:
                    with open(os.path.join(PROMPTS_DIR, new_prompt_name), "w", encoding="utf-8") as f:
                        f.write(prompt_text)
                    st.success(f"提示 '{new_prompt_name}' 保存成功！")
                    st.session_state["selected_prompt_name"] = new_prompt_name
                    st.rerun()
                except Exception as e:
                    st.error(f"保存提示时出错：{e}")
            else:
                st.warning("提示名称 and 内容不能为空。")
    with col2:
        if selected_prompt != "创建新提示":
            if st.button("删除提示", type="primary", use_container_width=True):
                try:
                    os.remove(os.path.join(PROMPTS_DIR, selected_prompt))
                    st.success(f"提示 '{selected_prompt}' 已删除。")
                    st.session_state["selected_prompt_name"] = ""
                    st.rerun()
                except Exception as e:
                    st.error(f"删除提示时出错：{e}")

elif page == "历史记录":
    st.header("历史记录")
    log_root = LOGS_DIR
    if os.path.exists(log_root):
        projects = [ d for d in os.listdir(log_root) if os.path.isdir(os.path.join(log_root, d)) ]
        if projects:
            selected_project = st.selectbox("选择项目", projects)
            project_path = os.path.join(log_root, selected_project)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("重新启动项目", use_container_width=True):
                    old_prompt_path = os.path.join(project_path, "prompt.txt")
                    if os.path.exists(old_prompt_path):
                        with open(old_prompt_path, "r", encoding="utf-8") as f:
                            st.session_state["input_prompt"] = f.read()
                    st.session_state["input_project_name"] = selected_project
                    st.session_state["navigate_to"] = "新项目"
                    st.rerun()
            with col2:
                if st.session_state.get(f"confirm_delete_{selected_project}"):
                    st.warning("您确定要删除此项目吗？")
                    if st.button("是的，删除它", key=f"yes_{selected_project}", type="primary", use_container_width=True):
                        shutil.rmtree(project_path)
                        del st.session_state[f"confirm_delete_{selected_project}"]
                        st.rerun()
                    if st.button("不，取消", key=f"no_{selected_project}", use_container_width=True):
                        del st.session_state[f"confirm_delete_{selected_project}"]
                        st.rerun()
                else:
                    if st.button("删除项目", type="primary", use_container_width=True):
                        st.session_state[f"confirm_delete_{selected_project}"] = True
                        st.rerun()
            
            prompt_path = os.path.join(project_path, "prompt.txt")
            if os.path.exists(prompt_path):
                with open(prompt_path, "r", encoding="utf-8") as f:
                    st.text_area("使用的提示", f.read(), disabled=True)
            
            input_dir = os.path.join(project_path, "inputs")
            output_dir = os.path.join(project_path, "outputs")
            
            if os.path.exists(input_dir):
                st.subheader("输入/输出比较")
                input_files = sorted([f for f in os.listdir(input_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))])
                if input_files:
                    for f_name in input_files:
                        c1, c2 = st.columns(2)
                        img_path = os.path.join(input_dir, f_name)
                        img = Image.open(img_path)
                        with c1:
                            st.image(img, caption=f"输入：{f_name}", use_container_width=True)
                        
                        out_candidates = [f"model_output_{f_name}", f_name]
                        found_output = Falserefactor: restructure project modules and improve code reuse
                        if os.path.exists(output_dir):
                            for cand in out_candidates:
                                out_path = os.path.join(output_dir, cand)
                                if os.path.exists(out_path):
                                    out_img = Image.open(out_path)
                                    with c2:
                                        st.image(out_img, caption=f"输出：{cand}", use_container_width=True)
                                    found_output = True
                                    break
                        if not found_output:
                            with c2:
                                st.info("未找到此输入的输出图像。")
            
            output_path = os.path.join(project_path, "outputs", "result.txt")
            if os.path.exists(output_path):
                st.subheader("结果")
                with open(output_path, "r", encoding="utf-8") as f:
                    st.markdown(f.read())
        else:
            st.info("在日志目录中找不到任何项目。")
    else:
        st.info("未找到日志目录。")
