from typing import Type
from .adapters.base import BaseLLM

class LLMProviderRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._providers = {}
        return cls._instance

    def register(self, provider_name: str, adapter_class: Type[BaseLLM]):
        self._providers[provider_name] = adapter_class
    
    def get_adapter(self, provider_name: str) -> Type[BaseLLM]:
        if provider_name not in self._providers:
            raise ValueError(f"No adapter registered for provider {provider_name}")
        return self._providers[provider_name]

# Module-level singleton
provider_registry = LLMProviderRegistry() 