

from openai import OpenAI


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