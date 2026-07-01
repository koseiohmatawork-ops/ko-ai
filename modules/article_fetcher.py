import re

import requests
from bs4 import BeautifulSoup


def extract_first_url(text: str) -> str:
    """文章の中から最初のURLだけ抜き出す。"""
    match = re.search(r"https?://\S+", text)

    if not match:
        return ""

    return match.group(0).strip()


def fetch_article(url_or_text: str) -> str:
    """URLまたはURLを含む文章から記事本文を取得する。"""
    url = extract_first_url(url_or_text)

    if not url:
        return "記事取得失敗: URLが見つかりませんでした。"

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 "
                "(Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/137.0 Safari/537.36"
            )
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")

        text = "\n".join(
            p.get_text(strip=True)
            for p in paragraphs
            if len(p.get_text(strip=True)) > 40
        )

        if not text:
            return "記事取得失敗: 本文を取得できませんでした。"

        return text[:6000]

    except Exception as e:
        return f"記事取得失敗: {e}"