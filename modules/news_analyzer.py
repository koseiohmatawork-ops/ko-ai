from openai import OpenAI


def analyze_news(client: OpenAI, news_text: str) -> str:
    prompt = f"""
あなたはSNSマーケター兼ニュースアナリストです。

以下のニュースを分析してください。

ニュース
-----------------------
{news_text}
-----------------------

以下の形式で出力してください。

【要約】
（3〜5行）

【重要ポイント】
・
・
・

【SNSで発信するなら？】
・どんな切り口が良いか
・誰に刺さるか
・どんなテーマで展開できるか

【おすすめ投稿テーマ】
5個
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "あなたは優秀なニュースアナリストです。"
            },
            {
                "role": "user",
                "content": prompt
            },
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content