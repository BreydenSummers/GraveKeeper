from typing import Optional
from src.ai.providers.ollama import OllamaProvider

class ProviderFactory:
    @staticmethod
    def create(provider: str, model: Optional[str] = None, host: Optional[str] = None):
        provider = (provider or 'ollama').lower()
        if provider == 'ollama':
            return OllamaProvider(model=model or 'llama3.1', host=host or 'http://localhost:11434')
        raise ValueError(f"Unsupported provider: {provider}") 