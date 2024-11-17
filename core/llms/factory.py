# llms/factory.py
from .registry import provider_registry
from .adapters.base import BaseLLM
from core.models import LLMModel

def get_llm(model: LLMModel) -> BaseLLM:
    adapter_class = provider_registry.get_adapter(model.provider.name)
    return adapter_class(model=model)
