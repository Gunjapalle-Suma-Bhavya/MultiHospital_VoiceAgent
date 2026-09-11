import { useState, useRef, useEffect, useCallback } from 'react';
import { apiCall } from '../api/client';

export interface ChatMessage {
  id: string;
  sender: 'patient' | 'assistant' | 'system';
  text: string;
  timestamp: string;
  intent?: string;
  isEmergency?: boolean;
  isStreaming?: boolean;
}

export function useVoiceAgent() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [detectedIntent, setDetectedIntent] = useState<string>('GREETING');
  const [bargeInAlert, setBargeInAlert] = useState<boolean>(false);
  const [streamActive, setStreamActive] = useState<boolean>(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg-init',
      sender: 'assistant',
      text: 'Hello, this is the NexusHealth AI Voice Intake Agent. How can I assist you with your health or appointment scheduling today?',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      intent: 'GREETING',
    },
  ]);

  const recognitionRef = useRef<any>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const stopSpeaking = useCallback(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  }, []);

  const triggerBargeIn = useCallback(() => {
    stopSpeaking();
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setStreamActive(false);
    }
    setBargeInAlert(true);
    setTimeout(() => {
      setBargeInAlert(false);
    }, 1500);
  }, [stopSpeaking]);

  const speak = useCallback(
    (text: string) => {
      if (isMuted || !text.trim()) return;
      if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;

      stopSpeaking();

      const utterance = new SpeechSynthesisUtterance(text);
      const voices = window.speechSynthesis.getVoices();
      const preferredVoice = voices.find(
        (v) =>
          v.lang.startsWith('en') &&
          (v.name.includes('Natural') ||
            v.name.includes('Google') ||
            v.name.includes('Samantha') ||
            v.name.includes('Zira') ||
            v.name.includes('David'))
      ) || voices.find((v) => v.lang.startsWith('en'));

      if (preferredVoice) {
        utterance.voice = preferredVoice;
      }
      utterance.rate = 1.02;
      utterance.pitch = 1.0;

      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);

      window.speechSynthesis.speak(utterance);
    },
    [isMuted, stopSpeaking]
  );

  // Initialize Speech Recognition if supported in browser
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onspeechstart = () => {
        // True barge-in: cancel AI speech the moment patient voice begins
        triggerBargeIn();
      };

      recognition.onstart = () => {
        setIsRecording(true);
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognition.onerror = (e: any) => {
        console.warn('Speech recognition error:', e);
        setIsRecording(false);
      };

      recognitionRef.current = recognition;
    }

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {}
      }
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      stopSpeaking();
    };
  }, [triggerBargeIn, stopSpeaking]);

  const startVoiceRecording = (onTranscript: (text: string) => void) => {
    // Interruption on click
    triggerBargeIn();

    if (!recognitionRef.current) {
      alert('Speech Recognition is not supported by your browser. You can type or click preset prompt buttons.');
      return;
    }

    try {
      recognitionRef.current.onresult = (event: any) => {
        const transcript = Array.from(event.results)
          .map((res: any) => res[0].transcript)
          .join('');
        onTranscript(transcript);
      };
      recognitionRef.current.start();
    } catch (err) {
      console.warn('Recognition start failed:', err);
    }
  };

  const stopVoiceRecording = () => {
    if (recognitionRef.current && isRecording) {
      try {
        recognitionRef.current.stop();
      } catch {}
      setIsRecording(false);
    }
  };

  // Real-Time SSE Token Streaming
  const streamAIResponse = (userUtterance: string) => {
    triggerBargeIn();

    const streamMsgId = `msg-stream-${Date.now()}`;
    const newMsg: ChatMessage = {
      id: streamMsgId,
      sender: 'assistant',
      text: '',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      intent: 'SSE_STREAMING',
      isStreaming: true,
    };

    setMessages((prev) => [...prev, newMsg]);
    setStreamActive(true);

    let accumulated = '';
    const sse = new EventSource(
      `/api/v1/should-have/streaming/demo?utterance=${encodeURIComponent(userUtterance)}`
    );
    eventSourceRef.current = sse;

    sse.onmessage = (e) => {
      try {
        const frame = JSON.parse(e.data);
        if (frame.token) {
          accumulated += frame.token;
          setMessages((prev) =>
            prev.map((m) => (m.id === streamMsgId ? { ...m, text: accumulated } : m))
          );
        }
        if (frame.status === 'COMPLETED' || frame.done) {
          sse.close();
          setStreamActive(false);
          setMessages((prev) =>
            prev.map((m) => (m.id === streamMsgId ? { ...m, isStreaming: false } : m))
          );
          if (accumulated.trim()) {
            speak(accumulated);
          }
        }
      } catch {
        // Raw token text
        accumulated += ' ' + e.data;
        setMessages((prev) =>
          prev.map((m) => (m.id === streamMsgId ? { ...m, text: accumulated } : m))
        );
      }
    };

    sse.onerror = () => {
      sse.close();
      setStreamActive(false);
    };
  };

  const sendUtterance = async (
    text: string,
    patientPhone = '+1-555-SHOULDER',
    hospitalId = 'HOSP-CITY-01'
  ) => {
    if (!text.trim()) return null;

    triggerBargeIn();

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'patient',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages((prev) => [...prev, userMsg]);
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
        replyText =
          res.data.speech_response || res.data.response_text || res.data.message || replyText;
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

      setMessages((prev) => [...prev, aiMsg]);
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
      setMessages((prev) => [...prev, errorMsg]);
      return null;
    } finally {
      setIsProcessing(false);
    }
  };

  return {
    messages,
    isProcessing,
    isRecording,
    isSpeaking,
    isMuted,
    setIsMuted,
    latencyMs,
    detectedIntent,
    bargeInAlert,
    streamActive,
    startVoiceRecording,
    stopVoiceRecording,
    streamAIResponse,
    sendUtterance,
    triggerBargeIn,
    speak,
    stopSpeaking,
  };
}
