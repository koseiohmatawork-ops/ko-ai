

from datetime import datetime
from pathlib import Path

TODO_FILE = Path("todos.txt")


def add_todo(text: str) -> None:
    """ToDoを追加する。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with TODO_FILE.open("a", encoding="utf-8") as file:
        file.write(f"[ ] [{now}] {text}\n")

    print("\n✅ ToDoを追加しました。")


def load_todos() -> list[str]:
    """ToDo一覧を読み込む。"""
    if not TODO_FILE.exists():
        return []

    return TODO_FILE.read_text(encoding="utf-8").splitlines()


def show_todos() -> None:
    """未完了のToDoを表示する。"""
    todos = load_todos()
    active_todos = [todo for todo in todos if todo.startswith("[ ]")]

    if not active_todos:
        print("\n✅ 未完了のToDoはありません。")
        return

    print("\n✅ 未完了ToDo")
    print("-" * 50)
    for index, todo in enumerate(active_todos, start=1):
        print(f"{index}. {todo}")
    print("-" * 50)


def complete_todo(todo_number_text: str) -> None:
    """指定した番号のToDoを完了にする。"""
    if not todo_number_text.isdigit():
        print("\n番号を入力してください。例: done 1")
        return

    target_number = int(todo_number_text)
    todos = load_todos()
    active_indexes = [
        index for index, todo in enumerate(todos) if todo.startswith("[ ]")
    ]

    if target_number < 1 or target_number > len(active_indexes):
        print("\nその番号の未完了ToDoはありません。")
        return

    target_index = active_indexes[target_number - 1]
    todos[target_index] = todos[target_index].replace("[ ]", "[x]", 1)

    TODO_FILE.write_text("\n".join(todos) + "\n", encoding="utf-8")
    print("\n🎉 ToDoを完了にしました。")