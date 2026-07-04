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

if "template_post_theme" not in st.session_state:
    st.session_state.template_post_theme = ""

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
    stock_analysis_files = sorted(Path("posts/stock_analysis").glob("*.md"), reverse=True)
    freebie_files = sorted(Path("posts/freebies").glob("*.md"), reverse=True)
    paid_note_draft_files = sorted(Path("posts/paid_note_drafts").glob("*.md"), reverse=True)
    sales_funnel_files = sorted(Path("posts/sales_funnels").glob("*.md"), reverse=True)
    stock_cleanup_files = sorted(Path("posts/stock_cleanup").glob("*.md"), reverse=True)
    post_result_files = sorted(Path("posts/results").glob("*.md"), reverse=True)
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
        f"投稿ストック分析: {len(stock_analysis_files)}件 / "
        f"無料特典: {len(freebie_files)}件 / "
        f"有料note本文: {len(paid_note_draft_files)}件 / "
        f"販売導線まとめ: {len(sales_funnel_files)}件 / "
        f"投稿ストック整理案: {len(stock_cleanup_files)}件 / "
        f"投稿反応メモ: {len(post_result_files)}件 / "
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
        + stock_analysis_files
        + freebie_files
        + paid_note_draft_files
        + sales_funnel_files
        + stock_cleanup_files
        + post_result_files
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
            st.download_button(
                "📈 投稿反応メモをダウンロード",
                data=content,
                file_name=file_path.name,
                mime="text/markdown",
                key=f"download_post_result_{file_path.name}",
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


def save_post_result_memo(title: str, platform: str, memo: str) -> Path:
    """投稿後の反応メモを保存する。"""
    save_dir = Path("posts/results")
    save_dir.mkdir(parents=True, exist_ok=True)

    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = title.strip().replace("/", "_").replace(" ", "_")[:30] or "post_result"
    file_path = save_dir / f"{timestamp}_{platform}_{safe_title}.md"
    content = f"""
# 投稿反応メモ

## 投稿名
{title}

## 投稿先
{platform}

## 反応メモ
{memo}
""".strip()
    file_path.write_text(content, encoding="utf-8")
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
                post_result_title.strip() or "投稿反応メモ",
                calendar_platform if "calendar_platform" in st.session_state else "SNS",
                post_result_memo.strip(),
            )
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"📈 投稿反応メモを保存しました\n\n保存先: {saved_path}",
                }
            )
            st.success("投稿反応メモを保存しました")
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