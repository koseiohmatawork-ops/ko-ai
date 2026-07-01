from datetime import datetime
from pathlib import Path

from openai import OpenAI


THREADS_POSTS_FILE = Path("threads_posts.txt")
THREADS_POSTS_DIR = Path("posts/threads")


def generate_threads_post(client: OpenAI, theme: str) -> str:
    """Threads投稿案を生成する。"""

    prompt = f"""
あなたはThreads運用に強いSNSマーケターです。

テーマ: {theme}

以下の条件でThreads投稿を作成してください。

【条件】
・共感されやすい文章にする
・長すぎず、読みやすくする
・最初の1文で興味を引く
・最後にコメントしたくなる一言を入れる
・ハッシュタグは2〜4個
・副業、AI活用、収益化に興味がある人に刺さる内容にする
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "あなたは優秀なThreadsマーケターです。",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.8,
    )

    return response.choices[0].message.content


def save_threads_post(theme: str, post: str) -> None:
    """Threads投稿案を保存する。"""

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with THREADS_POSTS_FILE.open("a", encoding="utf-8") as file:
        file.write(f"\n[{now}] テーマ: {theme}\n")
        file.write("-" * 50 + "\n")
        file.write(post)
        file.write("\n" + "=" * 50 + "\n")

    THREADS_POSTS_DIR.mkdir(parents=True, exist_ok=True)

    safe_theme = "".join(
        c if c.isalnum() else "_"
        for c in theme
    ).strip("_")

    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_theme}.txt"

    (THREADS_POSTS_DIR / filename).write_text(
        post,
        encoding="utf-8",
    )