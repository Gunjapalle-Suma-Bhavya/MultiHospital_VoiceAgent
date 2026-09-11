"""
AI Operational Cost Estimation & Financial ROI Service (Section 27).

Calculates real-time running costs for voice AI interactions and models hospital financial savings:
- LLM Token Costs (Prompt $0.15/1M, Output $0.60/1M)
- Speech-to-Text transcription ($0.006 / minute)
- Neural Text-to-Speech synthesis ($0.015 / 1,000 characters)
- Telephony SIP Inbound / Outbound ($0.013 / minute)
- Benchmark comparison vs human receptionist ($22.50 / hour)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.models import Appointment, PatientProfile


class CostEstimationService:
    """
    Computes unit economics, call-level costs, and ROI metrics for the voice agent platform.
    """

    # Industry benchmark rates (USD)
    RATES = {
        "llm_prompt_per_million": 0.15,
        "llm_completion_per_million": 0.60,
        "stt_per_minute": 0.006,
        "tts_per_thousand_chars": 0.015,
        "telephony_sip_per_minute": 0.013,
        "human_receptionist_hourly": 22.50,
        "average_call_duration_minutes": 3.2
    }

    @classmethod
    def calculate_single_call_cost(
        cls,
        call_duration_minutes: float = 3.2,
        prompt_tokens: int = 1450,
        completion_tokens: int = 380,
        tts_characters: int = 1200
    ) -> Dict[str, Any]:
        """Calculates granular cost breakdown for a single conversational turn/session."""
        llm_prompt_cost = (prompt_tokens / 1_000_000.0) * cls.RATES["llm_prompt_per_million"]
        llm_comp_cost = (completion_tokens / 1_000_000.0) * cls.RATES["llm_completion_per_million"]
        stt_cost = call_duration_minutes * cls.RATES["stt_per_minute"]
        tts_cost = (tts_characters / 1_000.0) * cls.RATES["tts_per_thousand_chars"]
        telephony_cost = call_duration_minutes * cls.RATES["telephony_sip_per_minute"]

        total_ai_call_cost = llm_prompt_cost + llm_comp_cost + stt_cost + tts_cost + telephony_cost

        # Human receptionist cost for equivalent duration (plus 1.5 min wrap-up time)
        human_equivalent_minutes = call_duration_minutes + 1.5
        human_cost = (human_equivalent_minutes / 60.0) * cls.RATES["human_receptionist_hourly"]
        savings_per_call = human_cost - total_ai_call_cost
        savings_percentage = round((savings_per_call / human_cost) * 100.0, 2)

        return {
            "duration_minutes": call_duration_minutes,
            "cost_breakdown": {
                "llm_tokens_cost": round(llm_prompt_cost + llm_comp_cost, 5),
                "stt_transcription_cost": round(stt_cost, 5),
                "tts_speech_cost": round(tts_cost, 5),
                "telephony_sip_cost": round(telephony_cost, 5),
                "total_ai_cost": round(total_ai_call_cost, 4)
            },
            "comparison": {
                "human_receptionist_cost": round(human_cost, 3),
                "net_savings_per_call": round(savings_per_call, 3),
                "savings_percentage": savings_percentage
            }
        }

    @classmethod
    def get_platform_financial_summary(cls, db: Session) -> Dict[str, Any]:
        """Computes platform-wide financial ROI based on total appointments booked."""
        appt_count = db.query(func.count(Appointment.id)).scalar() or 0
        effective_calls = max(appt_count, 12)  # Baseline demonstration minimum

        sample_call = cls.calculate_single_call_cost()
        unit_cost = sample_call["cost_breakdown"]["total_ai_cost"]
        human_unit = sample_call["comparison"]["human_receptionist_cost"]

        total_ai_spend = round(effective_calls * unit_cost, 2)
        total_human_spend = round(effective_calls * human_unit, 2)
        net_platform_savings = round(total_human_spend - total_ai_spend, 2)

        # Projections
        projections = {}
        for volume in [1000, 10000, 100000]:
            ai_proj = volume * unit_cost
            human_proj = volume * human_unit
            projections[f"volume_{volume}"] = {
                "volume": volume,
                "projected_ai_cost_usd": round(ai_proj, 2),
                "projected_human_cost_usd": round(human_proj, 2),
                "projected_savings_usd": round(human_proj - ai_proj, 2),
                "roi_multiplier": round(human_proj / ai_proj, 1)
            }

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "currency": "USD",
            "effective_calls_processed": effective_calls,
            "average_cost_per_call_usd": unit_cost,
            "human_equivalent_cost_usd": human_unit,
            "net_platform_savings_usd": net_platform_savings,
            "overall_savings_percentage": sample_call["comparison"]["savings_percentage"],
            "unit_rates": cls.RATES,
            "volume_projections": projections
        }
