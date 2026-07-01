from datetime import datetime
from pathlib import Path
from openai import OpenAI


NOTE_ARTICLES_FILE = Path("note_articles.txt")


def create_note_article(client: OpenAI, topic: str) -> str:
    prompt = f"""
あなたはプロのWebライターです。

テーマ: {topic}

以下の構成でnote記事を書いてください。

- タイトル
- 導入
- 見出しを3つ以上
- まとめ
- 読者への行動喚起

読みやすく、自然な日本語で作成してください。
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "あなたは優秀なWebライターです。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content


def save_note_article(topic: str, article: str) -> None:
    """生成したnote記事案を保存する。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with NOTE_ARTICLES_FILE.open("a", encoding="utf-8") as file:
        file.write(f"\n[{now}] テーマ: {topic}\n")
        file.write("-" * 50 + "\n")
        file.write(article)
        file.write("\n" + "=" * 50 + "\n")