import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class OpenAIClient:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

        if not api_key:
            raise ValueError("GROQ_API_KEY is not set in .env")

        self.model = model

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        try:
            if hasattr(self.client, "responses") and callable(getattr(self.client.responses, "create", None)):
                response = self.client.responses.create(
                    model=self.model,
                    instructions=system_prompt,
                    input=user_prompt,
                )
                if hasattr(response, "output_text") and response.output_text:
                    return response.output_text
        except Exception:
            pass

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content or ""