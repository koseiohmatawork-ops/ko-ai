from datetime import datetime
from pathlib import Path

from openai import OpenAI

DRAFT_FILE = Path("drafts.txt")


def create_sns_draft(client: OpenAI, topic: str) -> str:
    prompt = f"""
あなたはSNS運用のプロです。
以下のテーマについて、XとInstagram向けの投稿下書きを作ってください。

テーマ:
{topic}

条件:
- 日本語
- 大学生にも自然な文体
- あおりすぎない
- 怪しい副業感を出さない
- X用は短め
- Instagram用は少し詳しめ
- 最後にハッシュタグを5個つける

出力形式:
【X投稿】
本文

【Instagram投稿】
本文

【ハッシュタグ】
#〇〇 #〇〇 #〇〇 #〇〇 #〇〇
""".strip()

    response = client.responses.create(model="gpt-4.1-mini", input=prompt)
    return response.output_text


def create_x_draft(client: OpenAI, topic: str) -> str:
    prompt = f"""
あなたはX運用のプロです。
以下のテーマについて、X向けの投稿下書きを3パターン作ってください。

テーマ:
{topic}

条件:
- 日本語
- 大学生にも自然な文体
- あおりすぎない
- 怪しい副業感を出さない
- 1投稿あたり140字以内を目安にする
- 最後に使えそうなハッシュタグを3個つける

出力形式:
【X投稿案1】
本文

【X投稿案2】
本文

【X投稿案3】
本文

【ハッシュタグ】
#〇〇 #〇〇 #〇〇
""".strip()

    response = client.responses.create(model="gpt-4.1-mini", input=prompt)
    return response.output_text


def create_instagram_draft(client: OpenAI, topic: str) -> str:
    prompt = f"""
あなたはInstagram運用のプロです。
以下のテーマについて、Instagram向けの投稿下書きを作ってください。

テーマ:
{topic}

条件:
- 日本語
- 大学生にも自然な文体
- あおりすぎない
- 怪しい副業感を出さない
- 冒頭1行で興味を引く
- 本文は読みやすく改行する
- 箇条書きを使う
- 最後に保存を促す一文を入れる
- ハッシュタグを8個つける

出力形式:
【1枚目の見出し】
見出し

【本文】
本文

【ハッシュタグ】
#〇〇 #〇〇 #〇〇 #〇〇 #〇〇 #〇〇 #〇〇 #〇〇
""".strip()

    response = client.responses.create(model="gpt-4.1-mini", input=prompt)
    return response.output_text


def create_short_video_script(client: OpenAI, topic: str) -> str:
    prompt = f"""
あなたはショート動画構成のプロです。
以下のテーマについて、TikTok・Instagram Reels・YouTube Shorts向けの台本を作ってください。

テーマ:
{topic}

条件:
- 日本語
- 30〜45秒程度
- 顔出しなしでも作れる内容
- 冒頭3秒で興味を引く
- 怪しい副業感を出さない
- テロップ案も入れる
- 最後にフォローにつながる自然な一言を入れる

出力形式:
【タイトル】
タイトル

【冒頭3秒】
話す内容 / テロップ

【本編】
話す内容 / テロップ

【締め】
話す内容 / テロップ

【必要な素材】
素材リスト
""".strip()

    response = client.responses.create(model="gpt-4.1-mini", input=prompt)
    return response.output_text


def save_draft(topic: str, draft_text: str) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with DRAFT_FILE.open("a", encoding="utf-8") as file:
        file.write("=" * 50 + "\n")
        file.write(f"[{now}] テーマ: {topic}\n")
        file.write(draft_text + "\n")


def show_drafts() -> None:
    if not DRAFT_FILE.exists():
        print("\n📝 まだ投稿下書きはありません。")
        return

    drafts = DRAFT_FILE.read_text(encoding="utf-8").strip()

    if not drafts:
        print("\n📝 まだ投稿下書きはありません。")
        return

    print("\n📝 保存済みSNS投稿下書き")
    print("-" * 50)
    print(drafts)
    print("-" * 50)


def clear_drafts() -> None:
    if not DRAFT_FILE.exists():
        print("\n📝 削除する投稿下書きはありません。")
        return

    DRAFT_FILE.unlink()
    print("\n🗑️ SNS投稿下書きをすべて削除しました。")