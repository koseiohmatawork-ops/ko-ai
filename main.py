from dotenv import load_dotenv
from openai import OpenAI

from modules.ai import ask_ko_ai
from modules.commands import handle_command
from modules.memory import save_history

load_dotenv()
client = OpenAI()

def main() -> None:
    """Ko AIを起動する。"""
    print("=" * 50)
    print("🤖 Ko AI Ver.3.8")
    print("main関数を追加して起動処理を整理しました")
    print("help と入力すると使えるコマンドを確認できます")
    print("=" * 50)

    while True:
        user_input = input("\nあなた > ").strip()

        if not user_input:
            print("入力が空です。何か入力してください。")
            continue

        command = user_input.lower()

        command_handled, should_exit = handle_command(client, user_input, command)

        if should_exit:
            break

        if command_handled:
            continue

        save_history("あなた", user_input)

        try:
            ai_text = ask_ko_ai(client, user_input)
            print(f"\n🤖 Ko AI > {ai_text}")
            save_history("Ko AI", ai_text)

        except Exception as e:
            error_message = str(e)
            print(f"\n❌ エラーが発生しました。\n{error_message}")
            save_history("エラー", error_message)


if __name__ == "__main__":
    main()