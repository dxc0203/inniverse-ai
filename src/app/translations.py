# translations.py

TRANSLATIONS = {
    "sidebar": {
        "en": {
            "menu": "Menu",
            "new_project": "New Project",
            "history": "History",
            "dev_tools": "⚙️ Developer Tools",
            "test_mode": "Enable Test Mode",
            "test_mode_warning": "⚠️ Currently in Test Mode. No API costs will be incurred.",
        },
        "zh-TW": {
            "menu": "功能選單",
            "new_project": "新增專案",
            "history": "歷史紀錄",
            "dev_tools": "⚙️ 開發者工具",
            "test_mode": "開啟測試模式 (Test Mode)",
            "test_mode_warning": "⚠️ 目前處於測試模式，不會產生 API 費用。",
        },
    },
    "new_project_page": {
        "en": {
            "main_title": "👗 Inniverse AI Product Image Generator",
            "project_name": "Project Name",
            "prompt_input": "Enter Prompt",
            "upload_label": "Select Images (Max 5)",
            "upload_error_max": "⚠️ Max 5 images allowed (Current: {}). Please reduce selection.",
            "preview_caption": "Preview {}",
            "run_ai": "🚀 Run AI Analysis",
            "processing_spinner": "Processing all images at once...",
            "result_header": "AI Analysis Result",
            "test_response": "[Test Mode] AI has received all images. This is a simulated AI description: These images show a collection of garments using high-quality fabrics..."
        },
        "zh-TW": {
            "main_title": "👗 Inniverse AI 產品生圖工具",
            "project_name": "專案名稱 (Project Name)",
            "prompt_input": "輸入 Prompt 指令",
            "upload_label": "選擇圖片 (最多 5 張)",
            "upload_error_max": "⚠️ 最多只能上傳 5 張圖片 (目前: {} 張)。請減少選擇數量。",
            "preview_caption": "預覽 {}",
            "run_ai": "🚀 執行 AI 分析",
            "processing_spinner": "正在一次性處理所有圖片...",
            "result_header": "AI 分析結果",
            "test_response": "【測試模式】AI 已收到所有圖片。這是一段模擬的 AI 描述：這些圖片展示了系列服裝，採用高級面料..."
        },
    },
    "history_page": {
        "en": {
            "history_header": "📜 Project History",
            "select_project": "Select Project",
            "restart_btn": "🔄 Load Project Settings (Restart)",
            "delete_btn": "🗑️ Delete Project",
            "confirm_delete": "⚠️ Are you sure you want to delete?",
            "yes_delete": "✅ Yes, Delete",
            "no_cancel": "❌ Cancel",
            "prompt_used": "Prompt Used",
            "input_images": "Input Images",
            "comparison_header": "🖼️ Image Comparison",
            "input_col": "Original Input",
            "output_col": "Generated Output",
            "no_output_img": "⚠️ No output image yet",
            "no_projects": "No project history found",
            "no_logs": "Logs folder not found",
        },
        "zh-TW": {
            "history_header": "📜 歷史專案檢視",
            "select_project": "選擇專案",
            "restart_btn": "🔄 載入此專案設定 (Restart Project)",
            "delete_btn": "🗑️ 刪除此專案 (Delete Project)",
            "confirm_delete": "⚠️ 確定要刪除嗎？",
            "yes_delete": "✅ 是，刪除",
            "no_cancel": "❌ 取消",
            "prompt_used": "使用的 Prompt",
            "input_images": "輸入圖片",
            "comparison_header": "🖼️ 圖片對比 (Image Comparison)",
            "input_col": "原始圖片 (Input)",
            "output_col": "生成圖片 (Output)",
            "no_output_img": "⚠️ 尚未生成圖片",
            "no_projects": "暫無專案紀錄",
            "no_logs": "尚未建立 logs 資料夾",
        },
    },
    "general": {
        "en": {
            "success_msg": "Processing Complete!",
        },
        "zh-TW": {
            "success_msg": "處理完成！",
        },
    }
}

def get_translation(key, lang):
    """
    Retrieves a translation from the TRANSLATIONS dictionary.
    - key: A string representing the path to the translation, e.g., "sidebar.menu"
    - lang: The desired language code, e.g., "en"
    """
    try:
        keys = key.split('.')
        result = TRANSLATIONS
        for k in keys:
            result = result[k]
        return result[lang]
    except (KeyError, TypeError):
        return f"[MISSING TRANSLATION: {key}]"
