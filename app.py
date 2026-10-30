import streamlit as st
import google.generativeai as genai
import urllib.parse
import re

# 페이지 기본 설정
st.set_page_config(page_title="냉장고 파먹기 AI 요리사", page_icon="🍳")

st.title("🍳 냉장고 파먹기 AI 요리사")
st.write("재료를 입력하면 AI가 맞춤 레시피와 완성 요리 사진을 찾아드립니다!")

# Streamlit Secrets에서 Gemini API 키 가져오기
gemini_key = st.secrets.get("GEMINI_API_KEY", None)

text_input = st.text_input("1. 냉장고에 있는 재료", placeholder="예: 계란, 대파, 찬밥")
desired_menu = st.text_input("2. 먹고 싶은 특정 메뉴 (선택사항)", placeholder="예: 계란볶음밥")

if st.button("🍳 레시피 추천받기"):
    if not gemini_key:
        st.error("Streamlit Secrets에 'GEMINI_API_KEY'가 설정되지 않았습니다.")
    elif not text_input:
        st.warning("재료를 입력해 주세요!")
    else:
        genai.configure(api_key=gemini_key)
        
        # 이용 가능한 기본 Gemini 모델 사용
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = (
            f"사용자 입력 재료: {text_input}\n"
            f"희망 메뉴: {desired_menu if desired_menu else '없음'}\n\n"
            "당신은 냉장고 파먹기 전용 AI 요리사입니다.\n"
            "1. 입력된 재료와 기본 조미료(물, 소금, 후추, 식용유, 간장, 설탕) 외 임의의 재료를 절대로 추가하지 마세요.\n"
            "2. 첫 줄은 반드시 '추천 요리: [요리이름]' 형식으로 작성하세요.\n"
            "3. 이어서 재료 목록과 Step-by-Step 조리 순서를 작성해 주세요."
        )

        with st.spinner("👨‍🍳 레시피를 작성 중입니다..."):
            try:
                response = model.generate_content(prompt)
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

                # 1. Unsplash 오픈 웹을 통한 요리 사진 출력 (API 오류 없는 방식)
                st.divider()
                st.subheader("🖼️ 완성 요리 이미지")
                encoded_dish = urllib.parse.quote(dish_name)
                photo_url = f"https://source.unsplash.com/800x600/?food,{encoded_dish}"
                st.image(photo_url, caption=f"'{dish_name}' 관련 대표 이미지", use_container_width=True)

                # 2. 유튜브 및 구글 검색 직행 링크
                search_term = f"{dish_name} 레시피"
                encoded_term = urllib.parse.quote(search_term)
                direct_video_url = f"https://www.youtube.com/results?search_query={encoded_term}&sp=EgIQAQ%253D%253D"
                google_image_url = f"https://www.google.com/search?tbm=isch&q={encoded_term}"

                st.subheader("🎬 관련 조리 영상 & 검색")
                st.markdown(f"▶️ **[YouTube에서 '{dish_name}' 영상 보기]({direct_video_url})**")
                st.markdown(f"🖼️ **[Google에서 '{dish_name}' 실물 사진 검색]({google_image_url})**")

            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")