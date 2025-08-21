from typing import Iterable, List, Dict
from openai import OpenAI
from core.config import settings


class OpenAIClient:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    def stream_completion(self, messages: List[Dict[str, str]]) -> Iterable[str]:
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


openai_client = OpenAIClient()
