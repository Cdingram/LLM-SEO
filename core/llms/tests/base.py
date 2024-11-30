from abc import ABC, abstractmethod
from typing import Type, List, Any, Optional
from dataclasses import dataclass
from core.llms.adapters.base import BaseLLM
from core.llms.factory import get_llm
from core.models import LLMModel, LLMProvider

@dataclass
class TestResult:
    success: bool = False
    error: str = None
    # Human-readable summary
    readable_response: str = None
    # Raw response from LLM for debugging (optional)
    raw_responses: List[dict] = None
    # Structured data for visualization/analysis
    structured_data: Optional[Any] = None
    # Metadata about the test run
    metadata: dict = None

class BaseLLMTest(ABC):
    # Define as class variable that will be overridden by subclasses
    required_capabilities: List[str] = []

    @staticmethod
    def get_analysis_llm() -> BaseLLM:
        """Get the designated LLM for analysis operations"""
        provider = LLMProvider.objects.get(name="OpenAI")
        model = LLMModel.objects.filter(
            provider=provider,
            model_name="chatgpt-4o-latest",
            is_active=True
        ).first()
        return get_llm(model)

    @classmethod
    @abstractmethod
    def test_name(cls) -> str:
        """Unique identifier for the test"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what the test does"""
        pass
    
    @abstractmethod
    def run(self, llm: BaseLLM) -> TestResult:
        """Execute the test against an LLM"""
        pass
