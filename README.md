

# Ko AI 🤖

Ko AI は、OpenAI API を利用した自分専用の AI アシスタントです。

## 主な機能

- AIチャット
- 会話履歴の保存
- メモ保存
- ToDo管理
- SNS投稿下書き作成
- ショート動画台本作成
- Googleニュース取得

## プロジェクト構成

```
ko-ai/
├── main.py
├── modules/
│   ├── ai.py
│   ├── commands.py
│   ├── config.py
│   ├── memory.py
│   ├── news.py
│   ├── sns.py
│   └── todo.py
├── README.md
├── requirements.txt
└── .env
```

## 起動方法

```bash
python3 main.py
```

## 主なコマンド

- help
- memo
- memos
- history
- todo
- todos
- done
- draft
- draftx
- draftinsta
- draftshort
- drafts
- news
- newsraw
- exit

## 使用技術

- Python
- OpenAI API
- python-dotenv
- Google News RSS

## 今後追加予定

- 音声入力
- Discord連携
- LINE連携
- GUI化
- データベース対応