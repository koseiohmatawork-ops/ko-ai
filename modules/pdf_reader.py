from pypdf import PdfReader


def extract_pages_from_pdf(uploaded_file) -> list[dict[str, str | int]]:
    """アップロードされたPDFからページごとにテキストを抽出する。"""
    reader = PdfReader(uploaded_file)
    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.strip()

        if text:
            pages.append(
                {
                    "page": page_number,
                    "text": text,
                }
            )

    return pages


def extract_text_from_pdf(uploaded_file) -> str:
    """従来用。アップロードされたPDFから全文テキストを抽出する。"""
    pages = extract_pages_from_pdf(uploaded_file)

    return "\n\n".join(
        f"--- {page['page']}ページ目 ---\n{page['text']}" for page in pages
    ).strip()


def find_relevant_pages(
    pdf_text: str,
    question: str,
    max_pages: int = 3,
) -> str:
    """質問に関係ありそうなページだけを簡易的に選ぶ。"""
    page_blocks = pdf_text.split("--- ")
    question_words = set(question.lower().split())
    scored_pages = []

    for block in page_blocks:
        block = block.strip()
        if not block:
            continue

        block_lower = block.lower()
        score = sum(1 for word in question_words if word in block_lower)

        scored_pages.append(
            {
                "score": score,
                "text": "--- " + block,
            }
        )

    scored_pages.sort(key=lambda item: item["score"], reverse=True)
    selected_pages = scored_pages[:max_pages]

    if not selected_pages:
        return pdf_text

    return "\n\n".join(item["text"] for item in selected_pages)


def ask_pdf_question(client, pdf_text: str, question: str) -> str:
    """PDF本文に対する質問へAIで回答する。"""
    relevant_text = find_relevant_pages(pdf_text, question)

    prompt = f"""
あなたはPDF内容をもとに質問へ答えるAIです。
以下のPDF本文だけを根拠にして、日本語で答えてください。

ルール:
- PDFに書かれていないことは断定しない
- わからない場合は「PDF内では確認できません」と答える
- 大学生にもわかる言葉で説明する
- 回答の最後に、根拠にしたページ番号を「参考ページ: 〇ページ目」の形で書く

PDF本文:
{relevant_text}

質問:
{question}
""".strip()

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
    )

    return response.output_text