import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import urllib.parse
import re
import io

# 페이지 기본 설정
st.set_page_config(page_title="냉장고 파먹기 AI 요리사", page_icon="🍳")

st.title("🍳 냉장고 파먹기 AI 요리사")
st.write("재료를 입력하거나 사진을 올리면, Gemini AI가 레시피와 컷만화 조리법을 직접 그려줍니다!")

# Streamlit Secrets에서 Gemini API 키 가져오기
gemini_key = st.secrets.get("GEMINI_API_KEY", None)

text_input = st.text_input("1. 냉장고에 있는 재료", placeholder="예: 계란, 대파, 찬밥")
desired_menu = st.text_input("2. 먹고 싶은 특정 메뉴 (선택사항)", placeholder="예: 계란볶음밥")
uploaded_file = st.file_uploader("3. 📸 재료/냉장고 사진 첨부 (선택사항)", type=["jpg", "jpeg", "png"])

if st.button("🍳 레시피 & 만화 조리법 생성하기"):
    if not gemini_key:
        st.error("Streamlit Secrets에 'GEMINI_API_KEY'가 설정되지 않았습니다.")
    elif not text_input and not uploaded_file:
        st.warning("재료를 적거나 사진을 첨부해 주세요!")
    else:
        # Google GenAI 클라이언트 생성
        client = genai.Client(api_key=gemini_key)
        
        contents = []
        prompt_text = f"사용자가 입력한 재료: {text_input}\n"
        if desired_menu:
            prompt_text += f"희망 메뉴: {desired_menu}\n"
            
        contents.append(prompt_text)

        if uploaded_file:
            uploaded_image = Image.open(uploaded_file)
            contents.append(uploaded_image)
            contents.append("사진 속 보이는 재료만 인식해서 사용하세요.")

        system_instruction = (
            "당신은 냉장고 파먹기 전용 AI 요리사입니다.\n"
            "1. 입력된 재료와 필수 기본 조미료(물, 소금, 후추, 식용유, 간장, 설탕) 외 임의의 재료를 절대로 추가하지 마세요.\n"
            "2. 첫 줄은 반드시 '추천 요리: [요리이름]' 형식으로 작성하세요.\n"
            "3. 이어서 재료 목록과 Step-by-Step 조리 순서를 정리해 주세요."
        )

        with st.spinner("👨‍🍳 Gemini 요리사가 레시피를 작성 중입니다..."):
            try:
                # 1. 텍스트 레시피 생성 (gemini-2.5-flash)
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction
                    )
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
                    dish_name = text_input + " 요리"

                # 2. 이미지 생성 (Imagen 3)
                with st.spinner("🎨 구글 Imagen AI가 컷만화 조리법을 그리는 중입니다..."):
                    try:
                        image_prompt = (
                            f"A detailed step-by-step cooking comic strip collage illustrating how to make {dish_name}. "
                            "4-6 sequential panels showing cooking process, comic book style with realistic details, vibrant colors."
                        )
                        
                        result = client.models.generate_images(
                            model='imagen-3.0-generate-002',
                            prompt=image_prompt,
                            config=types.GenerateImagesConfig(
                                number_of_images=1,
                                aspect_ratio="1:1"
                            )
                        )

                        for generated_image in result.generated_images:
                            image = Image.open(io.BytesIO(generated_image.image.image_bytes))
                            st.image(image, caption=f"🖼️ {dish_name} 조리 과정 만화 컷", use_container_width=True)

                    except Exception as img_err:
                        st.warning("💡 이미지 생성 부분에 잠시 지연이 발생했습니다. 실물 사진/영상 링크를 이용해 보세요.")

                # 3. 유튜브 및 구글 직행 링크
                search_term = f"{dish_name} 레시피"
                encoded_term = urllib.parse.quote(search_term)
                direct_video_url = f"https://www.youtube.com/results?search_query={encoded_term}&sp=EgIQAQ%253D%253D"
                google_image_url = f"https://www.google.com/search?tbm=isch&q={encoded_term}"

                st.divider()
                st.subheader("🎬 관련 조리 영상 & 실물 사진")
                st.markdown(f"▶️ **[YouTube에서 '{dish_name}' 추천 동영상 시청하기]({direct_video_url})**")
                st.markdown(f"🖼️ **[Google에서 '{dish_name}' 완성 실물 사진 보기]({google_image_url})**")

            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")