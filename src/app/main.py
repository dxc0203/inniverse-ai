import streamlit as st
import os
import time
import shutil
from dotenv import load_dotenv
from google import genai
from PIL import Image
from .translations import get_translation

# --- Constants ---
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOGS_DIR = os.path.join(ROOT_DIR, "logs")

st.set_page_config(page_title="Inniverse AI Lab", layout="wide")

if "language" not in st.session_state:
    st.session_state["language"] = "zh-TW"

lang = st.session_state["language"]

st.title(get_translation("new_project_page.main_title", lang))

# 2. 設定中心 (側邊欄)
with st.sidebar:
    st.selectbox("Language / 語言", ["zh-TW", "en"], key="language")
    # Refresh lang in case of immediate update needs
    lang = st.session_state["language"]

    page = st.radio(
        get_translation("sidebar.menu", lang),
        [
            get_translation("sidebar.new_project", lang),
            get_translation("sidebar.history", lang),
        ],
        key="page_nav",
    )
    st.divider()

    if page == get_translation("sidebar.new_project", lang):
        st.header(get_translation("sidebar.dev_tools", lang))
        # 🌟 加入 Test Mode 開關
        test_mode = st.checkbox(get_translation("sidebar.test_mode", lang), value=True)
        if test_mode:
            st.warning(get_translation("sidebar.test_mode_warning", lang))

        st.divider()
        # 設定專案與 Prompt
        project_name = st.text_input(
            get_translation("new_project_page.project_name", lang),
            value="MyProject_001",
            key="input_project_name",
        )
        user_prompt = st.text_area(
            get_translation("new_project_page.prompt_input", lang),
            value="Describe this garment for a B2B platform. Focus on fabric and design.",
            height=150,
            key="input_prompt",
        )

# 3. 核心處理邏輯
def process_images(images, prompt, is_test, lang_code):
    if is_test:
        # 模擬 AI 處理時間
        time.sleep(1)
        return get_translation("new_project_page.test_response", lang_code)
    else:
        # 真正連線到 Gemini 的邏輯
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        contents = [prompt] + images
        response = client.models.generate_content(
            model="gemini-1.5-flash", contents=contents
        )
        return response.text


# 4. 主介面：上傳與執行
if page == get_translation("sidebar.new_project", lang):
    uploaded_files = st.file_uploader(
        get_translation("new_project_page.upload_label", lang),
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        if len(uploaded_files) > 5:
            st.error(
                get_translation("new_project_page.upload_error_max", lang).format(
                    len(uploaded_files)
                )
            )
        else:
            # 預覽與縮圖處理
            processed_imgs = []
            cols = st.columns(len(uploaded_files))

            for idx, up_file in enumerate(uploaded_files):
                img = Image.open(up_file)
                # 限制圖片大小以優化上傳與 AI 讀取 (Max 1024px)
                img.thumbnail((1024, 1024))
                processed_imgs.append(img)

                with cols[idx]:
                    st.image(
                        img,
                        caption=get_translation(
                            "new_project_page.preview_caption", lang
                        ).format(idx + 1),
                        use_container_width=True,
                    )

            if st.button(get_translation("new_project_page.run_ai", lang)):
                # 建立專案 Log 資料夾
                log_dir = os.path.join(LOGS_DIR, project_name)
                os.makedirs(os.path.join(log_dir, "inputs"), exist_ok=True)
                os.makedirs(os.path.join(log_dir, "outputs"), exist_ok=True)

                # 儲存 Prompt
                with open(
                    os.path.join(log_dir, "prompt.txt"), "w", encoding="utf-8"
                ) as f:
                    f.write(user_prompt)

                # 先儲存所有圖片
                for i, img in enumerate(processed_imgs):
                    img.save(os.path.join(log_dir, "inputs", f"image_{i+1}.png"))

                with st.spinner(
                    get_translation("new_project_page.processing_spinner", lang)
                ):
                    result = process_images(
                        processed_imgs, user_prompt, test_mode, lang
                    )
                    st.subheader(
                        get_translation("new_project_page.result_header", lang)
                    )
                    st.write(result)

                    # 儲存輸出結果
                    with open(
                        os.path.join(log_dir, "outputs", "result.txt"),
                        "w",
                        encoding="utf-8",
                    ) as f:
                        f.write(result)

                st.success(get_translation("general.success_msg", lang))

elif page == get_translation("sidebar.history", lang):
    st.header(get_translation("history_page.history_header", lang))
    log_root = LOGS_DIR
    if os.path.exists(log_root):
        projects = [
            d for d in os.listdir(log_root) if os.path.isdir(os.path.join(log_root, d))
        ]
        if projects:
            selected_project = st.selectbox(
                get_translation("history_page.select_project", lang), projects
            )
            project_path = os.path.join(log_root, selected_project)

            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    get_translation("history_page.restart_btn", lang),
                    use_container_width=True,
                ):
                    # 讀取舊 Prompt
                    old_prompt_path = os.path.join(project_path, "prompt.txt")
                    if os.path.exists(old_prompt_path):
                        with open(old_prompt_path, "r", encoding="utf-8") as f:
                            st.session_state["input_prompt"] = f.read()
                    st.session_state["input_project_name"] = selected_project
                    st.session_state["page_nav"] = get_translation(
                        "sidebar.new_project", lang
                    )
                    st.rerun()
            with col2:
                # 確認刪除狀態檢查
                if st.session_state.get(f"confirm_delete_{selected_project}"):
                    st.warning(get_translation("history_page.confirm_delete", lang))
                    if st.button(
                        get_translation("history_page.yes_delete", lang),
                        key=f"yes_{selected_project}",
                        type="primary",
                        use_container_width=True,
                    ):
                        shutil.rmtree(project_path)
                        del st.session_state[f"confirm_delete_{selected_project}"]
                        st.rerun()
                    if st.button(
                        get_translation("history_page.no_cancel", lang),
                        key=f"no_{selected_project}",
                        use_container_width=True,
                    ):
                        del st.session_state[f"confirm_delete_{selected_project}"]
                        st.rerun()
                else:
                    if st.button(
                        get_translation("history_page.delete_btn", lang),
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
                        get_translation("history_page.prompt_used", lang),
                        f.read(),
                        disabled=True,
                    )

            # 顯示圖片對比 (輸入 vs 輸出)
            input_dir = os.path.join(project_path, "inputs")
            output_dir = os.path.join(project_path, "outputs")

            if os.path.exists(input_dir):
                st.subheader(
                    get_translation("history_page.comparison_header", lang)
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
                                caption=f"{get_translation('history_page.input_col', lang)}: {f_name}",
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
                                            caption=f"{get_translation('history_page.output_col', lang)}: {cand}",
                                            use_container_width=True,
                                        )
                                    found_output = True
                                    break

                        if not found_output:
                            with c2:
                                st.info(
                                    get_translation(
                                        "history_page.no_output_img", lang
                                    )
                                )

            # 顯示輸出結果
            output_path = os.path.join(project_path, "outputs", "result.txt")
            if os.path.exists(output_path):
                st.subheader(get_translation("new_project_page.result_header", lang))
                with open(output_path, "r", encoding="utf-8") as f:
                    st.markdown(f.read())
        else:
            st.info(get_translation("history_page.no_projects", lang))
    else:
        st.info(get_translation("history_page.no_logs", lang))
