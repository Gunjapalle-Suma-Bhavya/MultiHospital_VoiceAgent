"""
Live LLM Client for Conversational Voice & Reasoning (OpenAI / AICredits Compatible).
"""

import os
import re
import json
from typing import Dict, Any, List, Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

LANGUAGE_NAMES = {
    "te": "Telugu (తెలుగు)",
    "hi": "Hindi (हिन्दी)",
    "es": "Spanish (Español)",
    "zh": "Mandarin Chinese (中文)",
    "en": "English",
}


class LiveLLMClient:
    """
    High-performance client connecting to OpenAI-compatible endpoints (e.g. AICredits, OpenAI, Azure, vLLM).
    Falls back gracefully to deterministic clinical logic if unconfigured or unreachable.
    """

    def __init__(self):
        self._client: Optional[httpx.Client] = None

    @property
    def api_key(self) -> str:
        return os.getenv("OPENAI_API_KEY", "").strip()

    @property
    def base_url(self) -> str:
        return os.getenv("OPENAI_BASE_URL", "https://api.aicredits.in/v1").rstrip("/")

    @property
    def model(self) -> str:
        return os.getenv("OPENAI_MODEL") or os.getenv("LLM_MODEL", "gpt-4o-mini")

    def is_configured(self) -> bool:
        key = self.api_key
        if not key or len(key) <= 5:
            return False
        if any(ph in key.lower() for ph in ["your-api-key", "placeholder", "xxx", "todo"]):
            return False
        return True

    def _get_http_client(self, timeout_sec: float) -> httpx.Client:
        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(timeout=timeout_sec)
        return self._client

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 250,
        temperature: float = 0.3,
        timeout_sec: float = 6.0
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
            client = self._get_http_client(timeout_sec)
            resp = client.post(
                endpoint,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    raw_text = choices[0]["message"]["content"].strip()
                    # Clean up any accidental markdown asterisks so TTS speaks cleanly
                    cleaned = re.sub(r"\*\*|\*|#+", "", raw_text).strip()
                    return cleaned
        except Exception:
            return None

        return None

    def generate_grounded_response(
        self,
        user_utterance: str,
        language: str = "en",
        intent: str = "GENERAL_CONVERSATION",
        clinical_facts: Optional[Dict[str, Any]] = None,
        timeout_sec: float = 6.0
    ) -> Optional[str]:
        """
        Generates a natural, empathetic, dynamic voice response grounded in verified database facts.
        Outputs directly in the patient's selected language.
        """
        if not self.is_configured():
            return None

        lang_code = (language or "en").lower()
        target_lang_name = LANGUAGE_NAMES.get(lang_code, "English")

        facts_lines = []
        if clinical_facts:
            for k, v in clinical_facts.items():
                if v is not None and v != "":
                    facts_lines.append(f"- {k.replace('_', ' ').title()}: {v}")
        facts_text = "\n".join(facts_lines) if facts_lines else "- General medical / hospital inquiry"

        system_prompt = f"""You are NexusHealth's intelligent, empathetic AI Clinical Voice Intake Coordinator on an audio phone/web call with a patient.

PRIMARY CONVERSATIONAL DIRECTIVES:
1. Target Language: You MUST respond ENTIRELY in {target_lang_name}. Speak naturally, fluently, and warmly in {target_lang_name}.
2. Spoken Voice Optimization: Your response is converted to spoken audio by a neural voice synthesizer.
   - Keep responses concise (2 to 4 spoken sentences).
   - NEVER use markdown (no asterisks **, no bullet points, no numbered lists, no hashtags). Output plain natural sentences.
3. Ground Truth Integrity:
   - Base your statements strictly on the verified facts provided below.
   - Mention the doctor name(s), hospital campus, specialty, appointment times, or verification code provided in the facts.
   - Never make up doctors or hospitals not listed in the facts.
4. Clinical Guardrail:
   - Do NOT provide a definitive medical self-diagnosis or prescribe drugs.
   - Reassure the patient and guide them to their consultation slot or next step.

VERIFIED CLINICAL FACTS:
{facts_text}"""

        user_prompt = f'Patient said: "{user_utterance}"\nIntent: {intent}'

        return self.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=250,
            temperature=0.3,
            timeout_sec=timeout_sec
        )


# Global singleton client
live_llm_client = LiveLLMClient()
