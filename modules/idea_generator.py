from openai import OpenAI


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