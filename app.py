import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from modules.ai import ask_ko_ai
from modules.memory import save_history
from modules.pdf_reader import ask_pdf_question, extract_text_from_pdf

load_dotenv()
client = OpenAI()

st.set_page_config(page_title="Ko AI", page_icon="🤖")

st.title("🤖 Ko AI")
st.caption("自分専用AIアシスタント")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

with st.sidebar:
    st.header("📄 PDF読み込み")
    if st.session_state.pdf_text:
        st.success("PDFモード中")
        st.caption(f"読み込み文字数: {len(st.session_state.pdf_text):,}文字")

        if st.button("PDFを解除"):
            st.session_state.pdf_text = ""
            st.success("PDFを解除しました")
            st.rerun()
    else:
        st.info("PDFは未読み込みです")
    uploaded_pdf = st.file_uploader("PDFをアップロード", type=["pdf"])

    if uploaded_pdf is not None:
        st.session_state.pdf_text = extract_text_from_pdf(uploaded_pdf)
        st.success("PDFを読み込みました")
        st.caption(f"読み込み文字数: {len(st.session_state.pdf_text):,}文字")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("Ko AIに話しかける")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.write(user_input)

    try:
        save_history("あなた", user_input)

        if st.session_state.pdf_text:
            response = ask_pdf_question(client, st.session_state.pdf_text, user_input)
        else:
            response = ask_ko_ai(client, user_input)

        save_history("Ko AI", response)

    except Exception as e:
        response = f"エラーが発生しました: {e}"

    st.session_state.messages.append({"role": "assistant", "content": response})

    with st.chat_message("assistant"):
        st.write(response)