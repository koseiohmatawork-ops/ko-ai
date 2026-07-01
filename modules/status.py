from modules.memory import get_long_term_memory_text, load_memos
from modules.todo import load_todos


def get_app_status() -> str:
    memory_text = get_long_term_memory_text()
    memory_count = len(memory_text.splitlines()) if memory_text else 0

    todos = load_todos()
    active_todos = [todo for todo in todos if todo.startswith("[ ]")]

    memos = load_memos()
    memo_status = "あり" if memos else "なし"

    return f"""
📊 Ko AI 状態チェック

🧠 長期記憶: {memory_count}件
✅ 未完了ToDo: {len(active_todos)}件
📝 メモ: {memo_status}
📄 PDF機能: あり
📅 daily機能: あり

状態: 正常
""".strip()