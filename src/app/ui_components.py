import streamlit as st

def prompt_builder_ui(key_suffix):
    with st.expander("快速提示构建器（中文界面，英文提示）", expanded=False):
        content_type = st.radio(
            "内容类型",
            ["通用场景", "服装/模特相关"],
            key=f"pb_content_type_{key_suffix}"
        )
        scene_type_cn = st.selectbox(
            "使用场景",
            ["电商 product 图", "广告海报", "社交媒体封面", "插画/概念设计", "头像/肖像", "其他"],
            key=f"pb_scene_type_{key_suffix}"
        )
        main_subject_cn = st.text_input(
            "主要主体（中文描述，会自动翻译为英文结构）",
            value="一位年轻女性模特穿着夏季连衣裙",
            key=f"pb_main_subject_{key_suffix}"
        )
        style_cn = st.selectbox(
            "整体风格",
            ["写实摄影风", "插画风", "3D 渲染", "卡通/动漫风", "赛博朋克", "极简现代"],
            key=f"pb_style_{key_suffix}"
        )
        mood_cn = st.selectbox(
            "氛围/情绪",
            ["明亮轻快", "温暖治愈", "冷酷未来感", "高级时尚感", "自然生活感", "戏剧张力强"],
            key=f"pb_mood_{key_suffix}"
        )
        
        cloth_type_cn = None
        display_type_cn = None
        target_platform_cn = None
        focus_cn_list = []
        
        if content_type == "服装/模特相关":
            cloth_type_cn = st.selectbox(
                "服装类型",
                ["T 恤", "连衣裙", "衬衫", "外套", "牛仔裤", "套装", "运动服", "内衣/居家服", "配饰（包/鞋/帽）"],
                key=f"pb_cloth_type_{key_suffix}"
            )
            display_type_cn = st.selectbox(
                "展示方式",
                ["白底平铺", "挂拍", "无头模特", "全身模特", "半身模特", "街拍场景", "静物搭配拍摄"],
                key=f"pb_display_type_{key_suffix}"
            )
            target_platform_cn = st.selectbox(
                "目标平台",
                ["电商详情页", "电商主图", "社交媒體（小紅書/IG）", "Banner 海報", "Lookbook"],
                key=f"pb_target_platform_{key_suffix}"
            )
            focus_cn_list = st.multiselect(
                "重点强调",
                ["版型", "面料质感", "颜色还原", "细节特写（领口/袖口/下摆）", "穿搭场景", "身材修饰效果"],
                key=f"pb_focus_{key_suffix}"
            )
            
        aspect_ratio_cn = st.selectbox(
            "画面比例",
            ["1:1 正方形", "4:5 竖图", "3:4 竖图", "16:9 横图", "9:16 竖版封面"],
            key=f"pb_aspect_ratio_{key_suffix}"
        )
        camera_cn = st.selectbox(
            "构图/机位",
            ["全身远景", "中景（膝盖以上）", "半身特写", "特写（脸/细节）", "俯视平铺", "45 度侧面"],
            key=f"pb_camera_{key_suffix}"
        )
        lighting_cn = st.selectbox(
            "光线",
            ["柔和棚拍光", "自然窗光", "户外日光", "黄昏暖光", "冷调高对比"],
            key=f"pb_lighting_{key_suffix}"
        )
        quality_cn_list = st.multiselect(
            "质量要求",
            ["高清细节", "噪点极低", "色彩还原准确", "适合后期剪裁", "适合电商详情页排版"],
            key=f"pb_quality_{key_suffix}"
        )
        extra_cn = st.text_input(
            "补充说明",
            value="画面简洁干净，适合在线商店展示。",
            key=f"pb_extra_{key_suffix}"
        )

        scene_map = {"电商 product 图": "e-commerce product image", "广告海报": "advertising poster", "社交媒体封面": "social media cover image", "插画/概念设计": "illustration or concept art", "头像/肖像": "portrait", "其他": "general purpose image"}
        style_map = {"写实攝影风": "realistic photography style", "插画风": "illustration style", "3D 渲染": "3D rendered style", "卡通/动漫风": "cartoon / anime style", "赛博朋克": "cyberpunk style", "极简现代": "minimal and modern style"}
        mood_map = {"明亮轻快": "bright and cheerful mood", "温暖治愈": "warm and comforting mood", "冷酷未来感": "cool futuristic mood", "高级时尚感": "high-fashion editorial mood", "自然生活感": "natural everyday-life mood", "戏剧张力强": "dramatic and intense mood"}
        cloth_type_map = {"T 恤": "T-shirt", "连衣裙": "dress", "衬衫": "shirt", "外套": "jacket", "牛仔裤": "jeans", "套装": "suit set", "运动服": "sportswear", "内衣/居家服": "loungewear or underwear", "配饰（包/鞋/帽）": "fashion accessories"}
        display_type_map = {"白底平鋪": "flat lay on a clean white background", "掛拍": "hanging on a hanger", "無頭模特": "on a headless mannequin", "全身模特": "on a full-body model", "半身模特": "on a half-body model", "街拍場景": "street photography scene", "靜物搭配拍攝": "styled still life composition"}
        target_platform_map = {"电商详情页": "e-commerce detail page", "电商主图": "e-commerce main image", "社交媒體（小紅書/IG）": "social media", "Banner 海報": "banner", "Lookbook": "lookbook"}
        focus_map = {"版型": "silhouette", "面料质感": "fabric texture", "颜色还原": "color accuracy", "细节特写（领口/袖口/下摆）": "close-up details", "穿搭场景": "styling context", "身材修饰效果": "body-flattering"}
        aspect_ratio_map = {"1:1 正方形": "1:1 ratio", "4:5 竖图": "4:5 ratio", "3:4 竖图": "3:4 ratio", "16:9 横图": "16:9 ratio", "9:16 竖版封面": "9:16 ratio"}
        camera_map = {"全身远景": "full-body shot", "中景（膝盖以上）": "medium shot", "半身特写": "half-body shot", "特写（脸/细节）": "close-up", "俯视平铺": "top-down flat lay", "45 度侧面": "45-degree angle"}
        lighting_map = {"柔和棚拍光": "soft studio lighting", "自然窗光": "natural window light", "户外日光": "outdoor daylight", "黄昏暖光": "warm golden hour lighting", "冷调高对比": "cool high-contrast lighting"}
        quality_map = {"高清细节": "high-resolution", "噪点极低": "low noise", "色彩还原准确": "accurate color", "适合后期剪裁": "suitable for cropping", "适合电商详情页排版": "suitable for layout"}

        if st.button("生成到提示文本（英文）", key=f"pb_generate_{key_suffix}"):
            scene_en = scene_map.get(scene_type_cn, "image")
            base_en = f"Create an image for {scene_en}. Subject: {main_subject_cn}. Style: {style_map.get(style_cn, '')}, Mood: {mood_map.get(mood_cn, '')}."
            
            cloth_part_en = ""
            if content_type == "服装/模特相关":
                cloth_part_en = f" Show {cloth_type_map.get(cloth_type_cn, 'clothing')} {display_type_map.get(display_type_cn, '')} for {target_platform_map.get(target_platform_cn, '')}."
                if focus_cn_list:
                    cloth_part_en += " Focus on " + ", ".join([focus_map[f] for f in focus_cn_list if f in focus_map]) + "."
            
            model_part_en = f" Use {aspect_ratio_map.get(aspect_ratio_cn, '')}, {camera_map.get(camera_cn, '')}, {lighting_map.get(lighting_cn, '')}."
            if quality_cn_list:
                model_part_en += " High quality: " + ", ".join([quality_map[q] for q in quality_cn_list if q in quality_map]) + "."
                
            final_prompt = (base_en + " " + cloth_part_en + " " + model_part_en + f" Additional: {extra_cn}. Clean composition, no text/watermarks.").strip()
            return final_prompt
        return None
