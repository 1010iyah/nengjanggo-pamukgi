import streamlit as st
from google import genai
from PIL import Image
import urllib.parse
import re

# 페이지 기본 설정
st.set_page_config(page_title="냉장고 파먹기 AI 요리사", page_icon="🍳")

st.title("🍳 냉장고 파먹기 AI 요리사")
st.write("재료를 입력하거나 사진을 올리면, AI가 맞춤 레시피와 요리 사진을 찾아드립니다!")

# Streamlit Secrets에서 Gemini API 키 가져오기
gemini_key = st.secrets.get("GEMINI_API_KEY", None)

text_input = st.text_input("1. 냉장고에 있는 재료", placeholder="예: 계란, 대파, 찬밥")
desired_menu = st.text_input("2. 먹고 싶은 특정 메뉴 (선택사항)", placeholder="예: 계란볶음밥")
uploaded_file = st.file_uploader("3. 📸 재료/냉장고 사진 첨부 (선택사항)", type=["jpg", "jpeg", "png"])

if st.button("🍳 레시피 추천받기"):
    if not gemini_key:
        st.error("Streamlit Secrets에 'GEMINI_API_KEY'가 설정되지 않았습니다.")
    elif not text_input and not uploaded_file:
        st.warning("재료를 적거나 사진을 첨부해 주세요!")
    else:
        client = genai.Client(api_key=gemini_key)
        
        contents = []
        
        prompt_text = (
            f"사용자 입력 재료: {text_input}\n"
            f"희망 메뉴: {desired_menu if desired_menu else '없음'}\n\n"
            "당신은 냉장고 파먹기 전용 AI 요리사입니다.\n"
            "1. 입력된 재료(및 사진 속 재료)와 기본 조미료(물, 소금, 후추, 식용유, 간장, 설탕) 외 임의의 재료를 절대로 추가하지 마세요.\n"
            "2. 첫 줄은 반드시 '추천 요리: [요리이름]' 형식으로 작성하세요.\n"
            "3. 이어서 재료 목록과 Step-by-Step 조리 순서를 작성해 주세요."
        )
        contents.append(prompt_text)

        if uploaded_file:
            uploaded_image = Image.open(uploaded_file)
            contents.append(uploaded_image)
            contents.append("사진에 있는 재료들을 분석하여 레시피에 적극 활용하세요.")

        with st.spinner("👨‍🍳 Gemini 요리사가 레시피를 작성 중입니다..."):
            try:
                response = client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=contents
                )
                recipe_result = response.text
                
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
                    dish_name = "요리"

                # 완성 요리 관련 링크
                st.divider()
                search_term = f"{dish_name} 레시피"
                encoded_term = urllib.parse.quote(search_term)
                direct_video_url = f"https://www.youtube.com/results?search_query={encoded_term}&sp=EgIQAQ%253D%253D"
                google_image_url = f"https://www.google.com/search?tbm=isch&q={encoded_term}"

                st.subheader("🎬 관련 조리 영상 & 검색")
                st.markdown(f"▶️ **[YouTube에서 '{dish_name}' 추천 동영상 보기]({direct_video_url})**")
                st.markdown(f"🖼️ **[Google에서 '{dish_name}' 실물 사진 검색]({google_image_url})**")

            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")