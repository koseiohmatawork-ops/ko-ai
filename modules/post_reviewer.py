from openai import OpenAI


def review_post(client: OpenAI, post_text: str) -> str:
    """投稿内容を採点し、改善案を返す。"""
    prompt = f"""
あなたはSNS投稿とnote記事の編集者です。
以下の投稿を、収益化・拡散・読みやすさの観点で採点してください。

【採点ルール】
- 総合点を100点満点で出す
- 良い点を3つ挙げる
- 弱い点を3つ挙げる
- すぐ直せる改善案を出す
- 最後に改善後の投稿例を1つ作る

【見る観点】
1. 冒頭で読む理由があるか
2. 読者の悩みや欲求に刺さっているか
3. 具体性があるか
4. 最後まで読みやすいか
5. 保存・拡散・行動につながるか
6. AI副業・SNS運用・収益化につながるか

【投稿】
{post_text}
""".strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "あなたはSNS投稿、note記事、コンテンツ販売に強い編集者です。厳しめだが実用的に添削してください。",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    return response.choices[0].message.content or "投稿を採点できませんでした。"


def improve_post(client: OpenAI, post_text: str) -> str:
    """投稿内容を、より伸びやすく収益化につながる形に改善する。"""
    prompt = f"""
あなたはSNS投稿とnote記事の編集者です。
以下の投稿を、より読まれやすく、保存・拡散・収益化につながりやすい形に改善してください。

【改善ルール】
- 冒頭で読む理由を強くする
- 読者の悩みや欲求に寄せる
- 抽象的な表現を具体的にする
- 文章を短く読みやすくする
- 最後に行動したくなる一文を入れる
- AI副業・SNS運用・収益化につながる内容にする

【出力形式】
1. 改善の方向性
2. 改善後の投稿
3. さらに伸ばすための一言アドバイス

【元の投稿】
{post_text}
""".strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "あなたはSNS投稿、note記事、コンテンツ販売に強い編集者です。読者が思わず読みたくなる投稿に改善してください。",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    return response.choices[0].message.content or "投稿を改善できませんでした。"