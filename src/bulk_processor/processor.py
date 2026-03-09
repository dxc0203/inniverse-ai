import os
import time
from dotenv import load_dotenv
from google import genai
from PIL import Image

# 1. 載入環境變數與 Client
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROMPT_FILE = os.path.join(ROOT_DIR, 'data', 'prompts', 'bulk_prompt.txt')
INPUT_FOLDER = os.path.join(ROOT_DIR, 'data', 'inputs')
OUTPUT_FOLDER = os.path.join(ROOT_DIR, 'data', 'outputs')

def load_prompt():
    """從 prompt.txt 讀取你嘅專屬指令"""
    try:
        with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"❌ 讀取 prompt.txt 失敗: {e}")
        return None

def run_test():
    # 確保輸出路徑存在
    if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER)
    
    user_prompt = load_prompt()
    if not user_prompt: return

    # 搵出 inputs 入面嘅相片
    image_files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    print(f"🚀 搵到 {len(image_files)} 張測試圖片，開始執行...")

    for index, filename in enumerate(image_files):
        img_path = os.path.join(INPUT_FOLDER, filename)
        print(f"🎨 [{index+1}/{len(image_files)}] 正在處理: {filename}...")
        
        try:
            # 讀取產品相片
            product_img = Image.open(img_path)
            
            # 使用 Nano Banana 2 (Gemini 3 Flash Image) 進行編輯/合成
            # 佢會根據你嘅 Prompt 將產品與 Model 結合
            response = client.models.generate_image(
                model='gemini-3-flash-image', 
                prompt=user_prompt,
                reference_images=[product_img]  # 將產品相作為參考圖
            )
            
            # 儲存生成圖
            output_filename = f"model_output_{filename}"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            
            # 假設 response 返回圖片數據
            with open(output_path, "wb") as f:
                f.write(response.generated_images[0].image_bytes)
                
            print(f"✅ 成功生成並儲存至: {output_path}")
            
        except Exception as e:
            print(f"❌ {filename} 處理失敗: {e}")
        
        # 配合你帳戶嘅 5 RPM 限制，每張相中間休息 12 秒
        if index < len(image_files) - 1:
            print("⏳ 遵從 Rate Limit，休息 12 秒...")
            time.sleep(12)

    print("\n✨ 測試完成！請到 outputs 資料夾檢查結果。")

if __name__ == "__main__":
    run_test()