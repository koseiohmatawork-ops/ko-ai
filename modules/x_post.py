from datetime import datetime
from pathlib import Path

from openai import OpenAI


X_POSTS_FILE = Path("x_posts.txt")
X_POSTS_DIR = Path("posts/x")


def generate_x_post(client: OpenAI, theme: str) -> str:
    """テーマからX投稿案を生成する。"""
    prompt = f"""
あなたはX運用に強いSNSマーケターです。

テーマ: {theme}

以下の条件でX投稿を1つ作成してください。

条件:
- 140文字以内
- 読みやすく改行する
- 最後に関連するハッシュタグを2〜4個つける
- 煽りすぎず、自然で保存したくなる内容にする
- 収益化や副業に関心がある人に刺さる文章にする
""".strip()

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "あなたは優秀なSNSマーケターです。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
    )

    return response.choices[0].message.content


def save_x_post(theme: str, post: str) -> None:
    """生成したX投稿案を保存する。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with X_POSTS_FILE.open("a", encoding="utf-8") as file:
        file.write(f"\n[{now}] テーマ: {theme}\n")
        file.write("-" * 50 + "\n")
        file.write(post)
        file.write("\n" + "=" * 50 + "\n")

    X_POSTS_DIR.mkdir(parents=True, exist_ok=True)
    safe_theme = "".join(char if char.isalnum() else "_" for char in theme).strip("_")
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_theme}.txt"
    file_path = X_POSTS_DIR / filename

    file_path.write_text(post, encoding="utf-8")