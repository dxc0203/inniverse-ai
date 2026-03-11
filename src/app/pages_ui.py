import streamlit as st
import os
import shutil
from PIL import Image
from models import generate_image_from_text, generate_image_from_image_and_text
from ui_components import prompt_builder_ui

def render_new_project(LOGS_DIR, test_mode):
    project_name = st.text_input("项目名称", value="我的项目_001", key="input_project_name")
    
    # --- ✨ 新功能: 模特与场景预设 ---
    with st.expander("✨ 模特与场景快捷预设", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            model_ethnicity = st.selectbox("模特族裔", ["西方人 (Western)", "亚洲人 (Asian)", "非洲人 (African)", "拉丁裔 (Hispanic)"], index=0)
        with col2:
            model_age = st.selectbox("模特年龄", ["20多岁 (20s)", "30多岁 (30s)", "40多岁 (40s)"], index=0)
        with col3:
            scene_bg = st.selectbox("背景场景", ["灰色影棚 (Grey Studio)", "户外街道 (Street)", "公园 (Park)", "室内客厅 (Living Room)"], index=0)
        
        use_default_prompt = st.checkbox("使用智能系统提示词 (推荐)", value=True, help="开启后将自动结合以上预设和默认服饰展示逻辑。")

    # --- 提示词构建器 ---
    new_prompt = prompt_builder_ui("new_project")
    if new_prompt:
        st.session_state["input_prompt"] = new_prompt
        st.success("已从构建器生成提示词。")
    
    # 手动输入区域
    user_prompt_base = st.text_area("详细提示词描述 (可选)", value=st.session_state.get("input_prompt", ""), key="input_prompt_area", height=100, help="如果您有特定要求，可以在此输入。")
    
    # 提示词组装逻辑
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

    task_type = st.selectbox("选择任务类型", ["从文本生成图像", "从图像和文本生成图像"], key="task_type_selector", index=1)
    
    if task_type == "从图像和文本生成图像":
        st.info("💡 提示：您可以上传最多 5 张不同角度的商品图（平铺或挂拍），AI 将参考这些图片生成模特上身效果。")
        newly_uploaded_files = st.file_uploader("上传商品图片 (可多选)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
        if newly_uploaded_files:
            st.session_state["uploaded_files"] = newly_uploaded_files
    
    # 图像预览与管理
    if task_type == "从图像和文本生成图像" and st.session_state["uploaded_files"]:
        if len(st.session_state["uploaded_files"]) > 5:
            st.error(f"您上传了 {len(st.session_state['uploaded_files'])} 个文件。最多支持 5 个。")
        else:
            processed_imgs = []
            cols = st.columns(min(len(st.session_state["uploaded_files"]), 5))
            for idx, up_file in enumerate(st.session_state["uploaded_files"]):
                img = Image.open(up_file)
                img.thumbnail((1024, 1024))
                processed_imgs.append(img)
                with cols[idx]:
                    st.image(img, caption=f"角度 {idx + 1}", use_container_width=True)
                    if st.button("删除", key=f"delete_{idx}"):
                        st.session_state["uploaded_files"].pop(idx)
                        st.rerun()
    
    if st.button("运行 AI", type="primary", use_container_width=True):
        final_prompt = assemble_prompt(user_prompt_base, use_default_prompt, model_ethnicity, model_age, scene_bg)
        
        log_dir = os.path.join(LOGS_DIR, project_name)
        os.makedirs(os.path.join(log_dir, "inputs"), exist_ok=True)
        os.makedirs(os.path.join(log_dir, "outputs"), exist_ok=True)
        
        with open(os.path.join(log_dir, "prompt.txt"), "w", encoding="utf-8") as f:
            f.write(final_prompt)
        
        with st.spinner("AI 正在构思模特试穿效果..."):
            if task_type == "从文本生成图像":
                image_results = generate_image_from_text(final_prompt, test_mode)
            else:
                if 'processed_imgs' in locals() and processed_imgs:
                                        # Save all input images and pass them all to the model
                    for save_idx, save_img in enumerate(processed_imgs):
                        save_img.save(os.path.join(log_dir, "inputs", f"input_image_{save_idx+1}.png"))
                    image_results = generate_image_from_image_and_text(processed_imgs, final_prompt, test_mode)
                    st.warning("请上传至少一张商品图片。")
                    return

            if image_results:
                st.subheader("✨ 生成结果")
                res_cols = st.columns(len(image_results))
                for i, img_data in enumerate(image_results):
                    img_path = img_data if test_mode else os.path.join(log_dir, "outputs", f"generated_image_{i+1}.png")
                    if not test_mode:
                        with open(img_path, "wb") as f:
                            f.write(img_data)
                    with res_cols[i]:
                        st.image(img_path, caption=f"效果图 {i+1}", use_container_width=True)
                        if not test_mode:
                             with open(img_path, "rb") as file:
                                 st.download_button(label=f"下载效果图 {i+1}", data=file, file_name=f"result_{i+1}.png", mime="image/png", key=f"dl_{i}")
                st.success("图像生成完成！已保存到历史记录。")

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

# End of pages_ui.py
