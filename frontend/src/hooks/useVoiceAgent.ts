import { useState, useRef } from 'react';
import { apiCall } from '../api/client';

export interface ChatMessage {
  id: string;
  sender: 'patient' | 'assistant' | 'system';
  text: string;
  timestamp: string;
  intent?: string;
  isEmergency?: boolean;
}

export function useVoiceAgent() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [detectedIntent, setDetectedIntent] = useState<string>('GREETING');
  const [bargeInAlert, setBargeInAlert] = useState<boolean>(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg-init',
      sender: 'assistant',
      text: 'Hello Patient A, I can help you schedule an appointment or answer questions. Please tell me what symptoms you are experiencing.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      intent: 'GREETING',
    }
  ]);

  const speak = (text: string) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      window.speechSynthesis.speak(utterance);
    }
  };

  const triggerBargeIn = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setBargeInAlert(true);
    setTimeout(() => {
      setBargeInAlert(false);
    }, 1800);
  };

  const sendUtterance = async (
    text: string,
    patientPhone = '+1-555-SHOULDER',
    hospitalId = 'HOSP-CITY-01'
  ) => {
    if (!text.trim()) return null;

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'patient',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages(prev => [...prev, userMsg]);
    setIsProcessing(true);

    const startTime = performance.now();

    try {
      const res = await apiCall('/api/voice/chat', {
        method: 'POST',
        body: JSON.stringify({
          patient_phone: patientPhone,
          user_utterance: text,
          hospital_id: hospitalId,
        }),
      });

      const elapsed = Math.round(performance.now() - startTime);
      setLatencyMs(elapsed);

      let replyText = 'I have received your inquiry.';
      let intent = 'CLINICAL_INTAKE';
      let isEmergency = false;

      if (res.ok && res.data) {
        replyText = res.data.speech_response || res.data.response_text || res.data.message || replyText;
        intent = res.data.detected_intent || intent;
        isEmergency = !!res.data.escalation_triggered || intent.includes('EMERGENCY');
      }

      setDetectedIntent(intent);

      const aiMsg: ChatMessage = {
        id: `msg-ai-${Date.now()}`,
        sender: 'assistant',
        text: replyText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        intent,
        isEmergency,
      };

      setMessages(prev => [...prev, aiMsg]);
      speak(replyText);

      return {
        replyText,
        intent,
        isEmergency,
        data: res.data,
      };
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `msg-err-${Date.now()}`,
        sender: 'system',
        text: `Error processing request: ${err.message}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages(prev => [...prev, errorMsg]);
      return null;
    } finally {
      setIsProcessing(false);
    }
  };

  return {
    messages,
    isProcessing,
    latencyMs,
    detectedIntent,
    bargeInAlert,
    sendUtterance,
    triggerBargeIn,
    speak,
  };
}
