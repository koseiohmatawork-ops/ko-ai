

from openai import OpenAI

from modules.config import SYSTEM_PROMPT
from modules.memory import load_memos, load_recent_history
from modules.todo import load_todos


def build_prompt(user_input: str) -> str:
    """Ko AIに送るプロンプトを作る。"""
    recent_history = load_recent_history()
    memos = load_memos()
    todos = "\n".join(load_todos())

    return f"""
{SYSTEM_PROMPT}

以下はユーザーが保存した重要メモです。
返答に必要なら積極的に参考にしてください。

{memos}

以下はユーザーのToDo一覧です。
作業提案や優先順位付けが必要な場合に参考にしてください。

{todos}

以下は直近の会話履歴です。
必要な場合だけ参考にしてください。

{recent_history}

今回のユーザー入力:
{user_input}
""".strip()


def ask_ko_ai(client: OpenAI, user_input: str) -> str:
    """OpenAI APIに質問して、Ko AIの返答を取得する。"""
    prompt = build_prompt(user_input)

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
    )

    return response.output_text