# Ko AI 🤖


Ko AI は、OpenAI API を利用した自分専用の AI アシスタントです。  
ターミナル版とブラウザで使える GUI 版の両方に対応しています。

## 🌐 デモ（Web版）

https://fxg2etotgfixvckh74hhgq.streamlit.app

## 主な機能

- AIチャット
- 会話履歴の保存
- メモ保存
- ToDo管理
- SNS投稿下書き作成
- ショート動画台本作成
- Googleニュース取得
- StreamlitによるGUI表示
- PDFアップロードとPDF内容への質問回答
- 長期記憶の保存・表示
- 今日の作業メニュー表示

## プロジェクト構成

```text
ko-ai/
├── app.py
├── main.py
├── modules/
│   ├── ai.py
│   ├── commands.py
│   ├── config.py
│   ├── memory.py
│   ├── news.py
│   ├── pdf_reader.py
│   ├── sns.py
│   └── todo.py
├── README.md
├── requirements.txt
└── .env
```

## セットアップ

必要なライブラリをインストールします。

```bash
pip install -r requirements.txt
```

プロジェクト直下に `.env` ファイルを作成し、OpenAI APIキーを設定してください。

```env
OPENAI_API_KEY=あなたのAPIキー
```

## 起動方法

### ターミナル版

```bash
python3 main.py
```

### GUI版（Streamlit）

```bash
streamlit run app.py
```

ブラウザで以下のURLを開きます。

```
http://localhost:8501
```

## 主なコマンド

- `help`：使えるコマンドを表示
- `daily`：今日のAI作業メニューを表示
- `check`：Ko AIの現在の状態を確認
- `memo 内容`：メモを保存
- `memos`：保存したメモを表示
- `history`：会話履歴を表示
- `todo 内容`：ToDoを追加
- `todos`：未完了ToDoを表示
- `done 番号`：ToDoを完了
- `draft テーマ`：SNS投稿の下書きを作成
- `draftx テーマ`：X用の投稿下書きを作成
- `draftinsta テーマ`：Instagram用の投稿下書きを作成
- `draftshort テーマ`：ショート動画台本を作成
- `drafts`：保存した下書きを表示
- `news テーマ`：ニュースを取得して要約
- `newsraw テーマ`：ニュースタイトルとURLを表示
- `exit`：終了

## 使用技術

- Python
- OpenAI API
- Streamlit
- pypdf
- python-dotenv
- Google News RSS
- Git / GitHub

## 注意

以下のファイルは `.gitignore` によりGitHubへアップロードされません。

- `.env`
- `chat_history.txt`
- `memos.txt`
- `todos.txt`
- `drafts.txt`
- `news_results.txt`

## 今後追加予定

- PDF検索精度の向上（RAG）
- Word / PowerPoint対応
- 会話履歴のGUI表示
- 音声入力
- Discord / LINE連携
- データベース対応

## ライセンス

個人学習・ポートフォリオ用プロジェクト