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

// Global reference to prevent Chrome garbage-collection of active utterance
let activeUtterance: SpeechSynthesisUtterance | null = null;
let resumeTimer: any = null;

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
  const [voiceNotice, setVoiceNotice] = useState<string | null>(null);
  const [hasSpeechSupport, setHasSpeechSupport] = useState<boolean>(true);

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
  const onInterimRef = useRef<((text: string) => void) | null>(null);

  const stopSpeaking = useCallback(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      try {
        window.speechSynthesis.cancel();
      } catch {}
      activeUtterance = null;
      if (resumeTimer) {
        clearInterval(resumeTimer);
        resumeTimer = null;
      }
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

      setTimeout(() => {
        try {
          const utterance = new SpeechSynthesisUtterance(text);
          activeUtterance = utterance;
          utterance.lang = 'en-US';

          const voices = window.speechSynthesis.getVoices();
          if (voices && voices.length > 0) {
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
          }

          utterance.rate = 1.0;
          utterance.pitch = 1.0;

          utterance.onstart = () => {
            setIsSpeaking(true);
          };

          utterance.onend = () => {
            activeUtterance = null;
            if (resumeTimer) {
              clearInterval(resumeTimer);
              resumeTimer = null;
            }
            setIsSpeaking(false);
          };

          utterance.onerror = (e) => {
            console.warn('Speech synthesis notice:', e);
            activeUtterance = null;
            if (resumeTimer) {
              clearInterval(resumeTimer);
              resumeTimer = null;
            }
            setIsSpeaking(false);
          };

          window.speechSynthesis.speak(utterance);

          // Keep-alive timer for Chromium Windows bug
          if (resumeTimer) clearInterval(resumeTimer);
          resumeTimer = setInterval(() => {
            if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
              if (window.speechSynthesis.speaking) {
                window.speechSynthesis.resume();
              } else {
                clearInterval(resumeTimer);
                resumeTimer = null;
              }
            }
          }, 3000);
        } catch (err) {
          console.warn('speak exception:', err);
          setIsSpeaking(false);
        }
      }, 30);
    },
    [isMuted, stopSpeaking]
  );

  // Initialize Speech Recognition
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setHasSpeechSupport(false);
      setVoiceNotice('Browser Notice: Speech recognition is native to Chrome, Edge, and Chromium browsers.');
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onspeechstart = () => {
        triggerBargeIn();
      };

      recognition.onstart = () => {
        setIsRecording(true);
        setVoiceNotice(null);
      };

      recognition.onresult = (event: any) => {
        let current = '';
        for (let i = 0; i < event.results.length; i++) {
          current += event.results[i][0].transcript;
        }
        lastTranscriptRef.current = current;
        setTranscriptLive(current);
        if (onInterimRef.current) {
          onInterimRef.current(current);
        }
      };

      recognition.onend = () => {
        setIsRecording(false);
        const finalVal = lastTranscriptRef.current.trim();
        if (finalVal && onAutoSendRef.current) {
          const fn = onAutoSendRef.current;
          onAutoSendRef.current = null;
          lastTranscriptRef.current = '';
          setTranscriptLive('');
          fn(finalVal);
        }
      };

      recognition.onerror = (e: any) => {
        console.warn('Speech recognition status:', e.error);
        setIsRecording(false);
        if (e.error === 'not-allowed') {
          setVoiceNotice('Microphone blocked: Please click the lock or camera icon in your browser address bar to Allow microphone access.');
        } else if (e.error === 'no-speech') {
          setVoiceNotice('No words heard: Speak closer to your microphone or click a quick scenario below.');
        } else if (e.error === 'network') {
          setVoiceNotice('Speech recognition network paused: You can click any quick scenario or type below to talk with AI.');
        } else {
          setVoiceNotice(`Microphone status: ${e.error}`);
        }
      };

      recognitionRef.current = recognition;
    } catch (err) {
      console.warn('Speech recognition init failed:', err);
      setHasSpeechSupport(false);
    }

    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.onvoiceschanged = () => {
        try {
          window.speechSynthesis.getVoices();
        } catch {}
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
    setVoiceNotice(null);

    if (!recognitionRef.current) {
      setVoiceNotice('Microphone speech recognition is not available in this browser. Please use Chrome/Edge or click a quick scenario.');
      return;
    }

    if (onInterim) {
      onInterimRef.current = onInterim;
    }
    if (onFinalSubmit) {
      onAutoSendRef.current = onFinalSubmit;
    }

    try {
      lastTranscriptRef.current = '';
      setTranscriptLive('');
      recognitionRef.current.start();
    } catch (err: any) {
      console.warn('Recognition start caught error:', err);
      try {
        recognitionRef.current.stop();
        setTimeout(() => {
          recognitionRef.current.start();
        }, 150);
      } catch (retryErr) {
        setVoiceNotice('Microphone starting... Click again if your browser is prompting for permission.');
      }
    }
  };

  const stopVoiceRecording = () => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {}
      setIsRecording(false);
      const textToSend = lastTranscriptRef.current.trim();
      if (textToSend && onAutoSendRef.current) {
        const fn = onAutoSendRef.current;
        onAutoSendRef.current = null;
        lastTranscriptRef.current = '';
        setTranscriptLive('');
        fn(textToSend);
      }
    }
  };

  const testSpeaker = () => {
    speak('NexusHealth AI voice system is active. Your audio output is working properly.');
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
    voiceNotice,
    hasSpeechSupport,
    startVoiceRecording,
    stopVoiceRecording,
    streamAIResponse,
    sendUtterance,
    triggerBargeIn,
    speak,
    stopSpeaking,
    testSpeaker,
  };
}
