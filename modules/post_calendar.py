from datetime import datetime
from pathlib import Path

from openai import OpenAI


def create_post_calendar(client: OpenAI, theme: str, platform: str = "SNS") -> str:
    """7日分の投稿カレンダーを作る。"""
    prompt = f"""
あなたはSNS運用、コンテンツ販売、投稿設計に強いマーケターです。
以下のテーマについて、{platform}向けの7日分投稿カレンダーを作ってください。

【目的】
単発投稿ではなく、1週間の流れで読者の興味を高め、保存・フォロー・note購入・商品購入につなげること。

【出力形式】
Day1: 悩み共感投稿
- 投稿テーマ
- 投稿内容
- 狙い
- CTA

Day2: ノウハウ投稿
- 投稿テーマ
- 投稿内容
- 狙い
- CTA

Day3: 失敗談・気づき投稿
- 投稿テーマ
- 投稿内容
- 狙い
- CTA

Day4: チェックリスト投稿
- 投稿テーマ
- 投稿内容
- 狙い
- CTA

Day5: 具体例投稿
- 投稿テーマ
- 投稿内容
- 狙い
- CTA

Day6: 有料note・無料特典への導線投稿
- 投稿テーマ
- 投稿内容
- 狙い
- CTA

Day7: まとめ・保存促進投稿
- 投稿テーマ
- 投稿内容
- 狙い
- CTA

最後に、この7日間の運用方針も短くまとめてください。

【テーマ】
{theme}
""".strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "あなたはSNS投稿を収益化につなげる投稿設計の専門家です。初心者でもそのまま使える具体的な投稿カレンダーを作ってください。",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    return response.choices[0].message.content or "投稿カレンダーを作成できませんでした。"


def save_post_calendar(theme: str, platform: str, calendar_text: str) -> Path:
    """投稿カレンダーを保存する。"""
    save_dir = Path("posts/calendars")
    save_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_theme = theme.replace("/", "_").replace(" ", "_")
    file_path = save_dir / f"{timestamp}_{platform}_{safe_theme}_calendar.md"

    content = f"""
# 7日分投稿カレンダー

## 投稿先
{platform}

## テーマ
{theme}

## 投稿カレンダー
{calendar_text}
""".strip()

    file_path.write_text(content, encoding="utf-8")
    return file_path

def create_weekly_posts(
    client: OpenAI,
    calendar_text: str,
    platform: str = "SNS",
) -> str:
    """投稿カレンダーから7日分の実投稿を作る。"""
    prompt = f"""
あなたはSNS投稿作成とコンテンツ販売に強いライターです。
以下の投稿カレンダーをもとに、{platform}向けの7日分の実投稿文を作ってください。

【目的】
投稿カレンダーの内容を、そのまま投稿できる具体的な文章に変換すること。
読者の共感・保存・フォロー・note購入につながる投稿にしてください。

【ルール】
- Day1〜Day7まで作る
- 各投稿はそのままSNSに投稿できる文章にする
- 冒頭で読む理由を作る
- 読みやすく改行する
- 最後にCTAを入れる
- 押し売り感は出さない
- {platform}向けの文体にする

【出力形式】
Day1 投稿文
本文

Day2 投稿文
本文

Day3 投稿文
本文

Day4 投稿文
本文

Day5 投稿文
本文

Day6 投稿文
本文

Day7 投稿文
本文

【投稿カレンダー】
{calendar_text}
""".strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "あなたはSNS投稿を収益化につなげるライターです。カレンダー内容を実際に投稿できる文章に変換してください。",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    return response.choices[0].message.content or "7日分の実投稿を作成できませんでした。"


def save_weekly_posts(theme: str, platform: str, weekly_posts: str) -> Path:
    """7日分の実投稿を保存する。"""
    save_dir = Path("posts/weekly_posts")
    save_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_theme = theme.replace("/", "_").replace(" ", "_")
    file_path = save_dir / f"{timestamp}_{platform}_{safe_theme}_weekly_posts.md"

    content = f"""
# 7日分実投稿

## 投稿先
{platform}

## テーマ
{theme}

## 実投稿
{weekly_posts}
""".strip()

    file_path.write_text(content, encoding="utf-8")
    return file_path