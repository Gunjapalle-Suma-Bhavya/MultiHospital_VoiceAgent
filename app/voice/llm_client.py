"""
Live LLM Client for Conversational Voice & Reasoning (OpenAI / AICredits Compatible).
"""

import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()


class LiveLLMClient:
    """
    Client connecting to OpenAI-compatible endpoints (e.g. OpenAI, AICredits, Azure OpenAI, vLLM).
    Falls back gracefully to deterministic fallback if unconfigured or unreachable.
    """

    def __init__(self):
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.aicredits.in/v1").rstrip("/")
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def is_configured(self) -> bool:
        key = (self.api_key or "").strip()
        if not key or len(key) <= 5:
            return False
        if any(ph in key.lower() for ph in ["your-api-key", "placeholder", "xxx", "todo"]):
            return False
        return True

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 150,
        temperature: float = 0.3,
        timeout_sec: float = 5.0
    ) -> Optional[str]:
        """
        Sends a non-streaming chat completion request with a fast timeout.
        Returns the generated text or None on timeout/error.
        """
        if not self.is_configured():
            return None

        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0]["message"]["content"].strip()
        except Exception as e:
            # Fallback to local rule engine without breaking the voice flow
            return None

        return None


# Global singleton client
live_llm_client = LiveLLMClient()
