from datetime import datetime
from pathlib import Path

from openai import OpenAI


def review_post(client: OpenAI, post_text: str, platform: str = "SNS") -> str:
    """投稿内容を採点し、改善案を返す。"""
    prompt = f"""
あなたはSNS投稿とnote記事の編集者です。
以下の投稿を、{platform}向けとして、収益化・拡散・読みやすさの観点で採点してください。

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


def improve_post(client: OpenAI, post_text: str, platform: str = "SNS") -> str:
    """投稿内容を、より伸びやすく収益化につながる形に改善する。"""
    prompt = f"""
あなたはSNS投稿とnote記事の編集者です。
以下の投稿を、{platform}向けに、より読まれやすく、保存・拡散・収益化につながりやすい形に改善してください。

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

def save_reviewed_post(platform: str, original_post: str, improved_post: str) -> Path:
    """改善した投稿をストックとして保存する。"""
    save_dir = Path("posts/reviewed")
    save_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = save_dir / f"{timestamp}_{platform}_reviewed.md"

    content = f"""
# 改善済み投稿

## 投稿先
{platform}

## 元の投稿
{original_post}

## 改善後の投稿
{improved_post}
""".strip()

    file_path.write_text(content, encoding="utf-8")
    return file_path

def create_monetization_plan(client: OpenAI, post_text: str, platform: str = "SNS") -> str:
    """投稿から収益化につながる導線案を作る。"""
    prompt = f"""
あなたはSNS運用とコンテンツ販売に強いマーケターです。
以下の投稿を、{platform}向けに収益化へつなげる導線を考えてください。

【目的】
投稿を見た人が、保存・フォロー・プロフィール閲覧・note購入・無料相談・商品購入などの次の行動を取りやすくすること。

【出力形式】
1. この投稿で狙える読者層
2. 読者の悩み・欲求
3. 自然に入れられるCTAを3つ
4. 無料特典のアイデアを3つ
5. 有料note・商品化できるテーマを3つ
6. 投稿の最後に入れるおすすめ導線文
7. 収益化につなげるための次の一手

【投稿】
{post_text}
""".strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "あなたはSNS発信を収益化につなげるマーケターです。押し売りではなく、自然な導線を提案してください。",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    return response.choices[0].message.content or "収益導線を作成できませんでした。"

def save_monetization_plan(platform: str, original_post: str, monetization_plan: str) -> Path:
    """収益導線案をストックとして保存する。"""
    save_dir = Path("posts/monetization")
    save_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = save_dir / f"{timestamp}_{platform}_monetization.md"

    content = f"""
# 収益導線案

## 投稿先
{platform}

## 元の投稿
{original_post}

## 収益導線案
{monetization_plan}
""".strip()

    file_path.write_text(content, encoding="utf-8")
    return file_path

def create_paid_note_outline(client: OpenAI, post_text: str, platform: str = "SNS") -> str:
    """投稿内容から有料noteの構成案を作る。"""
    prompt = f"""
あなたは有料note、コンテンツ販売、SNS導線設計に強い編集者です。
以下の{platform}投稿をもとに、有料noteとして販売できる構成案を作ってください。

【目的】
SNS投稿で興味を持った読者が、もっと詳しく知りたいと思って購入したくなる有料noteの設計を作ること。

【出力形式】
1. 有料noteのタイトル案を5つ
2. 想定読者
3. 読者の悩み
4. このnoteで得られる結果
5. 章立て案
6. 無料部分に書く内容
7. 有料部分に書く内容
8. 価格帯の目安
9. 販売ページの一言コピー
10. SNS投稿からnoteへ誘導する文章

【元の投稿】
{post_text}
""".strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "あなたは有料noteの構成作成と販売導線に強い編集者です。初心者でもそのまま作れる具体的な構成にしてください。",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    return response.choices[0].message.content or "有料note構成案を作成できませんでした。"

def save_paid_note_outline(platform: str, original_post: str, paid_note_outline: str) -> Path:
    """有料note構成案をストックとして保存する。"""
    save_dir = Path("posts/paid_note_outlines")
    save_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = save_dir / f"{timestamp}_{platform}_paid_note_outline.md"

    content = f"""
# 有料note構成案

## 投稿先
{platform}

## 元の投稿
{original_post}

## 有料note構成案
{paid_note_outline}
""".strip()

    file_path.write_text(content, encoding="utf-8")
    return file_path