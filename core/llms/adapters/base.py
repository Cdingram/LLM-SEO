# llms/base.py
from abc import ABC, abstractmethod
from typing import List
from core.models import LLMModel
from django.conf import settings

class BaseLLM(ABC):
    GATEWAY_URL = f"https://gateway.ai.cloudflare.com/v1/{settings.CLOUDFLARE_ACCOUNT_ID}/llm-tests/"

    def __init__(self, model: LLMModel):
        self.model = model

    @abstractmethod
    def capabilities(self) -> List[str]:
        """Return a list of capabilities supported by the model"""
        pass

    @abstractmethod
    def name(self) -> str:
        """Return the name of the model"""
        pass

    @abstractmethod
    def query(self, query: dict) -> dict:
        """Send a query to the LLM and return the response"""
        pass
