

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
# Ko AI 🤖

Ko AI は、OpenAI API を利用した自分専用の AI アシスタントです。
ターミナル版とブラウザで使えるGUI版の両方に対応しています。

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

## プロジェクト構成

```
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

`.env` ファイルを作成し、OpenAI APIキーを設定します。

```env
OPENAI_API_KEY=ここにAPIキーを貼る
```

## 起動方法

ターミナル版:

```bash
python3 main.py
```

GUI版:

```bash
streamlit run app.py
```

## 主なコマンド

- `help`：使えるコマンドを表示
- `memo 内容`：メモを保存
- `memos`：保存したメモを表示
- `history`：会話履歴を表示
- `todo 内容`：ToDoを追加
- `todos`：未完了ToDoを表示
- `done 番号`：ToDoを完了
- `draft テーマ`：XとInstagram用の投稿下書きを作成
- `draftx テーマ`：X用の投稿下書きを作成
- `draftinsta テーマ`：Instagram用の投稿下書きを作成
- `draftshort テーマ`：ショート動画台本を作成
- `drafts`：保存した投稿下書きを表示
- `news テーマ`：ニュースを取得してSNS向けに整理
- `newsraw テーマ`：ニュースタイトルとURLだけ表示
- `exit`：終了

## 使用技術

- Python
- OpenAI API
- python-dotenv
- Google News RSS
- Streamlit
- pypdf

## 注意

`.env` には OpenAI APIキーを保存します。
このファイルは `.gitignore` によって GitHub には公開しません。

また、以下のファイルもGit管理から除外しています。

- `chat_history.txt`
- `memos.txt`
- `todos.txt`
- `drafts.txt`
- `news_results.txt`

## 今後追加予定

- PDF検索精度の向上
- Word / PowerPointファイル対応
- 会話履歴のGUI表示
- 音声入力
- Discord / LINE連携
- データベース対応
# Ko AI 🤖

Ko AI は、OpenAI API を利用した自分専用の AI アシスタントです。
ターミナル版とブラウザで使えるGUI版の両方に対応しています。

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

## プロジェクト構成

```
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

`.env` ファイルを作成し、OpenAI APIキーを設定します。

```env
OPENAI_API_KEY=ここにAPIキーを貼る
```

## 起動方法

ターミナル版:

```bash
python3 main.py
```

GUI版:

```bash
streamlit run app.py
```

## 主なコマンド

- `help`：使えるコマンドを表示
- `memo 内容`：メモを保存
- `memos`：保存したメモを表示
- `history`：会話履歴を表示
- `todo 内容`：ToDoを追加
- `todos`：未完了ToDoを表示
- `done 番号`：ToDoを完了
- `draft テーマ`：XとInstagram用の投稿下書きを作成
- `draftx テーマ`：X用の投稿下書きを作成
- `draftinsta テーマ`：Instagram用の投稿下書きを作成
- `draftshort テーマ`：ショート動画台本を作成
- `drafts`：保存した投稿下書きを表示
- `news テーマ`：ニュースを取得してSNS向けに整理
- `newsraw テーマ`：ニュースタイトルとURLだけ表示
- `exit`：終了

## 使用技術

- Python
- OpenAI API
- python-dotenv
- Google News RSS
- Streamlit
- pypdf

## 注意

`.env` には OpenAI APIキーを保存します。
このファイルは `.gitignore` によって GitHub には公開しません。

また、以下のファイルもGit管理から除外しています。

- `chat_history.txt`
- `memos.txt`
- `todos.txt`
- `drafts.txt`
- `news_results.txt`

## 今後追加予定

- PDF検索精度の向上
- Word / PowerPointファイル対応
- 会話履歴のGUI表示
- 音声入力
- Discord / LINE連携
- データベース対応