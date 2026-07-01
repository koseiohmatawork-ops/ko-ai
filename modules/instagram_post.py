from datetime import datetime
from pathlib import Path

from openai import OpenAI


INSTAGRAM_POSTS_FILE = Path("instagram_posts.txt")
INSTAGRAM_POSTS_DIR = Path("posts/instagram")


def generate_instagram_post(client: OpenAI, theme: str) -> str:
    """Instagramカルーセル投稿を生成する。"""

    prompt = f"""
あなたはInstagram運用のプロです。

テーマ: {theme}

以下の形式でInstagramカルーセル投稿を作成してください。

【条件】
・1枚目（タイトル）
・2〜6枚目（内容）
・7枚目（まとめ・行動喚起）
・最後にキャプション
・最後にハッシュタグ10個程度

読みやすく、保存したくなる内容にしてください。
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "あなたは優秀なInstagramマーケターです。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.8,
    )

    return response.choices[0].message.content


def save_instagram_post(theme: str, post: str) -> None:
    """Instagram投稿を保存する。"""

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with INSTAGRAM_POSTS_FILE.open("a", encoding="utf-8") as file:
        file.write(f"\n[{now}] テーマ: {theme}\n")
        file.write("-" * 50 + "\n")
        file.write(post)
        file.write("\n" + "=" * 50 + "\n")

    INSTAGRAM_POSTS_DIR.mkdir(parents=True, exist_ok=True)

    safe_theme = "".join(
        c if c.isalnum() else "_"
        for c in theme
    ).strip("_")

    filename = (
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_theme}.md"
    )

    (INSTAGRAM_POSTS_DIR / filename).write_text(
        post,
        encoding="utf-8",
    )