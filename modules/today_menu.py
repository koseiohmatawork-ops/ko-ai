from datetime import datetime
from pathlib import Path

from openai import OpenAI


def load_recent_stock(max_chars: int = 6000) -> str:
    """保存済み投稿ストックを読み込む。"""
    folders = [
        "posts/x",
        "posts/instagram",
        "posts/threads",
        "posts/note",
        "posts/ideas",
        "posts/reviewed",
        "posts/monetization",
        "posts/paid_note_outlines",
        "posts/calendars",
        "posts/weekly_posts",
    ]

    stock_texts = []

    for folder in folders:
        folder_path = Path(folder)
        if not folder_path.exists():
            continue

        files = sorted(folder_path.glob("*"), reverse=True)

        for file_path in files[:3]:
            if file_path.is_file():
                try:
                    content = file_path.read_text(encoding="utf-8")
                    stock_texts.append(
                        f"""
【ファイル】
{file_path}

【内容】
{content[:1200]}
""".strip()
                    )
                except Exception:
                    continue

    joined_text = "\n\n---\n\n".join(stock_texts)
    return joined_text[:max_chars]


def create_today_post_menu(client: OpenAI, stock_text: str) -> str:
    """保存済みストックから今日の投稿メニューを作る。"""
    today = datetime.now().strftime("%Y-%m-%d")

    prompt = f"""
あなたはSNS運用とコンテンツ販売に強い編集者です。
以下の保存済み投稿ストックをもとに、今日やるべき投稿メニューを作ってください。

【今日の日付】
{today}

【目的】
今日の投稿作業を迷わず進められるようにすること。
特に、保存・フォロー・note購入・無料特典・有料コンテンツ販売につながる行動を優先してください。

【出力形式】
1. 今日いちばん投稿すべき内容
2. その理由
3. 今日投稿する文章案
4. 最後に入れるCTA
5. 余力があればやること
6. note・有料noteにつなげるならどうするか
7. 明日につなげる投稿案

【保存済み投稿ストック】
{stock_text}
""".strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "あなたはSNS投稿を収益化につなげる運用担当です。今日やるべきことを具体的に指示してください。",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    return response.choices[0].message.content or "今日の投稿メニューを作成できませんでした。"


def save_today_post_menu(today_menu: str) -> Path:
    """今日の投稿メニューを保存する。"""
    save_dir = Path("posts/today_menus")
    save_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = save_dir / f"{timestamp}_today_menu.md"

    content = f"""
# 今日の投稿メニュー

{today_menu}
""".strip()

    file_path.write_text(content, encoding="utf-8")
    return file_path