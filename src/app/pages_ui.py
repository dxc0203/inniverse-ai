import streamlit as st
import os
import shutil
import time
import json
from PIL import Image
from models import generate_image_from_text, generate_image_from_image_and_text
from constants import ROOT_DIR

ETHNICITIES = ["西方人 (Western)", "亚洲人 (Asian)", "非洲人 (African)", "拉丁裔 (Hispanic)"]
AGES = ["20多岁 (20s)", "30多岁 (30s)", "40多岁 (40s)"]
BACKGROUNDS = ["灰色影棚 (Grey Studio)", "户外街道 (Street)", "公园 (Park)", "室内客厅 (Living Room)"]

def render_new_project(LOGS_DIR, PROMPTS_DIR, test_mode):
    st.header("新建项目")

    if not os.path.exists(PROMPTS_DIR):
        os.makedirs(PROMPTS_DIR, exist_ok=True)

    prompt_files = sorted([f for f in os.listdir(PROMPTS_DIR) if f.endswith(".txt")])
    prompt_options = ["从空白开始 (Blank)"] + prompt_files

    bulk_count = st.number_input("想一次建立几个新専案？", min_value=1, max_value=5, value=1, step=1)
    projects_data = []

    for i in range(bulk_count):
        with st.expander(f"项目 {i+1} 配置", expanded=(i==0)):
            p_name = st.text_input(f"项目名称 / Product ID", value=f"PROJ_{int(time.time())}_{i+1}", key=f"bulk_name_{i}")
            col1, col2, col3 = st.columns(3)
            with col1:
                eth = st.selectbox("模特族裔", ETHNICITIES, index=0, key=f"bulk_eth_{i}")
            with col2:
                age = st.selectbox("模特年龄", AGES, index=0, key=f"bulk_age_{i}")
            with col3:
                bg = st.selectbox("背景场景", BACKGROUNDS, index=0, key=f"bulk_bg_{i}")
            use_def = st.checkbox("使用智能系统提示词 (推荐)", value=True, key=f"bulk_use_def_{i}")
            selected_template = st.selectbox(f"选择提示词模板 (项目 {i+1})", prompt_options, key=f"bulk_p_sel_{i}")
            template_content = ""
            if selected_template != "从空白开始 (Blank)":
                try:
                    with open(os.path.join(PROMPTS_DIR, selected_template), "r", encoding="utf-8") as f:
                        template_content = f.read()
                except:
                    pass
            u_prompt = st.text_area("详细提示词描述", value=template_content, key=f"bulk_prompt_{i}", height=100)
            save_prompt = False
            save_name = ""
            if selected_template == "从空白开始 (Blank)":
                save_prompt = st.checkbox("记录此新提示词 (Save as template)", value=False, key=f"bulk_save_check_{i}")
                if save_prompt:
                    save_name = st.text_input("提示词模板名称", value=f"Template_{int(time.time())}", key=f"bulk_save_name_{i}")
            t_type = st.selectbox("选择任务类型", ["从文本生成图像", "从图像和文本生成图像"], key=f"bulk_task_{i}", index=1)
            up_files = None
            if t_type == "从图像和文本生成图像":
                up_files = st.file_uploader(f"上传商品图片 (项目 {i+1})", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key=f"bulk_up_{i}")
                if up_files:
                    st.markdown("**图片预览 (Limit: 150px width):**")
                    preview_cols = st.columns(5)
                    for idx, up_file in enumerate(up_files[:5]):
                        with preview_cols[idx]:
                            st.image(up_file, width=150)
            projects_data.append({
                "name": p_name, "eth": eth, "age": age, "bg": bg,
                "use_def": use_def, "prompt": u_prompt, "task_type": t_type,
                "files": up_files, "save_prompt": save_prompt, "save_name": save_name
            })

def assemble_prompt(base_text, use_default, ethnicity, age, bg):
    if not use_default and base_text.strip():
        return base_text
    eth_map = {"西方人 (Western)": "western girl", "亚洲人 (Asian)": "asian girl", "非洲人 (African)": "african girl", "拉丁裔 (Hispanic)": "hispanic girl"}
    age_map = {"20多岁 (20s)": "in her mid 20s", "30多岁 (30s)": "in her 30s", "40多岁 (40s)": "in her 40s"}
    bg_map = {"灰色影棚 (Grey Studio)": "in a grey studio background", "户外街道 (Street)": "in a sunny street background", "公园 (Park)": "in a green park background", "室内客厅 (Living Room)": "in a cozy living room background"}
    system_base = f"A {eth_map[ethnicity]} {age_map[age]} wearing the garment, taking the photo {bg_map[bg]}."
    return f"{system_base} {base_text}" if base_text.strip() else system_base

    if st.button("批量运行 AI", type="primary", use_container_width=True):
        for idx, data in enumerate(projects_data):
            st.write(f"### 正在处理项目 {idx+1}: {data['name']}...")
            if data['save_prompt'] and data['save_name'] and data['prompt']:
                s_name = data['save_name'] if data['save_name'].endswith(".txt") else data['save_name'] + ".txt"
                with open(os.path.join(PROMPTS_DIR, s_name), "w", encoding="utf-8") as f:
                    f.write(data['prompt'])
                st.info(f"已保存新提示词模板: {s_name}")
            final_p = assemble_prompt(data['prompt'], data['use_def'], data['eth'], data['age'], data['bg'])
            log_dir = os.path.join(LOGS_DIR, data['name'])
            os.makedirs(os.path.join(log_dir, "inputs"), exist_ok=True)
            os.makedirs(os.path.join(log_dir, "outputs"), exist_ok=True)
            with open(os.path.join(log_dir, "prompt.txt"), "w", encoding="utf-8") as f:
                f.write(final_p)
            metadata = {"id": data['name'], "timestamp": time.time(), "ethnicity": data['eth'], "age": data['age'], "background": data['bg'], "task_type": data['task_type'], "use_default": data['use_def'], "base_prompt": data['prompt'], "test_mode": test_mode}
            with open(os.path.join(log_dir, "metadata.json"), "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=4)
            processed_imgs = []
            if data['task_type'] == "从图像和文本生成图像":
                if data['files']:
                    for f_idx, up_file in enumerate(data['files'][:5]):
                        img = Image.open(up_file)
                        img.thumbnail((512, 512))
                        img.save(os.path.join(log_dir, "inputs", f"input_image_{f_idx+1}.png"))
                        processed_imgs.append(img)
                else:
                    continue
            with st.spinner(f"AI 正在为 {data['name']} 生成结果..."):
                if data['task_type'] == "从文本生成图像":
                    image_results = generate_image_from_text(final_p, test_mode)
                else:
                    image_results = generate_image_from_image_and_text(processed_imgs, final_p, test_mode)
            if image_results:
                for i, img_data in enumerate(image_results):
                    img_path = img_data if test_mode else os.path.join(log_dir, "outputs", f"generated_image_{i+1}.png")
                    if not test_mode:
                        with open(img_path, "wb") as f:
                            f.write(img_data)
                st.success(f"项目 {data['name']} 生成完成！")
                st.balloons()
                st.session_state["navigate_to"] = "历史记录"
                st.rerun()

def render_prompt_management(PROMPTS_DIR):
    st.header("提示词管理")

    if not os.path.exists(PROMPTS_DIR):
        os.makedirs(PROMPTS_DIR, exist_ok=True)

    prompt_files = [f for f in os.listdir(PROMPTS_DIR) if f.endswith(".txt")]
    selected_prompt = st.selectbox("选择提示", ["创建新提示"] + prompt_files)

    prompt_content = ""
    saved_tags = {}
    if selected_prompt != "创建新提示":
        try:
            with open(os.path.join(PROMPTS_DIR, selected_prompt), "r", encoding="utf-8") as f:
                prompt_content = f.read()
        except:
            pass
        tag_file = os.path.join(PROMPTS_DIR, selected_prompt.replace(".txt", "_tags.json"))
        if os.path.exists(tag_file):
            try:
                with open(tag_file, "r", encoding="utf-8") as f:
                    saved_tags = json.load(f)
            except:
                pass

    st.markdown("### 🏷️ 标签设置")
    col1, col2, col3 = st.columns(3)
    with col1:
        eth_idx = ETHNICITIES.index(saved_tags.get("ethnicity", ETHNICITIES[0])) if saved_tags.get("ethnicity") in ETHNICITIES else 0
        tag_eth = st.selectbox("模特族裔", ETHNICITIES, index=eth_idx, key="pm_eth")
    with col2:
        age_idx = AGES.index(saved_tags.get("age", AGES[0])) if saved_tags.get("age") in AGES else 0
        tag_age = st.selectbox("模特年龄", AGES, index=age_idx, key="pm_age")
    with col3:
        bg_idx = BACKGROUNDS.index(saved_tags.get("background", BACKGROUNDS[0])) if saved_tags.get("background") in BACKGROUNDS else 0
        tag_bg = st.selectbox("背景场景", BACKGROUNDS, index=bg_idx, key="pm_bg")

    st.markdown("### 📝 提示词内容")
    new_prompt_name = st.text_input("提示名称", value=selected_prompt if selected_prompt != "创建新提示" else "")
    prompt_text = st.text_area("提示内容", value=prompt_content, height=300)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("保存提示", use_container_width=True):
            if new_prompt_name and prompt_text:
                if not new_prompt_name.endswith(".txt"):
                    new_prompt_name += ".txt"
                with open(os.path.join(PROMPTS_DIR, new_prompt_name), "w", encoding="utf-8") as f:
                    f.write(prompt_text)
                tags_data = {"ethnicity": tag_eth, "age": tag_age, "background": tag_bg}
                tag_file = os.path.join(PROMPTS_DIR, new_prompt_name.replace(".txt", "_tags.json"))
                with open(tag_file, "w", encoding="utf-8") as f:
                    json.dump(tags_data, f, ensure_ascii=False, indent=4)
                st.success(f"提示 '{new_prompt_name}' 保存成功！")
                st.rerun()
    with col2:
        if selected_prompt != "创建新提示" and st.button("删除提示", type="primary", use_container_width=True):
            os.remove(os.path.join(PROMPTS_DIR, selected_prompt))
            tag_file = os.path.join(PROMPTS_DIR, selected_prompt.replace(".txt", "_tags.json"))
            if os.path.exists(tag_file):
                os.remove(tag_file)
            st.success("已删除。")
            st.rerun()

def render_history(LOGS_DIR):
    st.header("Picture Generation Tracker")
    log_root = LOGS_DIR
    if not os.path.exists(log_root):
        return
    projects = [d for d in os.listdir(log_root) if os.path.isdir(os.path.join(log_root, d))]
    if not projects:
        st.info("暂无生成历史。")
        return
    tracker_data = []
    for p in projects:
        p_path = os.path.join(log_root, p)
        mtime = os.path.getmtime(p_path)
        prompt = ""
        if os.path.exists(os.path.join(p_path, "prompt.txt")):
            with open(os.path.join(p_path, "prompt.txt"), "r", encoding="utf-8") as f:
                prompt = f.read()
        metadata = {}
        if os.path.exists(os.path.join(p_path, "metadata.json")):
            with open(os.path.join(p_path, "metadata.json"), "r", encoding="utf-8") as f:
                metadata = json.load(f)
        preview = None
        out_dir = os.path.join(p_path, "outputs")
        if os.path.exists(out_dir):
            out_files = [f for f in os.listdir(out_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
            if out_files:
                preview = os.path.join(out_dir, sorted(out_files)[0])
        if not preview and metadata.get("test_mode"):
            placeholder_path = os.path.join(ROOT_DIR, "placeholder.png")
            if os.path.exists(placeholder_path):
                preview = placeholder_path
        tracker_data.append({"id": p, "prompt": prompt, "mtime": mtime, "preview": preview, "metadata": metadata})
    tracker_data.sort(key=lambda x: x["mtime"], reverse=True)
    with st.container():
        f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns([2, 1, 1, 1, 0.5])
        with f_col1:
            search_query = st.text_input("🔍 搜索 (Product ID / Prompt)", "").lower()
        ethnicities = sorted(list(set([d["metadata"].get("ethnicity", "N/A") for d in tracker_data if d.get("metadata")])))
        ages = sorted(list(set([d["metadata"].get("age", "N/A") for d in tracker_data if d.get("metadata")])))
        backgrounds = sorted(list(set([d["metadata"].get("background", "N/A") for d in tracker_data if d.get("metadata")])))
        with f_col2:
            f_eth = st.selectbox("族裔", ["全部"] + ethnicities)
        with f_col3:
            f_age = st.selectbox("年龄", ["全部"] + ages)
        with f_col4:
            f_bg = st.selectbox("背景", ["全部"] + backgrounds)
        with f_col5:
            st.write("")
            if st.button("🔄", help="重置筛选"):
                st.rerun()
    filtered_data = []
    for d in tracker_data:
        m = d.get("metadata", {})
        match_search = search_query in d["id"].lower() or search_query in d["prompt"].lower()
        match_eth = (f_eth == "全部") or (m.get("ethnicity") == f_eth)
        match_age = (f_age == "全部") or (m.get("age") == f_age)
        match_bg = (f_bg == "全部") or (m.get("background") == f_bg)
        if match_search and match_eth and match_age and match_bg:
            filtered_data.append(d)
    st.markdown("---")
    if not filtered_data:
        st.warning("没有找到匹配的项目。")
        return
    h_col1, h_col2, h_col3 = st.columns([1, 4, 1])
    h_col1.markdown("**预览**")
    h_col2.markdown("**项目详情 (Card View)**")
    h_col3.markdown("**操作**")
    for item in filtered_data:
        with st.container():
            c1, c2, c3 = st.columns([1, 4, 1])
            with c1:
                if item["preview"]:
                    st.image(item["preview"], use_container_width=True)
                else:
                    st.caption("No Output")
            with c2:
                st.markdown(f"### ID: `{item['id']}`")
                m = item.get("metadata", {})
                if m:
                    tags = []
                    if m.get("ethnicity"): tags.append(f"👤 {m['ethnicity']}")
                    if m.get("age"): tags.append(f"🎂 {m['age']}")
                    if m.get("background"): tags.append(f"🖼️ {m['background']}")
                    if m.get("task_type"): tags.append(f"⚙️ {m['task_type']}")
                    if m.get("test_mode"): tags.append(f"🧪 Test Mode")
                    st.markdown(" ".join([f"`{t}`" for t in tags]))
                st.caption(item["prompt"][:200] + "..." if len(item["prompt"]) > 200 else item["prompt"])
                st.caption(f"📅 {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(item['mtime']))}")
            with c3:
                with st.expander("查看详情"):
                    st.write(f"**完整提示词:**")
                    st.code(item["prompt"])
                    sub_col1, sub_col2 = st.columns(2)
                    with sub_col1:
                        if st.button("重新启动", key=f"restart_{item['id']}", use_container_width=True):
                            st.session_state["input_prompt"] = item["prompt"]
                            st.session_state["input_project_name"] = item["id"]
                            st.session_state["navigate_to"] = "新项目"
                            st.rerun()
                    with sub_col2:
                        if st.button("删除项目", key=f"del_{item['id']}", type="primary", use_container_width=True):
                            shutil.rmtree(os.path.join(log_root, item["id"]))
                            st.rerun()
            p_path = os.path.join(log_root, item["id"])
            input_dir = os.path.join(p_path, "inputs"); output_dir = os.path.join(p_path, "outputs")
            if os.path.exists(input_dir):
                in_files = sorted([f for f in os.listdir(input_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))])
                if in_files:
                    st.markdown("**输入图片:**")
                    in_cols = st.columns(3)
                    for idx, f_name in enumerate(in_files):
                        in_cols[idx % 3].image(os.path.join(input_dir, f_name), use_container_width=True)
            if os.path.exists(output_dir):
                out_files = sorted([f for f in os.listdir(output_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))])
                if out_files:
                    st.markdown("**生成结果:**")
                    out_cols = st.columns(2)
                    for idx, of in enumerate(out_files):
                        out_cols[idx % 2].image(os.path.join(output_dir, of), use_container_width=True)
                        with open(os.path.join(output_dir, of), "rb") as f:
                            st.download_button("下载", f, file_name=of, key=f"dl_{item['id']}_{idx}", use_container_width=True)
            st.markdown("---")

                st.rerun()
    filtered_data = []
    for d in tracker_data:
        m = d.get("metadata", {})
        match_search = search_query in d["id"].lower() or search_query in d["prompt"].lower()
        match_eth = (f_eth == "全部") or (m.get("ethnicity") == f_eth)
        match_age = (f_age == "全部") or (m.get("age") == f_age)
        match_bg = (f_bg == "全部") or (m.get("background") == f_bg)
        if match_search and match_eth and match_age and match_bg:
            filtered_data.append(d)
    st.markdown("---")
    if not filtered_data:
        st.warning("没有找到匹配的项目。")
        return
    h_col1, h_col2, h_col3 = st.columns([1, 4, 1])
    h_col1.markdown("**预览**")
    h_col2.markdown("**项目详情 (Card View)**")
    h_col3.markdown("**操作**")
    for item in filtered_data:
        with st.container():
            c1, c2, c3 = st.columns([1, 4, 1])
            with c1:
                if item["preview"]:
                    st.image(item["preview"], use_container_width=True)
                else:
                    st.caption("No Output")
            with c2:
                st.markdown(f"### ID: `{item['id']}`")
                m = item.get("metadata", {})
                if m:
                    tags = []
                    if m.get("ethnicity"): tags.append(f"👤 {m['ethnicity']}")
                    if m.get("age"): tags.append(f"🎂 {m['age']}")
                    if m.get("background"): tags.append(f"🖼️ {m['background']}")
                    if m.get("task_type"): tags.append(f"⚙️ {m['task_type']}")
                    if m.get("test_mode"): tags.append(f"🧪 Test Mode")
                    st.markdown(" ".join([f"`{t}`" for t in tags]))
                st.caption(item["prompt"][:200] + "..." if len(item["prompt"]) > 200 else item["prompt"])
                st.caption(f"📅 {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(item['mtime']))}")
            with c3:
                with st.expander("查看详情"):
                    st.write(f"**完整提示词:**")
                    st.code(item["prompt"])
                    sub_col1, sub_col2 = st.columns(2)
                    with sub_col1:
                        if st.button("重新启动", key=f"restart_{item['id']}", use_container_width=True):
                            st.session_state["input_prompt"] = item["prompt"]
                            st.session_state["input_project_name"] = item["id"]
                            st.session_state["navigate_to"] = "新项目"
                            st.rerun()
                    with sub_col2:
                        if st.button("删除项目", key=f"del_{item['id']}", type="primary", use_container_width=True):
                            shutil.rmtree(os.path.join(log_root, item["id"]))
                            st.rerun()
            p_path = os.path.join(log_root, item["id"])
            input_dir = os.path.join(p_path, "inputs"); output_dir = os.path.join(p_path, "outputs")
            if os.path.exists(input_dir):
                in_files = sorted([f for f in os.listdir(input_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))])
                if in_files:
                    st.markdown("**输入图片:**")
                    in_cols = st.columns(3)
                    for idx, f_name in enumerate(in_files):
                        in_cols[idx % 3].image(os.path.join(input_dir, f_name), use_container_width=True)
            if os.path.exists(output_dir):
                out_files = sorted([f for f in os.listdir(output_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))])
                if out_files:
                    st.markdown("**生成结果:**")
                    out_cols = st.columns(2)
                    for idx, of in enumerate(out_files):
                        out_cols[idx % 2].image(os.path.join(output_dir, of), use_container_width=True)
                        with open(os.path.join(output_dir, of), "rb") as f:
                            st.download_button("下载", f, file_name=of, key=f"dl_{item['id']}_{idx}", use_container_width=True)
            st.markdown("---")
