from datetime import datetime
from pathlib import Path

from openai import OpenAI


IMAGE_PROMPTS_FILE = Path("image_prompts.txt")
IMAGE_PROMPTS_DIR = Path("posts/image_prompts")


def generate_image_prompt(client: OpenAI, theme: str) -> str:
    prompt = f"""
あなたはSNS向け画像制作に強いプロンプトエンジニアです。

テーマ:
{theme}

ChatGPTの画像生成に貼り付けるための画像生成プロンプトを作ってください。

条件:
・Instagramの1枚目に使える正方形画像
・日本語タイトル入り
・初心者にも伝わるデザイン
・白、青、黒を基調
・AI、ビジネス、副業感が伝わる
・Canva風で見やすい
・そのまま画像生成AIに貼れる文章にする
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "あなたは優秀な画像生成プロンプトエンジニアです。",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.8,
    )

    return response.choices[0].message.content


def save_image_prompt(theme: str, image_prompt: str) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with IMAGE_PROMPTS_FILE.open("a", encoding="utf-8") as file:
        file.write(f"\n[{now}] テーマ: {theme}\n")
        file.write("-" * 50 + "\n")
        file.write(image_prompt)
        file.write("\n" + "=" * 50 + "\n")

    IMAGE_PROMPTS_DIR.mkdir(parents=True, exist_ok=True)

    safe_theme = "".join(
        c if c.isalnum() else "_"
        for c in theme
    ).strip("_")

    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_theme}.txt"

    (IMAGE_PROMPTS_DIR / filename).write_text(
        image_prompt,
        encoding="utf-8",
    )