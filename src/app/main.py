import streamlit as st
import os
import time
import shutil
import sys
from dotenv import load_dotenv
import pyperclip
import google.genai as genai
import base64
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Constants ---
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOGS_DIR = os.path.join(ROOT_DIR, "logs")
PROMPTS_DIR = os.path.join(ROOT_DIR, "Prompts")
os.makedirs(PROMPTS_DIR, exist_ok=True) # 確保資料夾存在
load_dotenv()

st.set_page_config(page_title="Inniverse AI 实验室", layout="wide")

# --- Session State ---
if "uploaded_files" not in st.session_state:
    st.session_state["uploaded_files"] = []
if "input_prompt" not in st.session_state:
    st.session_state["input_prompt"] = "一幅美丽的风景画."
if "selected_prompt_name" not in st.session_state:
    st.session_state["selected_prompt_name"] = ""
if "navigate_to" not in st.session_state:
    st.session_state["navigate_to"] = None


lang = "zh-CN"

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


# 3. 核心處理邏輯
def generate_image_from_text(prompt, is_test):
    if is_test:
        time.sleep(1)
        # In test mode, we return a placeholder image path
        placeholder_path = os.path.join(ROOT_DIR, "placeholder.png")
        if not os.path.exists(placeholder_path):
            img = Image.new('RGB', (256, 256), color = 'darkgray')
            img.save(placeholder_path)
        return [placeholder_path]
    else:
        api_key_to_use = st.session_state.get("api_key_input") or os.getenv("GEMINI_API_KEY")
        if not api_key_to_use:
            st.error("Gemini API 密钥未配置。")
            return None
        try:
            genai.configure(api_key=api_key_to_use)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)

            image_data_list = []
            if response and response.parts:
                for part in response.parts:
                    if part.inline_data:
                        image_data_list.append(part.inline_data.data)
            return image_data_list
        except Exception as e:
            st.error(f"生成图像时发生意外错误：{e}")
            return None

def generate_image_from_image_and_text(image, prompt, is_test):
    if is_test:
        time.sleep(1)
        # In test mode, we return a placeholder image path
        placeholder_path = os.path.join(ROOT_DIR, "placeholder.png")
        if not os.path.exists(placeholder_path):
            img = Image.new('RGB', (256, 256), color = 'darkgray')
            img.save(placeholder_path)
        return [placeholder_path]
    else:
        api_key_to_use = st.session_state.get("api_key_input") or os.getenv("GEMINI_API_KEY")
        if not api_key_to_use:
            st.error("Gemini API 密钥未配置。")
            return None
        try:
            genai.configure(api_key=api_key_to_use)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content([prompt, image])

            image_data_list = []
            if response and response.parts:
                for part in response.parts:
                    if part.inline_data:
                        image_data_list.append(part.inline_data.data)
            return image_data_list
        except Exception as e:
            st.error(f"生成图像时发生意外错误：{e}")
            return None


# 4. 主介面：上傳與執行
if page == "新项目":
    
    project_name = st.text_input(
        "项目名称",
        value="我的项目_001",
        key="input_project_name",
    )

    user_prompt = st.text_area(
        "提示",
        key="input_prompt",
        height=150
    )

    task_type = st.selectbox(
        "选择任务类型",
        ["从文本生成图像", "从图像和文本生成图像"],
        key="task_type_selector",
    )

    # Conditionally show the file uploader
    if task_type == "从图像和文本生成图像":
        newly_uploaded_files = st.file_uploader(
            "上传图片",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=False,
        )
        if newly_uploaded_files:
            st.session_state["uploaded_files"] = [newly_uploaded_files]


    if task_type == "从图像和文本生成图像" and st.session_state["uploaded_files"]:
        if len(st.session_state["uploaded_files"]) > 5:
            st.error(
                f"您上传了 {len(st.session_state['uploaded_files'])} 个文件。最多 5 个。"
            )
        else:
            # 預覽與縮圖處理
            processed_imgs = []
            cols = st.columns(len(st.session_state["uploaded_files"]))

            for idx, up_file in enumerate(st.session_state["uploaded_files"]):
                img = Image.open(up_file)
                # 限制圖片大小以優化上傳與 AI 讀取 (Max 1024px)
                img.thumbnail((1024, 1024))
                processed_imgs.append(img)

                with cols[idx]:
                    st.image(
                        img,
                        caption=f"预览 {idx + 1}",
                        use_container_width=True,
                    )
                    if st.button("删除", key=f"delete_{idx}"):
                        st.session_state["uploaded_files"].pop(idx)
                        st.rerun()

    if st.button("运行 AI"):
        # 建立專案 Log 資料夾
        log_dir = os.path.join(LOGS_DIR, project_name)
        os.makedirs(os.path.join(log_dir, "inputs"), exist_ok=True)
        os.makedirs(os.path.join(log_dir, "outputs"), exist_ok=True)

        # 儲存 Prompt
        with open(
            os.path.join(log_dir, "prompt.txt"), "w", encoding="utf-8"
        ) as f:
            f.write(user_prompt)

        with st.spinner("处理中..."):
            if task_type == "从文本生成图像":
                image_results = generate_image_from_text(user_prompt, test_mode)
                if image_results:
                    st.subheader("生成的图像")
                    # Create columns for the number of images
                    cols = st.columns(len(image_results))
                    for i, img_data in enumerate(image_results):
                        if test_mode: # Test mode returns a path
                            img_path = img_data
                            with cols[i]:
                                st.image(img_path, caption=f"生成的图像 {i+1}", use_container_width=True)
                        else: # Real mode returns image bytes
                            img_path = os.path.join(log_dir, "outputs", f"generated_image_{i+1}.png")
                            with open(img_path, "wb") as f:
                                f.write(img_data)
                            with cols[i]:
                                st.image(img_path, caption=f"生成的图像 {i+1}", use_container_width=True)

                    st.success("图像生成完成！")
            
            elif task_type == "从图像和文本生成图像":
                if 'processed_imgs' in locals() and processed_imgs:
                    input_image = processed_imgs[0] # Take the first image
                    input_image.save(os.path.join(log_dir, "inputs", "input_image.png"))

                    image_results = generate_image_from_image_and_text(input_image, user_prompt, test_mode)
                    if image_results:
                        st.subheader("生成的图像")
                        # Create columns for the number of images
                        cols = st.columns(len(image_results))
                        for i, img_data in enumerate(image_results):
                            if test_mode: # Test mode returns a path
                                img_path = img_data
                                with cols[i]:
                                    st.image(img_path, caption=f"生成的图像 {i+1}", use_container_width=True)
                            else: # Real mode returns image bytes
                                img_path = os.path.join(log_dir, "outputs", f"generated_image_{i+1}.png")
                                with open(img_path, "wb") as f:
                                    f.write(img_data)
                                with cols[i]:
                                    st.image(img_path, caption=f"生成的图像 {i+1}", use_container_width=True)

                        st.success("图像生成完成！")
                else:
                    st.warning("请为此任务上传图片。")

elif page == "提示词管理":
    st.header("提示词管理")

    prompt_files = [f for f in os.listdir(PROMPTS_DIR) if f.endswith(".txt")]
    selected_prompt = st.selectbox("选择提示", ["创建新提示"] + prompt_files)

    prompt_content = ""
    if selected_prompt != "创建新提示":
        try:
            with open(os.path.join(PROMPTS_DIR, selected_prompt), "r", encoding="utf-8") as f:
                prompt_content = f.read()
            st.session_state["selected_prompt_name"] = selected_prompt # 記錄選擇的檔案
        except FileNotFoundError:
            st.error("未找到提示文件。")
            prompt_content = "" # or handle appropriately
        except Exception as e:
            st.error(f"读取提示文件时出错：{e}")
            prompt_content = "" # or handle appropriately


    new_prompt_name = st.text_input("提示名称（例如 'my_prompt.txt'）", value=selected_prompt if selected_prompt != "创建新提示" else "")
    prompt_text = st.text_area("提示内容", value=prompt_content, height=300)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("保存提示", use_container_width=True):
            if new_prompt_name and prompt_text:
                # Basic validation for filename
                if not new_prompt_name.endswith(".txt"):
                    new_prompt_name += ".txt"

                try:
                    with open(os.path.join(PROMPTS_DIR, new_prompt_name), "w", encoding="utf-8") as f:
                        f.write(prompt_text)
                    st.success(f"提示 '{new_prompt_name}' 保存成功！")
                    st.session_state["selected_prompt_name"] = new_prompt_name # 更新選擇的檔案
                    # Rerun to update the selectbox
                    st.rerun()
                except Exception as e:
                    st.error(f"保存提示时出错：{e}")
            else:
                st.warning("提示名称和内容不能为空。")

    with col2:
        if selected_prompt != "创建新提示":
            if st.button("删除提示", type="primary", use_container_width=True):
                try:
                    os.remove(os.path.join(PROMPTS_DIR, selected_prompt))
                    st.success(f"提示 '{selected_prompt}' 已删除。")
                    st.session_state["selected_prompt_name"] = "" # 清除選擇
                    # Rerun to update the selectbox
                    st.rerun()
                except Exception as e:
                    st.error(f"删除提示时出错：{e}")

elif page == "历史记录":
    st.header("历史记录")
    log_root = LOGS_DIR
    if os.path.exists(log_root):
        projects = [
            d for d in os.listdir(log_root) if os.path.isdir(os.path.join(log_root, d))
        ]
        if projects:
            selected_project = st.selectbox(
                "选择项目", projects
            )
            project_path = os.path.join(log_root, selected_project)

            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "重新启动项目",
                    use_container_width=True,
                ):
                    # 讀取舊 Prompt
                    old_prompt_path = os.path.join(project_path, "prompt.txt")
                    if os.path.exists(old_prompt_path):
                        with open(old_prompt_path, "r", encoding="utf-8") as f:
                            st.session_state["input_prompt"] = f.read()
                    st.session_state["input_project_name"] = selected_project
                    st.session_state["navigate_to"] = "新项目"
                    st.rerun()
            with col2:
                # 確認刪除狀態檢查
                if st.session_state.get(f"confirm_delete_{selected_project}"):
                    st.warning("您确定要删除此项目吗？")
                    if st.button(
                        "是的，删除它",
                        key=f"yes_{selected_project}",
                        type="primary",
                        use_container_width=True,
                    ):
                        shutil.rmtree(project_path)
                        del st.session_state[f"confirm_delete_{selected_project}"]
                        st.rerun()
                    if st.button(
                        "不，取消",
                        key=f"no_{selected_project}",
                        use_container_width=True,
                    ):
                        del st.session_state[f"confirm_delete_{selected_project}"]
                        st.rerun()
                else:
                    if st.button(
                        "删除项目",
                        type="primary",
                        use_container_width=True,
                    ):
                        st.session_state[f"confirm_delete_{selected_project}"] = True
                        st.rerun()

            # 顯示 Prompt
            prompt_path = os.path.join(project_path, "prompt.txt")
            if os.path.exists(prompt_path):
                with open(prompt_path, "r", encoding="utf-8") as f:
                    st.text_area(
                        "使用的提示",
                        f.read(),
                        disabled=True,
                    )

            # 顯示圖片對比 (輸入 vs 輸出)
            input_dir = os.path.join(project_path, "inputs")
            output_dir = os.path.join(project_path, "outputs")

            if os.path.exists(input_dir):
                st.subheader(
                    "输入/输出比较"
                )
                input_files = sorted(
                    [
                        f
                        for f in os.listdir(input_dir)
                        if f.lower().endswith((".png", ".jpg", ".jpeg"))
                    ]
                )

                if input_files:
                    for f_name in input_files:
                        c1, c2 = st.columns(2)

                        # 顯示輸入圖
                        img_path = os.path.join(input_dir, f_name)
                        img = Image.open(img_path)
                        with c1:
                            st.image(
                                img,
                                caption=f"输入：{f_name}",
                                use_container_width=True,
                            )

                        # 嘗試尋找對應的輸出圖
                        # 支援兩種命名模式: 1. model_output_{filename} (bulk_processor.py) 2. {filename}
                        out_candidates = [f"model_output_{f_name}", f_name]
                        found_output = False

                        if os.path.exists(output_dir):
                            for cand in out_candidates:
                                out_path = os.path.join(output_dir, cand)
                                if os.path.exists(out_path):
                                    out_img = Image.open(out_path)
                                    with c2:
                                        st.image(
                                            out_img,
                                            caption=f"输出：{cand}",
                                            use_container_width=True,
                                        )
                                    found_output = True
                                    break

                        if not found_output:
                            with c2:
                                st.info(
                                    "未找到此输入的输出图像。"
                                )

            # 顯示輸出結果
            output_path = os.path.join(project_path, "outputs", "result.txt")
            if os.path.exists(output_path):
                st.subheader("结果")
                with open(output_path, "r", encoding="utf-8") as f:
                    st.markdown(f.read())
        else:
            st.info("在日志目录中找不到任何项目。")
    else:
        st.info("未找到日志目录。")
