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