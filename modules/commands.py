from modules.config import COMMANDS
from modules.daily import get_daily_plan
from modules.memory import clear_history, save_history, save_memo, show_history, show_memos
from modules.news import fetch_google_news, save_news_result, show_raw_news, summarize_news_for_sns
from modules.sns import (
    clear_drafts,
    create_instagram_draft,
    create_short_video_script,
    create_sns_draft,
    create_x_draft,
    save_draft,
    show_drafts,
)
from modules.status import get_app_status
from modules.todo import add_todo, complete_todo, show_todos


def show_help() -> None:
    print("\n📌 使えるコマンド")
    print("-" * 50)
    for command, description in COMMANDS.items():
        print(f"{command:<12} : {description}")
    print("-" * 50)


def handle_command(client, user_input: str, command: str) -> tuple[bool, bool]:
    if command == "exit":
        print("👋 Ko AI を終了します。")
        return True, True

    if command == "help":
        show_help()
        return True, False

    if command == "check":
        print(f"\n{get_app_status()}")
        return True, False

    if command == "daily":
        print(f"\n{get_daily_plan()}")
        return True, False

    if command == "history":
        show_history()
        return True, False

    if command == "clear":
        clear_history()
        return True, False

    if command.startswith("memo "):
        memo_text = user_input[5:].strip()
        if not memo_text:
            print("\nメモ内容が空です。例: memo AI投稿アカウントを作る")
            return True, False
        save_memo(memo_text)
        return True, False

    if command == "memo":
        print("\nメモ内容を入力してください。例: memo AI投稿アカウントを作る")
        return True, False

    if command == "memos":
        show_memos()
        return True, False

    if command.startswith("todo "):
        todo_text = user_input[5:].strip()
        if not todo_text:
            print("\nToDo内容が空です。例: todo ニュース収集機能を作る")
            return True, False
        add_todo(todo_text)
        return True, False

    if command == "todo":
        print("\nToDo内容を入力してください。例: todo ニュース収集機能を作る")
        return True, False

    if command == "todos":
        show_todos()
        return True, False

    if command.startswith("done "):
        complete_todo(user_input[5:].strip())
        return True, False

    if command == "done":
        print("\n完了するToDo番号を入力してください。例: done 1")
        return True, False

    if command.startswith("draft "):
        topic = user_input[6:].strip()
        draft_text = create_sns_draft(client, topic)
        print(f"\n📝 SNS投稿下書き\n{'-' * 50}\n{draft_text}\n{'-' * 50}")
        save_draft(topic, draft_text)
        return True, False

    if command == "draft":
        print("\n投稿テーマを入力してください。例: draft AI副業の注意点")
        return True, False

    if command.startswith("draftx "):
        topic = user_input[7:].strip()
        draft_text = create_x_draft(client, topic)
        print(f"\n📝 X投稿下書き\n{'-' * 50}\n{draft_text}\n{'-' * 50}")
        save_draft(f"X: {topic}", draft_text)
        return True, False

    if command == "draftx":
        print("\n投稿テーマを入力してください。例: draftx AI副業の注意点")
        return True, False

    if command.startswith("draftinsta "):
        topic = user_input[11:].strip()
        draft_text = create_instagram_draft(client, topic)
        print(f"\n📝 Instagram投稿下書き\n{'-' * 50}\n{draft_text}\n{'-' * 50}")
        save_draft(f"Instagram: {topic}", draft_text)
        return True, False

    if command == "draftinsta":
        print("\n投稿テーマを入力してください。例: draftinsta AI副業の注意点")
        return True, False

    if command.startswith("draftshort "):
        topic = user_input[11:].strip()
        draft_text = create_short_video_script(client, topic)
        print(f"\n🎬 ショート動画台本\n{'-' * 50}\n{draft_text}\n{'-' * 50}")
        save_draft(f"ShortVideo: {topic}", draft_text)
        return True, False

    if command == "draftshort":
        print("\n投稿テーマを入力してください。例: draftshort AI副業の注意点")
        return True, False

    if command == "drafts":
        show_drafts()
        return True, False

    if command == "cleardrafts":
        clear_drafts()
        return True, False

    if command.startswith("newsraw "):
        topic = user_input[8:].strip()
        news_items = fetch_google_news(topic)
        show_raw_news(topic, news_items)
        return True, False

    if command == "newsraw":
        print("\nニュース検索テーマを入力してください。例: newsraw OpenAI")
        return True, False

    if command.startswith("news "):
        topic = user_input[5:].strip()
        news_items = fetch_google_news(topic)
        summary = summarize_news_for_sns(client, topic, news_items)
        print(f"\n📰 ニュース収集結果\n{'-' * 50}\n{summary}\n{'-' * 50}")
        save_news_result(topic, summary, news_items)
        return True, False

    if command == "news":
        print("\nニュース検索テーマを入力してください。例: news AI 副業")
        return True, False

    return False, False