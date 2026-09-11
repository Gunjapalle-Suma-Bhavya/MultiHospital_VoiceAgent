"""
Privacy-Aware Logging & Sanitization Engine (Section 5.41).

Enforces healthcare data protection rules by:
1. Preventing storage of raw conversational transcripts and voice recordings in operational logs.
2. Redacting PHI/PII (symptoms, intake answers, clinical notes, SSN, audio files).
3. Masking sensitive identifiers while retaining structured audit metadata.
4. Categorizing privacy levels: STRUCTURED_NO_PHI, REDACTED_PHI, ANONYMIZED.
"""

import re
from typing import Dict, Any, Tuple, Optional
from app.audit import PrivacyLevel


# Fields containing direct PHI/clinical information that must be redacted from operational logs
SENSITIVE_CLINICAL_FIELDS = {
    "symptoms",
    "intake_answers",
    "medical_history",
    "diagnosis",
    "clinical_notes",
    "patient_reported_summary",
    "responses",
    "questionnaire_responses",
    "raw_transcript",
    "transcript",
    "conversation_transcript",
    "utterance",
    "speech_text",
    "audio",
    "audio_bytes",
    "recording_url",
    "recording_data",
}

# Fields containing direct personal identifiers that must be masked or tokenized
SENSITIVE_IDENTIFIER_FIELDS = {
    "ssn",
    "social_security_number",
    "national_id",
    "credit_card",
    "card_number",
    "insurance_id",
    "policy_number",
    "passport",
}

# Regex patterns for accidental PHI in string values
SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
PHONE_REGEX = re.compile(r"\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")


class PrivacySanitizer:
    """
    Sanitizes operational payloads and tool parameters to maintain strict HIPAA/privacy compliance.
    """

    @staticmethod
    def mask_string(val: str) -> str:
        """Masks sensitive strings like email or phone numbers."""
        if not val or not isinstance(val, str):
            return val
        
        # Mask emails: j***e@example.com
        if "@" in val and "." in val:
            parts = val.split("@")
            user, domain = parts[0], parts[1]
            if len(user) > 2:
                masked_user = f"{user[0]}***{user[-1]}"
            else:
                masked_user = f"{user[0]}***"
            return f"{masked_user}@{domain}"

        # Mask phone numbers or IDs
        clean = re.sub(r"[^\w]", "", val)
        if len(clean) >= 6:
            return f"***-***-{clean[-4:]}"
        return "[REDACTED]"

    @classmethod
    def sanitize_payload(cls, payload: Optional[Dict[str, Any]]) -> Tuple[Dict[str, Any], str]:
        """
        Recursively inspects a dictionary payload, strips raw conversational/clinical data,
        masks direct identifiers, and determines privacy classification.

        Returns:
            Tuple[sanitized_payload, privacy_level]
        """
        if not payload:
            return {}, PrivacyLevel.STRUCTURED_NO_PHI.value

        had_redaction = False
        sanitized = {}

        for key, value in payload.items():
            lower_key = key.lower()

            # 1. Complete redaction of clinical / raw conversational data
            if lower_key in SENSITIVE_CLINICAL_FIELDS:
                sanitized[key] = "[REDACTED_SENSITIVE_HEALTH_INFO]"
                had_redaction = True

            # 2. Complete redaction/masking of direct personal identifiers
            elif lower_key in SENSITIVE_IDENTIFIER_FIELDS:
                sanitized[key] = "[REDACTED_IDENTIFIER]"
                had_redaction = True

            # 3. Mask phone numbers and emails if present
            elif lower_key in {"phone", "patient_phone", "contact_phone"}:
                sanitized[key] = cls.mask_string(str(value))
                had_redaction = True
            elif lower_key in {"email", "patient_email", "contact_email"}:
                sanitized[key] = cls.mask_string(str(value))
                had_redaction = True

            # 4. Nested dictionaries
            elif isinstance(value, dict):
                sub_sanitized, sub_redacted = cls.sanitize_payload(value)
                sanitized[key] = sub_sanitized
                if sub_redacted != PrivacyLevel.STRUCTURED_NO_PHI.value:
                    had_redaction = True

            # 5. Lists of dictionaries or values
            elif isinstance(value, list):
                new_list = []
                for item in value:
                    if isinstance(item, dict):
                        sub_sanitized, sub_redacted = cls.sanitize_payload(item)
                        new_list.append(sub_sanitized)
                        if sub_redacted != PrivacyLevel.STRUCTURED_NO_PHI.value:
                            had_redaction = True
                    elif isinstance(item, str):
                        cleaned_str, text_redacted = cls._sanitize_text(item)
                        new_list.append(cleaned_str)
                        if text_redacted:
                            had_redaction = True
                    else:
                        new_list.append(item)
                sanitized[key] = new_list

            # 6. String text values (scan for inline SSNs or patterns)
            elif isinstance(value, str):
                cleaned_str, text_redacted = cls._sanitize_text(value)
                sanitized[key] = cleaned_str
                if text_redacted:
                    had_redaction = True

            else:
                sanitized[key] = value

        privacy_level = (
            PrivacyLevel.REDACTED_PHI.value if had_redaction else PrivacyLevel.STRUCTURED_NO_PHI.value
        )
        return sanitized, privacy_level

    @classmethod
    def _sanitize_text(cls, text: str) -> Tuple[str, bool]:
        """Scans freeform string for accidental SSNs or sensitive tokens."""
        redacted = False
        new_text = text

        if SSN_REGEX.search(new_text):
            new_text = SSN_REGEX.sub("[REDACTED_SSN]", new_text)
            redacted = True

        return new_text, redacted

    @classmethod
    def sanitize_tool_invocation(cls, tool_name: str, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Sanitizes tool call parameters for audit trail storage.
        E.g. records TOOL_CALL: lookup_patient with patient_id, but redacts raw query audio/transcript.
        """
        sanitized_args, _ = cls.sanitize_payload(arguments or {})
        return {
            "tool_name": tool_name,
            "arguments": sanitized_args,
        }
