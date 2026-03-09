import os
from dotenv import load_dotenv
from google import genai
from PIL import Image

# 1. 載入 .env 檔案入面嘅 API Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# 2. 初始化 Gemini Client
client = genai.Client(api_key=api_key)

def test_image_processing():
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    img_path = os.path.join(ROOT_DIR, 'data', 'inputs', '12501021.jpg') 
    
    if not os.path.exists(img_path):
        print(f"❌ 搵唔到 {img_path}，請擺張 product.jpg 喺同一個 folder 先！")
        return

    # 3. 讀取圖片
    img = Image.open(img_path)

    print("🚀 正在連線 Gemini 1.5 Flash API...")
    try:
        # 4. 使用截圖中顯示有額度 (5 RPM) 嘅模型
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=["Describe this garment for a B2B platform. Focus on fabric and design.", img]
        )
        
        print("-" * 30)
        print("📢 AI 分析結果：")
        print(response.text)
        print("-" * 30)
        
    except Exception as e:
        print(f"❌ 依然有錯：{e}")

if __name__ == "__main__":
    test_image_processing()