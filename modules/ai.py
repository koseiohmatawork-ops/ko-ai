from openai import OpenAI

from modules.config import SYSTEM_PROMPT
from modules.memory import get_long_term_memory_text, load_memos, load_recent_history
from modules.todo import load_todos


def build_prompt(user_input: str) -> str:
    recent_history = load_recent_history()
    memos = load_memos()
    todos = "\n".join(load_todos())
    long_term_memory = get_long_term_memory_text()

    return f"""
{SYSTEM_PROMPT}

以下はユーザーの長期記憶です。
返答に必要なら参考にしてください。

{long_term_memory}

以下はユーザーが保存したメモです。

{memos}

以下はユーザーのToDo一覧です。

{todos}

以下は直近の会話履歴です。

{recent_history}

今回のユーザー入力:
{user_input}
""".strip()


def ask_ko_ai(client: OpenAI, user_input: str) -> str:
    prompt = build_prompt(user_input)

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
    )

    return response.output_text