import os
import time
import streamlit as st
import google.genai as genai
from PIL import Image
from constants import ROOT_DIR

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
            st.error(f"生成图像时发生意外错误: {e}")
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
            
            # 准备输入：提示词加上一个或多个图像
            inputs = [prompt]
            if isinstance(image, list):
                inputs.extend(image)
            else:
                inputs.append(image)
                
            response = model.generate_content(inputs)
            image_data_list = []
            if response and response.parts:
                for part in response.parts:
                    if part.inline_data:
                        image_data_list.append(part.inline_data.data)
            return image_data_list
        except Exception as e:
            st.error(f"生成图像时发生意外错误: {e}")
            return None
