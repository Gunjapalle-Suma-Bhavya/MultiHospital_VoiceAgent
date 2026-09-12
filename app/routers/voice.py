"""
AI Real-Time Voice Pipeline, Telephony & Strategy Blueprint Router.
"""

import os
import time
import base64
import httpx
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

from app.database.config import get_db
from app.telephony.inbound_service import TelephonyInboundService
from app.agent.patient_access_agent import PatientAccessAgentService

router = APIRouter(prefix="", tags=["AI Voice & Telephony"])

# Pre-mapped ElevenLabs neural voices
ELEVENLABS_VOICE_MAP = {
    "clinical_female": "Xb7hH8MSUJpSbSDYk0k2",  # Alice
    "clinical_male": "JBFqnCBsd6RMkjVDRZzb",    # George
    "sarah": "EXAVITQu4vr4xnSDxMaL",            # Sarah
    "lily": "pFZP5JQG7iQjIQuC4Bku",             # Lily
    "george": "JBFqnCBsd6RMkjVDRZzb",           # George
    "alice": "Xb7hH8MSUJpSbSDYk0k2",            # Alice
}


class VoiceTurnInput(BaseModel):
    patient_phone: str = "+15551234567"
    user_utterance: str
    hospital_id: Optional[str] = None
    session_id: Optional[str] = None

class InboundCallInput(BaseModel):
    caller_phone_number: str

class TelephonyTurnInput(BaseModel):
    session_id: str
    caller_phone_number: str
    speech_text: str
    hospital_id: Optional[str] = None


@router.post("/api/voice/chat")
def voice_agent_chat_endpoint(payload: VoiceTurnInput, db: Session = Depends(get_db)):
    agent_svc = PatientAccessAgentService(db)
    res = agent_svc.process_patient_turn(
        patient_phone=payload.patient_phone,
        user_utterance=payload.user_utterance,
        hospital_id=payload.hospital_id,
        session_id=payload.session_id
    )
    try:
        from app.database.mongodb import persist_to_mongodb
        persist_to_mongodb("voice_sessions", {
            "session_id": res.get("session_id") or payload.session_id,
            "patient_phone": payload.patient_phone,
            "user_utterance": payload.user_utterance,
            "agent_response": res.get("agent_response"),
            "intent": res.get("intent"),
            "hospital_id": payload.hospital_id
        })
    except Exception:
        pass
    return res

@router.post("/api/v1/telephony/inbound-call")
def telephony_inbound_call(payload: InboundCallInput, db: Session = Depends(get_db)):
    svc = TelephonyInboundService(db)
    return svc.handle_inbound_call(payload.caller_phone_number)

@router.post("/api/v1/telephony/process-turn")
def telephony_process_turn(payload: TelephonyTurnInput, db: Session = Depends(get_db)):
    svc = TelephonyInboundService(db)
    return svc.process_telephony_turn(
        session_id=payload.session_id,
        caller_phone_number=payload.caller_phone_number,
        speech_text=payload.speech_text,
        hospital_id=payload.hospital_id
    )

@router.post("/api/v1/telephony/escalate")
def telephony_escalate(session_id: str, db: Session = Depends(get_db)):
    svc = TelephonyInboundService(db)
    return svc.terminate_call(session_id=session_id, reason="ESCALATED_TO_HUMAN")


class SynthesizeInput(BaseModel):
    text: str
    voice: str = "clinical_female"
    language: str = "en"


@router.post("/api/v1/voice/synthesize")
def synthesize_speech(payload: SynthesizeInput):
    """
    Universal server-side speech synthesis audio endpoint.
    Calls ElevenLabs Neural TTS when an API key is provided, falling back seamlessly to local audio.
    """
    start_time = time.time()
    api_key = os.getenv("ELEVENLABS_API_KEY", "")

    # 1. Attempt ElevenLabs Neural TTS synthesis if key is present
    if api_key and payload.text.strip():
        voice_id = ELEVENLABS_VOICE_MAP.get(payload.voice.lower(), "Xb7hH8MSUJpSbSDYk0k2")
        model_id = os.getenv("ELEVENLABS_MODEL_ID", "eleven_flash_v2_5")
        try:
            with httpx.Client(timeout=8.0) as client:
                res = client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?optimize_streaming_latency=4&output_format=mp3_22050_32",
                    headers={
                        "xi-api-key": api_key,
                        "Content-Type": "application/json",
                        "Accept": "audio/mpeg",
                    },
                    json={
                        "text": payload.text,
                        "model_id": model_id,
                        "voice_settings": {
                            "stability": 0.5,
                            "similarity_boost": 0.75,
                        },
                    },
                )
                if res.status_code == 200 and res.content:
                    latency_ms = int((time.time() - start_time) * 1000)
                    audio_b64 = base64.b64encode(res.content).decode("utf-8")
                    return {
                        "text": payload.text,
                        "language": payload.language,
                        "voice": payload.voice,
                        "voice_id": voice_id,
                        "provider": "elevenlabs",
                        "format": "audio/mpeg",
                        "audio_base64": f"data:audio/mpeg;base64,{audio_b64}",
                        "server_latency_ms": latency_ms,
                    }
                else:
                    print(f"[ElevenLabs Warning] Status {res.status_code}: {res.text[:150]}")
        except Exception as e:
            print(f"[ElevenLabs Warning] TTS call failed, engaging local audio fallback: {e}")

    # 2. Local Fallback: Generate valid 16-bit 44.1kHz mono WAV buffer
    import math

    wav_header = b'RIFF$\xac\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\xac\x00\x00'
    pcm_data = bytearray()
    for i in range(11025):  # 0.25s subtle tone
        val = int(32767 * 0.15 * math.sin(2 * math.pi * 523.25 * i / 44100))
        pcm_data.extend(val.to_bytes(2, byteorder="little", signed=True))
    full_wav = wav_header + bytes(pcm_data)
    audio_base64 = base64.b64encode(full_wav).decode("utf-8")
    latency_ms = max(int((time.time() - start_time) * 1000), 20)

    return {
        "text": payload.text,
        "language": payload.language,
        "voice": payload.voice,
        "provider": "local_fallback",
        "format": "audio/wav",
        "audio_base64": f"data:audio/wav;base64,{audio_base64}",
        "server_latency_ms": latency_ms,
    }

