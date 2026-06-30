from datetime import datetime


def get_daily_plan() -> str:
    today = datetime.now().strftime("%Y-%m-%d")

    return f"""
📅 今日のAI作業 ({today})

1. 📰 AIニュースを3件チェック
2. ✍️ SNS投稿を1件作成
3. 📄 PDFを1つ要約
4. ✅ ToDoを確認
5. 🧠 新しく覚えたことをMemoryへ保存

今日も頑張ろう！
""".strip()