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
    st.session_state["input_prompt"] = "A beautiful landscape painting."
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
        time.sleep(1) # In test mode, we return a placeholder image path
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
            # Note: The original code used genai.configure and genai.GenerativeModel
            # which are part of google-generativeai.
            # But the imports say google.genai as genai which is the new SDK.
            # I will keep the logic structure but adjust to likely required syntax if needed.
            # However, for this task, I am focusing on implementing the Prompt Builder.
            # Let's stick to the existing generation logic provided in the reference.
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
        time.sleep(1) # In test mode, we return a placeholder image path
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

    # ==== 快速提示构建器（中文 UI -> 英文 Prompt） ====
    with st.expander("快速提示构建器（中文界面，英文提示）", expanded=False):

        content_type = st.radio(
            "内容类型",
            ["通用场景", "服装/模特相关"],
            key="pb_content_type"
        )

        scene_type_cn = st.selectbox(
            "使用场景",
            ["电商 product 图", "广告海报", "社交媒体封面", "插画/概念设计", "头像/肖像", "其他"],
            key="pb_scene_type"
        )
        main_subject_cn = st.text_input(
            "主要主体（中文描述，会自动翻译为英文结构）",
            value="一位年轻女性模特穿着夏季连衣裙",
            key="pb_main_subject"
        )
        style_cn = st.selectbox(
            "整体风格",
            ["写实摄影风", "插画风", "3D 渲染", "卡通/动漫风", "赛博朋克", "极简现代"],
            key="pb_style"
        )
        mood_cn = st.selectbox(
            "氛围/情绪",
            ["明亮轻快", "温暖治愈", "冷酷未来感", "高级时尚感", "自然生活感", "戏剧张力强"],
            key="pb_mood"
        )

        cloth_type_cn = None
        display_type_cn = None
        target_platform_cn = None
        focus_cn_list = []

        if content_type == "服装/模特相关":
            cloth_type_cn = st.selectbox(
                "服装类型",
                ["T 恤", "连衣裙", "衬衫", "外套", "牛仔裤", "套装", "运动服", "内衣/居家服", "配饰（包/鞋/帽）"],
                key="pb_cloth_type"
            )
            display_type_cn = st.selectbox(
                "展示方式",
                ["白底平铺", "挂拍", "无头模特", "全身模特", "半身模特", "街拍场景", "静物搭配拍摄"],
                key="pb_display_type"
            )
            target_platform_cn = st.selectbox(
                "目标平台",
                ["电商详情页", "电商主图", "社交媒体（小红书/IG）", "Banner 海报", "Lookbook"],
                key="pb_target_platform"
            )
            focus_cn_list = st.multiselect(
                "重点强调",
                ["版型", "面料质感", "颜色还原", "细节特写（领口/袖口/下摆）", "穿搭场景", "身材修饰效果"],
                key="pb_focus"
            )

        aspect_ratio_cn = st.selectbox(
            "画面比例",
            ["1:1 正方形", "4:5 竖图", "3:4 竖图", "16:9 横图", "9:16 竖版封面"],
            key="pb_aspect_ratio"
        )
        camera_cn = st.selectbox(
            "构图/机位",
            ["全身远景", "中景（膝盖以上）", "半身特写", "特写（脸/细节）", "俯视平铺", "45 度侧面"],
            key="pb_camera"
        )
        lighting_cn = st.selectbox(
            "光线",
            ["柔和棚拍光", "自然窗光", "户外日光", "黄昏暖光", "冷调高对比"],
            key="pb_lighting"
        )
        quality_cn_list = st.multiselect(
            "质量要求",
            ["高清细节", "噪点极低", "色彩还原准确", "适合后期剪裁", "适合电商详情页排版"],
            key="pb_quality"
        )

        extra_cn = st.text_input(
            "补充说明（中文，会简要转成英文含义）",
            value="画面简洁干净，适合在线商店展示。",
            key="pb_extra"
        )

        scene_map = {
            "电商 product 图": "e-commerce product image",
            "广告海报": "advertising poster",
            "社交媒体封面": "social media cover image",
            "插画/概念设计": "illustration or concept art",
            "头像/肖像": "portrait",
            "其他": "general purpose image"
        }

        style_map = {
            "写实攝影风": "realistic photography style",
            "插画风": "illustration style",
            "3D 渲染": "3D rendered style",
            "卡通/动漫风": "cartoon / anime style",
            "赛博朋克": "cyberpunk style",
            "极简现代": "minimal and modern style"
        }

        mood_map = {
            "明亮轻快": "bright and cheerful mood",
            "温暖治愈": "warm and comforting mood",
            "冷酷未来感": "cool futuristic mood",
            "高级时尚感": "high-fashion editorial mood",
            "自然生活感": "natural everyday-life mood",
            "戏剧张力强": "dramatic and intense mood"
        }

        cloth_type_map = {
            "T 恤": "T-shirt",
            "连衣裙": "dress",
            "衬衫": "shirt",
            "外套": "jacket",
            "牛仔裤": "jeans",
            "套装": "suit set",
            "运动服": "sportswear",
            "内衣/居家服": "loungewear or underwear",
            "配饰（包/鞋/帽）": "fashion accessories such as bag, shoes or hat"
        }

        display_type_map = {
            "白底平铺": "flat lay on a clean white background",
            "挂拍": "hanging on a hanger",
            "无头模特": "on a headless mannequin",
            "全身模特": "on a full-body model",
            "半身模特": "on a half-body model",
            "街拍场景": "street photography scene",
            "静物搭配拍摄": "styled still life composition"
        }

        target_platform_map = {
            "电商详情页": "e-commerce product detail page",
            "电商主图": "e-commerce main product image",
            "社交媒体（小红书/IG）": "social media platforms like Instagram or Xiaohongshu",
            "Banner 海報": "banner or promotional poster",
            "Lookbook": "lookbook or fashion catalog"
        }

        focus_map = {
            "版型": "silhouette and fit of the garment",
            "面料质感": "fabric texture and material",
            "颜色还原": "accurate color representation",
            "细节特写（领口/袖口/下摆）": "close-up details of neckline, cuffs and hem",
            "穿搭场景": "styling and outfit context",
            "身材修饰效果": "body-flattering effect"
        }

        aspect_ratio_map = {
            "1:1 正方形": "1:1 square ratio",
            "4:5 竖图": "4:5 portrait ratio",
            "3:4 竖图": "3:4 portrait ratio",
            "16:9 横图": "16:9 landscape ratio",
            "9:16 竖版封面": "9:16 vertical ratio"
        }

        camera_map = {
            "全身远景": "full-body shot from a distance",
            "中景（膝盖以上）": "medium shot from knees up",
            "半身特写": "half-body shot",
            "特写（脸/细节）": "close-up of face or details",
            "俯视平铺": "top-down flat lay",
            "45 度侧面": "45-degree side angle"
        }

        lighting_map = {
            "柔和棚拍光": "soft studio lighting",
            "自然窗光": "natural window light",
            "户外日光": "outdoor daylight",
            "黄昏暖光": "warm golden hour lighting",
            "冷调高对比": "cool high-contrast lighting"
        }

        quality_map = {
            "高清细节": "high-resolution with fine details",
            "噪点极低": "very low noise",
            "色彩还原准确": "accurate color representation",
            "适合后期剪裁": "suitable for cropping and post-processing",
            "适合电商详情页排版": "suitable for e-commerce product detail layout"
        }

        if st.button("生成到提示文本（英文）", key="pb_generate"):
            scene_en = scene_map.get(scene_type_cn, "general purpose image")
            style_en = style_map.get(style_cn, "")
            mood_en = mood_map.get(mood_cn, "")

            base_en = (
                f"Create an image for {scene_en}. "
                f"The main subject is: {main_subject_cn}. "
                f"The overall style should be {style_en}, with a {mood_en}."
            )

            cloth_part_en = ""
            if content_type == "服装/模特相关" and cloth_type_cn and display_type_cn and target_platform_cn:
                cloth_en = cloth_type_map.get(cloth_type_cn, "a piece of clothing")
                display_en = display_type_map.get(display_type_cn, "on a model")
                target_en = target_platform_map.get(target_platform_cn, "an online store")

                focus_en_list = [focus_map[f] for f in focus_cn_list if f in focus_map]
                focus_en = ""
                if focus_en_list:
                    focus_en = " Emphasize " + ", ".join(focus_en_list) + "."

                cloth_part_en = (
                    f" Show {cloth_en} with {display_en}, mainly designed for {target_en}."
                    f"{focus_en}"
                )

            aspect_en = aspect_ratio_map.get(aspect_ratio_cn, "")
            camera_en = camera_map.get(camera_cn, "")
            lighting_en = lighting_map.get(lighting_cn, "")
            quality_en_list = [quality_map[q] for q in quality_cn_list if q in quality_map]
            quality_en = ""
            if quality_en_list:
                quality_en = " The image should have " + ", ".join(quality_en_list) + "."

            model_part_en = (
                f" Use {aspect_en}, with {camera_en} and {lighting_en}."
                f"{quality_en}"
            )

            extra_en = ""
            if extra_cn.strip():
                extra_en = f" Additional notes (from user in Chinese): {extra_cn}."

            tail_en = (
                " Keep the composition clean and uncluttered, suitable for online product display. "
                "Avoid any text, logos or watermarks in the image."
            )

            final_prompt_en = base_en + " " + cloth_part_en + " " + model_part_en + " " + extra_en + " " + tail_en
            st.session_state["input_prompt"] = final_prompt_en.strip()
            st.success("已生成英文提示，并写入下方文本框。")

    user_prompt = st.text_area(
        "提示", key="input_prompt", height=150
    )
    task_type = st.selectbox(
        "选择任务类型", ["从文本生成图像", "从图像和文本生成图像"], key="task_type_selector",
    )

    if task_type == "从图像和文本生成图像":
        newly_uploaded_files = st.file_uploader(
            "上传图片", type=["jpg", "jpeg", "png"], accept_multiple_files=False,
        )
        if newly_uploaded_files:
            st.session_state["uploaded_files"] = [newly_uploaded_files]

    if task_type == "从图像和文本生成图像" and st.session_state["uploaded_files"]:
        if len(st.session_state["uploaded_files"]) > 5:
            st.error(
                f"您上传了 {len(st.session_state['uploaded_files'])} 个文件。最多 5 个。"
            )
        else:
            processed_imgs = []
            cols = st.columns(len(st.session_state["uploaded_files"]))
            for idx, up_file in enumerate(st.session_state["uploaded_files"]):
                img = Image.open(up_file)
                img.thumbnail((1024, 1024))
                processed_imgs.append(img)
                with cols[idx]:
                    st.image(
                        img, caption=f"预览 {idx + 1}", use_container_width=True,
                    )
                if st.button("删除", key=f"delete_{idx}"):
                    st.session_state["uploaded_files"].pop(idx)
                    st.rerun()

    if st.button("运行 AI"):
        log_dir = os.path.join(LOGS_DIR, project_name)
        os.makedirs(os.path.join(log_dir, "inputs"), exist_ok=True)
        os.makedirs(os.path.join(log_dir, "outputs"), exist_ok=True)

        with open(
            os.path.join(log_dir, "prompt.txt"), "w", encoding="utf-8"
        ) as f:
            f.write(user_prompt)

        with st.spinner("处理中..."):
            if task_type == "从文本生成图像":
                image_results = generate_image_from_text(user_prompt, test_mode)
                if image_results:
                    st.subheader("生成的图像")
                    cols = st.columns(len(image_results))
                    for i, img_data in enumerate(image_results):
                        if test_mode:
                            img_path = img_data
                            with cols[i]:
                                st.image(img_path, caption=f"生成的图像 {i+1}", use_container_width=True)
                        else:
                            img_path = os.path.join(log_dir, "outputs", f"generated_image_{i+1}.png")
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
                            if test_mode:
                                img_path = img_data
                                with cols[i]:
                                    st.image(img_path, caption=f"生成的图像 {i+1}", use_container_width=True)
                            else:
                                img_path = os.path.join(log_dir, "outputs", f"generated_image_{i+1}.png")
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
    prompt_content = ""
    if selected_prompt != "创建新提示":
        try:
            with open(os.path.join(PROMPTS_DIR, selected_prompt), "r", encoding="utf-8") as f:
                prompt_content = f.read()
            st.session_state["selected_prompt_name"] = selected_prompt
        except Exception as e:
            st.error(f"读取提示文件时出错：{e}")
            prompt_content = ""
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
                st.warning("提示名称和内容不能为空。")
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
                        found_output = False
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
