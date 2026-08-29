from .openai_client import OpenAIClient


def main():
    client = OpenAIClient()

    response = client.generate(
        system_prompt=(
            "You are AURA, an AI fraud investigation assistant. "
            "Analyze fraud-related information carefully. "
            "Do not claim that a transaction is fraudulent without sufficient evidence."
        ),
        user_prompt=(
            "Explain why transaction velocity can be an important "
            "fraud investigation signal."
        ),
    )

    print("\n=== GROQ RESPONSE ===\n")
    print(response)


if __name__ == "__main__":
    main()