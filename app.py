import io
import zipfile

import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

from modules.ai import ask_ko_ai
from modules.chat import chat_with_ai
from modules.daily import get_daily_plan
from modules.memory import forget_text, get_long_term_memory_text, remember_text, save_history
from modules.note import create_note_article, save_note_article
from modules.pdf_reader import ask_pdf_question, extract_text_from_pdf
from modules.x_post import generate_x_post, save_x_post
from modules.instagram_post import generate_instagram_post, save_instagram_post
from modules.threads_post import generate_threads_post, save_threads_post
from modules.image_prompt import generate_image_prompt, save_image_prompt
from modules.news_analyzer import analyze_news, select_best_news
from modules.news_fetcher import fetch_ai_news
from modules.article_fetcher import fetch_article
from modules.idea_generator import generate_ideas, save_ideas
from modules.post_reviewer import improve_post, review_post

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

if "all_topic" not in st.session_state:
    st.session_state.all_topic = ""

if "note_topic" not in st.session_state:
    st.session_state.note_topic = ""

if "x_topic" not in st.session_state:
    st.session_state.x_topic = ""

if "instagram_topic" not in st.session_state:
    st.session_state.instagram_topic = ""

if "threads_topic" not in st.session_state:
    st.session_state.threads_topic = ""

if "image_prompt_theme" not in st.session_state:
    st.session_state.image_prompt_theme = ""

if "news_text" not in st.session_state:
    st.session_state.news_text = ""

if "latest_news" not in st.session_state:
    st.session_state.latest_news = ""

if "idea_theme" not in st.session_state:
    st.session_state.idea_theme = ""

if "stock_search_keyword" not in st.session_state:
    st.session_state.stock_search_keyword = ""

if "review_text" not in st.session_state:
    st.session_state.review_text = ""

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


def show_post_stock() -> None:
    st.header("📦 投稿ストック")

    search_keyword = st.text_input(
        "投稿ストック検索",
        placeholder="例: AI副業",
        key="stock_search_keyword",
    )

    note_files = sorted(Path("posts/note").glob("*.md"), reverse=True)
    x_files = sorted(Path("posts/x").glob("*.txt"), reverse=True)
    instagram_files = sorted(Path("posts/instagram").glob("*.md"), reverse=True)
    threads_files = sorted(Path("posts/threads").glob("*.txt"), reverse=True)
    idea_files = sorted(Path("posts/ideas").glob("*.txt"), reverse=True)

    if search_keyword.strip():
        keyword = search_keyword.strip().lower()

        def match_file(file_path: Path) -> bool:
            content = file_path.read_text(encoding="utf-8").lower()
            return keyword in file_path.name.lower() or keyword in content

        note_files = [file_path for file_path in note_files if match_file(file_path)]
        x_files = [file_path for file_path in x_files if match_file(file_path)]
        instagram_files = [
            file_path for file_path in instagram_files if match_file(file_path)
        ]
        threads_files = [
            file_path for file_path in threads_files if match_file(file_path)
        ]
        idea_files = [file_path for file_path in idea_files if match_file(file_path)]

    st.caption(
        f"note記事: {len(note_files)}件 / "
        f"X投稿: {len(x_files)}件 / "
        f"Instagram投稿: {len(instagram_files)}件 / "
        f"Threads投稿: {len(threads_files)}件 / "
        f"アイデア: {len(idea_files)}件"
    )

    all_stock_files = note_files + x_files + instagram_files + threads_files + idea_files

    if all_stock_files:
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in all_stock_files:
                zip_file.write(file_path, arcname=str(file_path))

        st.download_button(
            "📦 投稿ストックをまとめてZIPダウンロード",
            data=zip_buffer.getvalue(),
            file_name="ko_ai_post_stock.zip",
            mime="application/zip",
            key="download_all_post_stock_zip",
        )

    with st.expander("📝 note記事ストック"):
        if not note_files:
            st.caption("まだnote記事はありません")
        for file_path in note_files[:5]:
            content = file_path.read_text(encoding="utf-8")
            st.subheader(file_path.name)
            st.write(content)
            st.download_button(
                "📝 note記事をダウンロード",
                data=content,
                file_name=file_path.name,
                mime="text/markdown",
                key=f"download_note_{file_path.name}",
            )

    
    with st.expander("🐦 X投稿ストック"):
        if not x_files:
            st.caption("まだX投稿はありません")
        for file_path in x_files[:10]:
            content = file_path.read_text(encoding="utf-8")
            st.subheader(file_path.name)
            st.write(content)
            st.download_button(
                "🐦 X投稿をダウンロード",
                data=content,
                file_name=file_path.name,
                mime="text/plain",
                key=f"download_x_{file_path.name}",
            )

    with st.expander("📷 Instagram投稿ストック"):
        if not instagram_files:
            st.caption("まだInstagram投稿はありません")
        for file_path in instagram_files[:10]:
            content = file_path.read_text(encoding="utf-8")
            st.subheader(file_path.name)
            st.write(content)
            st.download_button(
                "📷 Instagram投稿をダウンロード",
                data=content,
                file_name=file_path.name,
                mime="text/markdown",
                key=f"download_instagram_{file_path.name}",
            )

    with st.expander("🧵 Threads投稿ストック"):
        if not threads_files:
            st.caption("まだThreads投稿はありません")
        for file_path in threads_files[:10]:
            content = file_path.read_text(encoding="utf-8")
            st.subheader(file_path.name)
            st.write(content)
            st.download_button(
                "🧵 Threads投稿をダウンロード",
                data=content,
                file_name=file_path.name,
                mime="text/plain",
                key=f"download_threads_{file_path.name}",
            )
    with st.expander("💡 アイデアストック"):
        if not idea_files:
            st.caption("まだアイデアはありません")
        for file_path in idea_files[:10]:
            content = file_path.read_text(encoding="utf-8")
            st.subheader(file_path.name)
            st.write(content)
            st.download_button(
                "💡 アイデアをダウンロード",
                data=content,
                file_name=file_path.name,
                mime="text/plain",
                key=f"download_idea_{file_path.name}",
            )


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
    st.header("🚀 全部生成")

    all_topic = st.text_input(
        "全部生成のテーマ",
        placeholder="例: AI副業で最初にやること",
        key="all_topic",
    )

    if st.button("note・X・Instagram・Threadsを全部作成"):
        if not all_topic.strip():
            st.warning("テーマを入力してください。")
        else:
            with st.spinner("全部まとめて作成中..."):
                note_article = create_note_article(client, all_topic.strip())
                save_note_article(all_topic.strip(), note_article)

                x_post = generate_x_post(client, all_topic.strip())
                save_x_post(all_topic.strip(), x_post)

                instagram_post = generate_instagram_post(client, all_topic.strip())
                save_instagram_post(all_topic.strip(), instagram_post)

                threads_post = generate_threads_post(client, all_topic.strip())
                save_threads_post(all_topic.strip(), threads_post)

            all_result = f"""
🚀 全部生成完了

📝 note記事案

{note_article}

---

🐦 X投稿案

{x_post}

---

📷 Instagram投稿案

{instagram_post}

---

🧵 Threads投稿案

{threads_post}
""".strip()

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": all_result,
                }
            )

            st.success("note・X・Instagram・Threadsを作成・保存しました")
            st.rerun()

    st.divider()
    st.header("💡 アイデア生成")

    idea_theme = st.text_input(
        "アイデアのテーマ",
        placeholder="例: AI副業",
        key="idea_theme",
    )

    if st.button("アイデア100個を作成"):
        if not idea_theme.strip():
            st.warning("アイデアのテーマを入力してください。")
        else:
            with st.spinner("アイデアを作成中..."):
                ideas = generate_ideas(client, idea_theme.strip())
                save_ideas(idea_theme.strip(), ideas)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"💡 アイデア100個\n\n{ideas}",
                }
            )
            st.success("アイデアを作成しました")
            st.rerun()

    st.divider()
    st.header("🎨 画像プロンプト生成")

    image_prompt_theme = st.text_input(
        "画像プロンプトのテーマ",
        placeholder="例: AI副業で最初にやること",
        key="image_prompt_theme",
    )

    if st.button("画像プロンプトを作成"):
        if not image_prompt_theme.strip():
            st.warning("画像プロンプトのテーマを入力してください。")
        else:
            with st.spinner("画像プロンプトを作成中..."):
                image_prompt = generate_image_prompt(
                    client,
                    image_prompt_theme.strip(),
                )
                save_image_prompt(
                    image_prompt_theme.strip(),
                    image_prompt,
                )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"🎨 画像生成プロンプト\n\n{image_prompt}",
                }
            )
            st.success("画像プロンプトを作成・保存しました")
            st.rerun()

    st.divider()
    st.header("📰 ニュース分析")

    if st.button("🤖 最新AIニュースを取得"):
        with st.spinner("ニュース取得中..."):
            st.session_state.news_text = fetch_ai_news()

        st.success("最新AIニュースを取得しました")
        st.rerun()

    if st.button("🤖 今日のAIニュース一括生成"):
        with st.spinner("今日のAIニュースから投稿一式を作成中..."):
            fetched_news = fetch_ai_news()
            selected_news = select_best_news(client, fetched_news)

            article_text = fetch_article(selected_news)
            news_source = article_text if not article_text.startswith("記事取得失敗") else selected_news

            news_analysis = analyze_news(client, news_source)

            note_article = create_note_article(client, news_analysis)
            save_note_article("今日のAIニュース", note_article)

            x_post = generate_x_post(client, news_analysis)
            save_x_post("今日のAIニュース", x_post)

            instagram_post = generate_instagram_post(client, news_analysis)
            save_instagram_post("今日のAIニュース", instagram_post)

            threads_post = generate_threads_post(client, news_analysis)
            save_threads_post("今日のAIニュース", threads_post)

            image_prompt = generate_image_prompt(client, news_analysis)
            save_image_prompt("今日のAIニュース", image_prompt)

        result = f"""
🤖 今日のAIニュース一括生成完了

【取得したニュース】

{fetched_news}

---

【選ばれたニュース】

{selected_news}

---

【取得した記事本文（先頭）】

{news_source[:1500]}

---

【ニュース分析】

{news_analysis}

---

📝 note記事案

{note_article}

---

🐦 X投稿案

{x_post}

---

📷 Instagram投稿案

{instagram_post}

---

🧵 Threads投稿案

{threads_post}

---

🎨 画像生成プロンプト

{image_prompt}
""".strip()

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": result,
            }
        )

        st.success("今日のAIニュースから投稿一式を作成・保存しました")
        st.rerun()

    news_text = st.text_area(
        "ニュース本文・URL・メモ",
        key="news_text",
        height=200,
    )

    if st.button("AIが使えそうなニュースを選ぶ"):
        if not news_text.strip():
            st.warning("ニュースを取得または入力してください。")
        else:
            with st.spinner("SNS向きのニュースを選定中..."):
                selected_news = select_best_news(client, news_text.strip())

            st.session_state.latest_news = selected_news

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"📰 選ばれたニュース\n\n{selected_news}",
                }
            )

            st.success("SNS向きのニュースを選びました")
            st.rerun()

    if st.button("ニュースから全部生成"):
        source_news = st.session_state.latest_news or news_text

        if not source_news.strip():
            st.warning("ニュース本文を入力してください。")
        else:
            with st.spinner("ニュースから投稿をまとめて作成中..."):
                news_analysis = analyze_news(client, source_news.strip())

                note_article = create_note_article(client, news_analysis)
                save_note_article("ニュース投稿", note_article)

                x_post = generate_x_post(client, news_analysis)
                save_x_post("ニュース投稿", x_post)

                instagram_post = generate_instagram_post(client, news_analysis)
                save_instagram_post("ニュース投稿", instagram_post)

                threads_post = generate_threads_post(client, news_analysis)
                save_threads_post("ニュース投稿", threads_post)

                image_prompt = generate_image_prompt(client, news_analysis)
                save_image_prompt("ニュース投稿", image_prompt)

            news_result = f"""
📰 ニュースから全部生成完了

【ニュース分析】

{news_analysis}

---

📝 note記事案

{note_article}

---

🐦 X投稿案

{x_post}

---

📷 Instagram投稿案

{instagram_post}

---

🧵 Threads投稿案

{threads_post}

---

🎨 画像生成プロンプト

{image_prompt}
""".strip()

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": news_result,
                }
            )

            st.success("ニュースから投稿一式を作成・保存しました")
            st.rerun()
    st.divider()
    st.header("📝 note記事生成")

    note_topic = st.text_input(
        "note記事のテーマ",
        placeholder="例: AI副業の始め方",
        key="note_topic",
    )

    if st.button("note記事を作成"):
        if not note_topic.strip():
            st.warning("note記事のテーマを入力してください。")
        else:
            with st.spinner("note記事を作成中..."):
                article = create_note_article(client, note_topic.strip())
                save_note_article(note_topic.strip(), article)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"📝 note記事案\n\n{article}",
                }
            )
            st.success("note記事案を作成・保存しました")
            st.rerun()

    st.divider()
    st.header("🐦 X投稿生成")

    x_topic = st.text_input(
        "X投稿のテーマ",
        placeholder="例: AI副業で最初にやること",
        key="x_topic",
    )

    if st.button("X投稿を作成"):
        if not x_topic.strip():
            st.warning("X投稿のテーマを入力してください。")
        else:
            with st.spinner("X投稿を作成中..."):
                x_post = generate_x_post(client, x_topic.strip())
                save_x_post(x_topic.strip(), x_post)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"🐦 X投稿案\n\n{x_post}",
                }
            )
            st.success("X投稿案を作成・保存しました")
            st.rerun()

    st.divider()
    st.header("📷 Instagram投稿生成")

    instagram_topic = st.text_input(
        "Instagram投稿のテーマ",
        placeholder="例: AI副業で最初にやること",
        key="instagram_topic",
    )

    if st.button("Instagram投稿を作成"):
        if not instagram_topic.strip():
            st.warning("Instagram投稿のテーマを入力してください。")
        else:
            with st.spinner("Instagram投稿を作成中..."):
                instagram_post = generate_instagram_post(
                    client,
                    instagram_topic.strip(),
                )
                save_instagram_post(
                    instagram_topic.strip(),
                    instagram_post,
                )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"📷 Instagram投稿案\n\n{instagram_post}",
                }
            )
            st.success("Instagram投稿案を作成・保存しました")
            st.rerun()

    st.divider()
    st.header("🧵 Threads投稿生成")

    threads_topic = st.text_input(
        "Threads投稿のテーマ",
        placeholder="例: AI副業で最初にやること",
        key="threads_topic",
    )

    if st.button("Threads投稿を作成"):
        if not threads_topic.strip():
            st.warning("Threads投稿のテーマを入力してください。")
        else:
            with st.spinner("Threads投稿を作成中..."):
                threads_post = generate_threads_post(
                    client,
                    threads_topic.strip(),
                )
                save_threads_post(
                    threads_topic.strip(),
                    threads_post,
                )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"🧵 Threads投稿案\n\n{threads_post}",
                }
            )
            st.success("Threads投稿案を作成・保存しました")
            st.rerun()

    st.divider()
    st.header("🔥 投稿採点")

    platform = st.selectbox(
        "投稿先を選んでください",
        ["X", "Instagram", "note", "TikTok", "YouTube Shorts"],
    )

    review_text = st.text_area(
        "採点したい投稿",
        placeholder="ここにnote、X、Instagram、Threadsの投稿を貼る",
        key="review_text",
        height=180,
    )

    if st.button("投稿を採点"):
        if not review_text.strip():
            st.warning("採点したい投稿を入力してください。")
        else:
            with st.spinner("投稿を採点中..."):
                review_result = review_post(client, review_text.strip(), platform)
                
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"🔥 投稿採点結果\n\n{review_result}",
                }
            )
            st.success("投稿の採点が完了しました")
            st.rerun()

    if st.button("投稿を改善"):
        if not review_text.strip():
            st.warning("改善したい投稿を入力してください。")
        else:
            with st.spinner("投稿を改善中..."):
                improved_post = improve_post(client, review_text.strip(), platform)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"✨ 投稿改善結果\n\n{improved_post}",
                }
            )
            st.success("投稿の改善が完了しました")
            st.rerun()

    st.divider()
    show_post_stock()

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
            response = chat_with_ai(client, user_input)

        save_history("Ko AI", response)

    except Exception as e:
        response = f"エラーが発生しました: {e}"

    st.session_state.messages.append({"role": "assistant", "content": response})

    with st.chat_message("assistant"):
        st.write(response)