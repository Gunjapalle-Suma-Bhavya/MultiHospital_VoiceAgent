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

  // Upgrade 1 & 8: Audio Device Selection & Decibel Level Meter
  const [audioDevices, setAudioDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('default');
  const [audioLevel, setAudioLevel] = useState<number>(0);
  const [voiceMode, setVoiceMode] = useState<'browser' | 'server'>('server');

  // Automatic Speech Endpointing (VAD) & Continuous Hands-Free Dialogue
  const [isEndpointPending, setIsEndpointPending] = useState<boolean>(false);
  const [handsFreeMode, setHandsFreeMode] = useState<boolean>(true);

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
  const serverAudioRef = useRef<HTMLAudioElement | null>(null);
  const audioSeqRef = useRef<number>(0);
  const isProcessingRef = useRef<boolean>(false);
  const isRecordingRef = useRef<boolean>(false);
  const currentAiSpeechTextRef = useRef<string>('');
  const endpointTimerRef = useRef<any>(null);
  const handsFreeRef = useRef<boolean>(true);
  const commitAndSendRef = useRef<() => void>(() => {});
  const startVoiceRef = useRef<((onInterim?: (t: string) => void, onFinal?: (t: string) => void) => void) | null>(null);
  const sessionIdRef = useRef<string>(`voice-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`);

  const isSelfEcho = (transcript: string, aiText: string): boolean => {
    if (!aiText || !transcript) return false;
    const cleanT = transcript.toLowerCase().trim().replace(/[^\w\s]/g, '');
    const cleanAi = aiText.toLowerCase().trim().replace(/[^\w\s]/g, '');
    if (!cleanT) return false;
    if (cleanAi.includes(cleanT) || cleanT.includes(cleanAi)) {
      return true;
    }
    const tWords = cleanT.split(/\s+/).filter(Boolean);
    const aiWords = new Set(cleanAi.split(/\s+/).filter(Boolean));
    if (tWords.length > 0) {
      const matchCount = tWords.filter((w) => aiWords.has(w)).length;
      if (matchCount / tWords.length >= 0.75 && tWords.length >= 2) {
        return true;
      }
    }
    return false;
  };

  const stopSpeaking = useCallback(() => {
    audioSeqRef.current += 1;
    currentAiSpeechTextRef.current = '';
    // 1. Immediately pause and destroy any playing ElevenLabs / server audio
    if (serverAudioRef.current) {
      try {
        serverAudioRef.current.pause();
        serverAudioRef.current.currentTime = 0;
      } catch {}
      serverAudioRef.current = null;
    }

    // 2. Immediately cancel browser speechSynthesis
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      try {
        window.speechSynthesis.cancel();
      } catch {}
      activeUtterance = null;
      if (resumeTimer) {
        clearInterval(resumeTimer);
        resumeTimer = null;
      }
    }
    setIsSpeaking(false);
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

  // Universal Server Audio Playback (ElevenLabs Neural TTS)
  const playServerAudio = useCallback(async (textToSpeak: string) => {
    // 1. Cancel previous audio and capture a fresh sequence token
    stopSpeaking();
    const seq = ++audioSeqRef.current;

    try {
      setIsSpeaking(true);
      const res = await fetch('/api/v1/voice/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: textToSpeak, language: 'en', voice: 'clinical_female' }),
      });

      // If interrupted during network fetch, drop stale audio
      if (audioSeqRef.current !== seq) {
        return;
      }

      if (res.ok) {
        const data = await res.json();
        if (audioSeqRef.current !== seq) return;

        if (data.audio_base64) {
          // Pause and clean up any previous audio element without advancing sequence
          if (serverAudioRef.current) {
            try {
              serverAudioRef.current.pause();
              serverAudioRef.current.currentTime = 0;
            } catch {}
            serverAudioRef.current = null;
          }

          setIsSpeaking(true);
          const audio = new Audio(data.audio_base64);
          serverAudioRef.current = audio;
          currentAiSpeechTextRef.current = textToSpeak;

          audio.onended = () => {
            if (serverAudioRef.current === audio) {
              serverAudioRef.current = null;
            }
            setIsSpeaking(false);
            currentAiSpeechTextRef.current = '';
            if (handsFreeRef.current && !isProcessingRef.current && !isRecordingRef.current) {
              setTimeout(() => {
                if (handsFreeRef.current && !isProcessingRef.current && !isRecordingRef.current) {
                  try {
                    recognitionRef.current?.start();
                  } catch {}
                }
              }, 200);
            }
          };
          audio.onerror = (e) => {
            console.warn('Server audio playback error:', e);
            if (serverAudioRef.current === audio) {
              serverAudioRef.current = null;
            }
            setIsSpeaking(false);
            currentAiSpeechTextRef.current = '';
          };

          try {
            await audio.play();
            // Full-duplex listening: Keep microphone active during playback so patient can interrupt anytime
            if (handsFreeRef.current && !isRecordingRef.current && !isProcessingRef.current) {
              setTimeout(() => {
                if (handsFreeRef.current && !isRecordingRef.current && !isProcessingRef.current) {
                  try {
                    recognitionRef.current?.start();
                  } catch {}
                }
              }, 150);
            }
            return;
          } catch (playErr) {
            console.warn('audio.play() failed, attempting fallback to browser speech:', playErr);
          }
        }
      }

      // Graceful fallback to browser speech synthesis if server audio is unavailable or play() was blocked
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        try {
          window.speechSynthesis.cancel();
          const utterance = new SpeechSynthesisUtterance(textToSpeak);
          utterance.lang = 'en-US';
          utterance.onstart = () => {
            setIsSpeaking(true);
            currentAiSpeechTextRef.current = textToSpeak;
            if (handsFreeRef.current && !isRecordingRef.current && !isProcessingRef.current) {
              setTimeout(() => {
                if (handsFreeRef.current && !isRecordingRef.current && !isProcessingRef.current) {
                  try {
                    recognitionRef.current?.start();
                  } catch {}
                }
              }, 150);
            }
          };
          utterance.onend = () => {
            setIsSpeaking(false);
            currentAiSpeechTextRef.current = '';
            if (handsFreeRef.current && !isProcessingRef.current && !isRecordingRef.current) {
              try {
                recognitionRef.current?.start();
              } catch {}
            }
          };
          utterance.onerror = () => {
            setIsSpeaking(false);
            currentAiSpeechTextRef.current = '';
          };
          setIsSpeaking(true);
          window.speechSynthesis.speak(utterance);
          return;
        } catch {}
      }

      setIsSpeaking(false);
      currentAiSpeechTextRef.current = '';
    } catch (err) {
      console.warn('playServerAudio caught error:', err);
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        try {
          const utterance = new SpeechSynthesisUtterance(textToSpeak);
          utterance.lang = 'en-US';
          window.speechSynthesis.speak(utterance);
        } catch {}
      }
      setIsSpeaking(false);
      currentAiSpeechTextRef.current = '';
    }
  }, [stopSpeaking]);

  // Enumerate input devices on mount
  useEffect(() => {
    if (typeof navigator !== 'undefined' && navigator.mediaDevices?.enumerateDevices) {
      navigator.mediaDevices.enumerateDevices().then((devices) => {
        const audioInputs = devices.filter((d) => d.kind === 'audioinput');
        setAudioDevices(audioInputs);
        if (audioInputs.length > 0 && selectedDeviceId === 'default') {
          setSelectedDeviceId(audioInputs[0].deviceId || 'default');
        }
      }).catch(() => {});
    }
  }, [selectedDeviceId]);

  const speak = useCallback(
    (text: string) => {
      if (isMuted || !text.trim()) return;

      // Always terminate any currently active speech first to guarantee zero double-voices
      stopSpeaking();

      // Check for server-side speech synthesis (ElevenLabs Neural)
      if (voiceMode === 'server' || typeof window === 'undefined' || !('speechSynthesis' in window)) {
        playServerAudio(text);
        return;
      }

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
            if (handsFreeRef.current && !isProcessingRef.current) {
              setTimeout(() => {
                if (handsFreeRef.current && !isProcessingRef.current && !activeUtterance) {
                  startVoiceRef.current?.();
                }
              }, 400);
            }
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
        // Sound detected by microphone.
      };

      recognition.onstart = () => {
        setIsRecording(true);
        isRecordingRef.current = true;
        setVoiceNotice(null);
      };

      recognition.onresult = (event: any) => {
        let current = '';
        for (let i = 0; i < event.results.length; i++) {
          current += event.results[i][0].transcript;
        }

        const trimmed = current.trim();
        if (!trimmed) return;

        // Full-duplex barge-in check: If AI is actively vocalizing audio
        const currentlySpeaking = !!serverAudioRef.current || (typeof window !== 'undefined' && window.speechSynthesis?.speaking);
        if (currentlySpeaking) {
          if (isSelfEcho(trimmed, currentAiSpeechTextRef.current)) {
            // Echo detected from computer speaker - ignore so AI audio is not falsely interrupted
            return;
          }
          // Real patient speech detected while AI was speaking: INSTANT INTERRUPT!
          stopSpeaking();
          setBargeInAlert(true);
          setTimeout(() => {
            setBargeInAlert(false);
          }, 1500);
        }

        lastTranscriptRef.current = current;
        setTranscriptLive(current);
        if (onInterimRef.current) {
          onInterimRef.current(current);
        }

        // Automatic Voice Activity Endpoint Detection (VAD)
        if (endpointTimerRef.current) {
          clearTimeout(endpointTimerRef.current);
          endpointTimerRef.current = null;
        }

        setIsEndpointPending(true);
        // 1200ms of natural silence after speaking triggers automatic dispatch to AI
        endpointTimerRef.current = setTimeout(() => {
          commitAndSendRef.current();
        }, 1200);
      };

      recognition.onspeechend = () => {
        // Natural speech pause detected by audio hardware: accelerate auto-dispatch
        if (lastTranscriptRef.current.trim().length > 0) {
          setIsEndpointPending(true);
          if (endpointTimerRef.current) {
            clearTimeout(endpointTimerRef.current);
          }
          endpointTimerRef.current = setTimeout(() => {
            commitAndSendRef.current();
          }, 600);
        }
      };

      recognition.onend = () => {
        setIsRecording(false);
        isRecordingRef.current = false;
        setIsEndpointPending(false);
        if (endpointTimerRef.current) {
          clearTimeout(endpointTimerRef.current);
          endpointTimerRef.current = null;
        }
        const finalVal = lastTranscriptRef.current.trim();
        if (finalVal && onAutoSendRef.current) {
          const fn = onAutoSendRef.current;
          lastTranscriptRef.current = '';
          setTranscriptLive('');
          fn(finalVal);
        } else if (handsFreeRef.current && !isProcessingRef.current) {
          // Seamlessly restart recognition so hands-free listening remains active
          setTimeout(() => {
            if (handsFreeRef.current && !isProcessingRef.current && !isRecordingRef.current) {
              try {
                recognitionRef.current?.start();
              } catch {}
            }
          }, 200);
        }
      };

      recognition.onerror = (e: any) => {
        console.warn('Speech recognition status:', e.error);
        setIsRecording(false);
        isRecordingRef.current = false;
        setIsEndpointPending(false);
        if (endpointTimerRef.current) {
          clearTimeout(endpointTimerRef.current);
          endpointTimerRef.current = null;
        }
        if (e.error === 'not-allowed') {
          setVoiceNotice('Microphone blocked: Please click the lock or camera icon in your browser address bar to Allow microphone access.');
        } else if (e.error === 'no-speech') {
          // Normal timeout on silence: In hands-free mode, restart after brief pause
          if (handsFreeRef.current && !isProcessingRef.current) {
            setTimeout(() => {
              if (handsFreeRef.current && !isProcessingRef.current && !isRecordingRef.current) {
                try {
                  recognitionRef.current?.start();
                } catch {}
              }
            }, 300);
          }
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
      if (endpointTimerRef.current) {
        clearTimeout(endpointTimerRef.current);
        endpointTimerRef.current = null;
      }
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

  const commitAndSendVoice = useCallback(() => {
    if (endpointTimerRef.current) {
      clearTimeout(endpointTimerRef.current);
      endpointTimerRef.current = null;
    }
    setIsEndpointPending(false);

    const finalVal = (lastTranscriptRef.current || '').trim();
    if (!finalVal) return;

    // Reset transcript immediately so recognition onend doesn't double-send
    lastTranscriptRef.current = '';
    setTranscriptLive('');

    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {}
    }
    setIsRecording(false);
    isRecordingRef.current = false;

    if (onAutoSendRef.current) {
      onAutoSendRef.current(finalVal);
    }
  }, []);

  useEffect(() => {
    commitAndSendRef.current = commitAndSendVoice;
  }, [commitAndSendVoice]);

  const startVoiceRecording = useCallback((
    onInterim?: (text: string) => void,
    onFinalSubmit?: (text: string) => void
  ) => {
    setVoiceNotice(null);
    handsFreeRef.current = true;
    if (endpointTimerRef.current) {
      clearTimeout(endpointTimerRef.current);
      endpointTimerRef.current = null;
    }
    setIsEndpointPending(false);

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

    if (isRecordingRef.current) {
      return;
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
  }, [triggerBargeIn]);

  useEffect(() => {
    startVoiceRef.current = startVoiceRecording;
  }, [startVoiceRecording]);

  const stopVoiceRecording = useCallback(() => {
    handsFreeRef.current = false;
    if (endpointTimerRef.current) {
      clearTimeout(endpointTimerRef.current);
      endpointTimerRef.current = null;
    }
    setIsEndpointPending(false);
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {}
      setIsRecording(false);
      isRecordingRef.current = false;
      const textToSend = lastTranscriptRef.current.trim();
      if (textToSend && onAutoSendRef.current) {
        const fn = onAutoSendRef.current;
        lastTranscriptRef.current = '';
        setTranscriptLive('');
        fn(textToSend);
      }
    }
  }, []);

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
    if (!text.trim() || isProcessingRef.current) return null;
    isProcessingRef.current = true;
    setIsProcessing(true);

    triggerBargeIn();

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'patient',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages((prev) => [...prev, userMsg]);

    const startTime = performance.now();

    try {
      const res = await apiCall('/api/voice/chat', {
        method: 'POST',
        body: JSON.stringify({
          session_id: sessionIdRef.current,
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
        if (res.data.session_id) {
          sessionIdRef.current = res.data.session_id;
        }
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
      isProcessingRef.current = false;
      setIsProcessing(false);
    }
  };

  const resetSession = useCallback(() => {
    sessionIdRef.current = `voice-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
    stopSpeaking();
    stopVoiceRecording();
  }, [stopSpeaking, stopVoiceRecording]);

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
    audioDevices,
    selectedDeviceId,
    setSelectedDeviceId,
    audioLevel,
    voiceMode,
    setVoiceMode,
    isEndpointPending,
    handsFreeMode,
    setHandsFreeMode,
    commitAndSendVoice,
    resetSession,
    sessionId: sessionIdRef.current,
  };
}
