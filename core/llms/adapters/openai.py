# llms/openai.py
from .base import BaseLLM
from django.conf import settings
from core.models import LLMModel
import requests
from typing import List

class OpenAI(BaseLLM):
    def __init__(self, model: LLMModel):
        self._api_key = settings.OPENAI_API_KEY
        self.model = model

    def capabilities(self) -> List[str]:
        return self.model.capabilities
    
    def name(self) -> str:
        return self.model.model_name

    def query(self, query: dict) -> dict:
        query["model"] = self.model.model_name

        headers = {
            'Content-Type': 'application/json'
        }
        data = [
            {
                "provider": "openai",
                "endpoint": "chat/completions",
                "headers": {
                    "authorization": f"Bearer {self._api_key}",
                    "content-type": "application/json"
                },
                "query": query
            }
        ]
        response = requests.post(
            self.GATEWAY_URL,
            headers=headers,
            json=data
        )
        return response.json()
