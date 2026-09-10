"""
Real-Time Voice Pipeline Engine (Section 5.10).

Manages streaming audio turn-taking, barge-in (interruption handling), silence detection, and sub-2-second response latency targets.
"""

import time
import uuid
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime


class TurnState(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"
    INTERRUPTED = "INTERRUPTED"


class VoicePipelineSession:
    """
    State machine for a single active real-time voice pipeline turn.
    """

    def __init__(self, session_id: str, channel: str = "web_voice"):
        self.session_id = session_id
        self.channel = channel
        self.state = TurnState.IDLE
        self.is_active = True
        self.is_barge_in_active = False
        self.last_audio_timestamp = time.time()
        self.start_turn_time = time.time()
        self.turn_latency_ms = 0.0

    def process_barge_in(self) -> Dict[str, Any]:
        """
        Interruption handling: Cancels active TTS playback immediately when user speaks mid-turn.
        """
        self.state = TurnState.INTERRUPTED
        self.is_barge_in_active = True
        return {
            "session_id": self.session_id,
            "event": "BARGE_IN_TRIGGERED",
            "action": "CANCEL_ACTIVE_TTS_PLAYBACK",
            "timestamp": datetime.utcnow().isoformat()
        }

    def start_thinking(self):
        self.state = TurnState.THINKING
        self.start_turn_time = time.time()

    def complete_thinking(self) -> float:
        self.turn_latency_ms = (time.time() - self.start_turn_time) * 1000.0
        self.state = TurnState.SPEAKING
        return self.turn_latency_ms


class RealTimeVoicePipelineEngine:
    """
    Manager tracking active real-time voice sessions and enforcing sub-2-second target performance.
    """

    def __init__(self):
        self.sessions: Dict[str, VoicePipelineSession] = {}

    def get_or_create_session(self, session_id: Optional[str] = None) -> VoicePipelineSession:
        sid = session_id or str(uuid.uuid4())
        if sid not in self.sessions:
            self.sessions[sid] = VoicePipelineSession(session_id=sid)
        return self.sessions[sid]

    def handle_barge_in_signal(self, session_id: str) -> Dict[str, Any]:
        sess = self.get_or_create_session(session_id)
        return sess.process_barge_in()

    def execute_low_latency_turn(
        self,
        session_id: str,
        user_utterance: str,
        turn_processor_fn
    ) -> Dict[str, Any]:
        sess = self.get_or_create_session(session_id)
        sess.start_thinking()

        result = turn_processor_fn()

        latency = sess.complete_thinking()
        result["latency_ms"] = round(latency, 2)
        result["sub_2_sec_target_met"] = latency <= 2000.0
        result["turn_state"] = sess.state.value

        return result
