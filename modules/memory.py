from datetime import datetime
from pathlib import Path

HISTORY_FILE = Path("chat_history.txt")
MEMO_FILE = Path("memos.txt")
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
    else:
        print("\n📄 削除する会話履歴はありません。")


def save_memo(text: str) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with MEMO_FILE.open("a", encoding="utf-8") as file:
        file.write(f"[{now}] {text}\n")

    print("\n📝 メモを保存しました。")


def show_memos() -> None:
    if not MEMO_FILE.exists():
        print("\n📝 まだメモはありません。")
        return

    memos = MEMO_FILE.read_text(encoding="utf-8").strip()

    if not memos:
        print("\n📝 まだメモはありません。")
        return

    print("\n📝 保存済みメモ")
    print("-" * 50)
    print(memos)
    print("-" * 50)


def load_memos() -> str:
    if not MEMO_FILE.exists():
        return ""

    return MEMO_FILE.read_text(encoding="utf-8").strip()