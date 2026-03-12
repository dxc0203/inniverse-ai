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
from constants import ROOT_DIR

# --- Configuration Constants ---
ETHNICITIES = ["西方人 (Western)", "亚洲人 (Asian)", "非洲人 (African)", "拉丁裔 (Hispanic)"]
AGES = ["20多岁 (20s)", "30多岁 (30s)", "40多岁 (40s)"]
GENDERS = ["女性 (Female)", "男性 (Male)", "中性 (Unisex)"]
BODY_TYPES = ["标准 (Standard)", "加大码 (Plus Size)", "运动型 (Athletic)"]
BACKGROUNDS = ["灰色影棚 (Grey Studio)", "户外街道 (Street)", "公園 (Park)", "室内客厅 (Living Room)"]
ASPECT_RATIOS = ["1:1 (Square)", "2:3 (Portrait/Fashion)", "3:2 (Landscape)", "16:9 (Banner)"]

def render_tag_selectors(prefix, saved_tags=None):
    """Shared UI component for model and scene selection."""
    if saved_tags is None:
        saved_tags = {}
    
    # Model Tags Row
    st.markdown("##### 👤 模特设置")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        eth_idx = ETHNICITIES.index(saved_tags.get("ethnicity", ETHNICITIES[0])) if saved_tags.get("ethnicity") in ETHNICITIES else 0
        eth = st.selectbox("族裔", ETHNICITIES, index=eth_idx, key=f"{prefix}_eth")
    with col2:
        age_idx = AGES.index(saved_tags.get("age", AGES[0])) if saved_tags.get("age") in AGES else 0
        age = st.selectbox("年龄", AGES, index=age_idx, key=f"{prefix}_age")
    with col3:
        gen_idx = GENDERS.index(saved_tags.get("gender", GENDERS[0])) if saved_tags.get("gender") in GENDERS else 0
        gender = st.selectbox("性别", GENDERS, index=gen_idx, key=f"{prefix}_gender")
    with col4:
        body_idx = BODY_TYPES.index(saved_tags.get("body_type", BODY_TYPES[0])) if saved_tags.get("body_type") in BODY_TYPES else 0
        body = st.selectbox("体型", BODY_TYPES, index=body_idx, key=f"{prefix}_body")

    # Scene & Format Row
    st.markdown("##### 🖼️ 场景与格式")
    col5, col6 = st.columns(2)
    with col5:
        bg_idx = BACKGROUNDS.index(saved_tags.get("background", BACKGROUNDS[0])) if saved_tags.get("background") in BACKGROUNDS else 0
        bg = st.selectbox("背景场景", BACKGROUNDS, index=bg_idx, key=f"{prefix}_bg")
    with col6:
        ar_idx = ASPECT_RATIOS.index(saved_tags.get("aspect_ratio", ASPECT_RATIOS[1])) if saved_tags.get("aspect_ratio") in ASPECT_RATIOS else 1
        ar = st.selectbox("画幅比例", ASPECT_RATIOS, index=ar_idx, key=f"{prefix}_ar")
        
    return {
        "ethnicity": eth, 
        "age": age, 
        "gender": gender, 
        "body_type": body, 
        "background": bg, 
        "aspect_ratio": ar
    }

def render_new_project(LOGS_DIR, PROMPTS_DIR, test_mode):
    st.header("新建项目")
    if not os.path.exists(PROMPTS_DIR):
        os.makedirs(PROMPTS_DIR, exist_ok=True)
    
    prompt_files = sorted([f for f in os.listdir(PROMPTS_DIR) if f.endswith(".txt")])
    prompt_options_display = ["从空白开始 (Blank)"] + [os.path.splitext(f)[0] for f in prompt_files]
    
    bulk_count = st.number_input("想一次建立几个新專案？", min_value=1, max_value=5, value=1, step=1)
    projects_data = []
    
    for i in range(bulk_count):
        with st.expander(f"项目 {i+1} 配置", expanded=(i==0)):
            p_name = st.text_input(f"项目名称 / Product ID", value=f"PROJ_{uuid.uuid4().hex[:8].upper()}", key=f"bulk_name_{i}")
            
            # Shared Tag Selectors
            tags = render_tag_selectors(f"bulk_{i}")
            use_def = st.checkbox("使用智能系统提示词 (推荐)", value=True, key=f"bulk_use_def_{i}")
            
            selected_display = st.selectbox(f"选择提示词模板 (项目 {i+1})", prompt_options_display, key=f"bulk_p_sel_{i}")
            template_content = ""
            if selected_display != "从空白开始 (Blank)":
                try:
                    with open(os.path.join(PROMPTS_DIR, selected_display + ".txt"), "r", encoding="utf-8") as f:
                        template_content = f.read()
                except:
                    pass
            
            u_prompt = st.text_area("詳細提示词描述", value=template_content, key=f"bulk_prompt_{i}", height=100, help="描述衣物的细节、材质等")
            neg_prompt = st.text_input("排除内容 (Negative Prompt)", value="watermark, text, blurry, low quality, distorted", key=f"bulk_neg_{i}")
            
            # Preview of assembled prompt
            final_p_preview = assemble_prompt(u_prompt, use_def, tags)
            with st.expander("📝 最终提示词预览"):
                st.code(final_p_preview)
            
            save_prompt = False
            save_name = ""
            if selected_display == "从空白开始 (Blank)":
                save_prompt = st.checkbox("記錄此新提示词 (Save as template)", value=False, key=f"bulk_save_check_{i}")
                if save_prompt:
                    save_name = st.text_input("提示词模板名称", value=f"Template_{int(time.time())}", key=f"bulk_save_name_{i}")
            
            t_type = st.selectbox("选择任务类型", ["从文本生成图像", "从图像和文本生成图像"], key=f"bulk_task_{i}", index=1)
            up_files = None
            if t_type == "从图像和文本生成图像":
                up_files = st.file_uploader(f"上传商品图片 (项目 {i+1})", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key=f"bulk_up_{i}")
                if up_files:
                    preview_cols = st.columns(5)
                    for idx, up_file in enumerate(up_files[:5]):
                        with preview_cols[idx]:
                            st.image(up_file, width=150)
            
            projects_data.append({
                "name": p_name,
                "tags": tags,
                "use_def": use_def,
                "prompt": u_prompt,
                "neg_prompt": neg_prompt,
                "task_type": t_type,
                "files": up_files,
                "save_prompt": save_prompt,
                "save_name": save_name
            })
            
    if st.button("批量运行 AI", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        for idx, data in enumerate(projects_data):
            # Validation
            if data['task_type'] == "从图像和文本生成图像" and not data['files']:
                st.error(f"项目 {idx+1} ({data['name']}): 请上传至少一张商品图片。")
                continue
                
            st.write(f"### 正在处理项目 {idx+1}/{len(projects_data)}: {data['name']}...")
            
            # Save prompt if requested
            if data['save_prompt'] and data['save_name'] and data['prompt']:
                s_name = data['save_name'] if data['save_name'].endswith(".txt") else data['save_name'] + ".txt"
                with open(os.path.join(PROMPTS_DIR, s_name), "w", encoding="utf-8") as f:
                    f.write(data['prompt'])
                st.info(f"已保存新提示词模板: {s_name}")
            
            final_p = assemble_prompt(data['prompt'], data['use_def'], data['tags'])
            if data['neg_prompt']:
                final_p += f" [Negative: {data['neg_prompt']}]"
                
            log_dir = os.path.join(LOGS_DIR, data['name'])
            os.makedirs(os.path.join(log_dir, "inputs"), exist_ok=True)
            os.makedirs(os.path.join(log_dir, "outputs"), exist_ok=True)
            
            with open(os.path.join(log_dir, "prompt.txt"), "w", encoding="utf-8") as f:
                f.write(final_p)
                
            metadata = {
                "id": data['name'],
                "timestamp": time.time(),
                "tags": data['tags'],
                "task_type": data['task_type'],
                "use_default": data['use_def'],
                "base_prompt": data['prompt'],
                "neg_prompt": data['neg_prompt'],
                "test_mode": test_mode
            }
            with open(os.path.join(log_dir, "metadata.json"), "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=4)
            
            processed_imgs = []
            if data['task_type'] == "从图像和文本生成图像":
                for f_idx, up_file in enumerate(data['files'][:5]):
                    img = Image.open(up_file)
                    img.thumbnail((1024, 1024))
                    img.save(os.path.join(log_dir, "inputs", f"input_image_{f_idx+1}.png"))
                    processed_imgs.append(img)
            
            with st.spinner(f"AI 正在生成结果..."):
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
            
            progress_bar.progress((idx + 1) / len(projects_data))
        
        st.success("批量处理完成！")
        st.balloons()
        st.session_state["navigate_to"] = "历史记录"
        st.rerun()

def assemble_prompt(base_text, use_default, tags):
    if not use_default and base_text.strip():
        return base_text
    
    eth_map = {"西方人 (Western)": "western", "亚洲人 (Asian)": "asian", "非洲人 (African)": "african", "拉丁裔 (Hispanic)": "hispanic"}
    age_map = {"20多岁 (20s)": "mid 20s", "30多岁 (30s)": "30s", "40多岁 (40s)": "40s"}
    gen_map = {"女性 (Female)": "female", "男性 (Male)": "male", "中性 (Unisex)": "unisex"}
    body_map = {"标准 (Standard)": "standard body type", "加大码 (Plus Size)": "plus size", "运动型 (Athletic)": "athletic build"}
    bg_map = {"灰色影棚 (Grey Studio)": "in a professional grey studio", "户外街道 (Street)": "on a sunny city street", "公園 (Park)": "in a green lush park", "室内客厅 (Living Room)": "in a cozy modern living room"}
    
    ar_str = tags['aspect_ratio'].split(" ")[0]
    
    system_base = f"A {age_map[tags['age']]} {eth_map[tags['ethnicity']]} {gen_map[tags['gender']]} model with {body_map[tags['body_type']]} wearing the garment, {bg_map[tags['background']]}. Fashion photography style, aspect ratio {ar_str}."
    
    return f"{system_base} {base_text}" if base_text.strip() else system_base

def render_prompt_management(PROMPTS_DIR):
    st.header("提示词管理")
    if not os.path.exists(PROMPTS_DIR):
        os.makedirs(PROMPTS_DIR, exist_ok=True)
    
    prompt_files = sorted([f for f in os.listdir(PROMPTS_DIR) if f.endswith(".txt")])
    display_names = [os.path.splitext(f)[0] for f in prompt_files]
    
    selected_display = st.selectbox("选择提示", ["创建新提示"] + display_names)
    selected_prompt_file = (selected_display + ".txt") if selected_display != "创建新提示" else None
    
    prompt_content = ""
    saved_tags = {}
    
    if selected_prompt_file:
        try:
            with open(os.path.join(PROMPTS_DIR, selected_prompt_file), "r", encoding="utf-8") as f:
                prompt_content = f.read()
        except:
            pass
        
        tag_file = os.path.join(PROMPTS_DIR, selected_prompt_file.replace(".txt", "_tags.json"))
        if os.path.exists(tag_file):
            try:
                with open(tag_file, "r", encoding="utf-8") as f:
                    saved_tags = json.load(f)
            except:
                pass
                
    st.markdown("### 🏷️ 默认标签设置")
    tags = render_tag_selectors("pm", saved_tags)
    
    st.markdown("### 📝 提示词内容")
    col_name, col_count = st.columns([3, 1])
    with col_name:
        new_prompt_name = st.text_input("提示名称", value=selected_display if selected_display != "创建新提示" else "")
    with col_count:
        st.write("") # Spacer
        st.caption(f"字符数: {len(prompt_content)}")
        
    prompt_text = st.text_area("提示内容", value=prompt_content, height=300)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("保存提示", use_container_width=True):
            if new_prompt_name and prompt_text:
                file_name = new_prompt_name if new_prompt_name.endswith(".txt") else new_prompt_name + ".txt"
                with open(os.path.join(PROMPTS_DIR, file_name), "w", encoding="utf-8") as f:
                    f.write(prompt_text)
                
                tag_file_name = file_name.replace(".txt", "_tags.json")
                with open(os.path.join(PROMPTS_DIR, tag_file_name), "w", encoding="utf-8") as f:
                    json.dump(tags, f, ensure_ascii=False, indent=4)
                
                st.success(f"提示 '{new_prompt_name}' 保存成功！")
                st.rerun()
    
    with col2:
        if selected_prompt_file:
            if st.button("📋 复制提示词", use_container_width=True):
                st.session_state["duplicate_prompt"] = f"{selected_display}_Copy"
                # Simple implementation: just pre-fill name and rerun
                st.rerun()
                
    with col3:
        if selected_prompt_file:
            if st.button("删除提示", type="primary", use_container_width=True):
                st.session_state["confirm_delete_prompt"] = selected_prompt_file
    
    if "confirm_delete_prompt" in st.session_state and st.session_state["confirm_delete_prompt"] == selected_prompt_file:
        st.warning(f"确定要删除 '{selected_display}' 吗？此操作不可撤回。")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("确认删除", type="primary", use_container_width=True):
                os.remove(os.path.join(PROMPTS_DIR, selected_prompt_file))
                tag_f = os.path.join(PROMPTS_DIR, selected_prompt_file.replace(".txt", "_tags.json"))
                if os.path.exists(tag_f):
                    os.remove(tag_f)
                del st.session_state["confirm_delete_prompt"]
                st.rerun()
        with c2:
            if st.button("取消", use_container_width=True):
                del st.session_state["confirm_delete_prompt"]
                st.rerun()

def render_history(LOGS_DIR):
    st.header("Picture Generation Tracker")
    if not os.path.exists(LOGS_DIR): return
    
    projects = [d for d in os.listdir(LOGS_DIR) if os.path.isdir(os.path.join(LOGS_DIR, d))]
    if not projects:
        st.info("暂无生成历史。")
        return
    
    tracker_data = []
    for p in projects:
        p_path = os.path.join(LOGS_DIR, p)
        mtime = os.path.getmtime(p_path)
        prompt = ""
        if os.path.exists(os.path.join(p_path, "prompt.txt")):
            with open(os.path.join(p_path, "prompt.txt"), "r", encoding="utf-8") as f:
                prompt = f.read()
        
        metadata = {}
        if os.path.exists(os.path.join(p_path, "metadata.json")):
            try:
                with open(os.path.join(p_path, "metadata.json"), "r", encoding="utf-8") as f:
                    metadata = json.load(f)
            except: pass
        
        preview = None
        out_dir = os.path.join(p_path, "outputs")
        if os.path.exists(out_dir):
            out_files = [f for f in os.listdir(out_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
            if out_files:
                preview = os.path.join(out_dir, sorted(out_files)[0])
        
        tracker_data.append({"id": p, "prompt": prompt, "mtime": mtime, "preview": preview, "metadata": metadata})
    
    tracker_data.sort(key=lambda x: x["mtime"], reverse=True)
    
    # Filter Row
    f_col1, f_col2, f_col3, f_col4 = st.columns([2, 1, 1, 0.5])
    with f_col1:
        search_query = st.text_input("🔍 搜索 (Product ID / Prompt)", "").lower()
    with f_col2:
        st.write("") # Spacer
    with f_col4:
        st.write("")
        if st.button("🔄", help="重置筛选"): st.rerun()
    
    filtered_data = [d for d in tracker_data if search_query in d["id"].lower() or search_query in d["prompt"].lower()]
    
    st.markdown("---")
    if not filtered_data:
        st.warning("没有找到匹配的项目。")
        return
    
    h_col1, h_col2, h_col3 = st.columns([1, 3, 1.5])
    h_col1.markdown("**预览**")
    h_col2.markdown("**项目详情**")
    h_col3.markdown("**操作**")
    
    for item in filtered_data:
        with st.container():
            c1, c2, c3 = st.columns([1, 3, 1.5])
            with c1:
                if item["preview"]: st.image(item["preview"], use_container_width=True)
                else: st.caption("No Output")
            with c2:
                st.markdown(f"### ID: `{item['id']}`")
                m = item.get("metadata", {})
                if m:
                    tags = m.get("tags", {})
                    badge_str = " ".join([f"`{v}`" for v in tags.values() if v])
                    st.markdown(badge_str)
                    if m.get("neg_prompt"):
                        st.caption(f"🚫 排除: {m['neg_prompt']}")
                st.caption(item["prompt"][:200] + "..." if len(item["prompt"]) > 200 else item["prompt"])
                st.caption(f"📅 {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(item['mtime']))}")
            
            with c3:
                # 1. Download ZIP of outputs
                out_dir = os.path.join(LOGS_DIR, item["id"], "outputs")
                if os.path.exists(out_dir):
                    out_files = [f for f in os.listdir(out_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
                    if out_files:
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w") as zf:
                            for f in out_files:
                                zf.write(os.path.join(out_dir, f), arcname=f)
                        st.download_button(
                            label="📦 下载全部图片 (ZIP)",
                            data=zip_buffer.getvalue(),
                            file_name=f"{item['id']}_outputs.zip",
                            mime="application/zip",
                            use_container_width=True,
                            key=f"zip_{item['id']}"
                        )

                # 2. Details & Delete
                with st.expander("更多选项", expanded=False):
                    if st.button("🔄 重新启动", key=f"restart_{item['id']}", use_container_width=True):
                        st.session_state["input_prompt"] = item["prompt"]
                        st.session_state["input_project_name"] = item["id"]
                        st.session_state["navigate_to"] = "新项目"
                        st.rerun()
                    
                    if st.button("🗑️ 删除项目", key=f"del_{item['id']}", type="primary", use_container_width=True):
                        st.session_state[f"confirm_del_{item['id']}"] = True
                    
                    if st.session_state.get(f"confirm_del_{item['id']}"):
                        st.error("确定删除吗？")
                        d_col1, d_col2 = st.columns(2)
                        with d_col1:
                            if st.button("确认", key=f"conf_del_{item['id']}", type="primary", use_container_width=True):
                                shutil.rmtree(os.path.join(LOGS_DIR, item["id"]))
                                del st.session_state[f"confirm_del_{item['id']}"]
                                st.rerun()
                        with d_col2:
                            if st.button("取消", key=f"canc_del_{item['id']}", use_container_width=True):
                                del st.session_state[f"confirm_del_{item['id']}"]
                                st.rerun()
            st.markdown("---")
