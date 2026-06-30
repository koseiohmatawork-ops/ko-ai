from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus
from urllib.request import urlopen
import xml.etree.ElementTree as ET

from openai import OpenAI

NEWS_FILE = Path("news_results.txt")


def fetch_google_news(topic: str, max_items: int = 5) -> list[dict[str, str]]:
    """GoogleニュースRSSから指定テーマのニュースを取得する。"""
    encoded_topic = quote_plus(topic)
    url = (
        "https://news.google.com/rss/search"
        f"?q={encoded_topic}&hl=ja&gl=JP&ceid=JP:ja"
    )

    with urlopen(url, timeout=10) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)
    items = root.findall("./channel/item")[:max_items]

    news_items = []
    for item in items:
        news_items.append(
            {
                "title": item.findtext("title", default="タイトルなし"),
                "link": item.findtext("link", default=""),
                "published": item.findtext("pubDate", default="日時不明"),
            }
        )

    return news_items


def summarize_news_for_sns(
    client: OpenAI,
    topic: str,
    news_items: list[dict[str, str]],
) -> str:
    """ニュースタイトルをSNS投稿ネタとして安全に整理する。"""
    if not news_items:
        return "ニュースが見つかりませんでした。"

    news_text = "\n".join(
        f"{index}. タイトル: {item['title']}\nURL: {item['link']}\n日時: {item['published']}"
        for index, item in enumerate(news_items, start=1)
    )

    prompt = f"""
あなたはSNS運用とニュース整理のプロです。
以下のGoogleニュースRSSの検索結果をもとに、SNS投稿のネタとして使える形に整理してください。

重要:
- あなたは記事本文を読んでいません。
- 判断できるのは、ニュースタイトル・URL・日時から分かる範囲だけです。
- タイトルから断定できない内容を事実のように書かないでください。
- 推測する場合は、必ず「推測」と明記してください。
- 架空の発表、存在しない製品名、未確認の数値を作らないでください。
- OpenAIやAI業界など変化が速い話題では特に慎重に書いてください。

検索テーマ:
{topic}

ニュース一覧:
{news_text}

出力条件:
- 日本語
- 事実と推測を分ける
- あおりすぎない
- 怪しい副業感を出さない
- 大学生にもわかる言葉で説明する
- 最後にSNS投稿テーマ案を3つ出す
- 最後に「投稿前に元記事確認が必要」と明記する

出力形式:
【確認できる事実】
・タイトルから確認できることだけを書く

【推測・考えられる流れ】
・推測を書く場合は必ず「推測」と書く

【注意点】
・記事本文は未確認であること
・投稿前に元記事確認が必要であること

【SNS投稿テーマ案】
1. テーマ案
2. テーマ案
3. テーマ案

【参照URL】
1. URL
2. URL
3. URL
""".strip()

    response = client.responses.create(model="gpt-4.1-mini", input=prompt)
    return response.output_text


def save_news_result(
    topic: str,
    summary: str,
    news_items: list[dict[str, str]],
) -> None:
    """ニュース取得結果を保存する。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with NEWS_FILE.open("a", encoding="utf-8") as file:
        file.write("=" * 50 + "\n")
        file.write(f"[{now}] 検索テーマ: {topic}\n")
        file.write(summary + "\n\n")
        file.write("【参照ニュース】\n")
        for index, item in enumerate(news_items, start=1):
            file.write(f"{index}. {item['title']}\n")
            file.write(f"   {item['link']}\n")


def show_raw_news(topic: str, news_items: list[dict[str, str]]) -> None:
    """AI要約なしでニュースタイトルとURLだけ表示する。"""
    if not news_items:
        print("\nニュースが見つかりませんでした。")
        return

    print("\n📰 ニュース一覧（AI要約なし）")
    print("-" * 50)
    print(f"検索テーマ: {topic}\n")

    for index, item in enumerate(news_items, start=1):
        print(f"{index}. {item['title']}")
        print(f"   日時: {item['published']}")
        print(f"   URL: {item['link']}\n")

    print("-" * 50)