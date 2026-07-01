import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from modules.ai import ask_ko_ai
from modules.memory import forget_text, get_long_term_memory_text, remember_text, save_history
from modules.pdf_reader import ask_pdf_question, extract_text_from_pdf
from modules.daily import get_daily_plan

load_dotenv()
client = OpenAI()

st.set_page_config(page_title="Ko AI", page_icon="🤖")

st.title("🤖 Ko AI")
st.caption("自分専用AIアシスタント")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = ""


def handle_memory_input(text: str) -> str | None:
    text = text.strip()

    if text.startswith("覚えて:") or text.startswith("覚えて："):
        content = text.replace("覚えて:", "", 1).replace("覚えて：", "", 1)
        return remember_text(content)

    if text.startswith("覚えて "):
        content = text.replace("覚えて ", "", 1)
        return remember_text(content)

    if text.startswith("忘れて:") or text.startswith("忘れて："):
        content = text.replace("忘れて:", "", 1).replace("忘れて：", "", 1)
        return forget_text(content)

    if text.startswith("忘れて "):
        content = text.replace("忘れて ", "", 1)
        return forget_text(content)

    return None


with st.sidebar:
    st.header("📊 現在の状態")

    memory_text = get_long_term_memory_text()
    memory_count = len(memory_text.splitlines()) if memory_text else 0

    st.write(f"🧠 長期記憶: {memory_count}件")

    if st.session_state.pdf_text:
        st.write("📄 PDFモード: ON")
    else:
        st.write("📄 PDFモード: OFF")

    st.divider()
    st.header("📄 PDF読み込み")

    if st.button("会話をクリア"):
        st.session_state.messages = []
        st.rerun()

    if st.button("今日の作業メニュー"):
        daily_plan = get_daily_plan()
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": daily_plan,
            }
        )
        st.rerun()

    st.divider()

    st.header("🧠 長期記憶")
    memory_text = get_long_term_memory_text()

    if memory_text:
        st.text(memory_text)
    else:
        st.caption("まだ記憶はありません")

    st.caption("例: 覚えて: 好きな食べ物はラーメン")

    st.divider()

    if st.session_state.pdf_text:
        st.success("PDFモード中")

        if st.session_state.pdf_name:
            st.caption(f"ファイル名: {st.session_state.pdf_name}")

        st.caption(f"読み込み文字数: {len(st.session_state.pdf_text):,}文字")

        if st.button("PDFを解除"):
            st.session_state.pdf_text = ""
            st.session_state.pdf_name = ""
            st.success("PDFを解除しました")
            st.rerun()
    else:
        st.info("PDFは未読み込みです")

    uploaded_pdf = st.file_uploader("PDFをアップロード", type=["pdf"])

    if uploaded_pdf is not None:
        st.session_state.pdf_name = uploaded_pdf.name
        st.session_state.pdf_text = extract_text_from_pdf(uploaded_pdf)
        st.success("PDFを読み込みました")
        st.caption(f"ファイル名: {st.session_state.pdf_name}")
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

        memory_response = handle_memory_input(user_input)

        if memory_response:
            response = memory_response

        elif st.session_state.pdf_text:
            response = ask_pdf_question(client, st.session_state.pdf_text, user_input)

        else:
            response = ask_ko_ai(client, user_input)

        save_history("Ko AI", response)

    except Exception as e:
        response = f"エラーが発生しました: {e}"

    st.session_state.messages.append({"role": "assistant", "content": response})

    with st.chat_message("assistant"):
        st.write(response)