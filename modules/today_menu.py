from datetime import datetime
from pathlib import Path

from openai import OpenAI


EXCLUDE_STOCK_KEYWORDS = [
    "出産二次創作",
    "出産シーン",
    "ゲームキャラの“出産",
    "ゲームキャラの出産",
]


def should_exclude_stock(content: str) -> bool:
    """今日の投稿メニューや分析に使わないストックを判定する。"""
    return any(keyword in content for keyword in EXCLUDE_STOCK_KEYWORDS)


def load_recent_stock(max_chars: int = 6000) -> str:
    """保存済み投稿ストックを読み込む。"""
    stock_sources = [
        ("posts/x", "X投稿"),
        ("posts/instagram", "Instagram投稿"),
        ("posts/threads", "Threads投稿"),
        ("posts/note", "note記事"),
        ("posts/ideas", "アイデア"),
        ("posts/reviewed", "改善済み投稿"),
        ("posts/monetization", "収益導線案"),
        ("posts/paid_note_outlines", "有料note構成案"),
        ("posts/freebies", "無料特典"),
        ("posts/paid_note_drafts", "有料note本文"),
        ("posts/sales_funnels", "販売導線まとめ"),
        ("posts/calendars", "投稿カレンダー"),
        ("posts/weekly_posts", "7日分実投稿"),
        ("posts/today_menus", "今日の投稿メニュー"),
        ("posts/stock_analysis", "投稿ストック分析"),
    ]

    stock_texts = []

    for folder, label in stock_sources:
        folder_path = Path(folder)
        if not folder_path.exists():
            continue

        files = sorted(folder_path.glob("*"), reverse=True)

        for file_path in files[:3]:
            if not file_path.is_file():
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception:
                continue

            if should_exclude_stock(content):
                continue

            stock_texts.append(
                f"""
【種類】
{label}

【ファイル】
{file_path}

【内容】
{content[:1200]}
""".strip()
            )

    if not stock_texts:
        return "保存済み投稿ストックはまだありません。"

    joined_text = "\n\n---\n\n".join(stock_texts)
    return joined_text[:max_chars]


def create_today_post_menu(client: OpenAI, stock_text: str) -> str:
    """保存済みストックから今日の投稿メニューを作る。"""
    today = datetime.now().strftime("%Y-%m-%d")

    prompt = f"""
あなたはSNS運用とコンテンツ販売に強い編集者です。
以下の保存済み投稿ストックをもとに、今日やるべき投稿メニューを作ってください。

【今日の日付】
{today}

【目的】
今日の投稿作業を迷わず進められるようにすること。
特に、保存・フォロー・note購入・無料特典・有料コンテンツ販売につながる行動を優先してください。
AI副業、SNS運用、自動化、投稿作成ノウハウ、無料特典、有料note販売に近いテーマを優先してください。
著作権・性的表現・炎上リスクが高い二次創作系テーマは避けてください。

【出力形式】
1. 今日いちばん投稿すべき内容
2. その理由
3. 今日投稿する文章案
4. 最後に入れるCTA
5. 余力があればやること
6. note・有料noteにつなげるならどうするか
7. 明日につなげる投稿案

【保存済み投稿ストック】
{stock_text}
""".strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "あなたはSNS投稿を収益化につなげる運用担当です。今日やるべきことを具体的に指示してください。",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    return response.choices[0].message.content or "今日の投稿メニューを作成できませんでした。"


def save_today_post_menu(today_menu: str) -> Path:
    """今日の投稿メニューを保存する。"""
    save_dir = Path("posts/today_menus")
    save_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = save_dir / f"{timestamp}_today_menu.md"

    content = f"""
# 今日の投稿メニュー

{today_menu}
""".strip()

    file_path.write_text(content, encoding="utf-8")
    return file_path

def create_stock_analysis(client: OpenAI, stock_text: str) -> str:
    """保存済み投稿ストックを分析し、収益化候補を出す。"""
    prompt = f"""
あなたはSNS運用とコンテンツ販売に強い編集者です。
以下の保存済み投稿ストックを分析し、収益化につながりやすい投稿や次に伸ばすべき方向性を整理してください。

【目的】
保存した投稿をただ貯めるだけでなく、どの投稿を使えばフォロー・保存・note購入・無料特典・有料コンテンツ販売につながりやすいか判断すること。
AI副業、SNS運用、自動化、投稿作成ノウハウ、無料特典、有料note販売に近いテーマを優先してください。
著作権・性的表現・炎上リスクが高い二次創作系テーマは低評価にしてください。

【出力形式】
1. 今あるストック全体の傾向
2. 収益化に使いやすい投稿テーマTOP5
3. 有料note化しやすいテーマTOP5
4. 無料特典にしやすいテーマTOP5
5. 今日すぐ使うべき投稿
6. 伸ばすために足りない投稿タイプ
7. 次に作るべき投稿テーマ10個
8. 収益化に向けた次の行動

【保存済み投稿ストック】
{stock_text}
""".strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "あなたは保存済みのSNS投稿ストックを分析し、収益化につなげる編集長です。実用的に判断してください。",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    return response.choices[0].message.content or "投稿ストック分析を作成できませんでした。"


def save_stock_analysis(stock_analysis: str) -> Path:
    """投稿ストック分析を保存する。"""
    save_dir = Path("posts/stock_analysis")
    save_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = save_dir / f"{timestamp}_stock_analysis.md"

    content = f"""
# 投稿ストック分析

{stock_analysis}
""".strip()

    file_path.write_text(content, encoding="utf-8")
    return file_path