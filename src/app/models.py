import os
import io
import time
import streamlit as st
import google.genai as genai
import google.genai.types as genai_types
from PIL import Image
from constants import ROOT_DIR

# Use gemini-2.0-flash-preview-image-generation which supports inline image output
IMAGE_MODEL = "gemini-2.0-flash-preview-image-generation"

def _get_placeholder():
    """Return a placeholder image path, creating it if needed."""
    placeholder_path = os.path.join(ROOT_DIR, "placeholder.png")
    if not os.path.exists(placeholder_path):
        img = Image.new('RGB', (512, 512), color='darkgray')
        img.save(placeholder_path)
    return placeholder_path

def _get_client():
    """Build and return a configured Gemini client."""
    api_key = st.session_state.get("api_key_input") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("Gemini API 密鑰未配置。请在左侧设置中输入。")
        return None
    return genai.Client(api_key=api_key)

def generate_image_from_text(prompt, is_test):
    if is_test:
        time.sleep(1)
        return [_get_placeholder()]
    
    client = _get_client()
    if not client:
        return None
    
    try:
        response = client.models.generate_content(
            model=IMAGE_MODEL,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"]
            )
        )
        image_bytes_list = []
        if response and response.candidates:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    image_bytes_list.append(part.inline_data.data)
        if not image_bytes_list:
            st.warning("模型未返回图像数据。")
        return image_bytes_list if image_bytes_list else None
    except Exception as e:
        st.error(f"生成图像时发生错误: {e}")
        return None

def generate_image_from_image_and_text(images, prompt, is_test):
    if is_test:
        time.sleep(1)
        return [_get_placeholder()]
    
    client = _get_client()
    if not client:
        return None
    
    try:
        # Build multimodal content: prompt text + all input images
        parts = [prompt]
        img_list = images if isinstance(images, list) else [images]
        for img in img_list:
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            parts.append(
                genai_types.Part.from_bytes(
                    data=buf.getvalue(),
                    mime_type="image/png"
                )
            )
        
        response = client.models.generate_content(
            model=IMAGE_MODEL,
            contents=parts,
            config=genai_types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"]
            )
        )
        image_bytes_list = []
        if response and response.candidates:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    image_bytes_list.append(part.inline_data.data)
        if not image_bytes_list:
            st.warning("模型未返回图像数据。")
        return image_bytes_list if image_bytes_list else None
    except Exception as e:
        st.error(f"生成图像时发生错误: {e}")
        return None
