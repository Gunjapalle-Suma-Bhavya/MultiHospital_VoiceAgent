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

// Helper to strip markdown and symbols so speech synthesis sounds natural
export const cleanTextForSpeech = (raw: string): string => {
  if (!raw) return '';
  return raw
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/\*(.*?)\*/g, '$1')
    .replace(/#{1,6}\s+/g, '')
    .replace(/`{1,3}.*?`{1,3}/gs, '')
    .replace(/\[(.*?)\]\(.*?\)/g, '$1')
    .replace(/[•\t\r]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
};

// Locale and multi-language mappings
export const LOCALE_MAP: Record<string, string> = {
  en: 'en-US',
  es: 'es-ES',
  hi: 'hi-IN',
  te: 'te-IN',
  zh: 'zh-CN',
};

export const GREETINGS: Record<string, string> = {
  en: 'Hello, this is the NexusHealth AI Voice Intake Agent. How can I assist you with your health or appointment scheduling today?',
  te: 'నమస్కారం! నేను మీ నెక్సస్ హెల్త్ ఏఐ వాయిస్ అసిస్టెంట్‌ని. ఈ రోజు మీ ఆరోగ్య సమస్య లేదా అపాయింట్‌మెంట్ బుకింగ్ కోసం ఎలా సహాయపడగలను?',
  hi: 'नमस्ते! मैं आपका नेक्सस हेल्थ एआई वॉयस असिस्टेंट हूँ। आज मैं आपकी स्वास्थ्य या अपॉइंटमेंट शेड्यूलिंग में कैसे मदद कर सकता हूँ?',
  es: '¡Hola! Este es el Agente de Voz de NexusHealth AI. ¿Cómo puedo ayudarle con su salud o programación de citas hoy?',
  zh: '您好，这里是 NexusHealth AI 语音分诊助手。今天有什么可以为您效劳？',
};

export function useVoiceAgent(selectedLanguage: string = 'en') {
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
  const [voiceMode, setVoiceMode] = useState<'browser' | 'server'>('browser');

  // Automatic Speech Endpointing (VAD) & Continuous Hands-Free Dialogue
  const [isEndpointPending, setIsEndpointPending] = useState<boolean>(false);
  const [handsFreeMode, setHandsFreeMode] = useState<boolean>(true);

  const selectedLanguageRef = useRef<string>(selectedLanguage);

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg-init',
      sender: 'assistant',
      text: GREETINGS[selectedLanguage] || GREETINGS.en,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      intent: 'GREETING',
    },
  ]);

  useEffect(() => {
    selectedLanguageRef.current = selectedLanguage;
    // Update initial greeting if user hasn't started talking yet
    setMessages((prev) => {
      if (prev.length === 1 && prev[0].id === 'msg-init') {
        return [
          {
            ...prev[0],
            text: GREETINGS[selectedLanguage] || GREETINGS.en,
          },
        ];
      }
      return prev;
    });

    const targetLocale = LOCALE_MAP[selectedLanguage] || 'en-US';
    if (recognitionRef.current) {
      recognitionRef.current.lang = targetLocale;
      if (isRecordingRef.current) {
        try {
          recognitionRef.current.stop();
          setTimeout(() => {
            try {
              recognitionRef.current?.start();
            } catch {}
          }, 150);
        } catch {}
      }
    }
  }, [selectedLanguage]);

  const recognitionRef = useRef<any>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const lastTranscriptRef = useRef<string>('');
  const onAutoSendRef = useRef<((text: string) => void) | null>(null);
  const onInterimRef = useRef<((text: string) => void) | null>(null);
  const serverAudioRef = useRef<HTMLAudioElement | null>(null);
  const audioSeqRef = useRef<number>(0);
  const isProcessingRef = useRef<boolean>(false);
  const isRecordingRef = useRef<boolean>(false);
  const isSpeakingRef = useRef<boolean>(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const currentAiSpeechTextRef = useRef<string>('');
  const endpointTimerRef = useRef<any>(null);
  const handsFreeRef = useRef<boolean>(true);
  const commitAndSendRef = useRef<() => void>(() => {});
  const startVoiceRef = useRef<((onInterim?: (t: string) => void, onFinal?: (t: string) => void) => void) | null>(null);
  const sessionIdRef = useRef<string>(`voice-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`);

  const stopSpeaking = useCallback(() => {
    audioSeqRef.current += 1;
    currentAiSpeechTextRef.current = '';
    isSpeakingRef.current = false;
    setIsSpeaking(false);

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
      (window as any).__nexusUtteranceQueue = [];
      (window as any).__nexusActiveUtterance = null;
      if (resumeTimer) {
        clearInterval(resumeTimer);
        resumeTimer = null;
      }
    }
  }, []);

  const triggerBargeIn = useCallback(() => {
    stopSpeaking();
    if (abortControllerRef.current) {
      try {
        abortControllerRef.current.abort();
      } catch {}
      abortControllerRef.current = null;
    }
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setStreamActive(false);
    }
    isProcessingRef.current = false;
    setIsProcessing(false);
    setBargeInAlert(true);
    setTimeout(() => {
      setBargeInAlert(false);
    }, 1500);
  }, [stopSpeaking]);

  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameAudioRef = useRef<number | null>(null);

  const startAudioMonitoring = useCallback(async () => {
    try {
      if (typeof window === 'undefined' || !navigator.mediaDevices?.getUserMedia) return;
      if (mediaStreamRef.current) return;

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true }
      });
      mediaStreamRef.current = stream;

      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioCtx) return;
      const audioCtx = new AudioCtx();
      audioContextRef.current = audioCtx;

      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      analyserRef.current = analyser;

      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);

      const dataArray = new Uint8Array(analyser.frequencyBinCount);

      const updateLevel = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
        }
        const avg = sum / dataArray.length;
        const normalized = Math.min(100, Math.round((avg / 128) * 100));
        setAudioLevel(normalized);
        animFrameAudioRef.current = requestAnimationFrame(updateLevel);
      };
      updateLevel();
    } catch (e) {
      console.warn('Microphone audio level monitoring unavailable:', e);
    }
  }, []);

  const stopAudioMonitoring = useCallback(() => {
    if (animFrameAudioRef.current) {
      cancelAnimationFrame(animFrameAudioRef.current);
      animFrameAudioRef.current = null;
    }
    if (mediaStreamRef.current) {
      try {
        mediaStreamRef.current.getTracks().forEach((t) => t.stop());
      } catch {}
      mediaStreamRef.current = null;
    }
    if (audioContextRef.current) {
      try {
        audioContextRef.current.close();
      } catch {}
      audioContextRef.current = null;
    }
    analyserRef.current = null;
    setAudioLevel(0);
  }, []);

  const speakWithBrowserTTS = useCallback((textToSpeak: string) => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      setIsSpeaking(false);
      isSpeakingRef.current = false;
      currentAiSpeechTextRef.current = '';
      return;
    }

    try {
      window.speechSynthesis.cancel();

      const cleaned = cleanTextForSpeech(textToSpeak);
      if (!cleaned) {
        setIsSpeaking(false);
        isSpeakingRef.current = false;
        currentAiSpeechTextRef.current = '';
        return;
      }

      // Crucial: Set speaking state to TRUE immediately so speech chunking starts and runs
      setIsSpeaking(true);
      isSpeakingRef.current = true;
      currentAiSpeechTextRef.current = cleaned;

      // Split into sentence chunks to prevent Chromium 15-second cutoff / GC bug
      const rawSentences = cleaned.match(/[^.!?\n]+[.!?\n]*/g) || [cleaned];
      const sentences = rawSentences.map((s) => s.trim()).filter((s) => s.length > 0);
      if (sentences.length === 0) sentences.push(cleaned);

      const currentLang = selectedLanguageRef.current || 'en';
      const targetLocale = LOCALE_MAP[currentLang] || 'en-US';

      // Pick best voice for selected language
      const voices = window.speechSynthesis.getVoices();
      let preferredVoice: SpeechSynthesisVoice | undefined;
      if (voices && voices.length > 0) {
        const langPrefix = currentLang.toLowerCase();
        preferredVoice =
          voices.find((v) => v.lang.toLowerCase().replace('_', '-').startsWith(langPrefix)) ||
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
      }

      let chunkIdx = 0;
      (window as any).__nexusUtteranceQueue = [];

      const speakNextChunk = () => {
        if (!isSpeakingRef.current) {
          (window as any).__nexusUtteranceQueue = [];
          activeUtterance = null;
          (window as any).__nexusActiveUtterance = null;
          return;
        }

        if (chunkIdx >= sentences.length) {
          // Finished all sentence chunks
          (window as any).__nexusUtteranceQueue = [];
          activeUtterance = null;
          (window as any).__nexusActiveUtterance = null;
          if (resumeTimer) {
            clearInterval(resumeTimer);
            resumeTimer = null;
          }
          setIsSpeaking(false);
          isSpeakingRef.current = false;
          currentAiSpeechTextRef.current = '';
          return;
        }

        const chunkText = sentences[chunkIdx++];
        const utterance = new SpeechSynthesisUtterance(chunkText);
        (window as any).__nexusUtteranceQueue.push(utterance);
        activeUtterance = utterance;
        (window as any).__nexusActiveUtterance = utterance;

        utterance.lang = targetLocale;
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.volume = 1.0; // Ensure 100% volume
        if (preferredVoice) utterance.voice = preferredVoice;

        utterance.onstart = () => {
          setIsSpeaking(true);
          isSpeakingRef.current = true;
          currentAiSpeechTextRef.current = chunkText;
        };

        utterance.onend = () => {
          if (!isSpeakingRef.current) return;
          setTimeout(speakNextChunk, 25);
        };

        utterance.onerror = (e) => {
          console.warn('Speech synthesis chunk warning:', e);
          if (!isSpeakingRef.current) return;
          setTimeout(speakNextChunk, 25);
        };

        try {
          window.speechSynthesis.resume();
          window.speechSynthesis.speak(utterance);
        } catch (speakErr) {
          console.warn('window.speechSynthesis.speak error:', speakErr);
        }
      };

      // Unpause Chromium speech synthesis and start speaking chunks
      try {
        window.speechSynthesis.resume();
      } catch {}
      setTimeout(() => {
        if (!isSpeakingRef.current) return;
        try {
          window.speechSynthesis.resume();
          speakNextChunk();
        } catch (e) {
          console.warn('Initial speak chunk error:', e);
        }
      }, 40);

      // Keep-alive heartbeat interval for Chromium Linux/Windows
      if (resumeTimer) clearInterval(resumeTimer);
      resumeTimer = setInterval(() => {
        if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
          if (window.speechSynthesis.speaking) {
            window.speechSynthesis.resume();
          } else if (!window.speechSynthesis.pending && chunkIdx >= sentences.length) {
            clearInterval(resumeTimer);
            resumeTimer = null;
          }
        }
      }, 1500);

    } catch (err) {
      console.warn('speakWithBrowserTTS error:', err);
      setIsSpeaking(false);
      isSpeakingRef.current = false;
      currentAiSpeechTextRef.current = '';
    }
  }, []);

  // Universal Server Audio Playback (ElevenLabs Neural TTS) with fallback to Browser TTS
  const playServerAudio = useCallback(async (textToSpeak: string) => {
    stopSpeaking();
    const seq = ++audioSeqRef.current;

    try {
      setIsSpeaking(true);
      isSpeakingRef.current = true;
      const currentLang = selectedLanguageRef.current || 'en';
      const res = await fetch('/api/v1/voice/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: textToSpeak, language: currentLang, voice: 'clinical_female' }),
      });

      if (audioSeqRef.current !== seq || !isSpeakingRef.current) return;

      if (res.ok) {
        const data = await res.json();
        if (audioSeqRef.current !== seq || !isSpeakingRef.current) return;

        // ONLY play ElevenLabs base64 audio if it's real neural TTS audio (provider: elevenlabs)!
        // If it's local_fallback (synthetic beep tone), DO NOT play the beep — speak with Browser TTS!
        if (data.provider === 'elevenlabs' && data.audio_base64) {
          if (serverAudioRef.current) {
            try {
              serverAudioRef.current.pause();
              serverAudioRef.current.currentTime = 0;
            } catch {}
            serverAudioRef.current = null;
          }

          setIsSpeaking(true);
          isSpeakingRef.current = true;
          const audio = new Audio(data.audio_base64);
          serverAudioRef.current = audio;
          currentAiSpeechTextRef.current = textToSpeak;

          audio.onended = () => {
            if (serverAudioRef.current === audio) {
              serverAudioRef.current = null;
            }
            setIsSpeaking(false);
            isSpeakingRef.current = false;
            currentAiSpeechTextRef.current = '';
          };

          audio.onerror = (e) => {
            console.warn('Server audio playback error, falling back to browser TTS:', e);
            if (serverAudioRef.current === audio) {
              serverAudioRef.current = null;
            }
            speakWithBrowserTTS(textToSpeak);
          };

          try {
            await audio.play();
            return;
          } catch (playErr) {
            console.warn('audio.play() blocked, using browser TTS:', playErr);
          }
        }
      }

      // If ElevenLabs was unavailable or returned local_fallback, speak with Browser TTS!
      speakWithBrowserTTS(textToSpeak);
    } catch (err) {
      console.warn('playServerAudio error, falling back to browser speech:', err);
      speakWithBrowserTTS(textToSpeak);
    }
  }, [stopSpeaking, speakWithBrowserTTS]);

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
      stopSpeaking();

      if (voiceMode === 'server') {
        playServerAudio(text);
      } else {
        speakWithBrowserTTS(text);
      }
    },
    [isMuted, stopSpeaking, voiceMode, playServerAudio, speakWithBrowserTTS]
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
      recognition.lang = LOCALE_MAP[selectedLanguageRef.current || 'en'] || 'en-US';

      recognition.onspeechstart = () => {
        // Natural speech detected by browser engine
      };

      recognition.onsoundstart = () => {
        // Audio wave detected by browser engine
      };

      recognition.onstart = () => {
        setIsRecording(true);
        isRecordingRef.current = true;
        setVoiceNotice(null);
      };

      recognition.onresult = (event: any) => {
        let fullTranscript = '';
        for (let i = 0; i < event.results.length; i++) {
          const piece = event.results[i][0].transcript.trim();
          if (piece) {
            fullTranscript = fullTranscript ? `${fullTranscript} ${piece}` : piece;
          }
        }

        const trimmed = fullTranscript.trim();
        if (!trimmed) return;

        // If AI is currently vocalizing, check if user actually said something distinct (not an echo of the AI)
        if (isSpeakingRef.current || (typeof window !== 'undefined' && window.speechSynthesis?.speaking) || serverAudioRef.current) {
          const currentAi = (currentAiSpeechTextRef.current || '').toLowerCase();
          const patientSaid = trimmed.toLowerCase();
          // If the recognized audio is simply picking up the AI's own words from the speaker, ignore it!
          if (currentAi && currentAi.includes(patientSaid)) {
            return;
          }
          // Patient deliberately spoke a new phrase/command: interrupt cleanly
          if (patientSaid.length >= 3) {
            triggerBargeIn();
          } else {
            return;
          }
        }

        lastTranscriptRef.current = trimmed;
        setTranscriptLive(trimmed);
        if (onInterimRef.current) {
          onInterimRef.current(trimmed);
        }

        // Active speech detected: clear any endpointing pending state while user is speaking
        setIsEndpointPending(false);

        // Clear previous endpoint timer
        if (endpointTimerRef.current) {
          clearTimeout(endpointTimerRef.current);
          endpointTimerRef.current = null;
        }

        // Automatic Voice Activity Endpoint Detection (VAD):
        // Wait for 750ms of true silence after patient finishes speaking before submitting
        endpointTimerRef.current = setTimeout(() => {
          setIsEndpointPending(true);
          setTimeout(() => {
            commitAndSendRef.current();
          }, 50);
        }, 750);
      };

      recognition.onspeechend = () => {
        // Natural speech pause detected by audio hardware
        if (lastTranscriptRef.current.trim().length > 0) {
          setIsEndpointPending(true);
          if (endpointTimerRef.current) {
            clearTimeout(endpointTimerRef.current);
          }
          endpointTimerRef.current = setTimeout(() => {
            commitAndSendRef.current();
          }, 650);
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
        }
        // Always maintain continuous listening in hands-free mode
        if (handsFreeRef.current) {
          setTimeout(() => {
            if (handsFreeRef.current && !isRecordingRef.current) {
              try {
                recognitionRef.current?.start();
                setIsRecording(true);
                isRecordingRef.current = true;
              } catch {}
            }
          }, 100);
        }
      };

      recognition.onerror = (e: any) => {
        console.warn('Speech recognition status:', e.error);
        if (endpointTimerRef.current) {
          clearTimeout(endpointTimerRef.current);
          endpointTimerRef.current = null;
        }
        if (e.error === 'not-allowed') {
          setIsRecording(false);
          isRecordingRef.current = false;
          setVoiceNotice('Microphone blocked: Please click the lock or camera icon in your browser address bar to Allow microphone access.');
        } else if (e.error === 'no-speech') {
          // Normal timeout on silence: in hands-free mode, restart immediately so mic stays ready
          if (handsFreeRef.current) {
            setTimeout(() => {
              if (handsFreeRef.current && !isRecordingRef.current) {
                try {
                  recognitionRef.current?.start();
                  setIsRecording(true);
                  isRecordingRef.current = true;
                } catch {}
              }
            }, 100);
          }
        } else if (e.error === 'network') {
          setVoiceNotice('Speech recognition network paused. Speak or click to talk.');
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

    // Abort and restart recognition quickly so event.results clears fresh for next turn
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch {}
      setTimeout(() => {
        if (handsFreeRef.current && !isRecordingRef.current) {
          try {
            recognitionRef.current?.start();
            setIsRecording(true);
            isRecordingRef.current = true;
          } catch {}
        }
      }, 80);
    }

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

    // Stop any AI audio immediately when user initiates speech intake
    stopSpeaking();

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

    // Immediately reflect active recording in UI and start live decibel visualizer
    setIsRecording(true);
    isRecordingRef.current = true;
    startAudioMonitoring();

    if (recognitionRef.current) {
      recognitionRef.current.lang = LOCALE_MAP[selectedLanguageRef.current || 'en'] || 'en-US';
    }

    try {
      lastTranscriptRef.current = '';
      setTranscriptLive('');
      recognitionRef.current.start();
    } catch (err: any) {
      try {
        recognitionRef.current.stop();
        setTimeout(() => {
          try {
            recognitionRef.current.start();
          } catch {}
        }, 120);
      } catch (retryErr) {
        setVoiceNotice('Microphone starting... Click again if your browser is prompting for permission.');
      }
    }
  }, [stopSpeaking, startAudioMonitoring]);

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
    stopAudioMonitoring();

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
  }, [stopAudioMonitoring]);

  const testSpeaker = () => {
    if (isMuted) setIsMuted(false);
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      try {
        window.speechSynthesis.resume();
      } catch {}
    }
    const testPhrases: Record<string, string> = {
      en: 'NexusHealth AI voice system is active. Your audio output is working properly.',
      te: 'నమస్కారం! నెక్సస్ హెల్త్ ఏఐ వాయిస్ సిస్టమ్ పనిచేస్తోంది. మీ ఆడియో అవుట్‌పుట్ సరిగ్గా ఉంది.',
      hi: 'नेक्सस हेल्थ एआई वॉयस सिस्टम सक्रिय है। आपका ऑडियो आउटपुट ठीक से काम कर रहा है।',
      es: 'El sistema de voz de NexusHealth AI está activo. Su salida de audio funciona correctamente.',
      zh: 'NexusHealth AI 语音系统已启动，您的音频输出正常。',
    };
    speak(testPhrases[selectedLanguageRef.current || 'en'] || testPhrases.en);
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
      `/api/v1/should-have/streaming/demo?utterance=${encodeURIComponent(userUtterance)}&language=${encodeURIComponent(selectedLanguageRef.current || 'en')}`
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
    hospitalId?: string
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

    if (abortControllerRef.current) {
      try {
        abortControllerRef.current.abort();
      } catch {}
      abortControllerRef.current = null;
    }
    const ac = new AbortController();
    abortControllerRef.current = ac;
    const startTime = performance.now();

    try {
      const res = await apiCall('/api/voice/chat', {
        method: 'POST',
        signal: ac.signal,
        body: JSON.stringify({
          session_id: sessionIdRef.current,
          patient_phone: patientPhone,
          user_utterance: text,
          hospital_id: hospitalId || undefined,
          language: selectedLanguageRef.current || 'en',
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
