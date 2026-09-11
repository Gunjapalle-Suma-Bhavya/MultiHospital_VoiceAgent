"""
Streaming AI Responses & Rich Voice Interaction Engine (Section 27).

Provides:
1. Low-latency Server-Sent Events (SSE) streaming for conversational voice responses.
2. Conversational fillers ("Let me check that calendar for you...", "One moment...") emitted within < 200ms to reduce perceived latency.
3. Word-by-word text streaming and simulated audio chunk frames.
4. Rich voice interaction controls: Barge-in interruption handling, silence threshold detection, and turn-taking cues.
"""

import time
import json
import uuid
from typing import Dict, Any, Generator, Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.agent.intent_understanding import SymptomIntentResolver
from app.voice.realtime_pipeline import RealTimeVoicePipelineEngine, TurnState


CONVERSATIONAL_FILLERS = [
    "Let me check the doctor's schedule for you...",
    "Looking up the latest available slots right now...",
    "One moment while I access the clinic calendar...",
    "Checking our department directory for you..."
]


class RichVoiceInteractionManager:
    """
    Manages conversational turn-taking, speech pauses, silence thresholds, and interruptions.
    """

    def __init__(self, silence_threshold_ms: int = 700):
        self.silence_threshold_ms = silence_threshold_ms
        self.active_interruptions: Dict[str, bool] = {}

    def register_barge_in(self, session_id: str) -> Dict[str, Any]:
        """Registers a user speech barge-in interrupt mid-response."""
        self.active_interruptions[session_id] = True
        return {
            "session_id": session_id,
            "status": "INTERRUPTED",
            "message": "Playback cancelled due to user barge-in.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def clear_barge_in(self, session_id: str):
        self.active_interruptions.pop(session_id, None)

    def is_interrupted(self, session_id: str) -> bool:
        return self.active_interruptions.get(session_id, False)

    def select_filler(self, utterance: str) -> str:
        lowered = utterance.lower()
        if "cancel" in lowered:
            return "Let me retrieve your appointment details to process the cancellation..."
        elif "reschedule" in lowered:
            return "Checking alternative times with the clinician..."
        elif "doctor" in lowered or "specialist" in lowered:
            return "Looking up our available specialists for you..."
        return "One moment, let me coordinate that for you..."


class StreamingAIService:
    """
    Produces incremental Server-Sent Events (SSE) token and audio streams for real-time browser interaction.
    """

    def __init__(self):
        self.interaction_manager = RichVoiceInteractionManager()

    def generate_sse_stream(
        self,
        session_id: str,
        user_utterance: str,
        db: Optional[Session] = None
    ) -> Generator[str, None, None]:
        """
        Yields standard SSE formatted chunks:
        - event: filler
        - event: token
        - event: tool_call
        - event: audio_chunk
        - event: done
        """
        start_time = time.time()
        self.interaction_manager.clear_barge_in(session_id)

        # 1. Immediate conversational filler (< 150ms)
        filler = self.interaction_manager.select_filler(user_utterance)
        filler_payload = {
            "session_id": session_id,
            "filler_text": filler,
            "elapsed_ms": round((time.time() - start_time) * 1000, 1),
            "turn_state": TurnState.SPEAKING.value
        }
        yield f"event: filler\ndata: {json.dumps(filler_payload)}\n\n"

        # Check for barge-in
        if self.interaction_manager.is_interrupted(session_id):
            yield f"event: interrupted\ndata: {json.dumps({'session_id': session_id, 'reason': 'User barge-in'})}\n\n"
            return

        # 2. Symptom / Intent Understanding & Response Generation
        nlu_result = SymptomIntentResolver.infer_specialty_from_utterance(user_utterance)
        if nlu_result.inferred_specialty:
            response_text = (
                f"I understand you are experiencing {nlu_result.symptom_detected or 'discomfort'}. "
                f"I can connect you with an {nlu_result.inferred_specialty} specialist. "
                f"Would you prefer a morning or afternoon consultation?"
            )
        else:
            response_text = (
                f"I would be glad to help coordinate your healthcare intake. "
                f"Could you please let me know your preferred department or doctor?"
            )

        # 3. Simulate tool call event if specialty was detected
        if nlu_result.inferred_specialty:
            tool_event = {
                "capability": "search_doctors",
                "parameters": {"specialty": nlu_result.inferred_specialty},
                "status": "EXECUTED",
                "elapsed_ms": round((time.time() - start_time) * 1000, 1)
            }
            yield f"event: tool_call\ndata: {json.dumps(tool_event)}\n\n"

        # 4. Stream Tokens Word-by-Word
        words = response_text.split(" ")
        for idx, word in enumerate(words):
            if self.interaction_manager.is_interrupted(session_id):
                yield f"event: interrupted\ndata: {json.dumps({'session_id': session_id, 'reason': 'User barge-in during token stream'})}\n\n"
                return

            token_data = {
                "token": word + (" " if idx < len(words) - 1 else ""),
                "index": idx,
                "elapsed_ms": round((time.time() - start_time) * 1000, 1)
            }
            yield f"event: token\ndata: {json.dumps(token_data)}\n\n"

            # 5. Emitted simulated audio frame every 3 tokens
            if idx % 3 == 0:
                audio_frame = {
                    "frame_index": idx // 3,
                    "sample_rate": 24000,
                    "encoding": "audio/pcm",
                    "chunk_size_bytes": 1024
                }
                yield f"event: audio_chunk\ndata: {json.dumps(audio_frame)}\n\n"

        # 6. Finalized Done Event
        total_latency_ms = round((time.time() - start_time) * 1000, 1)
        done_data = {
            "session_id": session_id,
            "status": "COMPLETED",
            "total_latency_ms": total_latency_ms,
            "sub_2_second_target_met": total_latency_ms <= 2000.0,
            "token_count": len(words),
            "response_text": response_text
        }
        yield f"event: done\ndata: {json.dumps(done_data)}\n\n"
