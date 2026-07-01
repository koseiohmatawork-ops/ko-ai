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

def select_best_news(client: OpenAI, news_text: str) -> str:
    prompt = f"""
あなたはSNSマーケター兼ニュース編集者です。

以下のニュース一覧から、SNS発信に一番向いているニュースを1つ選んでください。

ニュース一覧
-----------------------
{news_text}
-----------------------

選ぶ基準:
・AI、副業、仕事効率化、収益化と相性が良い
・一般の人にも分かりやすい
・note、X、Instagram、Threadsに展開しやすい
・話題性がある

以下の形式で出力してください。

【選んだニュース】
タイトル:
URL:

【選んだ理由】
・
・
・

【投稿テーマ】
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "あなたはSNSで伸びるニュースを選ぶ編集者です。",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content