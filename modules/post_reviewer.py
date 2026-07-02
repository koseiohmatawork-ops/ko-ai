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