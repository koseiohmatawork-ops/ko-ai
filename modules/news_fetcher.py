import feedparser


RSS_URLS = [
    "https://news.google.com/rss/search?q=AI&hl=ja&gl=JP&ceid=JP:ja",
    "https://news.google.com/rss/search?q=人工知能&hl=ja&gl=JP&ceid=JP:ja",
    "https://news.google.com/rss/search?q=生成AI&hl=ja&gl=JP&ceid=JP:ja",
]


def fetch_ai_news(limit: int = 5) -> str:
    news_items = []

    for url in RSS_URLS:
        feed = feedparser.parse(url)

        for entry in feed.entries[:limit]:
            title = entry.get("title", "")
            link = entry.get("link", "")
            published = entry.get("published", "")

            news_items.append(
                f"タイトル: {title}\n"
                f"公開日: {published}\n"
                f"URL: {link}"
            )

    if not news_items:
        return "ニュースを取得できませんでした。"

    return "\n\n---\n\n".join(news_items[:limit])