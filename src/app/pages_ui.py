import streamlit as st
import os
import shutil
import time
import json
import uuid
import io
import zipfile
from PIL import Image
from models import generate_image_from_text, generate_image_from_image_and_text
from constants import ROOT_DIR, MODEL_PROMPTS_DIR, SCENE_PROMPTS_DIR

# --- Configuration Constants ---
ETHNICITIES = ["西方人 (Western)", "亚洲人 (Asian)", "非洲人 (African)", "拉丁裔 (Hispanic)"]
AGES = ["20多岁 (20s)", "30多岁 (30s)", "40多岁 (40s)"]
GENDERS = ["女性 (Female)", "男性 (Male)", "中性 (Unisex)"]
BODY_TYPES = ["标准 (Standard)", "加大码 (Plus Size)", "运动型 (Athletic)"]
BACKGROUNDS = ["灰色影棚 (Grey Studio)", "户外街道 (Street)", "公園 (Park)", "室内客厅 (Living Room)"]
ASPECT_RATIOS = ["1:1 (Square)", "2:3 (Portrait/Fashion)", "3:2 (Landscape)", "16:9 (Banner)"]
# Model-specific tags
POSES = ["正面站立 (Standing Front)", "侧面站立 (Side View)", "坐姿 (Sitting)", "走动 (Walking)", "手叉腰 (Hand on Hip)"]
EXPRESSIONS = ["微笑 (Smiling)", "冷酷 (Serious/Cool)", "自信 (Confident)", "大笑 (Laughing)", "自然 (Natural)"]
HAIR_STYLES = ["披肩发 (Long Down)", "扎发 (Tied Up)", "短发 (Short)", "波浪卷 (Wavy)"]
LIGHTINGS = ["柔和光 (Soft Light)", "硬朗光 (Hard Light)", "黄金时段 (Golden Hour)", "影棚光 (Studio Lighting)"]

def render_tag_selectors(prefix, saved_tags=None, mode="both"):
    """Shared UI component for model and scene selection.
    mode: 'model' shows only model/pose tags, 'scene' shows only scene/format tags, 'both' shows all.
    """
    if saved_tags is None:
        saved_tags = {}

    tags = {
        "ethnicity": saved_tags.get("ethnicity", ETHNICITIES[0]),
        "age": saved_tags.get("age", AGES[0]),
        "gender": saved_tags.get("gender", GENDERS[0]),
        "body_type": saved_tags.get("body_type", BODY_TYPES[0]),
        "pose": saved_tags.get("pose", POSES[0]),
        "expression": saved_tags.get("expression", EXPRESSIONS[0]),
        "hair": saved_tags.get("hair", HAIR_STYLES[0]),
        "lighting": saved_tags.get("lighting", LIGHTINGS[0]),
        "background": saved_tags.get("background", BACKGROUNDS[0]),
        "aspect_ratio": saved_tags.get("aspect_ratio", ASPECT_RATIOS[1]),
    }

    if mode in ["model", "both"]:
        st.markdown("##### 👤 模特与形态")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            tags["ethnicity"] = st.selectbox("族裔", ETHNICITIES, index=ETHNICITIES.index(tags["ethnicity"]) if tags["ethnicity"] in ETHNICITIES else 0, key=f"{prefix}_eth")
        with c2:
            tags["age"] = st.selectbox("年龄", AGES, index=AGES.index(tags["age"]) if tags["age"] in AGES else 0, key=f"{prefix}_age")
        with c3:
            tags["gender"] = st.selectbox("性别", GENDERS, index=GENDERS.index(tags["gender"]) if tags["gender"] in GENDERS else 0, key=f"{prefix}_gender")
        with c4:
            tags["body_type"] = st.selectbox("体型", BODY_TYPES, index=BODY_TYPES.index(tags["body_type"]) if tags["body_type"] in BODY_TYPES else 0, key=f"{prefix}_body")
        st.markdown("##### 🎭 姿态与表情")
        c5, c6, c7, c8 = st.columns(4)
        with c5:
            tags["pose"] = st.selectbox("姿势", POSES, index=POSES.index(tags["pose"]) if tags["pose"] in POSES else 0, key=f"{prefix}_pose")
        with c6:
            tags["expression"] = st.selectbox("表情", EXPRESSIONS, index=EXPRESSIONS.index(tags["expression"]) if tags["expression"] in EXPRESSIONS else 0, key=f"{prefix}_expr")
        with c7:
            tags["hair"] = st.selectbox("发型", HAIR_STYLES, index=HAIR_STYLES.index(tags["hair"]) if tags["hair"] in HAIR_STYLES else 0, key=f"{prefix}_hair")
        with c8:
            tags["lighting"] = st.selectbox("光效", LIGHTINGS, index=LIGHTINGS.index(tags["lighting"]) if tags["lighting"] in LIGHTINGS else 0, key=f"{prefix}_light")

    if mode in ["scene", "both"]:
        st.markdown("##### 🖼️ 场景与格式")
        c9, c10 = st.columns(2)
        with c9:
            tags["background"] = st.selectbox("背景场景", BACKGROUNDS, index=BACKGROUNDS.index(tags["background"]) if tags["background"] in BACKGROUNDS else 0, key=f"{prefix}_bg")
        with c10:
            tags["aspect_ratio"] = st.selectbox("画幅比例", ASPECT_RATIOS, index=ASPECT_RATIOS.index(tags["aspect_ratio"]) if tags["aspect_ratio"] in ASPECT_RATIOS else 1, key=f"{prefix}_ar")

    return tags


def assemble_prompt(model_text, scene_text, use_default, tags):
    if not use_default:
        return f"{model_text} {scene_text}".strip()

    def get_val(key): return tags[key].split(" (")[1].replace(")", "") if "(" in tags[key] else tags[key]

    model_desc = f"{get_val('age')} {get_val('ethnicity')} {get_val('gender')} model, {get_val('body_type')}"
    style_desc = f"{get_val('pose')} pose, {get_val('expression')} expression, {get_val('hair')} hair"
    env_desc = f"{get_val('background')} background, {get_val('lighting')}"
    ar = tags['aspect_ratio'].split(" ")[0]

    full_model = f"{model_desc}, {style_desc}"
    if model_text.strip(): full_model = f"{full_model}, {model_text}"

    full_scene = f"{env_desc}"
    if scene_text.strip(): full_scene = f"{full_scene}, {scene_text}"

    final = f"Fashion photo: {full_model}, wearing the garment, {full_scene}. High quality, 8k, aspect ratio {ar}."
    return final

def render_new_project(LOGS_DIR, MODEL_DIR, SCENE_DIR, test_mode):
    st.header("新建项目")

    m_files = sorted([os.path.splitext(f)[0] for f in os.listdir(MODEL_DIR) if f.endswith(".txt")])
    s_files = sorted([os.path.splitext(f)[0] for f in os.listdir(SCENE_DIR) if f.endswith(".txt")])

    m_options = ["从空白开始 (Blank)"] + m_files
    s_options = ["从空白开始 (Blank)"] + s_files

    bulk_count = st.number_input("想一次建立几个新專案？", min_value=1, max_value=5, value=1, step=1)
    projects_data = []

    for i in range(bulk_count):
        with st.expander(f"项目 {i+1} 配置", expanded=(i==0)):
            p_name = st.text_input(f"项目名称 / Product ID", value=f"PROJ_{uuid.uuid4().hex[:8].upper()}", key=f"bulk_name_{i}")
            tags = render_tag_selectors(f"bulk_{i}", mode="both")
            use_def = st.checkbox("使用智能系统提示词 (推荐)", value=True, key=f"bulk_use_def_{i}")

            c1, c2 = st.columns(2)
            with c1:
                sel_m = st.selectbox(f"选择模特提示词模板", m_options, key=f"bulk_m_sel_{i}")
                m_content = ""
                if sel_m != "从空白开始 (Blank)":
                    with open(os.path.join(MODEL_DIR, sel_m + ".txt"), "r", encoding="utf-8") as f: m_content = f.read()
                m_p = st.text_area("模特详细描述", value=m_content, key=f"bulk_m_p_{i}", height=100)

            with c2:
                sel_s = st.selectbox(f"选择场景提示词模板", s_options, key=f"bulk_s_sel_{i}")
                s_content = ""
                if sel_s != "从空白开始 (Blank)":
                    with open(os.path.join(SCENE_DIR, sel_s + ".txt"), "r", encoding="utf-8") as f: s_content = f.read()
                s_p = st.text_area("场景详细描述", value=s_content, key=f"bulk_s_p_{i}", height=100)
            neg_prompt = st.text_input("排除内容 (Negative Prompt)", value="watermark, text, blurry, low quality", key=f"bulk_neg_{i}")

            final_p_preview = assemble_prompt(m_p, s_p, use_def, tags)
            with st.expander("📝 最终提示词预览"): st.code(final_p_preview)

            t_type = st.selectbox("选择任务类型", ["从文本生成图像", "从图像和文本生成图像"], key=f"bulk_task_{i}", index=1)
            up_files = None
            if t_type == "从图像和文本生成图像":
                up_files = st.file_uploader(f"上传商品图片 (项目 {i+1})", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key=f"bulk_up_{i}")

            projects_data.append({"name": p_name, "tags": tags, "use_def": use_def, "m_prompt": m_p, "s_prompt": s_p, "neg_prompt": neg_prompt, "task_type": t_type, "files": up_files})

    if st.button("批量运行 AI", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        for idx, data in enumerate(projects_data):
            if data['task_type'] == "从图像和文本生成图像" and not data['files']:
                st.error(f"项目 {data['name']}: 请上传图片。"); continue

            final_p = assemble_prompt(data['m_prompt'], data['s_prompt'], data['use_def'], data['tags'])
            if data['neg_prompt']: final_p += f" [Negative: {data['neg_prompt']}]"

            log_dir = os.path.join(LOGS_DIR, data['name'])
            os.makedirs(os.path.join(log_dir, "outputs"), exist_ok=True)
            with open(os.path.join(log_dir, "prompt.txt"), "w", encoding="utf-8") as f: f.write(final_p)
            metadata = {"id": data['name'], "timestamp": time.time(), "tags": data['tags'], "task_type": data['task_type'], "use_default": data['use_def'], "model_prompt": data['m_prompt'], "scene_prompt": data['s_prompt'], "neg_prompt": data['neg_prompt'], "test_mode": test_mode}
            with open(os.path.join(log_dir, "metadata.json"), "w", encoding="utf-8") as f: json.dump(metadata, f, ensure_ascii=False, indent=4)

            processed_imgs = []
            if data['task_type'] == "从图像和文本生成图像":
                for up_file in data['files'][:5]:
                    img = Image.open(up_file); img.thumbnail((1024, 1024)); processed_imgs.append(img)

            with st.spinner(f"生成中 {data['name']}..."):
                if data['task_type'] == "从文本生成图像": res = generate_image_from_text(final_p, test_mode)
                else: res = generate_image_from_image_and_text(processed_imgs, final_p, test_mode)
            if res:
                for j, img_data in enumerate(res):
                    if not test_mode:
                        with open(os.path.join(log_dir, "outputs", f"img_{j+1}.png"), "wb") as f: f.write(img_data)
            progress_bar.progress((idx + 1) / len(projects_data))
        st.success("全部完成！"); st.session_state["navigate_to"] = "历史记录"; st.rerun()

def render_prompt_gallery(MODEL_DIR, SCENE_DIR):
    st.header("🖼️ 提示词库 (Prompt Gallery)")

    t1, t2 = st.tabs(["模特提示词 (Model)", "场景提示词 (Scene)"])

    def show_gallery(dir, prefix):
        files = sorted([f for f in os.listdir(dir) if f.endswith(".txt")])
        if not files:
            st.info("尚无提示词。"); return

        search = st.text_input(f"🔍 搜索{prefix}库...", "", key=f"search_{prefix}").lower()
        cols = st.columns(3)
        for idx, f in enumerate(files):
            name = os.path.splitext(f)[0]
            if search and search not in name.lower(): continue
            with cols[idx % 3]:
                with st.container(border=True):
                    st.subheader(name)
                    with open(os.path.join(dir, f), "r", encoding="utf-8") as file: content = file.read()
                    st.caption(content[:150] + "..." if len(content) > 150 else content)

                    c1, c2 = st.columns(2)
                    if c1.button("使用", key=f"use_{prefix}_{f}", use_container_width=True):
                        st.session_state["navigate_to"] = "新项目"
                        st.rerun()
                    if c2.button("编辑", key=f"edit_gal_{prefix}_{f}", use_container_width=True):
                        st.session_state["selected_prompt_name"] = name
                        st.session_state["navigate_to"] = f"{prefix}提示词管理"
                        st.rerun()
    with t1: show_gallery(MODEL_DIR, "模特")
    with t2: show_gallery(SCENE_DIR, "场景")


def render_prompt_management(PROMPTS_DIR, type_label):
    st.header(f"{type_label}提示词管理")
    if not os.path.exists(PROMPTS_DIR): os.makedirs(PROMPTS_DIR, exist_ok=True)

    prompt_files = sorted([f for f in os.listdir(PROMPTS_DIR) if f.endswith(".txt")])
    display_names = ["创建新提示"] + [os.path.splitext(f)[0] for f in prompt_files]

    default_idx = display_names.index(st.session_state.get("selected_prompt_name")) if st.session_state.get("selected_prompt_name") in display_names else 0
    selected_display = st.selectbox("选择或创建", display_names, index=default_idx, key=f"sel_{type_label}")
    st.session_state["selected_prompt_name"] = None

    prompt_content = ""
    saved_tags = {}
    if selected_display != "创建新提示":
        with open(os.path.join(PROMPTS_DIR, selected_display + ".txt"), "r", encoding="utf-8") as f: prompt_content = f.read()
        tag_f = os.path.join(PROMPTS_DIR, selected_display + "_tags.json")
        if os.path.exists(tag_f):
            with open(tag_f, "r", encoding="utf-8") as f: saved_tags = json.load(f)

    st.markdown("### 🏷️ 关联标签 (可选)")
    # Model page shows model/pose tags only; scene page shows scene/format tags only
    tag_mode = "model" if type_label == "模特" else "scene"
    tags = render_tag_selectors(f"pm_{type_label}", saved_tags, mode=tag_mode)

    new_name = st.text_input("提示名称", value=selected_display if selected_display != "创建新提示" else "", key=f"name_{type_label}")
    prompt_text = st.text_area("提示内容", value=prompt_content, height=300, key=f"text_{type_label}")

    c1, c2, c3 = st.columns(3)
    if c1.button("💾 保存", use_container_width=True, key=f"save_{type_label}", type="primary"):
        if not new_name: st.error("请输入名称"); return
        fname = new_name if new_name.endswith(".txt") else new_name + ".txt"
        with open(os.path.join(PROMPTS_DIR, fname), "w", encoding="utf-8") as f: f.write(prompt_text)
        with open(os.path.join(PROMPTS_DIR, fname.replace(".txt", "_tags.json")), "w", encoding="utf-8") as f: json.dump(tags, f, indent=4)
        st.success("已保存！"); st.rerun()

    if selected_display != "创建新提示":
        if c2.button("📋 复制", use_container_width=True, key=f"copy_{type_label}"):
            st.rerun()
        if c3.button("🗑️ 删除", type="secondary", use_container_width=True, key=f"del_pm_{type_label}"):
            os.remove(os.path.join(PROMPTS_DIR, selected_display + ".txt"))
            st.rerun()


def render_history(LOGS_DIR):
    st.header("生成历史")
    if not os.path.exists(LOGS_DIR): return
    projects = sorted([d for d in os.listdir(LOGS_DIR) if os.path.isdir(os.path.join(LOGS_DIR, d))],
                      key=lambda x: os.path.getmtime(os.path.join(LOGS_DIR, x)), reverse=True)

    for p in projects:
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 3, 1])
            p_path = os.path.join(LOGS_DIR, p)
            out_dir = os.path.join(p_path, "outputs")
            if os.path.exists(out_dir):
                imgs = [f for f in os.listdir(out_dir) if f.endswith(".png")]
                if imgs: c1.image(os.path.join(out_dir, imgs[0]), use_container_width=True)

            c2.markdown(f"**ID: {p}**")
            p_file = os.path.join(p_path, "prompt.txt")
            if os.path.exists(p_file):
                with open(p_file, "r", encoding="utf-8") as f: c2.caption(f.read()[:200])

            if c3.button("📦 ZIP", key=f"zip_{p}"):
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w") as zf:
                    for img in imgs: zf.write(os.path.join(out_dir, img), arcname=img)
                st.download_button("下载 ZIP", buf.getvalue(), f"{p}.zip", "application/zip")
            if c3.button("🗑️", key=f"del_{p}", type="primary"):
                shutil.rmtree(p_path); st.rerun()

def render_prompt_builder(MODEL_DIR, SCENE_DIR):
    st.header("🛠️ 提示词构建器")
    st.info("🚧 此功能正在开发中...")
    st.markdown("""
    ### 即将推出：
    - 使用标签占位符创建提示词模板（如 `{ethnicity} {age} woman`）
    - 在提示词库中显示可用标签
    - 在新项目页面中合并模板和标签值
    """)
