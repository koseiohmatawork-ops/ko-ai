from datetime import datetime
from pathlib import Path

from openai import OpenAI


IDEAS_FILE = Path("ideas.txt")
IDEAS_DIR = Path("posts/ideas")


def generate_ideas(client: OpenAI, theme: str, count: int = 100) -> str:
    prompt = f"""
あなたはSNSマーケターです。

テーマ
{theme}

このテーマで発信できるアイデアを{count}個考えてください。

条件
・1行に1個
・番号付き
・初心者にも刺さる
・収益化につながる内容
・note、X、Instagram、Threadsで使える内容
・重複しない
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "あなたはSNS運用のプロです。"
            },
            {
                "role": "user",
                "content": prompt
            },
        ],
        temperature=0.9,
    )

    return response.choices[0].message.content


def save_ideas(theme: str, ideas: str) -> None:
    """生成したアイデアを保存する。"""

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with IDEAS_FILE.open("a", encoding="utf-8") as file:
        file.write(f"\n[{now}] テーマ: {theme}\n")
        file.write("-" * 50 + "\n")
        file.write(ideas)
        file.write("\n" + "=" * 50 + "\n")

    IDEAS_DIR.mkdir(parents=True, exist_ok=True)

    safe_theme = "".join(
        c if c.isalnum() else "_"
        for c in theme
    ).strip("_")

    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_theme}.txt"

    (IDEAS_DIR / filename).write_text(
        ideas,
        encoding="utf-8",
    )