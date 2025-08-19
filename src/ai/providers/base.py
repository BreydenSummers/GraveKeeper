from typing import Dict

class AIProvider:
    """Base interface for AI providers"""
    def analyze_text(self, text: str) -> Dict:
        """Analyze text and return a detection result dictionary"""
        raise NotImplementedError 