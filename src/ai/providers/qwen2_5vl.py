"""
Qwen2.5VL provider for local LLMs via Ollama
"""
from typing import Dict, Optional
import requests

from src.utils.logger import logger

class Qwen2_5VLProvider:

    def analyze_vision(self, image) -> Dict:
        """
        Describe the content of an image using Qwen2.5VL (vision prompt).
        Accepts a PIL Image object.
        """
        import base64
        from io import BytesIO
        try:
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_b64 = base64.b64encode(buffered.getvalue()).decode()
            vision_prompt = "Describe the content of this image."
            # Qwen2.5VL expects a vision prompt and image in the request
            payload = {
                "model": self.model,
                "prompt": vision_prompt,
                "images": [img_b64],
                "stream": False,
                "options": {"temperature": 0.2}
            }
            resp = requests.post(self.url_generate, json=payload, timeout=120)
            if resp.status_code == 404:
                # Fallback to /api/chat if needed
                chat_payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You return only compact JSON for image description."},
                        {"role": "user", "content": vision_prompt, "images": [img_b64]}
                    ],
                    "stream": False,
                    "options": {"temperature": 0.2}
                }
                chat_resp = requests.post(self.url_chat, json=chat_payload, timeout=120)
                chat_resp.raise_for_status()
                data = chat_resp.json()
                output = (data.get("message", {}) or {}).get("content", "").strip()
                return {"explanation": output, "provider": "qwen2.5vl", "model": self.model}
            resp.raise_for_status()
            data = resp.json()
            output = data.get("response", "").strip()
            return {"explanation": output, "provider": "qwen2.5vl", "model": self.model}
        except Exception as e:
            logger.error(f"Qwen2.5VL vision analyze error: {e}")
            return {"error": str(e), "provider": "qwen2.5vl", "model": self.model}
    """Use a local Ollama instance to analyze text/images with Qwen2.5VL"""

    def __init__(self, model: str = "qwen2.5vl", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host.rstrip("/")
        self.url_generate = f"{self.host}/api/generate"
        self.url_chat = f"{self.host}/api/chat"

    def analyze_text(self, text: str) -> Dict:
        try:
            prompt = self._build_prompt(text)
            resp = requests.post(self.url_generate, json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2}
            }, timeout=120)
            if resp.status_code == 404:
                chat_resp = requests.post(self.url_chat, json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You return only compact JSON for sensitivity classification."},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False,
                    "options": {"temperature": 0.2}
                }, timeout=120)
                chat_resp.raise_for_status()
                data = chat_resp.json()
                output = (data.get("message", {}) or {}).get("content", "").strip()
                return self._parse_output(output)
            resp.raise_for_status()
            data = resp.json()
            output = data.get("response", "").strip()
            return self._parse_output(output)
        except Exception as e:
            logger.error(f"Qwen2.5VL analyze error: {e}")
            return {
                'sensitivity_score': 1,
                'confidence': 0.0,
                'sensitive_categories': [],
                'detected_patterns': [],
                'explanation': f"Error occurred during analysis: {str(e)}",
                'recommendations': [],
                'provider_error': str(e)
            }

    def _build_prompt(self, text: str) -> str:
        instructions = (
            "You are a data sensitivity classifier. Rate the sensitivity of the text on a scale from 1-10, where 10 is extremely sensitive. Think why that data is actually sensitive. We don't want example files and such to be marked as sensitive."
            "Reply strictly as compact JSON with keys: "
            "sensitivity_score (integer 1-10), confidence (0..1), sensitive_categories (array of strings), "
            "detected_patterns (array of strings), explanation (string explaining the score), recommendations (array of strings). "
            "Sensitive categories can include: PII, PHI, Financial, Credentials, Secrets, StudentRecords, Legal, HR, Proprietary. "
            "Provide a clear explanation of why you assigned that sensitivity score."
        )
        return f"{instructions}\n\nText:\n'''\n{text}\n'''\n\nJSON:"

    def _parse_output(self, output: str) -> Dict:
        import json
        try:
            parsed = json.loads(output)
            return {
                'sensitivity_score': int(parsed.get('sensitivity_score', 1)),
                'confidence': float(parsed.get('confidence', 0.0)),
                'sensitive_categories': list(parsed.get('sensitive_categories', [])),
                'detected_patterns': list(parsed.get('detected_patterns', [])),
                'explanation': str(parsed.get('explanation', '')),
                'recommendations': list(parsed.get('recommendations', [])),
                'provider': 'qwen2.5vl',
                'model': self.model
            }
        except Exception:
            return {
                'sensitivity_score': 1,
                'confidence': 0.0,
                'sensitive_categories': [],
                'detected_patterns': [],
                'explanation': f"Failed to parse AI response: {output[:200]}",
                'recommendations': [output[:300]],
                'provider': 'qwen2.5vl',
                'model': self.model
            }
