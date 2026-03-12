import streamlit as st
import os
import shutil
import time
from PIL import Image
from models import generate_image_from_text, generate_image_from_image_and_text
from ui_components import prompt_builder_ui

def render_new_project(LOGS_DIR, test_mode):
    st.header("新建项目")
    
    # --- 批量生成功能 ---
    bulk_count = st.number_input("想一次建立几个新專案？", min_value=1, max_value=5, value=1, step=1)
    
    # 使用 list 存储每个项目的数据
    projects_data = []
    
    for i in range(bulk_count):
        with st.expander(f"项目 {i+1} 配置", expanded=(i==0)):
            p_name = st.text_input(f"项目名称 / Product ID", value=f"PROJ_{int(time.time())}_{i+1}", key=f"bulk_name_{i}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                eth = st.selectbox("模特族裔", ["西方人 (Western)", "亚洲人 (Asian)", "非洲人 (African)", "拉丁裔 (Hispanic)"], index=0, key=f"bulk_eth_{i}")
            with col2:
                age = st.selectbox("模特年龄", ["20多岁 (20s)", "30多岁 (30s)", "40多岁 (40s)"], index=0, key=f"bulk_age_{i}")
            with col3:
                bg = st.selectbox("背景场景", ["灰色影棚 (Grey Studio)", "户外街道 (Street)", "公园 (Park)", "室内客厅 (Living Room)"], index=0, key=f"bulk_bg_{i}")
            
            use_def = st.checkbox("使用智能系统提示词 (推荐)", value=True, key=f"bulk_use_def_{i}")
            
            u_prompt = st.text_area("详细提示词描述 (可选)", value="", key=f"bulk_prompt_{i}", height=100)
            
            t_type = st.selectbox("选择任务类型", ["从文本生成图像", "从图像和文本生成图像"], key=f"bulk_task_{i}", index=1)
            
            up_files = None
            if t_type == "从图像和文本生成图像":
                up_files = st.file_uploader(f"上传商品图片 (项目 {i+1})", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key=f"bulk_up_{i}")
            
            projects_data.append({
                "name": p_name,
                "eth": eth,
                "age": age,
                "bg": bg,
                "use_def": use_def,
                "prompt": u_prompt,
                "task_type": t_type,
                "files": up_files
            })

    def assemble_prompt(base_text, use_default, ethnicity, age, bg):
        if not use_default and base_text.strip():
            return base_text
        eth_map = {"西方人 (Western)": "western girl", "亚洲人 (Asian)": "asian girl", "非洲人 (African)": "african girl", "拉丁裔 (Hispanic)": "hispanic girl"}
        age_map = {"20多岁 (20s)": "in her mid 20s", "30多岁 (30s)": "in her 30s", "40多岁 (40s)": "in her 40s"}
        bg_map = {"灰色影棚 (Grey Studio)": "in a grey studio background", "户外街道 (Street)": "in a sunny street background", "公园 (Park)": "in a green park background", "室内客厅 (Living Room)": "in a modern living room background"}
        system_base = f"A {eth_map[ethnicity]} {age_map[age]} wearing the garment, taking the photo {bg_map[bg]}."
        if base_text.strip():
            return f"{system_base} {base_text}"
        return system_base

    if st.button("批量运行 AI", type="primary", use_container_width=True):
        for idx, data in enumerate(projects_data):
            st.write(f"### 正在处理项目 {idx+1}: {data['name']}...")
            
            final_p = assemble_prompt(data['prompt'], data['use_def'], data['eth'], data['age'], data['bg'])
            log_dir = os.path.join(LOGS_DIR, data['name'])
            os.makedirs(os.path.join(log_dir, "inputs"), exist_ok=True)
            os.makedirs(os.path.join(log_dir, "outputs"), exist_ok=True)
            
            with open(os.path.join(log_dir, "prompt.txt"), "w", encoding="utf-8") as f:
                f.write(final_p)
            
            processed_imgs = []
            if data['task_type'] == "从图像和文本生成图像":
                if data['files']:
                    for f_idx, up_file in enumerate(data['files'][:5]):
                        img = Image.open(up_file)
                        img.thumbnail((1024, 1024))
                        img.save(os.path.join(log_dir, "inputs", f"input_image_{f_idx+1}.png"))
                        processed_imgs.append(img)
                else:
                    st.warning(f"项目 {data['name']} 未上传图片，跳过。")
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
    prompt_files = [f for f in os.listdir(PROMPTS_DIR) if f.endswith(".txt")]
    selected_prompt = st.selectbox("选择提示", ["创建新提示"] + prompt_files)
    
    manage_prompt = prompt_builder_ui("manage")
    
    prompt_content = ""
    if selected_prompt != "创建新提示":
        try:
            with open(os.path.join(PROMPTS_DIR, selected_prompt), "r", encoding="utf-8") as f:
                prompt_content = f.read()
            st.session_state["selected_prompt_name"] = selected_prompt
        except Exception as e:
            st.error(f"读取提示文件时出错：{e}")
    
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

def render_history(LOGS_DIR):
    st.header("Picture Generation Tracker")
    log_root = LOGS_DIR
    if not os.path.exists(log_root):
        st.info("未找到日志目录。")
        return

    projects = [d for d in os.listdir(log_root) if os.path.isdir(os.path.join(log_root, d))]
    if not projects:
        st.info("在日志目录中找不到任何项目。")
        return

    # --- Tracker Summary View (Notion Style) ---
    tracker_data = []
    for p in projects:
        p_path = os.path.join(log_root, p)
        prompt_path = os.path.join(p_path, "prompt.txt")
        prompt_text = ""
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt_text = f.read()
        
        output_dir = os.path.join(p_path, "outputs")
        preview_img = None
        if os.path.exists(output_dir):
            out_files = sorted([f for f in os.listdir(output_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))])
            if out_files:
                preview_img = os.path.join(output_dir, out_files[0])
        
        tracker_data.append({
            "id": p,
            "preview": preview_img,
            "prompt": prompt_text,
            "mtime": os.path.getmtime(p_path)
        })
    
    tracker_data.sort(key=lambda x: x["mtime"], reverse=True)

    # Search bar for Tracker
    search_query = st.text_input("🔍 搜索项目 (Product ID / Prompt)", "").lower()
    filtered_data = [d for d in tracker_data if search_query in d["id"].lower() or search_query in d["prompt"].lower()]

    st.markdown("---")
    # Custom Row Headers
    h_col1, h_col2, h_col3 = st.columns([1, 4, 1])
    h_col1.markdown("**预览 (Preview)**")
    h_col2.markdown("**项目详情 (Project Details / Prompt)**")
    h_col3.markdown("**操作 (Action)**")

    for item in filtered_data:
        with st.container():
            c1, c2, c3 = st.columns([1, 4, 1])
            with c1:
                if item["preview"]:
                    st.image(item["preview"], use_container_width=True)
                else:
                    st.caption("No Output")
            with c2:
                st.markdown(f"**ID:** `{item['id']}`")
                st.caption(item["prompt"][:150] + "..." if len(item["prompt"]) > 150 else item["prompt"])
                st.caption(f"📅 {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(item['mtime']))}")
            with c3:
                if st.button("详情", key=f"view_{item['id']}", use_container_width=True):
                    st.session_state["history_selected_project"] = item["id"]
                    st.rerun()

    # Detailed Project View Overlay/Expansion
    selected_project = st.session_state.get("history_selected_project")
    if selected_project and selected_project in [p["id"] for p in tracker_data]:
        st.markdown("---")
        st.subheader(f"📑 详情檢視: {selected_project}")
        project_path = os.path.join(log_root, selected_project)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("重新启动 (Restart)", use_container_width=True):
                old_prompt_path = os.path.join(project_path, "prompt.txt")
                if os.path.exists(old_prompt_path):
                    with open(old_prompt_path, "r", encoding="utf-8") as f:
                        st.session_state["input_prompt"] = f.read()
                    st.session_state["input_project_name"] = selected_project
                    st.session_state["navigate_to"] = "新项目"
                    st.rerun()
        with col2:
            if st.session_state.get(f"confirm_del_{selected_project}"):
                st.warning("确定删除？")
                if st.button("确认删除", key=f"y_{selected_project}", type="primary", use_container_width=True):
                    shutil.rmtree(project_path)
                    del st.session_state[f"confirm_del_{selected_project}"]
                    del st.session_state["history_selected_project"]
                    st.rerun()
                if st.button("取消", key=f"n_{selected_project}", use_container_width=True):
                    del st.session_state[f"confirm_del_{selected_project}"]
                    st.rerun()
            else:
                if st.button("删除 (Delete)", type="primary", use_container_width=True):
                    st.session_state[f"confirm_del_{selected_project}"] = True
                    st.rerun()

        # Display content
        prompt_path = os.path.join(project_path, "prompt.txt")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                st.text_area("完整提示词", f.read(), height=150, disabled=True)
        
        input_dir = os.path.join(project_path, "inputs")
        output_dir = os.path.join(project_path, "outputs")
        
        st.subheader("输入与输出比较")
        if os.path.exists(input_dir):
            in_files = sorted([f for f in os.listdir(input_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))])
            for f_name in in_files:
                ic1, ic2 = st.columns(2)
                with ic1:
                    st.image(os.path.join(input_dir, f_name), caption="Input", use_container_width=True)
                
                # Try to find corresponding output
                out_name = f"generated_image_{f_name.split('_')[-1]}" if "input_image_" in f_name else f_name
                # Simple logic: show all outputs if matching fails
                with ic2:
                    out_path = os.path.join(output_dir, out_name)
                    if os.path.exists(out_path):
                        st.image(out_path, caption="Output", use_container_width=True)
                    else:
                        st.info("Output not mapped or multiple outputs available below.")

        st.subheader("所有生成结果")
        if os.path.exists(output_dir):
            out_files = sorted([f for f in os.listdir(output_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))])
            if out_files:
                res_cols = st.columns(3)
                for i, of in enumerate(out_files):
                    with res_cols[i % 3]:
                        st.image(os.path.join(output_dir, of), caption=of, use_container_width=True)
                        with open(os.path.join(output_dir, of), "rb") as f:
                            st.download_button("下载", f, file_name=of, key=f"dl_{selected_project}_{i}")
