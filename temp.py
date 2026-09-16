import os

from dotenv import load_dotenv
from litellm import token_counter

PNG_DATA_URL = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAF/gL+WjR4jwAAAABJRU5ErkJggg=="
)


def count(label: str, messages: list[dict], model: str) -> int:
    tokens = token_counter(model=model, messages=messages)
    print(f"{label}: {tokens} tokens")
    return tokens


def main() -> None:
    load_dotenv()
    model = os.getenv("MODEL")
    print(f"Tokenizer model: {model}\n")

    text_only = [{"role": "user", "content": "Describe this image briefly."}]
    image_low = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image briefly."},
                {
                    "type": "image_url",
                    "image_url": {"url": PNG_DATA_URL, "detail": "low"},
                },
            ],
        }
    ]
    image_high = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image briefly."},
                {
                    "type": "image_url",
                    "image_url": {"url": PNG_DATA_URL, "detail": "high"},
                },
            ],
        }
    ]

    text_tokens = count("Text only", text_only, model)
    low_tokens = count("Text + image (low detail)", image_low, model)
    high_tokens = count("Text + image (high detail)", image_high, model)

    if low_tokens <= text_tokens or high_tokens <= text_tokens:
        raise RuntimeError("Image tokens were not added to the message count.")

    print("\nPASS: LiteLLM counted both text and image_url content.")


if __name__ == "__main__":
    main()
