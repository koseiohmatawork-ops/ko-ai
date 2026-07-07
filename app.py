import io
import zipfile
from datetime import datetime

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

def simple_extract_field(content: str, field_name: str) -> str:
    marker = f"## {field_name}"
    if marker not in content:
        return ""
    value = content.split(marker, 1)[1].strip()
    if "\n## " in value:
        value = value.split("\n## ", 1)[0].strip()
    return value.strip()


def simple_clean_post_body(body: str) -> str:
    """コピー欄に不要な区切り線や空見出しを出さないように整える。"""
    cleaned_lines = []
    for line in body.strip().splitlines():
        stripped_line = line.strip()
        if stripped_line in ["---", "###", "##", "#"]:
            continue
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def simple_extract_post_body(content: str) -> str:
    """投稿予定や完成版投稿から、実際にコピーする投稿本文だけを取り出す。"""
    # 投稿予定の中に完成版投稿が丸ごと入っている場合は、
    # 「## 投稿本文」が複数回出るため、最後の「## 投稿本文」以降を使う。
    if content.count("## 投稿本文") >= 2:
        return simple_clean_post_body(content.split("## 投稿本文")[-1].strip())

    body = simple_extract_field(content, "投稿本文") or content.strip()

    # 念のため、本文の中に完成版投稿のメタ情報が残っていた場合も最後の本文だけを使う。
    if "## 投稿本文" in body:
        body = body.split("## 投稿本文")[-1].strip()

    # それでも完成版投稿の見出しだけが残る場合は、コピー欄には出さない。
    if body.strip() == "# 完成版投稿":
        return ""

    return simple_clean_post_body(body)


def simple_file_label(file_path: Path) -> str:
    """画面用に長い保存ファイル名を短く表示する。"""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        content = ""

    platform = simple_extract_field(content, "投稿先").strip()
    lower_path = str(file_path).lower()

    if platform.lower() == "x":
        platform = "X"
    elif platform.lower() == "instagram":
        platform = "Instagram"
    elif platform.lower() == "threads":
        platform = "Threads"
    elif platform.lower() == "note":
        platform = "note"
    elif not platform:
        if "/instagram/" in lower_path or "instagram" in lower_path:
            platform = "Instagram"
        elif "/x/" in lower_path or "_x_" in lower_path:
            platform = "X"
        elif "threads" in lower_path:
            platform = "Threads"
        elif "note" in lower_path:
            platform = "note"
        else:
            platform = "投稿"

    body = simple_extract_post_body(content)
    body_lines = [line.strip() for line in body.splitlines() if line.strip()]
    body_first_line = body_lines[0] if body_lines else ""

    title = simple_extract_field(content, "投稿名").strip()

    # 投稿名が保存ファイル名っぽい場合は使わず、投稿本文の1行目を表示名にする。
    title_looks_like_filename = (
        len(title) > 28
        or title.count("_") >= 2
        or sum(char.isdigit() for char in title) >= 8
    )

    if not title or title_looks_like_filename:
        title = body_first_line or file_path.stem

    title = title.replace("#", "").replace("##", "").strip()
    title = title[:24] + "..." if len(title) > 24 else title

    return f"{platform} / {title}"


def simple_file_options(file_paths: list[Path]) -> dict[str, Path]:
    """selectbox用に、短くて重複しない表示名を作る。"""
    options: dict[str, Path] = {}
    counts: dict[str, int] = {}

    for file_path in file_paths:
        base_label = simple_file_label(file_path)
        counts[base_label] = counts.get(base_label, 0) + 1

        if counts[base_label] == 1:
            label = base_label
        else:
            label = f"{base_label} ({counts[base_label]})"

        options[label] = file_path

    return options


def simple_clear_all_post_stocks() -> int:
    """シンプル管理画面用。posts配下の投稿ストックファイルを削除する。"""
    posts_dir = Path("posts")
    if not posts_dir.exists():
        return 0

    deleted_count = 0
    for file_path in posts_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix in [".md", ".txt"]:
            file_path.unlink()
            deleted_count += 1

    return deleted_count


def simple_delete_files(file_paths: list[Path]) -> int:
    """指定された投稿ストックファイルだけを削除する。"""
    deleted_count = 0
    for file_path in file_paths:
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            deleted_count += 1
    return deleted_count

def simple_create_test_today_post() -> Path:
    """シンプル画面の動作確認用に、今日投稿を1件作る。"""
    schedule_dir = Path("posts/schedule")
    schedule_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = schedule_dir / f"{timestamp}_X_simple_test_post.md"

    output = f"""
# 投稿予定

## 投稿名
シンプル動作確認用テスト投稿

## 投稿先
X

## 状態
今日投稿

## 元ファイル
管理画面で作成

## 投稿本文
📘 テスト投稿です。

Ko AIのシンプル画面で、今日投稿 → 投稿済み → 反応メモ作成 → 次投稿作成まで確認するための投稿です。

この投稿は実際には投稿せず、動作確認が終わったら管理画面から削除してください。

## 作成日時
{timestamp}
""".strip()

    save_path.write_text(output, encoding="utf-8")
    return save_path

def simple_run_post_flow_self_check() -> list[tuple[str, bool, str]]:
    """シンプル画面の投稿作成フローが壊れていないか確認する。"""
    result_dir = Path("posts/result_next_posts")
    result_dir.mkdir(parents=True, exist_ok=True)

    test_source_path = result_dir / "__simple_self_check_result_next_post.md"
    test_source_path.write_text(
        """
# 反応ベース次投稿案

## 元の反応メモファイル
posts/results/__simple_self_check.md

## 次投稿案

X投稿案
これはX用の自動チェック投稿です。

Instagram投稿案
これはInstagram用の自動チェック投稿です。

投稿前の注意点
これは完成版には混ざってほしくない注意点です。
""".strip(),
        encoding="utf-8",
    )

    created_paths: list[Path] = []
    results: list[tuple[str, bool, str]] = []

    try:
        x_final_path = simple_save_final_post_from_result_next_post(test_source_path, "X")
        instagram_final_path = simple_save_final_post_from_result_next_post(test_source_path, "Instagram")
        created_paths.extend([x_final_path, instagram_final_path])

        x_schedule_path = simple_save_scheduled_post_from_final_post(x_final_path, "今日投稿")
        instagram_schedule_path = simple_save_scheduled_post_from_final_post(instagram_final_path, "今日投稿")
        created_paths.extend([x_schedule_path, instagram_schedule_path])

        x_final_content = x_final_path.read_text(encoding="utf-8")
        instagram_final_content = instagram_final_path.read_text(encoding="utf-8")
        x_schedule_content = x_schedule_path.read_text(encoding="utf-8")
        instagram_schedule_content = instagram_schedule_path.read_text(encoding="utf-8")

        results.append(("X完成版ファイル作成", x_final_path.exists(), str(x_final_path)))
        results.append(("Instagram完成版ファイル作成", instagram_final_path.exists(), str(instagram_final_path)))
        results.append(("X本文切り出し", "これはX用の自動チェック投稿です。" in x_final_content, "X本文が入っているか"))
        results.append(("Instagram本文切り出し", "これはInstagram用の自動チェック投稿です。" in instagram_final_content, "Instagram本文が入っているか"))
        results.append(("XにInstagram本文が混ざっていない", "これはInstagram用の自動チェック投稿です。" not in x_final_content, "X本文にInstagramが混ざっていないか"))
        results.append(("InstagramにX本文が混ざっていない", "これはX用の自動チェック投稿です。" not in instagram_final_content, "Instagram本文にXが混ざっていないか"))
        results.append(("注意点が完成版に混ざっていない", "投稿前の注意点" not in x_final_content and "投稿前の注意点" not in instagram_final_content, "注意点が混ざっていないか"))
        results.append(("X今日投稿ファイル作成", x_schedule_path.exists() and "## 状態\n今日投稿" in x_schedule_content, str(x_schedule_path)))
        results.append(("Instagram今日投稿ファイル作成", instagram_schedule_path.exists() and "## 状態\n今日投稿" in instagram_schedule_content, str(instagram_schedule_path)))
    finally:
        if test_source_path.exists():
            test_source_path.unlink()
        for created_path in created_paths:
            if created_path.exists():
                created_path.unlink()

    return results

def simple_cleanup_today_posts_keep_latest_by_platform() -> tuple[int, list[Path]]:
    """今日投稿を投稿先ごとに最新1件だけ残して整理する。"""
    today_posts_by_platform: dict[str, list[Path]] = {}

    for file_path in sorted(Path("posts/schedule").glob("*.md"), reverse=True):
        content = file_path.read_text(encoding="utf-8")
        status = simple_extract_field(content, "状態")
        if status != "今日投稿":
            continue

        platform = simple_extract_field(content, "投稿先") or "投稿"
        today_posts_by_platform.setdefault(platform, []).append(file_path)

    deleted_paths: list[Path] = []
    for files in today_posts_by_platform.values():
        files_to_delete = files[1:]
        for file_path in files_to_delete:
            if file_path.exists():
                file_path.unlink()
                deleted_paths.append(file_path)

    return len(deleted_paths), deleted_paths

def simple_render_admin() -> None:
    """シンプル管理画面。普段使う最低限の管理だけ置く。"""
    st.subheader("⚙️ 管理")
    st.caption("テストデータを消したい時だけ使います。")

    stock_counts = {
        "投稿予定": len(list(Path("posts/schedule").glob("*.md"))),
        "完成版投稿": len(list(Path("posts/final_posts").glob("**/*.md"))),
        "反応メモ": len(list(Path("posts/results").glob("*.md"))),
        "反応ベース次投稿": len(list(Path("posts/result_next_posts").glob("*.md"))),
        "X投稿": len(list(Path("posts/x").glob("*.txt"))),
        "Instagram投稿": len(list(Path("posts/instagram").glob("*.md"))),
        "note記事": len(list(Path("posts/note").glob("*.md"))),
        "アイデア": len(list(Path("posts/ideas").glob("*.txt"))),
    }
    total_count = sum(stock_counts.values())

    st.markdown("**現在のストック件数**")
    count_col1, count_col2 = st.columns(2)
    stock_items = list(stock_counts.items())

    with count_col1:
        for label, count in stock_items[:4]:
            st.write(f"{label}: {count}件")

    with count_col2:
        for label, count in stock_items[4:]:
            st.write(f"{label}: {count}件")

    st.caption(f"合計: {total_count}件")

    with st.expander("🧪 投稿作成フローを確認", expanded=False):
        st.caption("反応ベース次投稿 → 完成版 → 今日投稿 の流れが壊れていないか確認します。")
        if st.button("🧪 動作チェックする", key="simple_post_flow_self_check"):
            check_results = simple_run_post_flow_self_check()
            failed_results = [result for result in check_results if not result[1]]

            for label, is_success, detail in check_results:
                if is_success:
                    st.success(f"✅ {label}: OK")
                else:
                    st.error(f"❌ {label}: NG（{detail}）")

            if failed_results:
                st.error("投稿作成フローに問題があります。NG項目を確認してください。")
            else:
                st.success("投稿作成フローは正常です。")

    with st.expander("🧪 テスト投稿を作る", expanded=False):
        st.caption("ゼロから一周テストしたい時だけ使います。今日投稿にテスト投稿を1件追加します。")
        if st.button("🧪 今日投稿のテスト投稿を作成", key="simple_create_test_today_post"):
            saved_path = simple_create_test_today_post()
            st.session_state.go_to_today_posts = True
            simple_set_execution_result("テスト投稿を作成しました。", [saved_path])
            st.rerun()

    with st.expander("🧹 今日投稿を整理", expanded=False):
        st.caption("投稿先ごとに最新1件だけ残して、増えすぎた今日投稿を削除します。")
        confirm_cleanup_today = st.checkbox(
            "今日投稿を整理することを確認しました",
            key="simple_confirm_cleanup_today_posts",
        )
        if st.button(
            "🧹 今日投稿を整理する",
            disabled=not confirm_cleanup_today,
            key="simple_cleanup_today_posts",
        ):
            deleted_count, deleted_paths = simple_cleanup_today_posts_keep_latest_by_platform()
            st.session_state.go_to_today_posts = True
            simple_set_execution_result(
                f"今日投稿を整理しました。{deleted_count}件削除しました。",
                deleted_paths,
            )
            st.rerun()

    stock_file_groups = {
        "投稿予定": list(Path("posts/schedule").glob("*.md")),
        "完成版投稿": list(Path("posts/final_posts").glob("**/*.md")),
        "反応メモ": list(Path("posts/results").glob("*.md")),
        "反応ベース次投稿": list(Path("posts/result_next_posts").glob("*.md")),
        "X投稿": list(Path("posts/x").glob("*.txt")),
        "Instagram投稿": list(Path("posts/instagram").glob("*.md")),
        "note記事": list(Path("posts/note").glob("*.md")),
        "アイデア": list(Path("posts/ideas").glob("*.txt")),
    }

    with st.expander("🧹 カテゴリ別に削除", expanded=False):
        delete_category = st.selectbox(
            "削除するカテゴリ",
            list(stock_file_groups.keys()),
            key="simple_delete_category",
        )
        delete_targets = stock_file_groups[delete_category]
        st.warning(f"{delete_category} のストック {len(delete_targets)}件を削除します。")
        confirm_category_delete = st.checkbox(
            f"{delete_category} を削除することを確認しました",
            key="simple_confirm_category_delete",
        )
        if st.button(
            f"🗑 {delete_category}を削除",
            disabled=not confirm_category_delete or not delete_targets,
            key="simple_delete_category_button",
        ):
            deleted_count = simple_delete_files(delete_targets)
            simple_set_execution_result(f"{delete_category}を{deleted_count}件削除しました。")
            st.rerun()

    with st.expander("🧹 全ストック削除", expanded=False):
        st.warning("posts配下の投稿ストックファイル（.md / .txt）を全部削除します。")
        confirm_clear = st.checkbox(
            "全ストックを削除することを確認しました",
            key="simple_confirm_clear_all_stocks",
        )
        if st.button("🧹 全ストックを削除", disabled=not confirm_clear, key="simple_clear_all_stocks"):
            deleted_count = simple_clear_all_post_stocks()
            simple_set_execution_result(f"{deleted_count}件のストックファイルを削除しました。")
            st.rerun()


def simple_update_schedule_status(file_path: Path, new_status: str) -> None:
    content = file_path.read_text(encoding="utf-8")
    if "## 状態" in content:
        before_status, after_status = content.split("## 状態", 1)
        lines = after_status.splitlines()
        if lines:
            lines[0] = ""
        if len(lines) >= 2:
            lines[1] = new_status
        else:
            lines.append(new_status)
        new_content = before_status + "## 状態" + "\n".join(lines)
    else:
        new_content = content + f"\n\n## 状態\n{new_status}"
    file_path.write_text(new_content, encoding="utf-8")


def simple_create_post_result_draft_from_schedule(file_path: Path) -> Path:
    """投稿予定から、投稿後の反応メモ下書きを作る。"""
    content = file_path.read_text(encoding="utf-8")
    title = simple_extract_field(content, "投稿名") or file_path.stem
    platform = simple_extract_field(content, "投稿先") or "X"
    body = simple_extract_post_body(content)

    results_dir = Path("posts/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    # 同じ投稿に対する反応メモがすでにある場合は、新規作成せず既存ファイルを使う。
    for existing_result_path in sorted(results_dir.glob("*.md"), reverse=True):
        existing_content = existing_result_path.read_text(encoding="utf-8")
        existing_source = simple_extract_field(existing_content, "元投稿")
        if existing_source == str(file_path):
            return existing_result_path

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = title.strip().replace("/", "_").replace(" ", "_")[:40] or "post_result"
    save_path = results_dir / f"{timestamp}_{platform}_{safe_title}.md"

    output = f"""
# 投稿反応メモ

## 投稿名
{title}

## 投稿先
{platform}

## 数字
- インプレッション: 0
- いいね: 0
- コメント: 0
- 保存: 0
- プロフィールクリック: 0
- リンククリック: 0

## 反応メモ
あとで実際の反応を入力する

## 元投稿
{file_path}

## 投稿本文
{body}

## 気づき

## 次に活かすこと
""".strip()

    save_path.write_text(output, encoding="utf-8")
    return save_path


def simple_extract_metric(content: str, metric_name: str) -> int:
    """反応メモの数字欄から数値を取り出す。"""
    marker = f"- {metric_name}:"
    for line in content.splitlines():
        if line.strip().startswith(marker):
            value_text = line.split(marker, 1)[1].strip()
            try:
                return int(value_text)
            except ValueError:
                return 0
    return 0


def simple_replace_markdown_section(content: str, section_name: str, new_body: str) -> str:
    """Markdownの指定セクションだけを置き換える。"""
    marker = f"## {section_name}"
    if marker not in content:
        return content + f"\n\n{marker}\n{new_body.strip()}"

    before, after = content.split(marker, 1)
    if "\n## " in after:
        current_section, rest = after.split("\n## ", 1)
        return before + marker + "\n" + new_body.strip() + "\n\n## " + rest.strip()

    return before + marker + "\n" + new_body.strip()


def simple_save_result_memo_edits(
    file_path: Path,
    impressions: int,
    likes: int,
    comments: int,
    saves: int,
    profile_clicks: int,
    link_clicks: int,
    memo: str,
) -> None:
    """反応メモの数字とメモ欄を保存する。"""
    content = file_path.read_text(encoding="utf-8")
    numbers_body = f"""
- インプレッション: {impressions}
- いいね: {likes}
- コメント: {comments}
- 保存: {saves}
- プロフィールクリック: {profile_clicks}
- リンククリック: {link_clicks}
""".strip()

    content = simple_replace_markdown_section(content, "数字", numbers_body)
    content = simple_replace_markdown_section(content, "反応メモ", memo.strip() or "あとで実際の反応を入力する")
    file_path.write_text(content, encoding="utf-8")


def simple_section_between(content: str, start_marker: str, end_markers: list[str]) -> str:
    """指定した見出し以降から、次の見出しの手前までを取り出す。"""
    if start_marker not in content:
        return ""

    section = content.split(start_marker, 1)[1].strip()
    end_positions = [section.find(end_marker) for end_marker in end_markers if end_marker in section]

    if end_positions:
        section = section[: min(end_positions)].strip()

    return simple_clean_post_body(section)


def simple_create_result_next_post_from_result_memo(file_path: Path) -> Path:
    """反応メモから次投稿案を作る。シンプル画面用。"""
    content = file_path.read_text(encoding="utf-8")
    result_dir = Path("posts/result_next_posts")
    result_dir.mkdir(parents=True, exist_ok=True)

    # 同じ反応メモから作った次投稿案がすでにある場合は、新規生成せず既存ファイルを使う。
    for existing_next_path in sorted(result_dir.glob("*.md"), reverse=True):
        existing_content = existing_next_path.read_text(encoding="utf-8")
        existing_source = simple_extract_field(existing_content, "元の反応メモファイル")
        if existing_source == str(file_path):
            return existing_next_path

    prompt = f"""
以下は投稿後の反応メモです。
この内容をもとに、次に投稿するための案を作ってください。

条件:
- 日本語
- 大学生が自然に書く感じ
- 煽りすぎない
- X投稿案とInstagram投稿案を分ける
- 投稿前の注意点も短く書く

反応メモ:
{content}
""".strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "あなたはSNS投稿改善に強い編集者です。"},
            {"role": "user", "content": prompt},
        ],
    )
    next_post = response.choices[0].message.content or ""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = file_path.stem.strip().replace("/", "_").replace(" ", "_")[:40] or "result_next_post"
    save_path = result_dir / f"{timestamp}_{safe_title}.md"

    output = f"""
# 反応ベース次投稿案

## 元の反応メモファイル
{file_path}

## 次投稿案
{next_post}
""".strip()

    save_path.write_text(output, encoding="utf-8")
    return save_path


def simple_save_final_post_from_result_next_post(file_path: Path, platform: str) -> Path:
    """反応ベース次投稿案から、指定プラットフォームの完成版投稿を作る。"""
    content = file_path.read_text(encoding="utf-8")
    save_dir = Path("posts/final_posts") / platform.lower()
    save_dir.mkdir(parents=True, exist_ok=True)

    if platform.lower() == "x":
        post_body = simple_section_between(content, "X投稿案", ["Instagram投稿案", "投稿前の注意点"])
    elif platform.lower() == "instagram":
        post_body = simple_section_between(content, "Instagram投稿案", ["投稿前の注意点"])
    else:
        post_body = simple_extract_post_body(content)

    if not post_body.strip():
        post_body = simple_extract_post_body(content)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = file_path.stem.strip().replace("/", "_").replace(" ", "_")[:40] or "final_post"
    save_path = save_dir / f"{timestamp}_{platform.lower()}_{safe_title}.md"

    output = f"""
# 完成版投稿

## 元ファイル
{file_path}

## 投稿先
{platform}

## 投稿本文
{post_body.strip()}
""".strip()

    save_path.write_text(output, encoding="utf-8")
    return save_path


def simple_save_scheduled_post_from_final_post(file_path: Path, status: str = "今日投稿") -> Path:
    """完成版投稿を投稿予定に追加する。"""
    content = file_path.read_text(encoding="utf-8")
    platform = simple_extract_field(content, "投稿先") or "X"
    post_body = simple_extract_post_body(content)

    schedule_dir = Path("posts/schedule")
    schedule_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = file_path.stem.strip().replace("/", "_").replace(" ", "_")[:40] or "scheduled_post"
    save_path = schedule_dir / f"{timestamp}_{platform}_{safe_title}.md"

    output = f"""
# 投稿予定

## 投稿名
{file_path.stem}

## 投稿先
{platform}

## 状態
{status}

## 元ファイル
{file_path}

## 投稿本文
{post_body}
""".strip()

    save_path.write_text(output, encoding="utf-8")
    return save_path


def simple_run_one_click_workflow() -> tuple[str, list[Path]]:
    """今ある素材から、次に進められるところまで自動で進める。"""
    created_paths: list[Path] = []

    reaction_memo_files = sorted(Path("posts/results").glob("*.md"), reverse=True)
    result_next_files = sorted(Path("posts/result_next_posts").glob("*.md"), reverse=True)
    final_post_files = sorted(Path("posts/final_posts").glob("**/*.md"), reverse=True)
    today_post_files = []

    for file_path in sorted(Path("posts/schedule").glob("*.md"), reverse=True):
        content = file_path.read_text(encoding="utf-8")
        if simple_extract_field(content, "状態") == "今日投稿":
            today_post_files.append(file_path)

    if today_post_files:
        return "すでに今日投稿があります。増やしすぎ防止のため、新しい今日投稿は作りませんでした。", today_post_files

    if reaction_memo_files:
        source_path = reaction_memo_files[0]
        next_post_path = simple_create_result_next_post_from_result_memo(source_path)
        x_final_path = simple_save_final_post_from_result_next_post(next_post_path, "X")
        instagram_final_path = simple_save_final_post_from_result_next_post(next_post_path, "Instagram")
        x_schedule_path = simple_save_scheduled_post_from_final_post(x_final_path, "今日投稿")
        instagram_schedule_path = simple_save_scheduled_post_from_final_post(instagram_final_path, "今日投稿")
        created_paths.extend([next_post_path, x_final_path, instagram_final_path, x_schedule_path, instagram_schedule_path])
        return "反応メモから、次投稿案・完成版・今日投稿まで一括作成しました。", created_paths

    if result_next_files:
        source_path = result_next_files[0]
        x_final_path = simple_save_final_post_from_result_next_post(source_path, "X")
        instagram_final_path = simple_save_final_post_from_result_next_post(source_path, "Instagram")
        x_schedule_path = simple_save_scheduled_post_from_final_post(x_final_path, "今日投稿")
        instagram_schedule_path = simple_save_scheduled_post_from_final_post(instagram_final_path, "今日投稿")
        created_paths.extend([x_final_path, instagram_final_path, x_schedule_path, instagram_schedule_path])
        return "反応ベース次投稿から、完成版・今日投稿まで一括作成しました。", created_paths

    if final_post_files:
        latest_by_platform: dict[str, Path] = {}
        for file_path in final_post_files:
            content = file_path.read_text(encoding="utf-8")
            platform = simple_extract_field(content, "投稿先") or "投稿"
            if platform not in latest_by_platform:
                latest_by_platform[platform] = file_path

        for file_path in latest_by_platform.values():
            created_paths.append(simple_save_scheduled_post_from_final_post(file_path, "今日投稿"))

        return "完成版投稿から、今日投稿に追加しました。", created_paths

    return "進められる素材がまだありません。まず投稿か反応メモを作ってください。", []


def simple_sidebar_status_counts() -> None:
    """左サイドバーに現在の投稿状態と簡易整理ボタンを表示する。"""
    today_count = 0
    posted_count = 0

    for file_path in Path("posts/schedule").glob("*.md"):
        content = file_path.read_text(encoding="utf-8")
        status = simple_extract_field(content, "状態")
        if status == "今日投稿":
            today_count += 1
        elif status == "投稿済み":
            posted_count += 1

    reaction_memo_count = len(list(Path("posts/results").glob("*.md")))
    result_next_count = len(list(Path("posts/result_next_posts").glob("*.md")))
    final_post_count = len(list(Path("posts/final_posts").glob("**/*.md")))

    st.markdown("### 現在の状態")
    st.caption(f"今日投稿: {today_count}件")
    st.caption(f"投稿済み: {posted_count}件")
    st.caption(f"反応メモ: {reaction_memo_count}件")
    st.caption(f"次投稿案: {result_next_count}件")
    st.caption(f"完成版: {final_post_count}件")

    if today_count > 2:
        st.warning("今日投稿が増えすぎています")
        if st.button("🧹 今日投稿を整理", key="simple_sidebar_cleanup_today_posts", use_container_width=True):
            deleted_count, deleted_paths = simple_cleanup_today_posts_keep_latest_by_platform()
            st.session_state.go_to_today_posts = True
            simple_set_execution_result(
                f"今日投稿を整理しました。{deleted_count}件削除しました。",
                deleted_paths,
            )
            st.rerun()


def simple_render_one_click_button() -> None:
    """左サイドバーに置くワンクリック実行ボタン。"""
    st.markdown("### 🚀 ワンクリック実行")
    st.caption("今ある素材から、作れるところまで自動で進めます。")

    if st.button("🚀 今日投稿まで作る", key="simple_one_click_workflow", use_container_width=True):
        message, created_paths = simple_run_one_click_workflow()
        st.session_state.go_to_today_posts = True
        simple_set_execution_result(message, created_paths)
        st.rerun()


def simple_set_execution_result(message: str, paths: list[Path] | None = None) -> None:
    """中央エリアに出す直近の実行結果を保存する。"""
    st.session_state.simple_execution_message = message
    st.session_state.simple_execution_paths = [str(path) for path in (paths or [])[:8]]


def simple_render_execution_result() -> None:
    """中央エリアに直近の実行結果を表示する。"""
    message = st.session_state.get("simple_execution_message", "")
    paths = st.session_state.get("simple_execution_paths", [])

    if not message:
        return

    with st.expander("✅ 直近の実行結果", expanded=True):
        st.success(message)
        for path_text in paths:
            st.caption(path_text)
        if st.button("実行結果を閉じる", key="simple_clear_execution_result"):
            st.session_state.simple_execution_message = ""
            st.session_state.simple_execution_paths = []
            st.rerun()


def simple_render_next_action_hint() -> None:
    """中央エリアに、今次に押すべき行動とボタンを表示する。"""
    today_count = 0
    posted_count = 0

    for file_path in Path("posts/schedule").glob("*.md"):
        content = file_path.read_text(encoding="utf-8")
        status = simple_extract_field(content, "状態")
        if status == "今日投稿":
            today_count += 1
        elif status == "投稿済み":
            posted_count += 1

    reaction_memo_count = len(list(Path("posts/results").glob("*.md")))
    result_next_count = len(list(Path("posts/result_next_posts").glob("*.md")))
    final_post_count = len(list(Path("posts/final_posts").glob("**/*.md")))

    with st.container(border=True):
        st.markdown("### 次にやること")

        if today_count > 2:
            st.warning("今日投稿が増えすぎています。まず整理した方がいいです。")
            if st.button("🧹 今日投稿を整理する", key="simple_center_cleanup_today_posts", use_container_width=True):
                deleted_count, deleted_paths = simple_cleanup_today_posts_keep_latest_by_platform()
                st.session_state.go_to_today_posts = True
                simple_set_execution_result(
                    f"今日投稿を整理しました。{deleted_count}件削除しました。",
                    deleted_paths,
                )
                st.rerun()
            return

        if today_count > 0:
            current_mode = st.session_state.get("simple_mode", "今日やる投稿")
            if current_mode == "今日やる投稿":
                st.info("下の投稿本文をコピーして投稿してください。投稿後は『投稿済みにして反応メモ下書きも作る』を押します。")
            else:
                st.info("今日やる投稿を開いて、投稿本文をコピーしてください。投稿後は『投稿済みにして反応メモ下書きも作る』を押します。")
                if st.button("📌 今日やる投稿を開く", key="simple_center_open_today_posts", use_container_width=True):
                    st.session_state.go_to_today_posts = True
                    st.rerun()
        elif reaction_memo_count > 0 or result_next_count > 0 or final_post_count > 0:
            st.info("今ある素材から今日投稿まで作れます。")
            if st.button("🚀 今日投稿まで作る", key="simple_center_one_click_workflow", use_container_width=True):
                message, created_paths = simple_run_one_click_workflow()
                st.session_state.go_to_today_posts = True
                simple_set_execution_result(message, created_paths)
                st.rerun()
        elif posted_count > 0:
            st.info("投稿済みの投稿から反応メモ下書きを作ってください。")
            if st.button("📦 投稿済みを開く", key="simple_center_open_posted_posts", use_container_width=True):
                st.session_state.go_to_today_posts = True
                st.session_state.open_posted_posts = True
                st.rerun()
        else:
            st.info("まだ素材が少ないです。まず一周テスト用の投稿を作れます。")
            if st.button("🧪 テスト投稿を作る", key="simple_center_create_test_today_post", use_container_width=True):
                saved_path = simple_create_test_today_post()
                st.session_state.go_to_today_posts = True
                simple_set_execution_result("テスト投稿を作成しました。", [saved_path])
                st.rerun()


def simple_render_today_posts() -> None:
    scheduled_files = sorted(Path("posts/schedule").glob("*.md"), reverse=True)

    groups = {
        "今日投稿": [],
        "明日投稿": [],
        "保留": [],
        "投稿済み": [],
    }

    for file_path in scheduled_files:
        content = file_path.read_text(encoding="utf-8")
        status = simple_extract_field(content, "状態") or "保留"
        if status in groups:
            groups[status].append(file_path)
        else:
            groups["保留"].append(file_path)

    st.subheader("📌 今日やる投稿")
    st.caption(
        f"今日投稿: {len(groups['今日投稿'])}件 / "
        f"明日投稿: {len(groups['明日投稿'])}件 / "
        f"保留: {len(groups['保留'])}件 / "
        f"投稿済み: {len(groups['投稿済み'])}件"
    )

    today_status_options = [
        f"今日投稿 {len(groups['今日投稿'])}件",
        f"明日投稿 {len(groups['明日投稿'])}件",
        f"保留 {len(groups['保留'])}件",
        f"投稿済み {len(groups['投稿済み'])}件",
    ]

    if st.session_state.get("simple_today_status") not in today_status_options:
        st.session_state.simple_today_status = today_status_options[0]

    if st.session_state.get("open_posted_posts"):
        st.session_state.simple_today_status = today_status_options[3]
        st.session_state.open_posted_posts = False

    selected_status_label = st.selectbox(
        "表示する投稿",
        today_status_options,
        key="simple_today_status",
    )
    selected_status = selected_status_label.split()[0]
    selected_files = groups[selected_status]

    if not selected_files:
        st.info(f"{selected_status}の投稿はありません")
        return

    today_file_options = simple_file_options(selected_files)
    selected_file_label = st.selectbox(
        "投稿を選ぶ",
        list(today_file_options.keys()),
        key="simple_today_file",
    )
    selected_file = today_file_options[selected_file_label]
    selected_content = selected_file.read_text(encoding="utf-8")
    selected_body = simple_extract_post_body(selected_content)

    st.text_area(
        "投稿本文だけコピー用",
        selected_body,
        height=320,
        key=f"simple_today_body_{selected_file.name}",
    )

    col1, col2 = st.columns(2)
    with col1:
        if selected_status != "投稿済み":
            if st.button("✅ 投稿済みにして反応メモ下書きも作る", key=f"simple_mark_posted_{selected_file.name}"):
                simple_update_schedule_status(selected_file, "投稿済み")
                saved_path = simple_create_post_result_draft_from_schedule(selected_file)
                st.session_state.go_to_reaction_memos = True
                st.session_state.open_reaction_memo_path = str(saved_path)
                simple_set_execution_result("投稿済みに変更し、反応メモ下書きを作りました。", [saved_path])
                st.rerun()
        else:
            if st.button("📈 反応メモ下書きを作る", key=f"simple_create_result_draft_{selected_file.name}"):
                saved_path = simple_create_post_result_draft_from_schedule(selected_file)
                st.session_state.go_to_reaction_memos = True
                st.session_state.open_reaction_memo_path = str(saved_path)
                simple_set_execution_result("反応メモ下書きを作りました。", [saved_path])
                st.rerun()
    with col2:
        if st.button("🗑 削除", key=f"simple_delete_schedule_{selected_file.name}"):
            deleted_path = selected_file
            selected_file.unlink()
            simple_set_execution_result("投稿予定を削除しました。", [deleted_path])
            st.rerun()

    with st.expander("詳細", expanded=False):
        st.write(selected_content)


def simple_render_stock_viewer() -> None:
    stock_groups = [
        ("投稿予定", sorted(Path("posts/schedule").glob("*.md"), reverse=True), "schedule"),
        ("完成版投稿", sorted(Path("posts/final_posts").glob("**/*.md"), reverse=True), "final_post"),
        ("反応メモ", sorted(Path("posts/results").glob("*.md"), reverse=True), "post_result"),
        ("反応ベース次投稿", sorted(Path("posts/result_next_posts").glob("*.md"), reverse=True), "result_next"),
        ("X投稿", sorted(Path("posts/x").glob("*.txt"), reverse=True), "normal"),
        ("Instagram投稿", sorted(Path("posts/instagram").glob("*.md"), reverse=True), "normal"),
        ("note記事", sorted(Path("posts/note").glob("*.md"), reverse=True), "normal"),
        ("アイデア", sorted(Path("posts/ideas").glob("*.txt"), reverse=True), "normal"),
    ]

    st.subheader("📦 投稿ストックを見る")
    stock_group_labels = [f"{label} {len(files)}件" for label, files, _ in stock_groups]

    if st.session_state.get("go_to_reaction_memos"):
        st.session_state.simple_stock_group = stock_group_labels[2]
        st.session_state.go_to_reaction_memos = False

    group_label = st.selectbox(
        "見るストック",
        stock_group_labels,
        key="simple_stock_group",
    )
    group_index = [f"{label} {len(files)}件" for label, files, _ in stock_groups].index(group_label)
    selected_files = stock_groups[group_index][1]
    selected_group_type = stock_groups[group_index][2]

    if not selected_files:
        st.info("このストックにはまだファイルがありません")
        return

    stock_file_options = simple_file_options(selected_files)
    open_reaction_memo_path = st.session_state.get("open_reaction_memo_path")
    if open_reaction_memo_path:
        for option_label, option_path in stock_file_options.items():
            if str(option_path) == open_reaction_memo_path:
                st.session_state.simple_stock_file = option_label
                break
        st.session_state.open_reaction_memo_path = ""

    selected_file_label = st.selectbox(
        "ファイルを選ぶ",
        list(stock_file_options.keys()),
        key="simple_stock_file",
    )
    selected_file = stock_file_options[selected_file_label]
    selected_content = selected_file.read_text(encoding="utf-8")

    st.text_area(
        "本文コピー用",
        selected_content,
        height=360,
        key=f"simple_stock_body_{selected_file}",
    )

    if selected_group_type == "post_result":
        with st.expander("反応メモを編集", expanded=False):
            current_memo = simple_extract_field(selected_content, "反応メモ")
            metric_col1, metric_col2 = st.columns(2)

            with metric_col1:
                edited_impressions = st.number_input(
                    "インプレッション",
                    min_value=0,
                    value=simple_extract_metric(selected_content, "インプレッション"),
                    key=f"edit_impressions_{selected_file.name}",
                )
                edited_likes = st.number_input(
                    "いいね",
                    min_value=0,
                    value=simple_extract_metric(selected_content, "いいね"),
                    key=f"edit_likes_{selected_file.name}",
                )
                edited_comments = st.number_input(
                    "コメント",
                    min_value=0,
                    value=simple_extract_metric(selected_content, "コメント"),
                    key=f"edit_comments_{selected_file.name}",
                )

            with metric_col2:
                edited_saves = st.number_input(
                    "保存",
                    min_value=0,
                    value=simple_extract_metric(selected_content, "保存"),
                    key=f"edit_saves_{selected_file.name}",
                )
                edited_profile_clicks = st.number_input(
                    "プロフィールクリック",
                    min_value=0,
                    value=simple_extract_metric(selected_content, "プロフィールクリック"),
                    key=f"edit_profile_clicks_{selected_file.name}",
                )
                edited_link_clicks = st.number_input(
                    "リンククリック",
                    min_value=0,
                    value=simple_extract_metric(selected_content, "リンククリック"),
                    key=f"edit_link_clicks_{selected_file.name}",
                )

            edited_memo = st.text_area(
                "反応メモ",
                current_memo,
                height=140,
                key=f"edit_result_memo_{selected_file.name}",
            )

            if st.button("💾 反応メモを保存", key=f"save_result_memo_edits_{selected_file.name}"):
                simple_save_result_memo_edits(
                    selected_file,
                    edited_impressions,
                    edited_likes,
                    edited_comments,
                    edited_saves,
                    edited_profile_clicks,
                    edited_link_clicks,
                    edited_memo,
                )
                simple_set_execution_result("反応メモを保存しました。", [selected_file])
                st.rerun()

        if st.button("📌 今日投稿まで一括作成", key=f"simple_auto_today_from_result_{selected_file.name}"):
            next_post_path = simple_create_result_next_post_from_result_memo(selected_file)
            x_final_path = simple_save_final_post_from_result_next_post(next_post_path, "X")
            instagram_final_path = simple_save_final_post_from_result_next_post(next_post_path, "Instagram")
            x_schedule_path = simple_save_scheduled_post_from_final_post(x_final_path, "今日投稿")
            instagram_schedule_path = simple_save_scheduled_post_from_final_post(instagram_final_path, "今日投稿")
            st.session_state.go_to_today_posts = True
            simple_set_execution_result(
                "今日投稿まで一括作成しました。",
                [next_post_path, x_final_path, instagram_final_path, x_schedule_path, instagram_schedule_path],
            )
            st.rerun()

    elif selected_group_type == "result_next":
        if st.button("📌 X・Instagramを今日投稿に追加", key=f"simple_today_from_result_next_{selected_file.name}"):
            x_final_path = simple_save_final_post_from_result_next_post(selected_file, "X")
            instagram_final_path = simple_save_final_post_from_result_next_post(selected_file, "Instagram")
            x_schedule_path = simple_save_scheduled_post_from_final_post(x_final_path, "今日投稿")
            instagram_schedule_path = simple_save_scheduled_post_from_final_post(instagram_final_path, "今日投稿")
            st.session_state.go_to_today_posts = True
            simple_set_execution_result(
                "X・Instagramを今日投稿に追加しました。",
                [x_final_path, instagram_final_path, x_schedule_path, instagram_schedule_path],
            )
            st.rerun()

    elif selected_group_type == "final_post":
        if st.button("📌 今日投稿に追加", key=f"simple_today_from_final_post_{selected_file}"):
            saved_path = simple_save_scheduled_post_from_final_post(selected_file, "今日投稿")
            st.session_state.go_to_today_posts = True
            simple_set_execution_result("今日投稿に追加しました。", [saved_path])
            st.rerun()

    with st.expander("細かい操作", expanded=False):
        st.download_button(
            "DL",
            data=selected_content,
            file_name=selected_file.name,
            mime="text/markdown" if selected_file.suffix == ".md" else "text/plain",
            key=f"simple_download_{selected_file}",
        )
        if st.button("🗑 削除", key=f"simple_delete_stock_{selected_file}"):
            deleted_path = selected_file
            selected_file.unlink()
            simple_set_execution_result("ストックを削除しました。", [deleted_path])
            st.rerun()


if st.session_state.get("go_to_today_posts"):
    st.session_state.simple_mode = "今日やる投稿"
    st.session_state.go_to_today_posts = False

if st.session_state.get("go_to_reaction_memos"):
    st.session_state.simple_mode = "投稿ストックを見る"

with st.sidebar:
    st.markdown("## 🤖 Ko AI")
    st.caption("自分専用AIアシスタント")
    st.divider()
    st.markdown("## 操作")
    simple_render_one_click_button()
    st.divider()
    simple_sidebar_status_counts()
    st.divider()
    simple_mode = st.radio(
        "使う画面",
        ["今日やる投稿", "投稿ストックを見る", "管理", "詳細モード（必要な時だけ）"],
        key="simple_mode",
    )
    st.divider()
    with st.expander("今日使う流れ", expanded=False):
        st.markdown(
            """
1. **今日やる投稿** で投稿本文をコピーする
2. 投稿したら **投稿済みにして反応メモ下書きも作る** を押す
3. **投稿ストックを見る → 反応メモ** で数字と気づきを入力する
4. **今日投稿まで一括作成** を押して、次のX・Instagram投稿を作る
5. 自動で **今日やる投稿** に戻るので、次の投稿本文を確認する

迷ったら、まずは **今日やる投稿** だけ見ればOKです。
            """.strip()
        )

simple_render_execution_result()
simple_render_next_action_hint()
st.divider()

if simple_mode == "今日やる投稿":
    simple_render_today_posts()
    st.stop()

if simple_mode == "投稿ストックを見る":
    simple_render_stock_viewer()
    st.stop()

if simple_mode == "管理":
    simple_render_admin()
    st.stop()


st.warning("詳細モードです。古い生成フォームや管理機能を使う時だけこの画面を使ってください。")

show_legacy_detail_mode = st.checkbox(
    "大量の詳細フォームを表示する",
    value=False,
    key="show_legacy_detail_mode",
)

if not show_legacy_detail_mode:
    st.info("詳細フォームは非表示です。必要な時だけチェックを入れて表示してください。")
    st.stop()

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

def run_result_next_post_finalize_self_check() -> list[tuple[str, bool, str]]:
    """反応ベース次投稿からX/Instagram完成版が正しく作れるか自動確認する。"""
    result_dir = Path("posts/result_next_posts")
    result_dir.mkdir(parents=True, exist_ok=True)

    test_source_path = result_dir / "__self_check_result_next_post.md"
    test_source_path.write_text(
        """
# 反応ベース次投稿案

## 元の反応メモファイル
posts/results/__self_check.md

## 次投稿案

X投稿案
これはX用の自動チェック投稿です。

Instagram投稿案
これはInstagram用の自動チェック投稿です。

投稿前の注意点
これは混ざってはいけない注意点です。
""".strip(),
        encoding="utf-8",
    )

    created_paths: list[Path] = []
    results: list[tuple[str, bool, str]] = []

    try:
        x_path = save_final_post_from_result_next_post(test_source_path, "X")
        instagram_path = save_final_post_from_result_next_post(test_source_path, "Instagram")
        created_paths.extend([x_path, instagram_path])

        x_content = x_path.read_text(encoding="utf-8")
        instagram_content = instagram_path.read_text(encoding="utf-8")

        results.append(("X完成版ファイル作成", x_path.exists(), str(x_path)))
        results.append(("Instagram完成版ファイル作成", instagram_path.exists(), str(instagram_path)))
        results.append(("X投稿本文だけ切り出し", "これはX用の自動チェック投稿です。" in x_content, "X本文が入っているか"))
        results.append(("XにInstagram投稿案が混ざっていない", "Instagram投稿案" not in x_content, "Instagram見出しが混ざっていないか"))
        results.append(("Instagram投稿本文だけ切り出し", "これはInstagram用の自動チェック投稿です。" in instagram_content, "Instagram本文が入っているか"))
        results.append(("InstagramにX投稿案が混ざっていない", "X投稿案" not in instagram_content, "X見出しが混ざっていないか"))
        results.append(("投稿前の注意点が混ざっていない", "投稿前の注意点" not in instagram_content and "投稿前の注意点" not in x_content, "注意点が混ざっていないか"))
    finally:
        if test_source_path.exists():
            test_source_path.unlink()
        for created_path in created_paths:
            if created_path.exists():
                created_path.unlink()

    return results


def clear_all_post_stock_files() -> int:
    """posts配下の投稿ストック用ファイルをすべて削除する。"""
    posts_dir = Path("posts")
    if not posts_dir.exists():
        return 0

    deleted_count = 0
    for file_path in posts_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix in [".md", ".txt"]:
            file_path.unlink()
            deleted_count += 1

    return deleted_count


def show_post_stock() -> None:
    st.header("📦 投稿ストック")

    with st.expander("⚙️ 管理・確認", expanded=False):
        st.caption("普段は開かなくてOK。動作確認・テストデータ削除・使い方だけここにまとめています。")

        st.markdown("**使い方**")
        st.write(
            "投稿予定を確認したい場合は『投稿予定』、投稿素材を探したい場合は『基本投稿』、"
            "分析や収益化に使う素材を見たい場合は『収益化・分析』を選んでください。"
        )
        st.caption("普段は『投稿予定』と『完成版・チェック済み』を中心に見ればOKです。")

        st.divider()
        st.markdown("**自動動作チェック**")
        if st.button("🧪 X・Instagram完成版の自動チェック", key="run_result_next_finalize_self_check"):
            check_results = run_result_next_post_finalize_self_check()
            failed_results = [result for result in check_results if not result[1]]

            for label, is_success, detail in check_results:
                if is_success:
                    st.success(f"✅ {label}: OK")
                else:
                    st.error(f"❌ {label}: NG（{detail}）")

            if not failed_results:
                st.success("自動チェックはすべて成功しました。")
            else:
                st.error("自動チェックで失敗があります。表示されたNG項目を確認してください。")

        st.divider()
        st.markdown("**ストック全削除**")
        st.warning("posts配下の投稿ストック用ファイル（.md / .txt）をすべて削除します。")
        confirm_clear_stock = st.checkbox(
            "全ストックを削除することを確認しました",
            key="confirm_clear_all_post_stocks",
        )
        if st.button("🧹 全ストックを削除", disabled=not confirm_clear_stock, key="clear_all_post_stocks"):
            deleted_count = clear_all_post_stock_files()
            st.success(f"{deleted_count}件のストックファイルを削除しました。")
            st.rerun()

    stock_view_category = st.selectbox(
        "表示するストックカテゴリ",
        [
            "全部",
            "投稿予定",
            "基本投稿",
            "収益化・分析",
            "完成版・チェック済み",
            "整理・archive",
        ],
        index=1,
        key="stock_view_category",
    )
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
    total_stock_count = (
        len(note_files)
        + len(x_files)
        + len(instagram_files)
        + len(threads_files)
        + len(idea_files)
        + len(reviewed_files)
        + len(monetization_files)
        + len(paid_note_outline_files)
        + len(calendar_files)
        + len(weekly_post_files)
        + len(today_menu_files)
        + len(today_menu_post_files)
        + len(stock_analysis_files)
        + len(stock_analysis_post_files)
        + len(freebie_files)
        + len(paid_note_draft_files)
        + len(sales_funnel_files)
        + len(stock_cleanup_files)
        + len(post_result_files)
        + len(result_next_post_files)
        + len(final_post_files)
        + len(safety_checked_files)
        + len(scheduled_post_files)
        + len(template_post_files)
        + len(archive_files)
    )

    st.caption(f"現在の表示カテゴリ: {stock_view_category} / ストック合計: {total_stock_count}件")

    if stock_view_category == "全部":
        with st.expander("📊 ストック件数を見る"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(f"note記事: {len(note_files)}件")
                st.write(f"X投稿: {len(x_files)}件")
                st.write(f"Instagram投稿: {len(instagram_files)}件")
                st.write(f"Threads投稿: {len(threads_files)}件")
                st.write(f"アイデア: {len(idea_files)}件")
                st.write(f"投稿予定: {len(scheduled_post_files)}件")
                st.write(f"完成版投稿: {len(final_post_files)}件")
                st.write(f"安全チェック済み: {len(safety_checked_files)}件")

            with col2:
                st.write(f"改善済み投稿: {len(reviewed_files)}件")
                st.write(f"収益導線案: {len(monetization_files)}件")
                st.write(f"有料note構成案: {len(paid_note_outline_files)}件")
                st.write(f"投稿カレンダー: {len(calendar_files)}件")
                st.write(f"7日分実投稿: {len(weekly_post_files)}件")
                st.write(f"今日の投稿メニュー: {len(today_menu_files)}件")
                st.write(f"今日メニュー実投稿: {len(today_menu_post_files)}件")
                st.write(f"テンプレ投稿: {len(template_post_files)}件")

            with col3:
                st.write(f"投稿ストック分析: {len(stock_analysis_files)}件")
                st.write(f"分析実投稿: {len(stock_analysis_post_files)}件")
                st.write(f"無料特典: {len(freebie_files)}件")
                st.write(f"有料note本文: {len(paid_note_draft_files)}件")
                st.write(f"販売導線まとめ: {len(sales_funnel_files)}件")
                st.write(f"投稿ストック整理案: {len(stock_cleanup_files)}件")
                st.write(f"投稿反応メモ: {len(post_result_files)}件")
                st.write(f"反応ベース次投稿: {len(result_next_post_files)}件")
                st.write(f"archive: {len(archive_files)}件")
    show_all_stock = stock_view_category == "全部"
    show_scheduled_stock = stock_view_category in ["全部", "投稿予定"]
    show_basic_stock = stock_view_category in ["全部", "基本投稿"]
    show_monetization_stock = stock_view_category in ["全部", "収益化・分析"]
    show_final_stock = stock_view_category in ["全部", "完成版・チェック済み"]
    show_archive_stock = stock_view_category in ["全部", "整理・archive"]
    

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

    if stock_view_category == "全部":
        with st.expander("📦 一括ダウンロード"):
            if not all_stock_files:
                st.caption("ダウンロードできる投稿ストックはありません")
            else:
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

    if stock_view_category == "投稿予定":
        st.subheader("📌 今日やる投稿")
        st.caption(
            f"今日投稿: {len(today_scheduled_files)}件 / "
            f"明日投稿: {len(tomorrow_scheduled_files)}件 / "
            f"保留: {len(pending_scheduled_files)}件 / "
            f"投稿済み: {len(posted_scheduled_files)}件"
        )

        schedule_view_mode = st.selectbox(
            "表示する予定",
            [
                f"今日投稿 {len(today_scheduled_files)}件",
                f"明日投稿 {len(tomorrow_scheduled_files)}件",
                f"保留 {len(pending_scheduled_files)}件",
                f"投稿済み {len(posted_scheduled_files)}件",
            ],
            key="compact_schedule_view_mode",
        )

        if schedule_view_mode.startswith("今日投稿"):
            compact_schedule_files = today_scheduled_files
            compact_empty_message = "今日投稿の予定はありません"
        elif schedule_view_mode.startswith("明日投稿"):
            compact_schedule_files = tomorrow_scheduled_files
            compact_empty_message = "明日投稿の予定はありません"
        elif schedule_view_mode.startswith("保留"):
            compact_schedule_files = pending_scheduled_files
            compact_empty_message = "保留中の投稿はありません"
        else:
            compact_schedule_files = posted_scheduled_files
            compact_empty_message = "投稿済みの投稿はありません"

        if not compact_schedule_files:
            st.info(compact_empty_message)
            return

        compact_options = [file_path.name for file_path in compact_schedule_files]
        selected_compact_file_name = st.selectbox(
            "投稿を選ぶ",
            compact_options,
            key="compact_schedule_selected_file",
        )
        selected_compact_file = next(
            file_path for file_path in compact_schedule_files if file_path.name == selected_compact_file_name
        )
        selected_compact_content = selected_compact_file.read_text(encoding="utf-8")
        selected_compact_body = extract_scheduled_post_body(selected_compact_content)

        st.text_area(
            "投稿本文だけコピー用",
            selected_compact_body,
            height=260,
            key=f"compact_schedule_body_{selected_compact_file.name}",
        )

        action_col1, action_col2 = st.columns(2)
        with action_col1:
            if "## 状態\n投稿済み" not in selected_compact_content:
                if st.button("✅ 投稿済みにする", key=f"compact_mark_posted_{selected_compact_file.name}"):
                    update_scheduled_post_status(selected_compact_file, "投稿済み")
                    st.success("投稿済みに変更しました")
                    st.rerun()
            else:
                if st.button("📈 反応メモ下書きを作成", key=f"compact_create_result_draft_{selected_compact_file.name}"):
                    saved_path = create_post_result_draft_from_scheduled(selected_compact_file)
                    st.success(f"反応メモ下書きを作成しました: {saved_path}")
                    st.rerun()

        with action_col2:
            if st.button("🗑 削除", key=f"compact_delete_scheduled_{selected_compact_file.name}"):
                delete_scheduled_post(selected_compact_file)
                st.success("投稿予定から削除しました")
                st.rerun()

        with st.expander("投稿予定の詳細", expanded=False):
            st.write(selected_compact_content)

        return

    compact_stock_groups: list[tuple[str, list[Path], str]] = []

    if show_basic_stock:
        compact_stock_groups.extend(
            [
                (f"note記事 {len(note_files)}件", note_files, "normal"),
                (f"X投稿 {len(x_files)}件", x_files, "normal"),
                (f"Instagram投稿 {len(instagram_files)}件", instagram_files, "normal"),
                (f"Threads投稿 {len(threads_files)}件", threads_files, "normal"),
                (f"アイデア {len(idea_files)}件", idea_files, "normal"),
            ]
        )

    if show_monetization_stock:
        compact_stock_groups.extend(
            [
                (f"改善済み投稿 {len(reviewed_files)}件", reviewed_files, "normal"),
                (f"収益導線 {len(monetization_files)}件", monetization_files, "normal"),
                (f"有料note構成 {len(paid_note_outline_files)}件", paid_note_outline_files, "normal"),
                (f"投稿カレンダー {len(calendar_files)}件", calendar_files, "normal"),
                (f"7日分実投稿 {len(weekly_post_files)}件", weekly_post_files, "normal"),
                (f"今日の投稿メニュー {len(today_menu_files)}件", today_menu_files, "normal"),
                (f"今日メニュー実投稿 {len(today_menu_post_files)}件", today_menu_post_files, "normal"),
                (f"投稿ストック分析 {len(stock_analysis_files)}件", stock_analysis_files, "normal"),
                (f"分析実投稿 {len(stock_analysis_post_files)}件", stock_analysis_post_files, "normal"),
                (f"無料特典 {len(freebie_files)}件", freebie_files, "normal"),
                (f"有料note本文 {len(paid_note_draft_files)}件", paid_note_draft_files, "normal"),
                (f"販売導線まとめ {len(sales_funnel_files)}件", sales_funnel_files, "normal"),
                (f"投稿反応メモ {len(post_result_files)}件", post_result_files, "post_result"),
                (f"反応ベース次投稿 {len(result_next_post_files)}件", result_next_post_files, "result_next"),
            ]
        )

    if show_final_stock:
        compact_stock_groups.extend(
            [
                (f"完成版投稿 {len(final_post_files)}件", final_post_files, "final_post"),
                (f"安全チェック済み {len(safety_checked_files)}件", safety_checked_files, "normal"),
                (f"テンプレ投稿 {len(template_post_files)}件", template_post_files, "normal"),
            ]
        )

    if show_archive_stock:
        compact_stock_groups.extend(
            [
                (f"投稿ストック整理案 {len(stock_cleanup_files)}件", stock_cleanup_files, "normal"),
                (f"archive {len(archive_files)}件", [file_path for file_path in archive_files if file_path.is_file()], "normal"),
            ]
        )

    compact_stock_groups = [
        (label, [file_path for file_path in files if file_path.is_file()], stock_type)
        for label, files, stock_type in compact_stock_groups
    ]

    st.subheader("📋 ストックを見る")
    compact_group_labels = [label for label, _, _ in compact_stock_groups]

    selected_compact_group_label = st.selectbox(
        "見るストック",
        compact_group_labels,
        key="compact_stock_group_label",
    )

    selected_group_files: list[Path] = []
    selected_group_type = "normal"
    for label, files, stock_type in compact_stock_groups:
        if label == selected_compact_group_label:
            selected_group_files = files
            selected_group_type = stock_type
            break

    if not selected_group_files:
        st.info("このストックにはまだファイルがありません")
        return

    selected_stock_file_name = st.selectbox(
        "ファイルを選ぶ",
        [file_path.name for file_path in selected_group_files],
        key="compact_stock_file_name",
    )
    selected_stock_file = next(
        file_path for file_path in selected_group_files if file_path.name == selected_stock_file_name
    )
    selected_stock_content = selected_stock_file.read_text(encoding="utf-8")

    st.text_area(
        "本文コピー用",
        selected_stock_content,
        height=360,
        key=f"compact_stock_content_{selected_stock_file}",
    )

    if selected_group_type == "post_result":
        if st.button("📌 今日投稿まで一括作成", key=f"compact_auto_today_from_result_{selected_stock_file.name}"):
            next_post_path = create_result_next_post_from_result_memo(selected_stock_file)
            x_final_path = save_final_post_from_result_next_post(next_post_path, "X")
            instagram_final_path = save_final_post_from_result_next_post(next_post_path, "Instagram")
            x_schedule_path = save_scheduled_post_from_final_post(x_final_path, "今日投稿")
            instagram_schedule_path = save_scheduled_post_from_final_post(instagram_final_path, "今日投稿")
            st.success("今日投稿まで一括作成しました。")
            st.caption(f"X今日投稿: {x_schedule_path}")
            st.caption(f"Instagram今日投稿: {instagram_schedule_path}")
            st.rerun()

    elif selected_group_type == "result_next":
        if st.button("📌 X・Instagramを今日投稿に追加", key=f"compact_today_from_result_next_{selected_stock_file.name}"):
            x_final_path = save_final_post_from_result_next_post(selected_stock_file, "X")
            instagram_final_path = save_final_post_from_result_next_post(selected_stock_file, "Instagram")
            x_schedule_path = save_scheduled_post_from_final_post(x_final_path, "今日投稿")
            instagram_schedule_path = save_scheduled_post_from_final_post(instagram_final_path, "今日投稿")
            st.success("X・Instagramを今日投稿に追加しました。")
            st.caption(f"X今日投稿: {x_schedule_path}")
            st.caption(f"Instagram今日投稿: {instagram_schedule_path}")
            st.rerun()

    elif selected_group_type == "final_post":
        if st.button("📌 今日投稿に追加", key=f"compact_schedule_today_final_{selected_stock_file}"):
            saved_path = save_scheduled_post_from_final_post(selected_stock_file, "今日投稿")
            st.success(f"今日投稿に追加しました: {saved_path}")
            st.rerun()

    with st.expander("細かい操作", expanded=False):
        st.download_button(
            "DL",
            data=selected_stock_content,
            file_name=selected_stock_file.name,
            mime="text/markdown" if selected_stock_file.suffix == ".md" else "text/plain",
            key=f"compact_download_{selected_stock_file}",
        )

        if selected_group_type == "post_result":
            if st.button("🗑 削除", key=f"compact_delete_post_result_{selected_stock_file.name}"):
                delete_post_result_memo(selected_stock_file)
                st.success("反応メモを削除しました")
                st.rerun()
        elif selected_group_type == "result_next":
            if st.button("🗑 削除", key=f"compact_delete_result_next_{selected_stock_file.name}"):
                delete_result_next_post(selected_stock_file)
                st.success("次投稿案を削除しました")
                st.rerun()
        elif selected_group_type == "final_post":
            if st.button("🗑 削除", key=f"compact_delete_final_post_{selected_stock_file}"):
                delete_final_post(selected_stock_file)
                st.success("完成版投稿を削除しました")
                st.rerun()
        else:
            if st.button("🗑 削除", key=f"compact_delete_normal_stock_{selected_stock_file}"):
                delete_stock_file(selected_stock_file)
                st.success("ストックを削除しました")
                st.rerun()

    return

    if show_scheduled_stock:
        st.subheader("📌 投稿予定まとめ")
        st.caption(
            f"今日投稿: {len(today_scheduled_files)}件 / "
            f"明日投稿: {len(tomorrow_scheduled_files)}件 / "
            f"保留: {len(pending_scheduled_files)}件 / "
            f"投稿済み: {len(posted_scheduled_files)}件"
        )

        today_tab, tomorrow_tab, pending_tab, posted_tab = st.tabs(
            [
                f"📌 今日 {len(today_scheduled_files)}",
                f"🌙 明日 {len(tomorrow_scheduled_files)}",
                f"⏸ 保留 {len(pending_scheduled_files)}",
                f"✅ 投稿済み {len(posted_scheduled_files)}",
            ]
        )

        with today_tab:
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

        with tomorrow_tab:
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

        with pending_tab:
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

        with posted_tab:
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

    if show_basic_stock:
        with st.expander("📝 note記事ストック"):
            if not note_files:
                st.caption("まだnote記事はありません")
            for file_path in note_files[:5]:
                content = file_path.read_text(encoding="utf-8")
                st.subheader(file_path.name)
                st.write(content)

                col1, col2 = st.columns(2)

                with col1:
                    st.download_button(
                        "📝 note記事をダウンロード",
                        data=content,
                        file_name=file_path.name,
                        mime="text/markdown",
                        key=f"download_note_{file_path.name}",
                    )

                with col2:
                    if st.button("🗑 note記事を削除", key=f"delete_note_{file_path.name}"):
                        delete_stock_file(file_path)
                        st.success("note記事を削除しました")
                        st.rerun()

        with st.expander("🐦 X投稿ストック"):
            if not x_files:
                st.caption("まだX投稿はありません")
            for file_path in x_files[:10]:
                content = file_path.read_text(encoding="utf-8")
                st.subheader(file_path.name)
                st.write(content)

                col1, col2 = st.columns(2)

                with col1:
                    st.download_button(
                        "🐦 X投稿をダウンロード",
                        data=content,
                        file_name=file_path.name,
                        mime="text/plain",
                        key=f"download_x_{file_path.name}",
                    )

                with col2:
                    if st.button("🗑 X投稿を削除", key=f"delete_x_{file_path.name}"):
                        delete_stock_file(file_path)
                        st.success("X投稿を削除しました")
                        st.rerun()

        with st.expander("📷 Instagram投稿ストック"):
            if not instagram_files:
                st.caption("まだInstagram投稿はありません")
            for file_path in instagram_files[:10]:
                content = file_path.read_text(encoding="utf-8")
                st.subheader(file_path.name)
                st.write(content)

                col1, col2 = st.columns(2)

                with col1:
                    st.download_button(
                        "📷 Instagram投稿をダウンロード",
                        data=content,
                        file_name=file_path.name,
                        mime="text/markdown",
                        key=f"download_instagram_{file_path.name}",
                    )

                with col2:
                    if st.button("🗑 Instagram投稿を削除", key=f"delete_instagram_{file_path.name}"):
                        delete_stock_file(file_path)
                        st.success("Instagram投稿を削除しました")
                        st.rerun()

        with st.expander("🧵 Threads投稿ストック"):
            if not threads_files:
                st.caption("まだThreads投稿はありません")
            for file_path in threads_files[:10]:
                content = file_path.read_text(encoding="utf-8")
                st.subheader(file_path.name)
                st.write(content)

                col1, col2 = st.columns(2)

                with col1:
                    st.download_button(
                        "🧵 Threads投稿をダウンロード",
                        data=content,
                        file_name=file_path.name,
                        mime="text/plain",
                        key=f"download_threads_{file_path.name}",
                    )

                with col2:
                    if st.button("🗑 Threads投稿を削除", key=f"delete_threads_{file_path.name}"):
                        delete_stock_file(file_path)
                        st.success("Threads投稿を削除しました")
                        st.rerun()
        with st.expander("💡 アイデアストック"):
            if not idea_files:
                st.caption("まだアイデアはありません")
            for file_path in idea_files[:10]:
                content = file_path.read_text(encoding="utf-8")
                st.subheader(file_path.name)
                st.write(content)

                col1, col2 = st.columns(2)

                with col1:
                    st.download_button(
                        "💡 アイデアをダウンロード",
                        data=content,
                        file_name=file_path.name,
                        mime="text/plain",
                        key=f"download_idea_{file_path.name}",
                    )

                with col2:
                    if st.button("🗑 アイデアを削除", key=f"delete_idea_{file_path.name}"):
                        delete_stock_file(file_path)
                        st.success("アイデアを削除しました")
                        st.rerun()
    if show_monetization_stock:
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

                if st.button("📌 今日投稿まで一括作成", key=f"auto_today_from_result_{file_path.name}"):
                    next_post_path = create_result_next_post_from_result_memo(file_path)
                    x_final_path = save_final_post_from_result_next_post(next_post_path, "X")
                    instagram_final_path = save_final_post_from_result_next_post(next_post_path, "Instagram")
                    x_schedule_path = save_scheduled_post_from_final_post(x_final_path, "今日投稿")
                    instagram_schedule_path = save_scheduled_post_from_final_post(instagram_final_path, "今日投稿")
                    st.success("今日投稿まで一括作成しました。")
                    st.caption(f"次投稿案: {next_post_path}")
                    st.caption(f"X完成版: {x_final_path}")
                    st.caption(f"Instagram完成版: {instagram_final_path}")
                    st.caption(f"X今日投稿: {x_schedule_path}")
                    st.caption(f"Instagram今日投稿: {instagram_schedule_path}")
                    st.rerun()

                with st.expander("細かい操作", expanded=False):
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.download_button(
                            "📈 DL",
                            data=content,
                            file_name=file_path.name,
                            mime="text/markdown",
                            key=f"download_post_result_{file_path.name}",
                        )

                    with col2:
                        if st.button("📝 次投稿案だけ", key=f"create_result_next_post_{file_path.name}"):
                            saved_path = create_result_next_post_from_result_memo(file_path)
                            st.success(f"次投稿案を作成しました: {saved_path}")
                            st.rerun()

                    with col3:
                        if st.button("🚀 完成版まで", key=f"auto_finalize_from_result_{file_path.name}"):
                            next_post_path = create_result_next_post_from_result_memo(file_path)
                            x_final_path = save_final_post_from_result_next_post(next_post_path, "X")
                            instagram_final_path = save_final_post_from_result_next_post(next_post_path, "Instagram")
                            st.success(f"次投稿案を作成しました: {next_post_path}")
                            st.success(f"X完成版を作成しました: {x_final_path}")
                            st.success(f"Instagram完成版を作成しました: {instagram_final_path}")
                            st.rerun()

                    with col4:
                        if st.button("🗑 削除", key=f"delete_post_result_{file_path.name}"):
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

                if st.button("📌 X・Instagramを今日投稿に追加", key=f"today_from_result_next_post_{file_path.name}"):
                    x_final_path = save_final_post_from_result_next_post(file_path, "X")
                    instagram_final_path = save_final_post_from_result_next_post(file_path, "Instagram")
                    x_schedule_path = save_scheduled_post_from_final_post(x_final_path, "今日投稿")
                    instagram_schedule_path = save_scheduled_post_from_final_post(instagram_final_path, "今日投稿")
                    st.success("X・Instagramを今日投稿に追加しました。")
                    st.caption(f"X今日投稿: {x_schedule_path}")
                    st.caption(f"Instagram今日投稿: {instagram_schedule_path}")
                    st.rerun()

                with st.expander("細かい操作", expanded=False):
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.download_button(
                            "📝 DL",
                            data=content,
                            file_name=file_path.name,
                            mime="text/markdown",
                            key=f"download_result_next_post_{file_path.name}",
                        )

                    with col2:
                        if st.button("✅ X完成版だけ", key=f"finalize_result_next_post_x_{file_path.name}"):
                            saved_path = save_final_post_from_result_next_post(file_path, "X")
                            st.success(f"X完成版投稿に追加しました: {saved_path}")
                            st.rerun()

                    with col3:
                        if st.button("📷 Instagram完成版だけ", key=f"finalize_result_next_post_instagram_{file_path.name}"):
                            saved_path = save_final_post_from_result_next_post(file_path, "Instagram")
                            st.success(f"Instagram完成版投稿に追加しました: {saved_path}")
                            st.rerun()

                    with col4:
                        if st.button("🗑 削除", key=f"delete_result_next_post_{file_path.name}"):
                            delete_result_next_post(file_path)
                            st.success("次投稿案を削除しました")
                            st.rerun()

    if show_final_stock:
        with st.expander("✅ 完成版投稿ストック"):
            if not final_post_files:
                st.caption("まだ完成版投稿はありません")
            for file_path in final_post_files[:20]:
                content = file_path.read_text(encoding="utf-8")
                st.subheader(str(file_path))
                st.write(content)

                if st.button("📌 今日投稿に追加", key=f"schedule_today_final_post_{file_path}"):
                    saved_path = save_scheduled_post_from_final_post(file_path, "今日投稿")
                    st.success(f"今日投稿に追加しました: {saved_path}")
                    st.rerun()

                with st.expander("細かい操作", expanded=False):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.download_button(
                            "✅ DL",
                            data=content,
                            file_name=file_path.name,
                            mime="text/markdown",
                            key=f"download_final_post_{file_path}",
                        )

                    with col2:
                        if st.button("⏸ 保留に追加", key=f"schedule_pending_final_post_{file_path}"):
                            saved_path = save_scheduled_post_from_final_post(file_path, "保留")
                            st.success(f"保留に追加しました: {saved_path}")
                            st.rerun()

                    with col3:
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

                col1, col2 = st.columns(2)

                with col1:
                    st.download_button(
                        "🧩 テンプレ投稿をダウンロード",
                        data=content,
                        file_name=file_path.name,
                        mime="text/markdown",
                        key=f"download_template_post_{file_path.name}",
                    )

                with col2:
                    if st.button("🗑 テンプレ投稿を削除", key=f"delete_template_post_{file_path.name}"):
                        delete_template_post(file_path)
                        st.success("テンプレ投稿を削除しました")
                        st.rerun()

    if show_archive_stock:
        with st.expander("🗄 archiveストック"):
            if not archive_files:
                st.caption("まだarchiveに移動したストックはありません")
            for file_path in archive_files[:20]:
                if not file_path.is_file():
                    continue
                content = file_path.read_text(encoding="utf-8")
                st.subheader(file_path.name)
                st.write(content)

                col1, col2 = st.columns(2)

                with col1:
                    st.download_button(
                        "🗄 archiveストックをダウンロード",
                        data=content,
                        file_name=file_path.name,
                        mime="text/plain",
                        key=f"download_archive_{file_path.name}",
                    )

                with col2:
                    if st.button("🗑 archiveから削除", key=f"delete_archive_{file_path.name}"):
                        delete_archive_file(file_path)
                        st.success("archiveから削除しました")
                        st.rerun()


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

def create_result_next_post_from_result_memo(file_path: Path) -> Path:
    """投稿反応メモから次投稿案を作成して保存する。"""
    save_dir = Path("posts/result_next_posts")
    save_dir.mkdir(parents=True, exist_ok=True)

    from datetime import datetime

    content = file_path.read_text(encoding="utf-8")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = file_path.stem.strip().replace("/", "_").replace(" ", "_")[:40] or "result_next_post"
    save_path = save_dir / f"{timestamp}_{safe_title}.md"

    prompt = f"""
以下の投稿反応メモをもとに、次に投稿するSNS投稿案を作ってください。

条件:
- 日本語
- 大学生でも自然に書ける文体
- 過度な煽りや断定は避ける
- 元投稿の良さを活かす
- 改善点があれば次投稿に反映する
- X投稿案とInstagram投稿案を両方出す
- 最後に投稿前の注意点も書く

投稿反応メモ:
{content}
""".strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "あなたはSNS投稿改善に強い編集者です。"},
            {"role": "user", "content": prompt},
        ],
    )

    next_post = response.choices[0].message.content or ""

    output = f"""
# 反応ベース次投稿案

## 元の反応メモファイル
{file_path}

## 次投稿案
{next_post.strip()}
""".strip()

    save_path.write_text(output, encoding="utf-8")
    return save_path

def extract_section_between_markers(content: str, start_marker: str, end_markers: list[str]) -> str:
    """指定した見出し以降から、次の見出しの手前までを取り出す。"""
    if start_marker not in content:
        return ""

    section = content.split(start_marker, 1)[1].strip()

    end_positions = [
        section.find(end_marker)
        for end_marker in end_markers
        if end_marker in section
    ]

    if end_positions:
        section = section[: min(end_positions)].strip()

    return section.strip()

def save_final_post_from_result_next_post(file_path: Path, platform: str = "X") -> Path:
    """反応ベース次投稿案を完成版投稿として保存する。"""
    save_dir = Path("posts/final_posts") / platform.lower()
    save_dir.mkdir(parents=True, exist_ok=True)

    from datetime import datetime

    content = file_path.read_text(encoding="utf-8")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = file_path.stem.strip().replace("/", "_").replace(" ", "_")[:40] or "final_post"
    save_path = save_dir / f"{timestamp}_{platform.lower()}_{safe_title}.md"

    if platform.lower() == "x":
        post_body = extract_section_between_markers(
            content,
            "X投稿案",
            ["Instagram投稿案", "投稿前の注意点"],
        )
    elif platform.lower() == "instagram":
        post_body = extract_section_between_markers(
            content,
            "Instagram投稿案",
            ["投稿前の注意点"],
        )
    else:
        post_body = content

    if not post_body.strip():
        post_body = content

    output = f"""
# 完成版投稿

## 元ファイル
{file_path}

## 投稿先
{platform}

## 投稿本文
{post_body.strip()}
""".strip()

    save_path.write_text(output, encoding="utf-8")
    return save_path

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

def delete_template_post(file_path: Path) -> None:
    """テンプレ投稿ファイルを削除する。"""
    if file_path.exists() and file_path.is_file():
        file_path.unlink()

def delete_archive_file(file_path: Path) -> None:
    """archiveファイルを削除する。"""
    if file_path.exists() and file_path.is_file():
        file_path.unlink()

def delete_stock_file(file_path: Path) -> None:
    """投稿ストックファイルを削除する。"""
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
    st.caption("迷ったら上から順番に使う")
    st.markdown(
        """
1. 📌 今日の投稿メニュー
2. 🧾 今日メニュー実投稿
3. 🛡 安全チェック
4. ✅ 完成版投稿
5. 📦 投稿ストック
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