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

// Global active utterance reference to prevent Chrome garbage collection bug
let activeUtterance: SpeechSynthesisUtterance | null = null;

export function useVoiceAgent() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [detectedIntent, setDetectedIntent] = useState<string>('GREETING');
  const [bargeInAlert, setBargeInAlert] = useState<boolean>(false);
  const [streamActive, setStreamActive] = useState<boolean>(false);
  const [transcriptLive, setTranscriptLive] = useState<string>('');
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
  const lastTranscriptRef = useRef<string>('');
  const onAutoSendRef = useRef<((text: string) => void) | null>(null);

  const stopSpeaking = useCallback(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      try {
        window.speechSynthesis.cancel();
      } catch {}
      activeUtterance = null;
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

      try {
        window.speechSynthesis.resume();
      } catch {}

      // Short delay after cancel to allow Chrome audio queue to reset cleanly
      setTimeout(() => {
        try {
          const utterance = new SpeechSynthesisUtterance(text);
          activeUtterance = utterance;

          const voices = window.speechSynthesis.getVoices();
          const preferredVoice =
            voices.find(
              (v) =>
                v.lang.startsWith('en') &&
                (v.name.includes('Natural') ||
                  v.name.includes('Google') ||
                  v.name.includes('Samantha') ||
                  v.name.includes('Zira') ||
                  v.name.includes('David') ||
                  v.name.includes('Jenny'))
            ) || voices.find((v) => v.lang.startsWith('en')) || voices[0];

          if (preferredVoice) {
            utterance.voice = preferredVoice;
          }
          utterance.rate = 1.0;
          utterance.pitch = 1.0;

          utterance.onstart = () => {
            setIsSpeaking(true);
          };

          utterance.onend = () => {
            activeUtterance = null;
            setIsSpeaking(false);
          };

          utterance.onerror = (e) => {
            console.warn('Speech synthesis utterance error:', e);
            activeUtterance = null;
            setIsSpeaking(false);
          };

          window.speechSynthesis.speak(utterance);
        } catch (err) {
          console.warn('speak exception:', err);
          setIsSpeaking(false);
        }
      }, 50);
    },
    [isMuted, stopSpeaking]
  );

  // Initialize Speech Recognition
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onspeechstart = () => {
          triggerBargeIn();
        };

        recognition.onstart = () => {
          setIsRecording(true);
        };

        recognition.onresult = (event: any) => {
          let current = '';
          for (let i = 0; i < event.results.length; i++) {
            current += event.results[i][0].transcript;
          }
          lastTranscriptRef.current = current;
          setTranscriptLive(current);
        };

        recognition.onend = () => {
          setIsRecording(false);
          const finalVal = lastTranscriptRef.current.trim();
          if (finalVal && onAutoSendRef.current) {
            onAutoSendRef.current(finalVal);
            lastTranscriptRef.current = '';
            setTranscriptLive('');
          }
        };

        recognition.onerror = (e: any) => {
          console.warn('Speech recognition status:', e.error);
          setIsRecording(false);
        };

        recognitionRef.current = recognition;
      } catch (err) {
        console.warn('Speech recognition init failed:', err);
      }
    }

    // Chrome voices changed listener
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.getVoices();
      };
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

  const startVoiceRecording = (
    onInterim?: (text: string) => void,
    onFinalSubmit?: (text: string) => void
  ) => {
    triggerBargeIn();

    if (!recognitionRef.current) {
      alert('Speech Recognition is not supported by this browser. You can type your request or click preset prompts.');
      return;
    }

    if (onFinalSubmit) {
      onAutoSendRef.current = onFinalSubmit;
    }

    try {
      lastTranscriptRef.current = '';
      setTranscriptLive('');
      recognitionRef.current.start();
    } catch (err) {
      console.warn('Recognition start caught error:', err);
      try {
        recognitionRef.current.stop();
        setTimeout(() => {
          recognitionRef.current.start();
        }, 100);
      } catch {}
    }
  };

  const stopVoiceRecording = () => {
    if (recognitionRef.current) {
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
    patientPhone = '+1-555-1234567',
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
      let intent = 'GENERAL_INQUIRY';
      let isEmergency = false;

      if (res.ok && res.data) {
        replyText =
          res.data.speech_response ||
          res.data.agent_response ||
          res.data.response_text ||
          res.data.message ||
          replyText;
        intent = res.data.detected_intent || res.data.intent_detected || intent;
        isEmergency = !!res.data.escalation_triggered || intent.includes('EMERGENCY');
      } else if (res.error) {
        replyText = `We encountered a momentary issue: ${res.error}`;
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
    transcriptLive,
    startVoiceRecording,
    stopVoiceRecording,
    streamAIResponse,
    sendUtterance,
    triggerBargeIn,
    speak,
    stopSpeaking,
  };
}
