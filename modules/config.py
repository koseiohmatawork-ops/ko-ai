SYSTEM_PROMPT = """
あなたは、ユーザー専用AI秘書「Ko AI」です。
以下のルールを必ず守ってください。

- 日本語で答える
- わかりやすく、短めに答える
- 必要なら順序立てて説明する
- ユーザーの作業を前に進めることを優先する
- プログラミング初心者にもわかる言葉を使う
""".strip()

COMMANDS = {
    "exit": "Ko AIを終了します",
    "help": "使えるコマンドを表示します",
    "daily": "今日のAI作業メニューを表示します",
    "check": "Ko AIの現在の状態を確認します",
    "history": "保存済みの会話履歴を表示します",
    "clear": "会話履歴を削除します",
    "memo": "残したいメモを保存します。例: memo AI投稿アカウントを作る",
    "memos": "保存したメモ一覧を表示します",
    "todo": "ToDoを追加します。例: todo ニュース収集機能を作る",
    "todos": "未完了のToDo一覧を表示します",
    "done": "ToDoを完了にします。例: done 1",
    "draft": "XとInstagram両方のSNS投稿下書きを作ります。例: draft AI副業の注意点",
    "draftx": "X専用の投稿下書きを作ります。例: draftx AI副業の注意点",
    "draftinsta": "Instagram専用の投稿下書きを作ります。例: draftinsta AI副業の注意点",
    "draftshort": "ショート動画台本を作ります。例: draftshort AI副業の注意点",
    "drafts": "保存したSNS投稿下書きを表示します",
    "cleardrafts": "保存済みのSNS投稿下書きをすべて削除します",
    "news": "GoogleニュースRSSからニュースを取得します。例: news AI 副業",
    "newsraw": "AI要約なしでニュースタイトルとURLだけ表示します。例: newsraw OpenAI",
}