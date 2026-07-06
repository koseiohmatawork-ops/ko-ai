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
from modules.post_reviewer import (
    create_freebie,
    create_monetization_plan,
    create_paid_note_draft,
    create_paid_note_outline,
    improve_post,
    review_post,
    save_freebie,
    save_monetization_plan,
    save_paid_note_draft,
    save_paid_note_outline,
    save_reviewed_post,
    save_sales_funnel,
)
from modules.post_calendar import (
    create_post_calendar,
    create_weekly_posts,
    save_post_calendar,
    save_weekly_posts,
)

from modules.today_menu import (
    archive_excluded_stock,
    create_stock_analysis,
    create_stock_cleanup_plan,
    create_today_post_menu,
    load_recent_stock,
    save_stock_analysis,
    save_stock_cleanup_plan,
    save_today_post_menu,
)

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

if "calendar_theme" not in st.session_state:
    st.session_state.calendar_theme = ""

if "sales_funnel_calendar_source" not in st.session_state:
    st.session_state.sales_funnel_calendar_source = ""

if "post_result_title" not in st.session_state:
    st.session_state.post_result_title = ""

if "post_result_memo" not in st.session_state:
    st.session_state.post_result_memo = ""

if "post_result_impressions" not in st.session_state:
    st.session_state.post_result_impressions = 0

if "post_result_likes" not in st.session_state:
    st.session_state.post_result_likes = 0

if "post_result_comments" not in st.session_state:
    st.session_state.post_result_comments = 0

if "post_result_saves" not in st.session_state:
    st.session_state.post_result_saves = 0

if "post_result_profile_clicks" not in st.session_state:
    st.session_state.post_result_profile_clicks = 0

if "post_result_link_clicks" not in st.session_state:
    st.session_state.post_result_link_clicks = 0

if "template_post_theme" not in st.session_state:
    st.session_state.template_post_theme = ""

if "today_menu_post_source" not in st.session_state:
    st.session_state.today_menu_post_source = ""

if "stock_analysis_post_source" not in st.session_state:
    st.session_state.stock_analysis_post_source = ""

if "safety_check_source" not in st.session_state:
    st.session_state.safety_check_source = ""

if "final_post_title" not in st.session_state:
    st.session_state.final_post_title = ""

if "final_post_body" not in st.session_state:
    st.session_state.final_post_body = ""

if "scheduled_post_title" not in st.session_state:
    st.session_state.scheduled_post_title = ""

if "scheduled_post_body" not in st.session_state:
    st.session_state.scheduled_post_body = ""

if "exclude_keywords_text" not in st.session_state:
    st.session_state.exclude_keywords_text = ""


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
    reviewed_files = sorted(Path("posts/reviewed").glob("*.md"), reverse=True)
    monetization_files = sorted(Path("posts/monetization").glob("*.md"), reverse=True)
    paid_note_outline_files = sorted(
        Path("posts/paid_note_outlines").glob("*.md"), reverse=True
    )
    calendar_files = sorted(Path("posts/calendars").glob("*.md"), reverse=True)
    weekly_post_files = sorted(Path("posts/weekly_posts").glob("*.md"), reverse=True)
    today_menu_files = sorted(Path("posts/today_menus").glob("*.md"), reverse=True)
    today_menu_post_files = sorted(Path("posts/today_menu_posts").glob("*.md"), reverse=True)
    stock_analysis_files = sorted(Path("posts/stock_analysis").glob("*.md"), reverse=True)
    stock_analysis_post_files = sorted(Path("posts/stock_analysis_posts").glob("*.md"), reverse=True)
    freebie_files = sorted(Path("posts/freebies").glob("*.md"), reverse=True)
    paid_note_draft_files = sorted(Path("posts/paid_note_drafts").glob("*.md"), reverse=True)
    sales_funnel_files = sorted(Path("posts/sales_funnels").glob("*.md"), reverse=True)
    stock_cleanup_files = sorted(Path("posts/stock_cleanup").glob("*.md"), reverse=True)
    post_result_files = sorted(Path("posts/results").glob("*.md"), reverse=True)
    result_next_post_files = sorted(Path("posts/result_next_posts").glob("*.md"), reverse=True)
    final_post_files = sorted(Path("posts/final_posts").glob("**/*.md"), reverse=True)
    scheduled_post_files = sorted(Path("posts/schedule").glob("*.md"), reverse=True)
    safety_checked_files = sorted(Path("posts/safety_checked").glob("*.md"), reverse=True)
    template_post_files = sorted(Path("posts/template_posts").glob("*.md"), reverse=True)
    archive_files = sorted(Path("posts/archive").glob("*"), reverse=True)

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
        reviewed_files = [
            file_path for file_path in reviewed_files if match_file(file_path)
        ]
        monetization_files = [
            file_path for file_path in monetization_files if match_file(file_path)
        ]
        paid_note_outline_files = [
            file_path for file_path in paid_note_outline_files if match_file(file_path)
        ]
        calendar_files = [
            file_path for file_path in calendar_files if match_file(file_path)
        ]
        weekly_post_files = [
            file_path for file_path in weekly_post_files if match_file(file_path)
        ]
        today_menu_files = [
            file_path for file_path in today_menu_files if match_file(file_path)
        ]
        stock_analysis_files = [
            file_path for file_path in stock_analysis_files if match_file(file_path)
        ]
        stock_analysis_post_files = [
            file_path for file_path in stock_analysis_post_files if match_file(file_path)
        ]
        freebie_files = [
            file_path for file_path in freebie_files if match_file(file_path)
        ]
        paid_note_draft_files = [
            file_path for file_path in paid_note_draft_files if match_file(file_path)
        ]
        sales_funnel_files = [
            file_path for file_path in sales_funnel_files if match_file(file_path)
        ]
        stock_cleanup_files = [
            file_path for file_path in stock_cleanup_files if match_file(file_path)
        ]
        post_result_files = [
            file_path for file_path in post_result_files if match_file(file_path)
        ]
        result_next_post_files = [
            file_path for file_path in result_next_post_files if match_file(file_path)
        ]
        final_post_files = [
            file_path for file_path in final_post_files if match_file(file_path)
        ]
        scheduled_post_files = [
            file_path for file_path in scheduled_post_files if match_file(file_path)
        ]
        safety_checked_files = [
            file_path for file_path in safety_checked_files if match_file(file_path)
        ]
        archive_files = [
            file_path for file_path in archive_files if file_path.is_file() and match_file(file_path)
        ]
    st.caption(
        f"note記事: {len(note_files)}件 / "
        f"X投稿: {len(x_files)}件 / "
        f"Instagram投稿: {len(instagram_files)}件 / "
        f"Threads投稿: {len(threads_files)}件 / "
        f"アイデア: {len(idea_files)}件 / "
        f"改善済み投稿: {len(reviewed_files)}件 / "
        f"収益導線案: {len(monetization_files)}件 / "
        f"有料note構成案: {len(paid_note_outline_files)}件 / "
        f"投稿カレンダー: {len(calendar_files)}件 / "
        f"7日分実投稿: {len(weekly_post_files)}件 / "
        f"今日の投稿メニュー: {len(today_menu_files)}件 / "
        f"今日メニュー実投稿: {len(today_menu_post_files)}件 / "
        f"投稿ストック分析: {len(stock_analysis_files)}件 / "
        f"分析実投稿: {len(stock_analysis_post_files)}件 / "
        f"無料特典: {len(freebie_files)}件 / "
        f"有料note本文: {len(paid_note_draft_files)}件 / "
        f"販売導線まとめ: {len(sales_funnel_files)}件 / "
        f"投稿ストック整理案: {len(stock_cleanup_files)}件 / "
        f"投稿反応メモ: {len(post_result_files)}件 / "
        f"反応ベース次投稿: {len(result_next_post_files)}件 / "
        f"完成版投稿: {len(final_post_files)}件 / "
        f"安全チェック済み: {len(safety_checked_files)}件 / "
        f"投稿予定: {len(scheduled_post_files)}件 / "
        f"テンプレ投稿: {len(template_post_files)}件 / "
        f"archive: {len(archive_files)}件"
    )
    

    all_stock_files = (
        note_files
        + x_files
        + instagram_files
        + threads_files
        + idea_files
        + reviewed_files
        + monetization_files
        + paid_note_outline_files
        + calendar_files
        + weekly_post_files
        + today_menu_files
        + today_menu_post_files
        + stock_analysis_files
        + stock_analysis_post_files
        + freebie_files
        + paid_note_draft_files
        + sales_funnel_files
        + stock_cleanup_files
        + post_result_files
        + result_next_post_files
        + scheduled_post_files
        + final_post_files
        + safety_checked_files
        + template_post_files
    )

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

    today_scheduled_files = []
    tomorrow_scheduled_files = []
    pending_scheduled_files = []
    posted_scheduled_files = []

    for file_path in scheduled_post_files:
        content = file_path.read_text(encoding="utf-8")
        if "## 状態\n今日投稿" in content:
            today_scheduled_files.append(file_path)
        elif "## 状態\n明日投稿" in content:
            tomorrow_scheduled_files.append(file_path)
        elif "## 状態\n保留" in content:
            pending_scheduled_files.append(file_path)
        elif "## 状態\n投稿済み" in content:
            posted_scheduled_files.append(file_path)

    st.subheader("📌 投稿予定まとめ")
    st.caption(
        f"今日投稿: {len(today_scheduled_files)}件 / "
        f"明日投稿: {len(tomorrow_scheduled_files)}件 / "
        f"保留: {len(pending_scheduled_files)}件 / "
        f"投稿済み: {len(posted_scheduled_files)}件"
    )

    with st.expander("📌 今日投稿する予定"):
        if not today_scheduled_files:
            st.caption("今日投稿の予定はありません")
        for file_path in today_scheduled_files[:10]:
            content = file_path.read_text(encoding="utf-8")
            post_body = extract_scheduled_post_body(content)
            st.subheader(file_path.name)
            st.text_area(
                "投稿本文だけコピー用",
                post_body,
                height=180,
                key=f"copy_today_scheduled_body_{file_path.name}",
            )
            with st.expander("投稿予定の詳細"):
                st.write(content)

            col1, col2 = st.columns(2)

            with col1:
                if st.button("✅ 投稿済みにする", key=f"mark_posted_{file_path.name}"):
                    update_scheduled_post_status(file_path, "投稿済み")
                    st.success("投稿済みに変更しました")
                    st.rerun()

            with col2:
                if st.button("🗑 投稿予定から削除", key=f"delete_today_scheduled_{file_path.name}"):
                    delete_scheduled_post(file_path)
                    st.success("投稿予定から削除しました")
                    st.rerun()

    with st.expander("🌙 明日投稿する予定"):
        if not tomorrow_scheduled_files:
            st.caption("明日投稿の予定はありません")
        for file_path in tomorrow_scheduled_files[:10]:
            content = file_path.read_text(encoding="utf-8")
            post_body = extract_scheduled_post_body(content)
            st.subheader(file_path.name)
            st.text_area(
                "投稿本文だけコピー用",
                post_body,
                height=180,
                key=f"copy_tomorrow_scheduled_body_{file_path.name}",
            )
            with st.expander("投稿予定の詳細"):
                st.write(content)

            col1, col2 = st.columns(2)

            with col1:
                if st.button("📌 今日投稿にする", key=f"mark_today_{file_path.name}"):
                    update_scheduled_post_status(file_path, "今日投稿")
                    st.success("今日投稿に変更しました")
                    st.rerun()

            with col2:
                if st.button("🗑 投稿予定から削除", key=f"delete_tomorrow_scheduled_{file_path.name}"):
                    delete_scheduled_post(file_path)
                    st.success("投稿予定から削除しました")
                    st.rerun()

    with st.expander("⏸ 保留中の投稿"):
        if not pending_scheduled_files:
            st.caption("保留中の投稿はありません")
        for file_path in pending_scheduled_files[:10]:
            content = file_path.read_text(encoding="utf-8")
            post_body = extract_scheduled_post_body(content)
            st.subheader(file_path.name)
            st.text_area(
                "投稿本文だけコピー用",
                post_body,
                height=180,
                key=f"copy_pending_scheduled_body_{file_path.name}",
            )
            with st.expander("投稿予定の詳細"):
                st.write(content)

            col1, col2 = st.columns(2)

            with col1:
                if st.button("📌 今日投稿にする", key=f"mark_pending_today_{file_path.name}"):
                    update_scheduled_post_status(file_path, "今日投稿")
                    st.success("今日投稿に変更しました")
                    st.rerun()

            with col2:
                if st.button("🗑 投稿予定から削除", key=f"delete_pending_scheduled_{file_path.name}"):
                    delete_scheduled_post(file_path)
                    st.success("投稿予定から削除しました")
                    st.rerun()

    with st.expander("✅ 投稿済み"):
        if not posted_scheduled_files:
            st.caption("投稿済みの投稿はありません")
        for file_path in posted_scheduled_files[:10]:
            content = file_path.read_text(encoding="utf-8")
            post_body = extract_scheduled_post_body(content)
            st.subheader(file_path.name)
            st.text_area(
                "投稿本文だけコピー用",
                post_body,
                height=180,
                key=f"copy_posted_scheduled_body_{file_path.name}",
            )
            with st.expander("投稿予定の詳細"):
                st.write(content)

            col1, col2 = st.columns(2)

            with col1:
                if st.button("📈 反応メモ下書きを作成", key=f"create_result_draft_{file_path.name}"):
                    saved_path = create_post_result_draft_from_scheduled(file_path)
                    st.success(f"反応メモ下書きを作成しました: {saved_path}")
                    st.rerun()

            with col2:
                if st.button("🗑 投稿済み一覧から削除", key=f"delete_posted_scheduled_{file_path.name}"):
                    delete_scheduled_post(file_path)
                    st.success("投稿済み一覧から削除しました")
                    st.rerun()

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
    with st.expander("✨ 改善済み投稿ストック"):
        if not reviewed_files:
            st.caption("まだ改善済み投稿はありません")
        for file_path in reviewed_files[:10]:
            content = file_path.read_text(encoding="utf-8")
            st.subheader(file_path.name)
            st.write(content)
            st.download_button(
                "✨ 改善済み投稿をダウンロード",
                data=content,
                file_name=file_path.name,
                mime="text/markdown",
                key=f"download_reviewed_{file_path.name}",
            )

    with st.expander("💰 収益導線ストック"):
        if not monetization_files:
            st.caption("まだ収益導線案はありません")
        for file_path in monetization_files[:10]:
            content = file_path.read_text(encoding="utf-8")
            st.subheader(file_path.name)
            st.write(content)
            st.download_button(
                "💰 収益導線案をダウンロード",
                data=content,
                file_name=file_path.name,
                mime="text/markdown",
                key=f"download_monetization_{file_path.name}",
            )

    with st.expander("📝 有料note構成ストック"):
        if not paid_note_outline_files:
            st.caption("まだ有料note構成案はありません")
        for file_path in paid_note_outline_files[:10]:
            content = file_path.read_text(encoding="utf-8")
            st.subheader(file_path.name)
            st.write(content)
            st.download_button(
                "📝 有料note構成案をダウンロード",
                data=content,
                file_name=file_path.name,
                mime="text/markdown",
                key=f"download_paid_note_outline_{file_path.name}",
            )

    with st.expander("📅 投稿カレンダーストック"):
        if not calendar_files:
            st.caption("まだ投稿カレンダーはありません")
        for file_path in calendar_files[:10]:
            content = file_path.read_text(encoding="utf-8")
            st.subheader(file_path.name)
            st.write(content)
            st.download_button(
                "📅 投稿カレンダーをダウンロード",
                data=content,
                file_name=file_path.name,
                mime="text/markdown",
                key=f"download_calendar_{file_path.name}",
            )

    with st.expander("📝 7日分実投稿ストック"):
        if not weekly_post_files:
            st.caption("まだ7日分実投稿はありません")
        for file_path in weekly_post_files[:10]:
            content = file_path.read_text(encoding="utf-8")
            st.subheader(file_path.name)
            st.write(content)
            st.download_button(
                "📝 7日分実投稿をダウンロード",
                data=content,
                file_name=file_path.name,
                mime="text/markdown",
                key=f"download_weekly_posts_{file_path.name}",
            )

    with st.expander("📌 今日の投稿メニューストック"):
        if not today_menu_files:
            st.caption("まだ今日の投稿メニューはありません")
        for file_path in today_menu_files[:10]:
            content = file_path.read_text(encoding="utf-8")
            st.subheader(file_path.name)
            st.write(content)
            st.download_button(
                "📌 今日の投稿メニューをダウンロード",
                data=content,
                file_name=file_path.name,
                mime="text/markdown",
                key=f"download_today_menu_{file_path.name}",
            )

    with st.expander("🧾 今日メニュー実投稿ストック"):
        if not today_menu_post_files:
            st.caption("まだ今日メニュー実投稿はありません")
        for file_path in today_menu_post_files[:10]:
            content = file_path.read_text(encoding="utf-8")
            st.subheader(file_path.name)
            st.write(content)
            st.download_button(
                "🧾 今日メニュー実投稿をダウンロード",
                data=content,
                file_name=file_path.name,
                mime="text/markdown",
                key=f"download_today_menu_posts_{file_path.name}",
            )

    with st.expander("📊 投稿ストック分析ストック"):
        if not stock_analysis_files:
            st.caption("まだ投稿ストック分析はありません")
        for file_path in stock_analysis_files[:10]:
            content = file_path.read_text(encoding="utf-8")
            st.subheader(file_path.name)
            st.write(content)
            st.download_button(
                "📊 投稿ストック分析をダウンロード",
                data=content,
                file_name=file_path.name,
                mime="text/markdown",
                key=f"download_stock_analysis_{file_path.name}",
            )

    with st.expander("📊 分析実投稿ストック"):
        if not stock_analysis_post_files:
            st.caption("まだ分析実投稿はありません")
        for file_path in stock_analysis_post_files[:10]:
            content = file_path.read_text(encoding="utf-8")
            st.subheader(file_path.name)
            st.write(content)
            st.download_button(
                "📊 分析実投稿をダウンロード",
                data=content,
                file_name=file_path.name,
                mime="text/markdown",
                key=f"download_stock_analysis_posts_{file_path.name}",
            )

    with st.expander("🎁 無料特典ストック"):
        if not freebie_files:
            st.caption("まだ無料特典はありません")
        for file_path in freebie_files[:10]:
            content = file_path.read_text(encoding="utf-8")
            st.subheader(file_path.name)
            st.write(content)
            st.download_button(
                "🎁 無料特典をダウンロード",
                data=content,
                file_name=file_path.name,
                mime="text/markdown",
                key=f"download_freebie_{file_path.name}",
            )

    with st.expander("📝 有料note本文ストック"):
        if not paid_note_draft_files:
            st.caption("まだ有料note本文はありません")
        for file_path in paid_note_draft_files[:10]:
            content = file_path.read_text(encoding="utf-8")
            st.subheader(file_path.name)
            st.write(content)
            st.download_button(
                "📝 有料note本文をダウンロード",
                data=content,
                file_name=file_path.name,
                mime="text/markdown",
                key=f"download_paid_note_draft_{file_path.name}",
            )

    with st.expander("🚀 販売導線まとめストック"):
        if not sales_funnel_files:
            st.caption("まだ販売導線まとめはありません")
        for file_path in sales_funnel_files[:10]:
            content = file_path.read_text(encoding="utf-8")
            st.subheader(file_path.name)
            st.write(content)
            st.download_button(
                "🚀 販売導線まとめをダウンロード",
                data=content,
                file_name=file_path.name,
                mime="text/markdown",
                key=f"download_sales_funnel_{file_path.name}",
            )

    with st.expander("🗂 投稿ストック整理案ストック"):
        if not stock_cleanup_files:
            st.caption("まだ投稿ストック整理案はありません")
        for file_path in stock_cleanup_files[:10]:
            content = file_path.read_text(encoding="utf-8")
            st.subheader(file_path.name)
            st.write(content)
            st.download_button(
                "🗂 投稿ストック整理案をダウンロード",
                data=content,
                file_name=file_path.name,
                mime="text/markdown",
                key=f"download_stock_cleanup_{file_path.name}",
            )

    with st.expander("📈 投稿反応メモストック"):
        if not post_result_files:
            st.caption("まだ投稿反応メモはありません")
        for file_path in post_result_files[:10]:
            content = file_path.read_text(encoding="utf-8")
            st.subheader(file_path.name)
            st.write(content)

            col1, col2 = st.columns(2)

            with col1:
                st.download_button(
                    "📈 投稿反応メモをダウンロード",
                    data=content,
                    file_name=file_path.name,
                    mime="text/markdown",
                    key=f"download_post_result_{file_path.name}",
                )

            with col2:
                if st.button("🗑 反応メモを削除", key=f"delete_post_result_{file_path.name}"):
                    delete_post_result_memo(file_path)
                    st.success("反応メモを削除しました")
                    st.rerun()

    
    with st.expander("📝 反応ベース次投稿ストック"):
        if not result_next_post_files:
            st.caption("まだ反応ベースの次投稿案はありません")
        for file_path in result_next_post_files[:10]:
            content = file_path.read_text(encoding="utf-8")
            st.subheader(file_path.name)
            st.write(content)

            col1, col2 = st.columns(2)

            with col1:
                st.download_button(
                    "📝 反応ベース次投稿をダウンロード",
                    data=content,
                    file_name=file_path.name,
                    mime="text/markdown",
                    key=f"download_result_next_post_{file_path.name}",
                )

            with col2:
                if st.button("🗑 次投稿案を削除", key=f"delete_result_next_post_{file_path.name}"):
                    delete_result_next_post(file_path)
                    st.success("次投稿案を削除しました")
                    st.rerun()

    with st.expander("✅ 完成版投稿ストック"):
        if not final_post_files:
            st.caption("まだ完成版投稿はありません")
        for file_path in final_post_files[:20]:
            content = file_path.read_text(encoding="utf-8")
            st.subheader(str(file_path))
            st.write(content)

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.download_button(
                    "✅ ダウンロード",
                    data=content,
                    file_name=file_path.name,
                    mime="text/markdown",
                    key=f"download_final_post_{file_path}",
                )

            with col2:
                if st.button("📅 投稿予定に追加", key=f"schedule_final_post_{file_path}"):
                    saved_path = save_scheduled_post_from_final_post(file_path, "保留")
                    st.success(f"投稿予定に追加しました: {saved_path}")
                    st.rerun()

            with col3:
                if st.button("📌 今日投稿に追加", key=f"schedule_today_final_post_{file_path}"):
                    saved_path = save_scheduled_post_from_final_post(file_path, "今日投稿")
                    st.success(f"今日投稿に追加しました: {saved_path}")
                    st.rerun()

            with col4:
                if st.button("🗑 削除", key=f"delete_final_post_{file_path}"):
                    delete_final_post(file_path)
                    st.success("完成版投稿を削除しました")
                    st.rerun()

    with st.expander("📅 投稿予定ストック"):
        if not scheduled_post_files:
            st.caption("まだ投稿予定はありません")
        for file_path in scheduled_post_files[:20]:
            content = file_path.read_text(encoding="utf-8")
            st.subheader(file_path.name)
            st.write(content)
            st.download_button(
                "📅 投稿予定をダウンロード",
                data=content,
                file_name=file_path.name,
                mime="text/markdown",
                key=f"download_scheduled_post_{file_path.name}",
            )

    with st.expander("🛡 安全チェック済みストック"):
        if not safety_checked_files:
            st.caption("まだ安全チェック済み投稿はありません")
        for file_path in safety_checked_files[:10]:
            content = file_path.read_text(encoding="utf-8")
            st.subheader(file_path.name)
            st.write(content)

            col1, col2 = st.columns(2)

            with col1:
                st.download_button(
                    "🛡 安全チェック済み投稿をダウンロード",
                    data=content,
                    file_name=file_path.name,
                    mime="text/markdown",
                    key=f"download_safety_checked_{file_path.name}",
                )

            with col2:
                if st.button("🗑 安全チェック済み投稿を削除", key=f"delete_safety_checked_{file_path.name}"):
                    delete_safety_checked_post(file_path)
                    st.success("安全チェック済み投稿を削除しました")
                    st.rerun()

    with st.expander("🧩 テンプレ投稿ストック"):
        if not template_post_files:
            st.caption("まだテンプレ投稿はありません")
        for file_path in template_post_files[:10]:
            content = file_path.read_text(encoding="utf-8")
            st.subheader(file_path.name)
            st.write(content)
            st.download_button(
                "🧩 テンプレ投稿をダウンロード",
                data=content,
                file_name=file_path.name,
                mime="text/markdown",
                key=f"download_template_post_{file_path.name}",
            )

    with st.expander("🗄 archiveストック"):
        if not archive_files:
            st.caption("まだarchiveに移動したストックはありません")
        for file_path in archive_files[:20]:
            if not file_path.is_file():
                continue
            content = file_path.read_text(encoding="utf-8")
            st.subheader(file_path.name)
            st.write(content)
            st.download_button(
                "🗄 archiveストックをダウンロード",
                data=content,
                file_name=file_path.name,
                mime="text/plain",
                key=f"download_archive_{file_path.name}",
            )


def create_sales_funnel_calendar(client: OpenAI, sales_funnel_text: str, platform: str) -> str:
    """販売導線まとめから7日分の投稿カレンダーを作成する。"""
    prompt = f"""
あなたはSNS収益化に強い投稿設計アシスタントです。
以下の販売導線まとめをもとに、{platform}向けの7日分投稿カレンダーを作ってください。

目的:
- 無料特典への誘導
- 有料noteへの自然な誘導
- AI副業・SNS運用・自動化に興味がある人を集める
- 売り込み感を出しすぎず、保存・共感・行動につながる流れにする

出力形式:
Day1:
投稿目的:
投稿テーマ:
投稿内容の方向性:
CTA:

Day2:
投稿目的:
投稿テーマ:
投稿内容の方向性:
CTA:

Day7まで同じ形式で作成してください。

販売導線まとめ:
{sales_funnel_text}
""".strip()

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "あなたはSNS収益化と投稿設計の専門家です。"},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content or ""


def save_sales_funnel_calendar(platform: str, calendar_text: str) -> Path:
    """販売導線から作った投稿カレンダーを保存する。"""
    save_dir = Path("posts/calendars")
    save_dir.mkdir(parents=True, exist_ok=True)

    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = save_dir / f"{timestamp}_{platform}_sales_funnel_calendar.md"
    file_path.write_text(calendar_text, encoding="utf-8")
    return file_path




# --- 追加: 投稿予定ファイルから項目抽出・反応メモ下書き生成 ---
def extract_scheduled_post_field(content: str, field_name: str) -> str:
    """投稿予定ファイルから指定した項目を取り出す。"""
    marker = f"## {field_name}"
    if marker not in content:
        return ""

    after_marker = content.split(marker, 1)[1].strip()
    lines = []
    for line in after_marker.splitlines():
        if line.startswith("## "):
            break
        lines.append(line)

    return "\n".join(lines).strip()


def create_post_result_draft_from_scheduled(file_path: Path) -> Path:
    """投稿済み予定から反応メモの下書きを作成する。"""
    content = file_path.read_text(encoding="utf-8")
    title = extract_scheduled_post_field(content, "投稿名") or file_path.stem
    platform = extract_scheduled_post_field(content, "投稿先") or "不明"
    post_body = extract_scheduled_post_body(content)

    memo = f"""
## 元投稿
{post_body}

## 気づき
- 

## 次に活かすこと
- 
""".strip()

    return save_post_result_memo(
        title=title,
        platform=platform,
        memo=memo,
        impressions=0,
        likes=0,
        comments=0,
        saves=0,
        profile_clicks=0,
        link_clicks=0,
    )


def extract_scheduled_post_body(content: str) -> str:
    """投稿予定ファイルから投稿本文だけを取り出す。"""
    marker = "## 投稿本文"
    if marker not in content:
        return content
    return content.split(marker, 1)[1].strip()

def delete_scheduled_post(file_path: Path) -> None:
    """投稿予定ファイルを削除する。"""
    if file_path.exists() and file_path.is_file():
        file_path.unlink()

def delete_post_result_memo(file_path: Path) -> None:
    """投稿反応メモファイルを削除する。"""
    if file_path.exists() and file_path.is_file():
        file_path.unlink()

def delete_result_next_post(file_path: Path) -> None:
    """反応ベース次投稿ファイルを削除する。"""
    if file_path.exists() and file_path.is_file():
        file_path.unlink()

def delete_final_post(file_path: Path) -> None:
    """完成版投稿ファイルを削除する。"""
    if file_path.exists() and file_path.is_file():
        file_path.unlink()

def delete_safety_checked_post(file_path: Path) -> None:
    """安全チェック済み投稿ファイルを削除する。"""
    if file_path.exists() and file_path.is_file():
        file_path.unlink()

def save_scheduled_post_from_final_post(final_post_file_path: Path, status: str = "保留") -> Path:
    """完成版投稿ファイルを投稿予定として保存する。"""
    save_dir = Path("posts/schedule")
    save_dir.mkdir(parents=True, exist_ok=True)

    from datetime import datetime

    platform = final_post_file_path.parent.name
    title = final_post_file_path.stem

    for existing_file_path in save_dir.glob("*.md"):
        existing_content = existing_file_path.read_text(encoding="utf-8")
        if f"## 元ファイル\n{final_post_file_path}" in existing_content:
            update_scheduled_post_status(existing_file_path, status)
            return existing_file_path

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = title.strip().replace("/", "_").replace(" ", "_")[:40] or "scheduled_post"
    file_path = save_dir / f"{timestamp}_{platform}_{safe_title}.md"

    body = final_post_file_path.read_text(encoding="utf-8")   

    content = f"""
# 投稿予定

## 投稿名
{title}

## 投稿先
{platform}

## 状態
{status}

## 元ファイル
{final_post_file_path}

## 投稿本文
{body}
""".strip()

    file_path.write_text(content, encoding="utf-8")
    return file_path


def save_post_result_memo(
    title: str,
    platform: str,
    memo: str,
    impressions: int = 0,
    likes: int = 0,
    comments: int = 0,
    saves: int = 0,
    profile_clicks: int = 0,
    link_clicks: int = 0,
) -> Path:
    """投稿後の反応メモを保存する。"""
    save_dir = Path("posts/results")
    save_dir.mkdir(parents=True, exist_ok=True)

    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = title.strip().replace("/", "_").replace(" ", "_")[:30] or "post_result"
    file_path = save_dir / f"{timestamp}_{platform}_{safe_title}.md"

    reaction_rate = ((likes + comments + saves) / impressions * 100) if impressions else 0
    save_rate = (saves / impressions * 100) if impressions else 0
    profile_click_rate = (profile_clicks / impressions * 100) if impressions else 0
    link_click_rate = (link_clicks / impressions * 100) if impressions else 0

    content = f"""
# 投稿反応メモ

## 投稿名
{title}

## 投稿先
{platform}

## 数字
- インプレッション: {impressions}
- いいね: {likes}
- コメント: {comments}
- 保存: {saves}
- プロフィールクリック: {profile_clicks}
- リンククリック: {link_clicks}

## 自動計算
- 反応率: {reaction_rate:.2f}%
- 保存率: {save_rate:.2f}%
- プロフィールクリック率: {profile_click_rate:.2f}%
- リンククリック率: {link_click_rate:.2f}%

## 反応メモ
{memo}
""".strip()
    file_path.write_text(content, encoding="utf-8")
    return file_path

def create_post_result_ranking() -> str:
    """保存済みの投稿反応メモから簡易ランキングを作成する。"""
    result_files = sorted(Path("posts/results").glob("*.md"), reverse=True)

    if not result_files:
        return "まだ投稿反応メモがありません。"

    rows = []

    for file_path in result_files[:50]:
        content = file_path.read_text(encoding="utf-8")
        title = file_path.stem
        platform = "不明"
        impressions = 0
        likes = 0
        comments = 0
        saves = 0
        profile_clicks = 0
        link_clicks = 0

        lines = content.splitlines()
        for index, line in enumerate(lines):
            line = line.strip()
            if line == "## 投稿名" and index + 1 < len(lines):
                title = lines[index + 1].strip() or title
            elif line == "## 投稿先" and index + 1 < len(lines):
                platform = lines[index + 1].strip() or platform
            elif line.startswith("- インプレッション:"):
                impressions = int(line.replace("- インプレッション:", "").strip() or 0)
            elif line.startswith("- いいね:"):
                likes = int(line.replace("- いいね:", "").strip() or 0)
            elif line.startswith("- コメント:"):
                comments = int(line.replace("- コメント:", "").strip() or 0)
            elif line.startswith("- 保存:"):
                saves = int(line.replace("- 保存:", "").strip() or 0)
            elif line.startswith("- プロフィールクリック:"):
                profile_clicks = int(line.replace("- プロフィールクリック:", "").strip() or 0)
            elif line.startswith("- リンククリック:"):
                link_clicks = int(line.replace("- リンククリック:", "").strip() or 0)

        reaction_rate = ((likes + comments + saves) / impressions * 100) if impressions else 0
        save_rate = (saves / impressions * 100) if impressions else 0
        profile_click_rate = (profile_clicks / impressions * 100) if impressions else 0
        link_click_rate = (link_clicks / impressions * 100) if impressions else 0

        rows.append(
            {
                "title": title,
                "platform": platform,
                "impressions": impressions,
                "likes": likes,
                "comments": comments,
                "saves": saves,
                "profile_clicks": profile_clicks,
                "link_clicks": link_clicks,
                "reaction_rate": reaction_rate,
                "save_rate": save_rate,
                "profile_click_rate": profile_click_rate,
                "link_click_rate": link_click_rate,
            }
        )

    def format_ranking(metric_key: str, label: str) -> str:
        ranked_rows = sorted(rows, key=lambda row: row[metric_key], reverse=True)[:5]
        ranking_lines = [f"## {label}"]
        for rank, row in enumerate(ranked_rows, start=1):
            ranking_lines.append(
                f"{rank}. {row['title']}（{row['platform']}）: {row[metric_key]:.2f}% "
                f"/ 表示 {row['impressions']} / いいね {row['likes']} / 保存 {row['saves']} / "
                f"プロフィールクリック {row['profile_clicks']} / リンククリック {row['link_clicks']}"
            )
        return "\n".join(ranking_lines)

    result = [
        "# 📊 投稿反応ランキング",
        "",
        format_ranking("reaction_rate", "反応率ランキング"),
        "",
        format_ranking("save_rate", "保存率ランキング"),
        "",
        format_ranking("profile_click_rate", "プロフィールクリック率ランキング"),
        "",
        format_ranking("link_click_rate", "リンククリック率ランキング"),
    ]

    return "\n".join(result)


def create_post_result_insight(client: OpenAI) -> str:
    """投稿反応メモから伸びた投稿パターンと次の改善案を作成する。"""
    result_files = sorted(Path("posts/results").glob("*.md"), reverse=True)

    if not result_files:
        return "まだ投稿反応メモがありません。"

    result_texts = []
    for file_path in result_files[:20]:
        content = file_path.read_text(encoding="utf-8")
        result_texts.append(f"## {file_path.name}\n{content}")

    results_text = "\n\n---\n\n".join(result_texts)

    prompt = f"""
あなたはSNS運用の分析担当です。
以下の投稿反応メモをもとに、伸びた投稿パターンと次に改善すべき内容を分析してください。

見るポイント:
- 反応率が高い投稿の共通点
- 保存率が高い投稿の共通点
- プロフィールクリックやリンククリックにつながった投稿の共通点
- 反応が弱い投稿の原因
- 次に作るべき投稿テーマ
- 次に試すべきCTA

出力形式:
1. 全体まとめ
2. 伸びた投稿パターン
3. 弱かった投稿パターン
4. 次に作るべき投稿TOP3
5. 次に試すCTA
6. 明日やること

投稿反応メモ:
{results_text}
""".strip()

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "あなたはSNS投稿分析と改善提案の専門家です。"},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content or ""


def create_next_posts_from_result(client: OpenAI) -> str:
    """投稿反応メモをもとに次に投稿する案を作成する。"""
    result_files = sorted(Path("posts/results").glob("*.md"), reverse=True)

    if not result_files:
        return "まだ投稿反応メモがありません。"

    result_texts = []
    for file_path in result_files[:20]:
        content = file_path.read_text(encoding="utf-8")
        result_texts.append(f"## {file_path.name}\n{content}")

    results_text = "\n\n---\n\n".join(result_texts)

    prompt = f"""
あなたはSNS投稿作成と改善の担当です。
以下の投稿反応メモをもとに、次に投稿するべき内容を具体的に作ってください。

目的:
- 反応が良かった投稿パターンを活かす
- 保存率・プロフィールクリック率・リンククリック率を上げる
- 無料特典やプロフィールリンクへの導線を自然に入れる
- 顔出しなしでも投稿できる内容にする
- 実績や収益を断定しない
- 「誰でも稼げる」「必ず月◯万円」などの収益保証表現は避ける
- 「私もよくそうでした」「初心者の私でも」など、本人の実体験に見える表現は避ける
- 「〇〇法」「〇〇するだけ」など、未完成・不自然・過度に簡単そうな表現は避ける
- 「リスクが少ない」「安全に始められる」など、損失や安全性を断定する表現は避ける
- 具体例は出してよいが、実在の成果・売上・成功事例のように見せない

出力形式:
1. 次に狙う投稿テーマTOP3
2. X投稿案3本
3. Instagramカルーセル案1本
   - 1枚目
   - 2枚目
   - 3枚目
   - 4枚目
   - 5枚目
   - キャプション
4. Threads投稿案1本
5. 無料特典への自然な誘導文
6. 投稿前の注意点

投稿反応メモ:
{results_text}
""".strip()

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "あなたはSNS投稿改善と投稿作成の専門家です。"},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content or ""

def save_next_posts_from_result(post_text: str) -> Path:
    """投稿反応から作った次の投稿案を保存する。"""
    save_dir = Path("posts/result_next_posts")
    save_dir.mkdir(parents=True, exist_ok=True)

    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = save_dir / f"{timestamp}_result_next_posts.md"
    file_path.write_text(post_text, encoding="utf-8")
    return file_path

def create_template_post(client: OpenAI, theme: str, platform: str, template_type: str) -> str:
    """決まった型に沿って投稿を作成する。"""
    prompt = f"""
あなたはSNS投稿と収益導線設計の専門家です。
以下の条件で、{platform}向けの投稿を作ってください。

テーマ:
{theme}

投稿テンプレート:
{template_type}

共通ルール:
- AI副業、SNS運用、自動化、投稿作成ノウハウに関心がある人向け
- 売り込み感を出しすぎない
- 保存・共感・行動につながる内容にする
- 最後に自然なCTAを入れる
- 顔出しなしでも使える内容にする

テンプレート別ルール:
保存されやすい型: 手順・チェックリスト・比較など、後で見返したくなる形にする
共感型: 初心者の悩みや不安から入り、解決の方向性を示す
無料特典誘導型: 無料で受け取る理由を自然に作り、押し売りにしない
有料note誘導型: 無料投稿では足りない部分を示し、有料noteへの興味を作る

出力形式:
投稿本文:

CTA:

狙い:
""".strip()

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "あなたはSNS投稿と収益化導線の専門家です。"},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content or ""


def save_template_post(theme: str, platform: str, template_type: str, post_text: str) -> Path:
    """テンプレート投稿を保存する。"""
    save_dir = Path("posts/template_posts")
    save_dir.mkdir(parents=True, exist_ok=True)

    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_theme = theme.strip().replace("/", "_").replace(" ", "_")[:30] or "template_post"
    safe_template = template_type.strip().replace("/", "_").replace(" ", "_")[:20]
    file_path = save_dir / f"{timestamp}_{platform}_{safe_template}_{safe_theme}.md"
    file_path.write_text(post_text, encoding="utf-8")
    return file_path


def create_posts_from_today_menu(client: OpenAI, today_menu_text: str) -> str:
    """今日の投稿メニューから実投稿セットを作成する。"""
    prompt = f"""
あなたはAI副業・SNS運用・無料特典・有料note販売に強いSNS投稿作成者です。
以下の今日の投稿メニューをもとに、そのまま投稿作業に使える実投稿セットを作ってください。

目的:
- 個人がAI副業やSNS運用を始める流れに寄せる
- 無料特典・プロフィールリンク・有料note販売につながる導線を入れる
- 企業向けAI活用ではなく、初心者・個人・副業を始めたい人向けにする
- 顔出しなしでも使える内容にする
- 実在しない成功事例や実績を断定しない。実績がない場合は「架空例」「シミュレーション」「例」と明記する
- 「誰でも稼げる」「必ず月◯万円」など、収益を保証する表現は避ける
- 「私もよくそうでした」「初心者の私でも」など、本人の実体験に見える表現は避ける
- 「〇〇法」「〇〇するだけ」など、未完成・不自然・過度に簡単そうな表現は避ける
- 「リスクが少ない」「安全に始められる」など、損失や安全性を断定する表現は避ける
- 具体例は出してよいが、実在の成果・売上・成功事例のように見せない

出力形式:
1. X投稿
2. Instagramカルーセル案
   - 1枚目
   - 2枚目
   - 3枚目
   - 4枚目
   - 5枚目
   - キャプション
3. Threads投稿
4. note導入文
5. 無料特典誘導文
6. 有料note誘導文
7. 投稿時の注意点

今日の投稿メニュー:
{today_menu_text}
""".strip()

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "あなたはSNS投稿と収益化導線の専門家です。"},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content or ""


def save_today_menu_posts(post_text: str) -> Path:
    """今日の投稿メニューから作った実投稿セットを保存する。"""
    save_dir = Path("posts/today_menu_posts")
    save_dir.mkdir(parents=True, exist_ok=True)

    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = save_dir / f"{timestamp}_today_menu_posts.md"
    file_path.write_text(post_text, encoding="utf-8")
    return file_path


def create_posts_from_stock_analysis(client: OpenAI, stock_analysis_text: str) -> str:
    """投稿ストック分析から次に作るべき実投稿セットを作成する。"""
    prompt = f"""
あなたはAI副業・SNS運用・無料特典・有料note販売に強いSNS投稿作成者です。
以下の投稿ストック分析をもとに、次に作るべき投稿を具体的に作成してください。

目的:
- 分析結果の「次に作るべき投稿テーマ」から、すぐ投稿できる形にする
- 個人のAI副業、SNS運用、投稿自動化、無料特典、有料note販売に寄せる
- 企業向けAI活用や一般的なAIニュースではなく、初心者・個人・副業を始めたい人向けにする
- 無料特典や有料noteへの導線を自然に入れる
- 実在しない成功事例や実績を断定しない。実績がない場合は「架空例」「シミュレーション」「例」と明記する
- 「誰でも稼げる」「必ず月◯万円」など、収益を保証する表現は避ける
- 「私もよくそうでした」「初心者の私でも」など、本人の実体験に見える表現は避ける
- 「〇〇法」「〇〇するだけ」など、未完成・不自然・過度に簡単そうな表現は避ける
- 「リスクが少ない」「安全に始められる」など、損失や安全性を断定する表現は避ける
- 具体例は出してよいが、実在の成果・売上・成功事例のように見せない

出力形式:
1. 今日作るべき投稿テーマTOP3
2. X投稿案3本
3. Instagramカルーセル案1本
   - 1枚目
   - 2枚目
   - 3枚目
   - 4枚目
   - 5枚目
   - キャプション
4. note記事タイトル案3つ
5. 無料特典案3つ
6. 有料noteにつなげる導線
7. 次の行動

投稿ストック分析:
{stock_analysis_text}
""".strip()

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "あなたはSNS投稿と収益化導線の専門家です。"},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content or ""


def save_stock_analysis_posts(post_text: str) -> Path:
    """投稿ストック分析から作った実投稿セットを保存する。"""
    save_dir = Path("posts/stock_analysis_posts")
    save_dir.mkdir(parents=True, exist_ok=True)

    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = save_dir / f"{timestamp}_stock_analysis_posts.md"
    file_path.write_text(post_text, encoding="utf-8")
    return file_path


def check_and_rewrite_post_safety(client: OpenAI, post_text: str) -> str:
    """投稿文の危ない表現を確認し、安全な表現に直す。"""
    prompt = f"""
あなたはSNS投稿の表現チェック担当です。
以下の投稿文を確認し、収益化・副業・AI活用に関する危ない表現を安全に直してください。

チェックする点:
- 実在しない成功事例や実績を断定していないか
- 「必ず稼げる」「誰でも稼げる」「月◯万円達成」など収益保証に見える表現がないか
- 架空の人物や事例を実在のように見せていないか
- 誇大広告に見える表現がないか
- 無料特典や有料noteへの導線が自然か
- 「私もよくそうでした」「初心者の私でも」など、本人の実体験に見える表現がないか
- 「〇〇法」「〇〇するだけ」など、未完成・不自然・過度に簡単そうな表現がないか
- 「リスクが少ない」「安全に始められる」など、損失や安全性を断定する表現がないか

修正ルール:
- 実績が不明な場合は「架空例」「シミュレーション」「例」と明記する
- 収益は保証せず「目指す」「可能性がある」「一例」などに弱める
- 本人の実体験に見える表現は、一般的な悩み・読者視点の表現に変える
- 「〇〇法」のような未完成表現は、具体的な手順名や自然な説明に変える
- 「リスクが少ない」「安全」などの断定は、「小さく試しやすい」「確認しながら進めやすい」などに弱める
- 投稿として使いやすい自然な文章にする

出力形式:
1. 危ない可能性がある表現
2. 修正理由
3. 安全に直した投稿文
4. 投稿前の注意点

投稿文:
{post_text}
""".strip()

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "あなたはSNS投稿の表現チェックと安全なリライトの専門家です。"},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content or ""


def save_safety_checked_post(post_text: str) -> Path:
    """安全チェック済み投稿を保存する。"""
    save_dir = Path("posts/safety_checked")
    save_dir.mkdir(parents=True, exist_ok=True)

    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = save_dir / f"{timestamp}_safety_checked.md"
    file_path.write_text(post_text, encoding="utf-8")
    return file_path


def save_final_post(title: str, platform: str, post_text: str) -> Path:
    """完成版投稿を投稿先ごとに保存する。"""
    save_dir = Path("posts/final_posts") / platform.lower()
    save_dir.mkdir(parents=True, exist_ok=True)

    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = title.strip().replace("/", "_").replace(" ", "_")[:30] or "final_post"
    file_path = save_dir / f"{timestamp}_{safe_title}.md"
    file_path.write_text(post_text, encoding="utf-8")
    return file_path

def save_scheduled_post(title: str, platform: str, status: str, post_text: str) -> Path:
    """投稿予定リストを保存する。"""
    save_dir = Path("posts/schedule")
    save_dir.mkdir(parents=True, exist_ok=True)

    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = title.strip().replace("/", "_").replace(" ", "_")[:30] or "scheduled_post"
    file_path = save_dir / f"{timestamp}_{status}_{platform}_{safe_title}.md"

    content = f"""
# 投稿予定

## 投稿名
{title}

## 投稿先
{platform}

## 状態
{status}

## 投稿本文
{post_text}
""".strip()
    file_path.write_text(content, encoding="utf-8")
    return file_path

def update_scheduled_post_status(file_path: Path, new_status: str) -> Path:
    """投稿予定の状態を更新する。"""
    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    for index, line in enumerate(lines):
        if line.strip() == "## 状態" and index + 1 < len(lines):
            lines[index + 1] = new_status
            break

    updated_content = "\n".join(lines).strip()
    file_path.write_text(updated_content, encoding="utf-8")
    return file_path

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
    st.header("🔥 今日やること")
    st.markdown(
        """
1. 📌 今日の投稿メニューを作成
2. 🧾 今日メニューから実投稿生成
3. 🛡 X投稿を安全チェック
4. 投稿する
5. 📈 投稿後の反応メモを保存
        """.strip()
    )

    st.divider()
    st.header("📌 今日の投稿メニュー")

    if st.button("今日の投稿メニューを作成"):
        with st.spinner("保存済みストックから今日の投稿メニューを作成中..."):
            stock_text = load_recent_stock()
            today_menu = create_today_post_menu(client, stock_text)
            saved_path = save_today_post_menu(today_menu)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": f"📌 今日の投稿メニュー\n\n{today_menu}\n\n保存先: {saved_path}",
            }
        )
        st.success("今日の投稿メニューを作成・保存しました")
        st.rerun()

    st.divider()
    st.header("📊 投稿ストック分析")

    if st.button("投稿ストックを分析"):
        with st.spinner("保存済みストックを分析中..."):
            stock_text = load_recent_stock(max_chars=9000)
            stock_analysis = create_stock_analysis(client, stock_text)
            saved_path = save_stock_analysis(stock_analysis)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": f"📊 投稿ストック分析\n\n{stock_analysis}\n\n保存先: {saved_path}",
            }
        )
        st.success("投稿ストック分析を作成・保存しました")
        st.rerun()

    st.divider()
    st.header("🗂 投稿ストック整理")

    exclude_keywords_text = st.text_area(
        "archive対象キーワード",
        key="exclude_keywords_text",
        height=120,
        placeholder="例：\n出産二次創作\n炎上\n著作権リスク\n性的",
        help="1行に1キーワード。ここに入れた言葉を含むストックをarchive対象にします。空欄のままならarchive移動は実行されません。",
    )

    exclude_keywords = [
        keyword.strip()
        for keyword in exclude_keywords_text.splitlines()
        if keyword.strip()
    ]

    if st.button("投稿ストック整理案を作成"):
        with st.spinner("保存済みストックを整理中..."):
            stock_text = load_recent_stock(max_chars=12000)
            cleanup_plan = create_stock_cleanup_plan(client, stock_text)
            saved_path = save_stock_cleanup_plan(cleanup_plan)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": f"🗂 投稿ストック整理案\n\n{cleanup_plan}\n\n保存先: {saved_path}",
            }
        )
        st.success("投稿ストック整理案を作成・保存しました")
        st.rerun()

    if st.button("リスク高めストックをarchiveへ移動"):
        if not exclude_keywords:
            st.warning("archive対象キーワードを1つ以上入力してください。")
        else:
            with st.spinner("除外対象ストックをarchiveへ移動中..."):
                moved_files = archive_excluded_stock(exclude_keywords)

            if moved_files:
                moved_text = "\n".join(moved_files)
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": f"🧹 archiveへ移動したストック\n\n{moved_text}",
                    }
                )
                st.success(f"{len(moved_files)}件をarchiveへ移動しました")
            else:
                st.info("archiveへ移動するストックはありませんでした")

            st.rerun()


    st.divider()
    st.header("🧾 今日メニューから実投稿生成")

    today_menu_post_source = st.text_area(
        "今日の投稿メニューを貼る",
        placeholder="ここに今日の投稿メニューの内容を貼る",
        key="today_menu_post_source",
        height=180,
    )

    if st.button("今日メニューから実投稿セットを作成"):
        if not today_menu_post_source.strip():
            st.warning("今日の投稿メニューを入力してください。")
        else:
            with st.spinner("今日の投稿メニューから実投稿セットを作成中..."):
                today_menu_posts = create_posts_from_today_menu(
                    client,
                    today_menu_post_source.strip(),
                )
                saved_path = save_today_menu_posts(today_menu_posts)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"🧾 今日メニューから作成した実投稿セット\n\n{today_menu_posts}\n\n保存先: {saved_path}",
                }
            )
            st.success("今日メニューから実投稿セットを作成・保存しました")
            st.rerun()

    st.divider()
    st.header("📊 分析から実投稿生成")

    stock_analysis_post_source = st.text_area(
        "投稿ストック分析を貼る",
        placeholder="ここに投稿ストック分析の内容を貼る",
        key="stock_analysis_post_source",
        height=180,
    )

    if st.button("分析から実投稿セットを作成"):
        if not stock_analysis_post_source.strip():
            st.warning("投稿ストック分析を入力してください。")
        else:
            with st.spinner("投稿ストック分析から実投稿セットを作成中..."):
                stock_analysis_posts = create_posts_from_stock_analysis(
                    client,
                    stock_analysis_post_source.strip(),
                )
                saved_path = save_stock_analysis_posts(stock_analysis_posts)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"📊 分析から作成した実投稿セット\n\n{stock_analysis_posts}\n\n保存先: {saved_path}",
                }
            )
            st.success("分析から実投稿セットを作成・保存しました")
            st.rerun()

    st.divider()
    st.header("🛡 投稿安全チェック")

    safety_check_source = st.text_area(
        "安全チェックしたい投稿を貼る",
        placeholder="ここにX投稿・Instagramキャプション・note導入文などを貼る",
        key="safety_check_source",
        height=180,
    )

    if st.button("投稿を安全チェックして修正"):
        if not safety_check_source.strip():
            st.warning("安全チェックしたい投稿を入力してください。")
        else:
            with st.spinner("投稿の危ない表現を確認・修正中..."):
                safety_checked_post = check_and_rewrite_post_safety(
                    client,
                    safety_check_source.strip(),
                )
                saved_path = save_safety_checked_post(safety_checked_post)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"🛡 投稿安全チェック結果\n\n{safety_checked_post}\n\n保存先: {saved_path}",
                }
            )
            st.success("投稿を安全チェック・保存しました")
            st.rerun()

        st.divider()
    st.header("✅ 完成版投稿を保存")
    final_post_title = st.text_input(
        "完成版投稿名",
        placeholder="例: 投稿ネタ3つの解決法",
        key="final_post_title",
    )
    final_post_platform = st.selectbox(
        "完成版投稿先",
        ["X", "Instagram", "Threads", "note", "その他"],
        key="final_post_platform",
    )
    final_post_body = st.text_area(
        "完成版投稿本文",
        height=180,
        placeholder="安全チェック後の完成版投稿を貼る",
        key="final_post_body",
    )
    if st.button("完成版投稿を保存", key="save_final_post_button"):
        if not final_post_title.strip():
            st.warning("完成版投稿名を入力してください。")
        elif not final_post_body.strip():
            st.warning("完成版投稿本文を入力してください。")
        else:
            saved_path = save_final_post(
                final_post_title.strip(),
                final_post_platform,
                final_post_body.strip(),
            )
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"✅ 完成版投稿を保存しました\n\n保存先: {saved_path}",
                }
            )
            st.success("完成版投稿を保存しました")
            st.rerun()

    st.divider()
    st.header("📅 投稿予定リスト")
    scheduled_post_title = st.text_input(
        "投稿予定名",
        placeholder="例: 明日投稿するX投稿",
        key="scheduled_post_title",
    )
    scheduled_post_platform = st.selectbox(
        "投稿予定の投稿先",
        ["X", "Instagram", "Threads", "note", "その他"],
        key="scheduled_post_platform",
    )
    scheduled_post_status = st.selectbox(
        "投稿状態",
        ["今日投稿", "明日投稿", "保留", "投稿済み"],
        key="scheduled_post_status",
    )
    scheduled_post_body = st.text_area(
        "投稿予定本文",
        height=180,
        placeholder="完成版投稿や投稿予定の本文を貼る",
        key="scheduled_post_body",
    )
    if st.button("投稿予定に保存", key="save_scheduled_post_button"):
        if not scheduled_post_title.strip():
            st.warning("投稿予定名を入力してください。")
        elif not scheduled_post_body.strip():
            st.warning("投稿予定本文を入力してください。")
        else:
            saved_path = save_scheduled_post(
                scheduled_post_title.strip(),
                scheduled_post_platform,
                scheduled_post_status,
                scheduled_post_body.strip(),
            )
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"📅 投稿予定に保存しました\n\n保存先: {saved_path}",
                }
            )
            st.success("投稿予定に保存しました")
            st.rerun()

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
    st.header("📅 投稿カレンダー生成")

    calendar_platform = st.selectbox(
        "投稿カレンダーの投稿先",
        ["X", "Instagram", "note", "TikTok", "YouTube Shorts"],
        key="calendar_platform",
    )

    calendar_theme = st.text_input(
        "投稿カレンダーのテーマ",
        placeholder="例: AI副業初心者向け",
        key="calendar_theme",
    )

    if st.button("7日分投稿カレンダーを作成"):
        if not calendar_theme.strip():
            st.warning("投稿カレンダーのテーマを入力してください。")
        else:
            with st.spinner("7日分投稿カレンダーを作成中..."):
                post_calendar = create_post_calendar(
                    client,
                    calendar_theme.strip(),
                    calendar_platform,
                )
                saved_path = save_post_calendar(
                    calendar_theme.strip(),
                    calendar_platform,
                    post_calendar,
                )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"📅 7日分投稿カレンダー\n\n{post_calendar}\n\n保存先: {saved_path}",
                }
            )
            st.success("7日分投稿カレンダーを作成・保存しました")
            st.rerun()

    sales_funnel_calendar_source = st.text_area(
        "販売導線まとめから7日分カレンダーを作る",
        placeholder="ここに販売導線まとめストックの内容を貼る",
        key="sales_funnel_calendar_source",
        height=180,
    )

    if st.button("販売導線から7日分カレンダーを作成"):
        if not sales_funnel_calendar_source.strip():
            st.warning("販売導線まとめを入力してください。")
        else:
            with st.spinner("販売導線から7日分投稿カレンダーを作成中..."):
                sales_calendar = create_sales_funnel_calendar(
                    client,
                    sales_funnel_calendar_source.strip(),
                    calendar_platform,
                )
                saved_path = save_sales_funnel_calendar(
                    calendar_platform,
                    sales_calendar,
                )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"🚀 販売導線から作成した7日分投稿カレンダー\n\n{sales_calendar}\n\n保存先: {saved_path}",
                }
            )
            st.success("販売導線から7日分投稿カレンダーを作成・保存しました")
            st.rerun()

    weekly_posts_source = st.text_area(
        "実投稿に変換したい投稿カレンダー",
        placeholder="ここに作成済みの7日分投稿カレンダーを貼る",
        key="weekly_posts_source",
        height=180,
    )

    if st.button("7日分の実投稿を作成"):
        if not weekly_posts_source.strip():
            st.warning("実投稿に変換したい投稿カレンダーを入力してください。")
        else:
            with st.spinner("7日分の実投稿を作成中..."):
                weekly_posts = create_weekly_posts(
                    client,
                    weekly_posts_source.strip(),
                    calendar_platform,
                )
                saved_path = save_weekly_posts(
                    calendar_theme.strip() or "投稿カレンダー",
                    calendar_platform,
                    weekly_posts,
                )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"📝 7日分実投稿\n\n{weekly_posts}\n\n保存先: {saved_path}",
                }
            )
            st.success("7日分の実投稿を作成・保存しました")
            st.rerun()

        st.divider()
    st.header("🧩 投稿テンプレ生成")

    template_post_platform = st.selectbox(
        "テンプレ投稿の投稿先",
        ["X", "Instagram", "note", "TikTok", "YouTube Shorts"],
        key="template_post_platform",
    )

    template_type = st.selectbox(
        "投稿テンプレート",
        ["保存されやすい型", "共感型", "無料特典誘導型", "有料note誘導型"],
        key="template_type",
    )

    template_post_theme = st.text_input(
        "テンプレ投稿のテーマ",
        placeholder="例: AI副業で最初にやること",
        key="template_post_theme",
    )

    if st.button("テンプレ投稿を作成"):
        if not template_post_theme.strip():
            st.warning("テンプレ投稿のテーマを入力してください。")
        else:
            with st.spinner("テンプレ投稿を作成中..."):
                template_post = create_template_post(
                    client,
                    template_post_theme.strip(),
                    template_post_platform,
                    template_type,
                )
                saved_path = save_template_post(
                    template_post_theme.strip(),
                    template_post_platform,
                    template_type,
                    template_post,
                )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"🧩 テンプレ投稿\n\n{template_post}\n\n保存先: {saved_path}",
                }
            )
            st.success("テンプレ投稿を作成・保存しました")
            st.rerun()

    st.divider()
    st.header("📈 投稿後の反応メモ")

    post_result_title = st.text_input(
        "投稿名・テーマ",
        placeholder="例: AI副業初心者向け X投稿 Day1",
        key="post_result_title",
    )

    post_result_platform = st.selectbox(
        "投稿先",
        ["X", "Instagram", "Threads", "note", "その他"],
        key="post_result_platform",
    )

    post_result_impressions = st.number_input(
        "インプレッション",
        min_value=0,
        step=1,
        key="post_result_impressions",
    )
    post_result_likes = st.number_input(
        "いいね数",
        min_value=0,
        step=1,
        key="post_result_likes",
    )
    post_result_comments = st.number_input(
        "コメント数",
        min_value=0,
        step=1,
        key="post_result_comments",
    )
    post_result_saves = st.number_input(
        "保存数",
        min_value=0,
        step=1,
        key="post_result_saves",
    )
    post_result_profile_clicks = st.number_input(
        "プロフィールクリック数",
        min_value=0,
        step=1,
        key="post_result_profile_clicks",
    )
    post_result_link_clicks = st.number_input(
        "リンククリック数",
        min_value=0,
        step=1,
        key="post_result_link_clicks",
    )

    post_result_memo = st.text_area(
        "投稿後の反応メモ",
        placeholder="例:\nいいね: 12\n保存: 3\nクリック: 1\n反応が良かった点: 冒頭の悩み訴求\n次に改善する点: CTAをもっと具体的にする",
        key="post_result_memo",
        height=160,
    )

    if st.button("投稿反応メモを保存"):
        if not post_result_memo.strip():
            st.warning("投稿後の反応メモを入力してください。")
        else:
            saved_path = save_post_result_memo(
                post_result_title.strip(),
                post_result_platform,
                post_result_memo.strip(),
                int(post_result_impressions),
                int(post_result_likes),
                int(post_result_comments),
                int(post_result_saves),
                int(post_result_profile_clicks),
                int(post_result_link_clicks),
            )
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"📈 投稿反応メモを保存しました\n\n保存先: {saved_path}",
                }
            )
            st.success("投稿反応メモを保存しました")
            st.rerun()

    if st.button("投稿反応ランキングを表示", key="show_post_result_ranking_button"):
        ranking_text = create_post_result_ranking()
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": ranking_text,
            }
        )
        st.rerun()

    if st.button("投稿反応から改善案を作成", key="create_post_result_insight_button"):
        with st.spinner("投稿反応メモから改善案を作成中..."):
            insight_text = create_post_result_insight(client)
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": f"📊 投稿反応から作成した改善案\n\n{insight_text}",
            }
        )
        st.rerun()

    if st.button("投稿反応から次の投稿を作成", key="create_next_posts_from_result_button"):
        with st.spinner("投稿反応メモから次の投稿案を作成中..."):
            next_posts_text = create_next_posts_from_result(client)
            saved_path = save_next_posts_from_result(next_posts_text)
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": f"📝 投稿反応から作成した次の投稿案\n\n{next_posts_text}\n\n保存先: {saved_path}",
            }
        )
        st.success("投稿反応から次の投稿案を作成・保存しました")
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
                saved_path = save_reviewed_post(
                    platform,
                    review_text.strip(),
                    improved_post,
                )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"✨ 投稿改善結果\n\n{improved_post}\n\n保存先: {saved_path}",
                }
            )
            st.success("投稿の改善と保存が完了しました")
            st.rerun()

    if st.button("収益導線を作成"):
        if not review_text.strip():
            st.warning("収益導線を作りたい投稿を入力してください。")
        else:
            with st.spinner("収益導線を作成中..."):
                monetization_plan = create_monetization_plan(
                    client,
                    review_text.strip(),
                    platform,
                )
                saved_path = save_monetization_plan(
                    platform,
                    review_text.strip(),
                    monetization_plan,
                )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"💰 収益導線案\n\n{monetization_plan}\n\n保存先: {saved_path}",
                }
            )
            st.success("収益導線を作成・保存しました")
            st.rerun()

    if st.button("有料note構成を作成"):
        if not review_text.strip():
            st.warning("有料note構成を作りたい投稿を入力してください。")
        else:
            with st.spinner("有料note構成を作成中..."):
                paid_note_outline = create_paid_note_outline(
                    client,
                    review_text.strip(),
                    platform,
                )
                saved_path = save_paid_note_outline(
                    platform,
                    review_text.strip(),
                    paid_note_outline,
                )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"📝 有料note構成案\n\n{paid_note_outline}\n\n保存先: {saved_path}",
                }
            )
            st.success("有料note構成を作成・保存しました")
            st.rerun()

    if st.button("有料note本文を作成"):
        if not review_text.strip():
            st.warning("有料note本文を作りたい構成案やテーマを入力してください。")
        else:
            with st.spinner("有料note本文を作成中..."):
                paid_note_draft = create_paid_note_draft(
                    client,
                    review_text.strip(),
                )
                saved_path = save_paid_note_draft(
                    platform,
                    paid_note_draft,
                )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"📝 有料note本文ドラフト\n\n{paid_note_draft}\n\n保存先: {saved_path}",
                }
            )
            st.success("有料note本文を作成・保存しました")
            st.rerun()

    if st.button("無料特典を作成"):
        if not review_text.strip():
            st.warning("無料特典を作りたい投稿やテーマを入力してください。")
        else:
            with st.spinner("無料特典を作成中..."):
                freebie_text = create_freebie(
                    client,
                    review_text.strip(),
                    platform,
                )
                saved_path = save_freebie(
                    review_text.strip()[:40],
                    platform,
                    freebie_text,
                )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"🎁 無料特典案\n\n{freebie_text}\n\n保存先: {saved_path}",
                }
            )
            st.success("無料特典を作成・保存しました")
            st.rerun()

    if st.button("販売導線をまとめて作成"):
        if not review_text.strip():
            st.warning("販売導線を作りたい投稿を入力してください。")
        else:
            with st.spinner("販売導線をまとめて作成中..."):
                improved_post = improve_post(client, review_text.strip(), platform)
                reviewed_path = save_reviewed_post(
                    platform,
                    review_text.strip(),
                    improved_post,
                )

                monetization_plan = create_monetization_plan(
                    client,
                    improved_post,
                    platform,
                )
                monetization_path = save_monetization_plan(
                    platform,
                    improved_post,
                    monetization_plan,
                )

                paid_note_outline = create_paid_note_outline(
                    client,
                    improved_post,
                    platform,
                )
                paid_note_outline_path = save_paid_note_outline(
                    platform,
                    improved_post,
                    paid_note_outline,
                )

                freebie_text = create_freebie(
                    client,
                    improved_post,
                    platform,
                )
                freebie_path = save_freebie(
                    "sales_funnel",
                    platform,
                    freebie_text,
                )

                paid_note_draft = create_paid_note_draft(
                    client,
                    paid_note_outline,
                )
                paid_note_draft_path = save_paid_note_draft(
                    platform,
                    paid_note_draft,
                )

                sales_funnel_path = save_sales_funnel(
                    platform,
                    improved_post,
                    monetization_plan,
                    paid_note_outline,
                    freebie_text,
                    paid_note_draft,
                )

            funnel_result = f"""
🚀 販売導線まとめ

## 1. 改善後の投稿
{improved_post}

保存先: {reviewed_path}

---

## 2. 収益導線案
{monetization_plan}

保存先: {monetization_path}

---

## 3. 有料note構成案
{paid_note_outline}

保存先: {paid_note_outline_path}

---

## 4. 無料特典案
{freebie_text}

保存先: {freebie_path}

---

## 5. 有料note本文ドラフト
{paid_note_draft}

保存先: {paid_note_draft_path}

---

## まとめファイル
保存先: {sales_funnel_path}
""".strip()

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": funnel_result,
                }
            )
            st.success("販売導線一式を作成・保存しました")
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