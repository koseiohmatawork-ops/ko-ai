import json
from datetime import datetime
from pathlib import Path

HISTORY_FILE = Path("chat_history.txt")
MEMO_FILE = Path("memos.txt")
MEMORY_FILE = Path("memory.json")
MAX_HISTORY_LINES = 20


def save_history(role: str, text: str) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with HISTORY_FILE.open("a", encoding="utf-8") as file:
        file.write(f"[{now}] {role}: {text}\n")


def load_recent_history() -> str:
    if not HISTORY_FILE.exists():
        return ""

    lines = HISTORY_FILE.read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[-MAX_HISTORY_LINES:])


def save_memo(text: str) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with MEMO_FILE.open("a", encoding="utf-8") as file:
        file.write(f"[{now}] {text}\n")

    print("\n📝 メモを保存しました。")


def show_memos() -> None:
    if not MEMO_FILE.exists():
        print("\n📝 まだメモはありません。")
        return

    print(MEMO_FILE.read_text(encoding="utf-8"))


def load_memos() -> str:
    if not MEMO_FILE.exists():
        return ""

    return MEMO_FILE.read_text(encoding="utf-8").strip()


def show_history() -> None:
    history = load_recent_history()
    if not history:
        print("\n📄 まだ会話履歴はありません。")
        return

    print("\n📄 直近の会話履歴")
    print("-" * 50)
    print(history)
    print("-" * 50)


def clear_history() -> None:
    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()
        print("\n🧹 会話履歴を削除しました。")


def load_memory_data() -> dict:
    if not MEMORY_FILE.exists():
        return {"memories": []}

    try:
        data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"memories": []}

    if "memories" not in data:
        data["memories"] = []

    return data


def save_memory_data(data: dict) -> None:
    MEMORY_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def remember_text(text: str) -> str:
    text = text.strip()

    if not text:
        return "覚える内容が空です。"

    data = load_memory_data()

    if text not in data["memories"]:
        data["memories"].append(text)
        save_memory_data(data)

    return f"覚えました: {text}"


def forget_text(keyword: str) -> str:
    keyword = keyword.strip()

    if not keyword:
        return "忘れる内容が空です。"

    data = load_memory_data()
    before_count = len(data["memories"])

    data["memories"] = [
        memory for memory in data["memories"] if keyword not in memory
    ]

    after_count = len(data["memories"])
    save_memory_data(data)

    if before_count == after_count:
        return f"「{keyword}」に関する記憶は見つかりませんでした。"

    return f"「{keyword}」に関する記憶を削除しました。"


def get_long_term_memory_text() -> str:
    data = load_memory_data()
    memories = data.get("memories", [])

    if not memories:
        return ""

    return "\n".join(f"- {memory}" for memory in memories)