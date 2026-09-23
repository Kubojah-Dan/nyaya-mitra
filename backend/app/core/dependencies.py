from fastapi import Depends

from app.core.config import Settings, get_settings


def get_current_settings(settings: Settings = Depends(get_settings)) -> Settings:
    """Dependency for injecting application settings."""
    return settings


class BaseLLMClient:
    """Interface for LLM provider abstraction."""
    async def generate(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError


class MockLLMClient(BaseLLMClient):
    """Deterministic mock client for offline tests."""
    async def generate(self, prompt: str, **kwargs) -> str:
        return "Mock response grounded in verified Indian statutes."


def get_llm_client(settings: Settings = Depends(get_settings)) -> BaseLLMClient:
    """Dependency provider for LLM client."""
    # We will expand actual provider routing in Phase 4/5
    return MockLLMClient()
