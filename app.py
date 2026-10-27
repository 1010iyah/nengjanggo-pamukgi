import streamlit as st
from openai import OpenAI
import base64

# 페이지 기본 설정
st.set_page_config(page_title="냉장고 파먹기 AI 요리사", page_icon="🍳")

st.title("🍳 냉장고 파먹기 AI 요리사")
st.write("재료 이름을 적거나, 냉장고 속 사진을 올려주세요!")

# Streamlit Secrets(비밀 저장소)에서 서버가 직접 API 키를 읽어옵니다.
# (사용자 화면에는 어떠한 API 키 입력창도 노출되지 않습니다.)
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    api_key = None

# 사용자 입력 요소
text_input = st.text_input("냉장고에 있는 재료", placeholder="예: 계란, 대파, 스팸")
uploaded_file = st.file_uploader("📸 재료/냉장고 사진 첨부", type=["jpg", "jpeg", "png"])

if st.button("레시피 추천받기"):
    if not api_key:
        st.error("현재 서버 설정(Secrets)에 API 키가 등록되지 않았습니다. 관리자에게 문의하세요.")
    elif not text_input and not uploaded_file:
        st.warning("재료 이름을 적거나 사진을 첨부해 주세요!")
    else:
        client = OpenAI(api_key=api_key)
        user_content = []

        if text_input:
            user_content.append({"type": "text", "text": f"냉장고에 있는 재료: {text_input}"})

        if uploaded_file:
            bytes_data = uploaded_file.getvalue()
            base64_image = base64.b64encode(bytes_data).decode('utf-8')
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })
            user_content.append({"type": "text", "text": "첨부된 사진 속 재료들도 함께 인식해서 사용할 수 있는 레시피를 추천해 주세요."})

        with st.spinner("👨‍🍳 AI 요리사가 최고의 레시피를 만드는 중입니다..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "당신은 한국 자취생과 가정집을 위한 친절한 백종원 스타일의 요리사입니다. 제공된 재료 텍스트와 사진 속 재료를 인식해 한국인 입맛에 맞는 추천 요리 1가지, 추가 양념, 조리 순서를 보기 쉽게 정리해 주세요."
                        },
                        {
                            "role": "user",
                            "content": user_content
                        }
                    ]
                )
                st.success("레시피가 완성되었습니다!")
                st.markdown(response.choices[0].message.content)
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")