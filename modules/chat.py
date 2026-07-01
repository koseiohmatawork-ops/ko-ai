from openai import OpenAI


def chat_with_ai(client: OpenAI, message: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "あなたは『Ko AI』という日本語AIアシスタントです。"
                    "分かりやすく、丁寧に、簡潔に回答してください。"
                ),
            },
            {
                "role": "user",
                "content": message,
            },
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content