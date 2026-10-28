import streamlit as st
from openai import OpenAI
import base64
import urllib.parse
import re

# 페이지 기본 설정
st.set_page_config(page_title="냉장고 파먹기 AI 요리사", page_icon="🍳")

st.title("🍳 냉장고 파먹기 AI 요리사")
st.write("재료를 입력하거나 사진을 올리면, AI가 레시피와 컷만화 조리법을 직접 그려줍니다!")

# Streamlit Secrets에서 API 키 가져오기
api_key = st.secrets.get("OPENAI_API_KEY", None)

text_input = st.text_input("1. 냉장고에 있는 재료", placeholder="예: 계란, 대파, 찬밥")
desired_menu = st.text_input("2. 먹고 싶은 특정 메뉴 (선택사항)", placeholder="예: 계란볶음밥")
uploaded_file = st.file_uploader("3. 📸 재료/냉장고 사진 첨부 (선택사항)", type=["jpg", "jpeg", "png"])

if st.button("🍳 레시피 & 만화 조리법 생성하기"):
    if not api_key:
        st.error("Streamlit Secrets에 'OPENAI_API_KEY'가 설정되지 않았습니다.")
    elif not text_input and not uploaded_file:
        st.warning("재료를 적거나 사진을 첨부해 주세요!")
    else:
        client = OpenAI(api_key=api_key)
        user_content = []

        prompt_text = f"사용자가 입력한 재료: {text_input}\n"
        if desired_menu:
            prompt_text += f"희망 메뉴: {desired_menu}\n"
        
        user_content.append({"type": "text", "text": prompt_text})

        if uploaded_file:
            bytes_data = uploaded_file.getvalue()
            base64_image = base64.b64encode(bytes_data).decode('utf-8')
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })
            user_content.append({"type": "text", "text": "사진 속 보이는 재료만 인식해서 사용하세요."})

        with st.spinner("👨‍🍳 AI 요리사가 레시피를 작성 중입니다..."):
            try:
                # 1. 레시피 텍스트 생성
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "당신은 냉장고 파먹기 전용 AI 요리사입니다.\n"
                                "1. 입력된 재료와 필수 기본 조미료(물, 소금, 후추, 식용유, 간장, 설탕) 외 임의의 재료를 절대로 추가하지 마세요.\n"
                                "2. 첫 줄은 반드시 '추천 요리: [요리이름]' 형식으로 작성하세요.\n"
                                "3. 이어서 재료 목록과 Step-by-Step 조리 순서를 정리해 주세요."
                            )
                        },
                        {
                            "role": "user",
                            "content": user_content
                        }
                    ]
                )
                
                recipe_result = response.choices[0].message.content
                st.success("레시피가 완성되었습니다!")
                st.markdown(recipe_result)

                # 요리 이름 추출
                dish_name = ""
                match = re.search(r"추천 요리:\s*([^\n]+)", recipe_result)
                if match:
                    dish_name = match.group(1).strip()
                elif desired_menu:
                    dish_name = desired_menu
                else:
                    dish_name = text_input + " 요리"

                # 2. DALL-E 이미지 생성
                with st.spinner("🎨 OpenAI DALL-E가 컷만화 이미지를 그리는 중입니다... (약 20~30초 소요)"):
                    image_prompt = (
                        f"A detailed step-by-step cooking comic strip collage illustrating how to make {dish_name}. "
                        "4-6 sequential panels showing cooking process, comic book style with realistic details, high quality, colorful."
                    )
                    
                    img_res = client.images.generate(
                        model="dall-e-3",
                        prompt=image_prompt,
                        size="1024x1024",
                        quality="standard",
                        n=1
                    )
                    
                    st.image(img_res.data[0].url, caption=f"🖼️ {dish_name} 조리 과정 만화 컷", use_container_width=True)

                # 3. 유튜브 및 구글 직행 링크
                search_term = f"{dish_name} 레시피"
                encoded_term = urllib.parse.quote(search_term)
                direct_video_url = f"https://www.youtube.com/results?search_query={encoded_term}&sp=EgIQAQ%253D%253D"
                google_image_url = f"https://www.google.com/search?tbm=isch&q={encoded_term}"

                st.divider()
                st.subheader("🎬 관련 조리 영상 & 실물 사진")
                st.markdown(f"▶️ **[YouTube에서 '{dish_name}' 추천 동영상 보기]({direct_video_url})**")
                st.markdown(f"🖼️ **[Google에서 '{dish_name}' 완제품 실물 사진 보기]({google_image_url})**")

            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")