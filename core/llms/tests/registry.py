from typing import Type, List
from .base import BaseLLMTest
from core.models import LLMModel
class TestRegistry:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tests = {}
        return cls._instance
    
    def register(self, test_class: Type[BaseLLMTest]):
        self._tests[test_class.test_name()] = test_class
    
    def get_available_tests(self, llm_model: LLMModel) -> List[Type[BaseLLMTest]]:
        """Get all tests that can run on this LLM based on its capabilities"""
        available_tests = []
        for test_name, test_class in self._tests.items():
            if all(cap in llm_model.capabilities for cap in test_class.required_capabilities):
                available_tests.append(test_class)
        return available_tests

test_registry = TestRegistry()