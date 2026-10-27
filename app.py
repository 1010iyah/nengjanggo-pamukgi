import streamlit as st
from openai import OpenAI
import base64
import urllib.parse
import re

# 페이지 기본 설정
st.set_page_config(page_title="냉장고 파먹기 AI 요리사", page_icon="🍳")

st.title("🍳 냉장고 파먹기 AI 요리사")
st.write("재료를 입력하거나 사진을 올리고, 원하는 메뉴가 있다면 적어주세요!")

# Streamlit Secrets에서 API 키 가져오기
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    api_key = None

# 입력 영역
text_input = st.text_input("1. 냉장고에 있는 재료", placeholder="예: 계란, 대파, 찬밥")
desired_menu = st.text_input("2. 먹고 싶은 특정 메뉴 (선택사항)", placeholder="예: 계란볶음밥 (비워두면 AI가 자동 추천)")
uploaded_file = st.file_uploader("3. 📸 재료/냉장고 사진 첨부 (선택사항)", type=["jpg", "jpeg", "png"])

if st.button("🍳 레시피 추천받기"):
    if not api_key:
        st.error("현재 서버 설정(Secrets)에 API 키가 등록되지 않았습니다.")
    elif not text_input and not uploaded_file:
        st.warning("재료 이름을 적거나 사진을 첨부해 주세요!")
    else:
        client = OpenAI(api_key=api_key)
        user_content = []

        prompt_text = f"냉장고 재료: {text_input}\n"
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
            user_content.append({"type": "text", "text": "첨부된 사진 속 재료들도 함께 인식해서 레시피에 반영해 주세요."})

        with st.spinner("👨‍🍳 AI 요리사가 최고의 레시피를 구상 중입니다..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "당신은 친절한 백종원 스타일의 AI 요리사입니다.\n"
                                "반드시 답변 첫 줄에 '추천 요리: [요리이름]' 형식을 포함해서 요리 이름을 명확히 작성해 주세요. "
                                "(예: 추천 요리: 백종원 대파 계란볶음밥)\n"
                                "이어서 필요한 준비 재료, 추가 양념, step-by-step 조리 순서를 보기 쉽게 정리해 주세요."
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

                # 검색 키워드 인코딩
                search_term = f"{dish_name} 레시피"
                encoded_term = urllib.parse.quote(search_term)

                st.divider()
                st.subheader(f"🎬 '{dish_name}' 관련 조리 영상/사진")

                # 1. 유튜브 검색창을 거치지 않고 가장 정확한 개별 동영상 목록으로 바로 연결되는 직행 링크
                direct_video_url = f"https://www.youtube.com/results?search_query={encoded_term}&sp=EgIQAQ%253D%253D"
                
                # 2. 구글 이미지 검색 직행 링크 (완성된 이미지/사진 바로 확인)
                google_image_url = f"https://www.google.com/search?tbm=isch&q={encoded_term}"

                st.markdown(f"▶️ **[이곳을 클릭하여 '{dish_name}' 추천 동영상 바로 재생하기]({direct_video_url})**")
                st.markdown(f"🖼️ **[이곳을 클릭하여 '{dish_name}' 완제품 실물 사진 모아보기]({google_image_url})**")

            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")