from pypdf import PdfReader


def extract_text_from_pdf(uploaded_file) -> str:
    reader = PdfReader(uploaded_file)
    pages_text = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages_text.append(f"--- {page_number}ページ目 ---\n{text}")

    return "\n\n".join(pages_text).strip()


def ask_pdf_question(client, pdf_text: str, question: str) -> str:
    prompt = f"""
あなたはPDF内容をもとに質問へ答えるAIです。
以下のPDF本文だけを根拠にして、日本語で答えてください。

PDF本文:
{pdf_text}

質問:
{question}
""".strip()

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
    )

    return response.output_text