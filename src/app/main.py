import streamlit as st
import os
import time
import shutil
import sys
from dotenv import load_dotenv
import pyperclip
import google.genai as genai
from google.genai import types
from google.api_core import exceptions
import base64
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Constants ---
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOGS_DIR = os.path.join(ROOT_DIR, "logs")
PROMPTS_DIR = os.path.join(ROOT_DIR, "Prompts")
os.makedirs(PROMPTS_DIR, exist_ok=True) # 確保資料夾存在
load_dotenv()

st.set_page_config(page_title="Inniverse AI Lab", layout="wide")

# --- Session State ---
if "uploaded_files" not in st.session_state:
    st.session_state["uploaded_files"] = []
if "input_prompt" not in st.session_state:
    st.session_state["input_prompt"] = "Describe this garment for a B2B platform. Focus on fabric and design."
if "selected_prompt_name" not in st.session_state:
    st.session_state["selected_prompt_name"] = ""


lang = "en"

st.title("Inniverse AI")

# 2. 設定中心 (側邊欄)
with st.sidebar:
    page = st.radio(
        "Menu",
        [
            "New Project",
            "Prompt Management",
            "History",
        ],
        key="page_nav",
    )
    st.divider()

    if page == "New Project":
        st.header("Developer Tools")
        # API Key 設定
        api_key = st.text_input(
            "Gemini API Key",
            type="password",
            key="api_key_input",
            help="Enter your API key. If not provided, the app will try to use environment variables."
        )
        # 🌟 加入 Test Mode 開關
        test_mode = st.checkbox("Test Mode", value=True)
        if test_mode:
            st.warning("Test mode is on. No API calls will be made.")

        st.divider()

        # --- Task Type Selection ---
        task_type = st.selectbox(
            "Select Task Type",
            ["Analyze Image & Generate Text", "Generate Image from Text", "Generate Image from Image & Text"],
            key="task_type_selector",
        )
        st.divider()

        # 設定專案與 Prompt
        project_name = st.text_input(
            "Project Name",
            value="MyProject_001",
            key="input_project_name",
        )

        # --- 從 Prompt Management 載入 ---
        if st.session_state.get("selected_prompt_name"):
             if st.button(f"Load '{st.session_state.selected_prompt_name}'"):
                prompt_path = os.path.join(PROMPTS_DIR, st.session_state.selected_prompt_name)
                if os.path.exists(prompt_path):
                    with open(prompt_path, "r", encoding="utf-8") as f:
                        st.session_state["input_prompt"] = f.read()


        user_prompt = st.text_area(
            "Prompt",
            key="input_prompt",
            height=150
        )


# 3. 核心處理邏輯
def generate_text_from_images(images, prompt, is_test):
    if is_test:
        # 模擬 AI 處理時間
        time.sleep(1)
        return "This is a test response from the AI."
    else:
        # 決定要使用哪個 API Key
        api_key_to_use = st.session_state.get("api_key_input") or os.getenv("GEMINI_API_KEY")

        if not api_key_to_use:
            st.error("Gemini API key is not configured. Please enter it in the sidebar or set the GEMINI_API_KEY environment variable.")
            return None # 或者可以返回一個錯誤訊息的字串

        try:
            # 真正連線到 Gemini 的邏輯
            genai.configure(api_key=api_key_to_use)
            model = genai.GenerativeModel('gemini-1.5-flash')
            contents = [prompt] + images
            response = model.generate_content(contents)
            return response.text
        except exceptions.PermissionDenied as e:
            st.error(f"Permission denied. Please check your API key and permissions. Details: {e}")
            return None
        except exceptions.InvalidArgument as e:
            st.error(f"Invalid argument provided to the API. Details: {e}")
            return None
        except Exception as e:
            st.error(f"An unexpected error occurred while calling the Gemini API: {e}")
            return None

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
            st.error("Gemini API key is not configured.")
            return None
        try:
            genai.configure(api_key=api_key_to_use)
            client = genai.Client()
            response = client.models.generate_content(
                model='gemini-2.5-flash-image', # Use the correct model for image generation
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"]
                )
            )

            image_data_list = []
            if response and response.candidates:
                for candidate in response.candidates:
                    for part in candidate.content.parts:
                        if part.image:
                            # The image data is in part.image.data, which are bytes
                            image_data_list.append(part.image.data)
            return image_data_list
        except exceptions.PermissionDenied as e:
            st.error(f"Permission denied. Please check your API key and permissions. Details: {e}")
            return None
        except exceptions.InvalidArgument as e:
            st.error(f"Invalid argument provided to the API. Details: {e}")
            return None
        except Exception as e:
            st.error(f"An unexpected error occurred while generating the image: {e}")
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
            st.error("Gemini API key is not configured.")
            return None
        try:
            genai.configure(api_key=api_key_to_use)
            client = genai.Client()
            response = client.models.generate_content(
                model='gemini-2.5-flash-image', # Use the correct model for image generation
                contents=[prompt, image],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"]
                )
            )

            image_data_list = []
            if response and response.candidates:
                for candidate in response.candidates:
                    for part in candidate.content.parts:
                        if part.image:
                            # The image data is in part.image.data, which are bytes
                            image_data_list.append(part.image.data)
            return image_data_list
        except exceptions.PermissionDenied as e:
            st.error(f"Permission denied. Please check your API key and permissions. Details: {e}")
            return None
        except exceptions.InvalidArgument as e:
            st.error(f"Invalid argument provided to the API. Details: {e}")
            return None
        except Exception as e:
            st.error(f"An unexpected error occurred while generating the image: {e}")
            return None


# 4. 主介面：上傳與執行
if page == "New Project":

    # Conditionally show the file uploader
    if task_type == "Analyze Image & Generate Text":
        newly_uploaded_files = st.file_uploader(
            "Upload Images (max 5)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
        )
        if newly_uploaded_files:
            st.session_state["uploaded_files"].extend(newly_uploaded_files)
    elif task_type == "Generate Image from Image & Text":
        newly_uploaded_files = st.file_uploader(
            "Upload an image",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=False,
        )
        if newly_uploaded_files:
            st.session_state["uploaded_files"] = [newly_uploaded_files]


    if (task_type == "Analyze Image & Generate Text" or task_type == "Generate Image from Image & Text") and st.session_state["uploaded_files"]:
        if len(st.session_state["uploaded_files"]) > 5:
            st.error(
                f"You have uploaded {len(st.session_state['uploaded_files'])} files. The maximum is 5."
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
                        caption=f"Preview {idx + 1}",
                        use_container_width=True,
                    )
                    if st.button("Delete", key=f"delete_{idx}"):
                        st.session_state["uploaded_files"].pop(idx)
                        st.rerun()

    if st.button("Run AI"):
        # 建立專案 Log 資料夾
        log_dir = os.path.join(LOGS_DIR, project_name)
        os.makedirs(os.path.join(log_dir, "inputs"), exist_ok=True)
        os.makedirs(os.path.join(log_dir, "outputs"), exist_ok=True)

        # 儲存 Prompt
        with open(
            os.path.join(log_dir, "prompt.txt"), "w", encoding="utf-8"
        ) as f:
            f.write(user_prompt)

        with st.spinner("Processing..."):
            if task_type == "Analyze Image & Generate Text":
                if 'processed_imgs' in locals() and processed_imgs:
                    # 先儲存所有圖片
                    for i, img in enumerate(processed_imgs):
                        img.save(os.path.join(log_dir, "inputs", f"image_{i+1}.png"))

                    result = generate_text_from_images(
                        processed_imgs, user_prompt, test_mode
                    )
                    if result:
                        st.subheader("Result")
                        st.write(result)
                        if st.button("Copy to Clipboard"):
                            pyperclip.copy(result)
                            st.success("Copied to clipboard!")

                        # 儲存輸出結果
                        with open(
                            os.path.join(log_dir, "outputs", "result.txt"),
                            "w",
                            encoding="utf-8",
                        ) as f:
                            f.write(result)
                        st.success("Processing complete!")
                else:
                    st.warning("Please upload at least one image for this task.")

            elif task_type == "Generate Image from Text":
                image_results = generate_image_from_text(user_prompt, test_mode)
                if image_results:
                    st.subheader("Generated Images")
                    # Create columns for the number of images
                    cols = st.columns(len(image_results))
                    for i, img_data in enumerate(image_results):
                        if is_test: # Test mode returns a path
                            img_path = img_data
                            with cols[i]:
                                st.image(img_path, caption=f"Generated Image {i+1}", use_container_width=True)
                        else: # Real mode returns image bytes
                            img_path = os.path.join(log_dir, "outputs", f"generated_image_{i+1}.png")
                            with open(img_path, "wb") as f:
                                f.write(img_data)
                            with cols[i]:
                                st.image(img_path, caption=f"Generated Image {i+1}", use_container_width=True)

                    st.success("Image generation complete!")
            
            elif task_type == "Generate Image from Image & Text":
                if 'processed_imgs' in locals() and processed_imgs:
                    input_image = processed_imgs[0] # Take the first image
                    input_image.save(os.path.join(log_dir, "inputs", "input_image.png"))

                    image_results = generate_image_from_image_and_text(input_image, user_prompt, test_mode)
                    if image_results:
                        st.subheader("Generated Images")
                        # Create columns for the number of images
                        cols = st.columns(len(image_results))
                        for i, img_data in enumerate(image_results):
                            if is_test: # Test mode returns a path
                                img_path = img_data
                                with cols[i]:
                                    st.image(img_path, caption=f"Generated Image {i+1}", use_container_width=True)
                            else: # Real mode returns image bytes
                                img_path = os.path.join(log_dir, "outputs", f"generated_image_{i+1}.png")
                                with open(img_path, "wb") as f:
                                    f.write(img_data)
                                with cols[i]:
                                    st.image(img_path, caption=f"Generated Image {i+1}", use_container_width=True)

                        st.success("Image generation complete!")
                else:
                    st.warning("Please upload an image for this task.")

elif page == "Prompt Management":
    st.header("Prompt Management")

    prompt_files = [f for f in os.listdir(PROMPTS_DIR) if f.endswith(".txt")]
    selected_prompt = st.selectbox("Select a prompt", ["Create new prompt"] + prompt_files)

    prompt_content = ""
    if selected_prompt != "Create new prompt":
        try:
            with open(os.path.join(PROMPTS_DIR, selected_prompt), "r", encoding="utf-8") as f:
                prompt_content = f.read()
            st.session_state["selected_prompt_name"] = selected_prompt # 記錄選擇的檔案
        except FileNotFoundError:
            st.error("Prompt file not found.")
            prompt_content = "" # or handle appropriately
        except Exception as e:
            st.error(f"Error reading prompt file: {e}")
            prompt_content = "" # or handle appropriately


    new_prompt_name = st.text_input("Prompt Name (e.g., 'my_prompt.txt')", value=selected_prompt if selected_prompt != "Create new prompt" else "")
    prompt_text = st.text_area("Prompt Content", value=prompt_content, height=300)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Prompt", use_container_width=True):
            if new_prompt_name and prompt_text:
                # Basic validation for filename
                if not new_prompt_name.endswith(".txt"):
                    new_prompt_name += ".txt"

                try:
                    with open(os.path.join(PROMPTS_DIR, new_prompt_name), "w", encoding="utf-8") as f:
                        f.write(prompt_text)
                    st.success(f"Prompt '{new_prompt_name}' saved successfully!")
                    st.session_state["selected_prompt_name"] = new_prompt_name # 更新選擇的檔案
                    # Rerun to update the selectbox
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving prompt: {e}")
            else:
                st.warning("Prompt name and content cannot be empty.")

    with col2:
        if selected_prompt != "Create new prompt":
            if st.button("Delete Prompt", type="primary", use_container_width=True):
                try:
                    os.remove(os.path.join(PROMPTS_DIR, selected_prompt))
                    st.success(f"Prompt '{selected_prompt}' deleted.")
                    st.session_state["selected_prompt_name"] = "" # 清除選擇
                    # Rerun to update the selectbox
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting prompt: {e}")

elif page == "History":
    st.header("History")
    log_root = LOGS_DIR
    if os.path.exists(log_root):
        projects = [
            d for d in os.listdir(log_root) if os.path.isdir(os.path.join(log_root, d))
        ]
        if projects:
            selected_project = st.selectbox(
                "Select a project", projects
            )
            project_path = os.path.join(log_root, selected_project)

            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "Restart Project",
                    use_container_width=True,
                ):
                    # 讀取舊 Prompt
                    old_prompt_path = os.path.join(project_path, "prompt.txt")
                    if os.path.exists(old_prompt_path):
                        with open(old_prompt_path, "r", encoding="utf-8") as f:
                            st.session_state["input_prompt"] = f.read()
                    st.session_state["input_project_name"] = selected_project
                    st.session_state["page_nav"] = "New Project"
                    st.rerun()
            with col2:
                # 確認刪除狀態檢查
                if st.session_state.get(f"confirm_delete_{selected_project}"):
                    st.warning("Are you sure you want to delete this project?")
                    if st.button(
                        "Yes, delete it",
                        key=f"yes_{selected_project}",
                        type="primary",
                        use_container_width=True,
                    ):
                        shutil.rmtree(project_path)
                        del st.session_state[f"confirm_delete_{selected_project}"]
                        st.rerun()
                    if st.button(
                        "No, cancel",
                        key=f"no_{selected_project}",
                        use_container_width=True,
                    ):
                        del st.session_state[f"confirm_delete_{selected_project}"]
                        st.rerun()
                else:
                    if st.button(
                        "Delete Project",
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
                        "Prompt Used",
                        f.read(),
                        disabled=True,
                    )

            # 顯示圖片對比 (輸入 vs 輸出)
            input_dir = os.path.join(project_path, "inputs")
            output_dir = os.path.join(project_path, "outputs")

            if os.path.exists(input_dir):
                st.subheader(
                    "Input/Output Comparison"
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
                                caption=f"Input: {f_name}",
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
                                            caption=f"Output: {cand}",
                                            use_container_width=True,
                                        )
                                    found_output = True
                                    break

                        if not found_output:
                            with c2:
                                st.info(
                                    "No output image found for this input."
                                )

            # 顯示輸出結果
            output_path = os.path.join(project_path, "outputs", "result.txt")
            if os.path.exists(output_path):
                st.subheader("Result")
                with open(output_path, "r", encoding="utf-8") as f:
                    st.markdown(f.read())
        else:
            st.info("No projects found in the log directory.")
    else:
        st.info("Log directory not found.")
