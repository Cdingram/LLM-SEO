from abc import ABC, abstractmethod
from typing import Type, List
from dataclasses import dataclass
from core.llms.adapters.base import BaseLLM

@dataclass
class TestResult:
    details: dict = None
    success: bool = False

class BaseLLMTest(ABC):
    # Define as class variable that will be overridden by subclasses
    required_capabilities: List[str] = []

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