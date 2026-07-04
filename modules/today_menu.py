from datetime import datetime
from pathlib import Path
import shutil

from openai import OpenAI


EXCLUDE_STOCK_KEYWORDS = [
    "出産二次創作",
    "出産シーン",
    "ゲームキャラの“出産",
    "ゲームキャラの出産",
]


def should_exclude_stock(content: str, keywords: list[str] | None = None) -> bool:
    """今日の投稿メニューや分析に使わないストックを判定する。"""
    target_keywords = keywords or EXCLUDE_STOCK_KEYWORDS
    return any(keyword in content for keyword in target_keywords)

def archive_excluded_stock(keywords: list[str] | None = None) -> list[str]:
    """除外対象キーワードを含む投稿ストックをarchiveへ移動する。"""
    stock_folders = [
        "posts/note",
        "posts/x",
        "posts/instagram",
        "posts/threads",
        "posts/ideas",
        "posts/reviewed",
        "posts/monetization",
        "posts/paid_note_outlines",
        "posts/freebies",
        "posts/paid_note_drafts",
        "posts/sales_funnels",
        "posts/template_posts",
        "posts/calendars",
        "posts/weekly_posts",
        "posts/today_menus",
        "posts/stock_analysis",
        "posts/stock_cleanup",
    ]

    moved_files = []
    archive_dir = Path("posts/archive")
    archive_dir.mkdir(parents=True, exist_ok=True)

    for folder in stock_folders:
        folder_path = Path(folder)
        if not folder_path.exists():
            continue

        for file_path in folder_path.glob("*"):
            if not file_path.is_file():
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception:
                continue

            if not should_exclude_stock(content, keywords):
                continue

            destination = archive_dir / file_path.name
            if destination.exists():
                destination = archive_dir / f"{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_path.suffix}"

            shutil.move(str(file_path), str(destination))
            moved_files.append(f"{file_path} -> {destination}")

    return moved_files


def load_recent_stock(max_chars: int = 6000) -> str:
    """保存済み投稿ストックを読み込む。"""
    stock_sources = [
        ("posts/stock_analysis_posts", "分析実投稿"),
        ("posts/today_menu_posts", "今日メニュー実投稿"),
        ("posts/template_posts", "テンプレ投稿"),
        ("posts/sales_funnels", "販売導線まとめ"),
        ("posts/results", "投稿反応メモ"),
        ("posts/freebies", "無料特典"),
        ("posts/paid_note_drafts", "有料note本文"),
        ("posts/paid_note_outlines", "有料note構成案"),
        ("posts/monetization", "収益導線案"),
        ("posts/reviewed", "改善済み投稿"),
        ("posts/calendars", "投稿カレンダー"),
        ("posts/weekly_posts", "7日分実投稿"),
        ("posts/today_menus", "今日の投稿メニュー"),
        ("posts/x", "X投稿"),
        ("posts/instagram", "Instagram投稿"),
        ("posts/threads", "Threads投稿"),
        ("posts/note", "note記事"),
        ("posts/ideas", "アイデア"),
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
AI副業、SNS運用、自動化、投稿作成ノウハウ、無料特典、有料note販売に近いテーマを最優先してください。
企業向けAI活用、法人向けDX、業務効率化だけの話、一般的なAIニュースだけの投稿は原則として選ばないでください。
今日いちばん投稿すべき内容は、必ず「個人がAIで副業を始める」「SNS投稿をAIで作る」「投稿作成を自動化する」「無料特典で見込み客を集める」「有料note販売につなげる」のどれかに寄せてください。
文章案の主語は、企業ではなく「個人」「初心者」「副業を始めたい人」「SNS運用を始めたい人」にしてください。
投稿反応メモがある場合は、反応が良かった投稿や改善点を参考にしてください。
分析実投稿がある場合は、次に投稿すべき具体案として最優先で参考にしてください。
テンプレ投稿がある場合は、保存されやすい型・共感型・無料特典誘導型・有料note誘導型を優先的に活用してください。
最後のCTAには、可能な限り無料特典・プロフィールリンク・note誘導のいずれかを入れてください。
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
                "content": "あなたはAI副業・SNS運用・無料特典・有料note販売に強いSNS運用担当です。今日やるべき収益化行動を具体的に指示してください。",
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
AI副業、SNS運用、自動化、投稿作成ノウハウ、無料特典、有料note販売に近いテーマを最優先してください。
企業向けAI活用、法人向けDX、業務効率化だけの話、一般的なAIニュースだけの投稿は、個人の副業・SNS運用・note販売につながらない限り優先度を下げてください。
評価するときは、企業向けの話題よりも「個人がすぐ実践できるAI副業」「SNS投稿作成」「無料特典」「有料note販売」に近いものを高く評価してください。
投稿反応メモがある場合は、反応が良かった投稿タイプ・伸びにくかった投稿タイプ・次に改善すべき点を分析に反映してください。
分析実投稿がある場合は、どの投稿案がすぐ投稿できて収益導線に近いかも評価してください。
テンプレ投稿がある場合は、どの型が収益導線に使いやすいかも評価してください。
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


def create_stock_cleanup_plan(client: OpenAI, stock_text: str) -> str:
    """保存済みストックから、今後使うもの・避けるものを整理する案を作る。"""
    prompt = f"""
あなたはSNS運用とコンテンツ販売に強い編集者です。
以下の保存済み投稿ストックを見て、今後の収益化に使うべきものと、使わない方がよいものを整理してください。

【目的】
Ko AIが今後、AI副業・SNS運用・投稿自動化・無料特典・有料note販売に寄った投稿を作れるように、ストックを整理すること。

【判断基準】
・AI副業、SNS運用、自動化、投稿作成ノウハウ、無料特典、有料note販売に近いものは残す
・企業向けAI活用、法人向けDX、業務効率化だけの話、一般的なAIニュースだけのものは、個人の副業・SNS運用・note販売につながらない場合は優先度を下げる
・個人がすぐ実践できるAI副業、SNS投稿作成、無料特典、有料note販売に近いものを優先する
・著作権、性的表現、炎上、二次創作リスクが高いものは避ける
・収益化につながりにくいものは優先度を下げる
・今後の投稿メニューに使うべきテーマを明確にする

【出力形式】
1. 今後も使うべきストック
2. 投稿反応メモを踏まえて伸ばすべき投稿パターン
3. テンプレ投稿の中で優先的に使うべき型
4. 優先して投稿に使うべきテーマ
5. archiveに移してもよいストック
6. 使わない方がよい理由
7. 今後作るべき安全な投稿テーマ10個
8. 今日からの運用ルール

【保存済み投稿ストック】
{stock_text}
""".strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "あなたは投稿ストックを整理し、収益化に使える安全なテーマへ寄せる編集長です。実用的に判断してください。",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    return response.choices[0].message.content or "投稿ストック整理案を作成できませんでした。"


def save_stock_cleanup_plan(cleanup_plan: str) -> Path:
    """投稿ストック整理案を保存する。"""
    save_dir = Path("posts/stock_cleanup")
    save_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = save_dir / f"{timestamp}_stock_cleanup.md"

    content = f"""
# 投稿ストック整理案

{cleanup_plan}
""".strip()

    file_path.write_text(content, encoding="utf-8")
    return file_path