import { useState, useEffect, useRef, useCallback } from 'react';

export function useVoiceSynthesis() {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const currentUtteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  // Stop speaking immediately (Barge-In)
  const stop = useCallback(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      currentUtteranceRef.current = null;
      setIsSpeaking(false);
    }
  }, []);

  const speak = useCallback(
    (text: string, onEnd?: () => void) => {
      if (isMuted || !text.trim()) return;
      if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;

      // Stop any prior playback before new speech
      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      currentUtteranceRef.current = utterance;

      // Select a clear English voice if available
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

      utterance.rate = 1.05; // natural clinical speech speed
      utterance.pitch = 1.0;

      utterance.onstart = () => {
        setIsSpeaking(true);
      };

      utterance.onend = () => {
        setIsSpeaking(false);
        currentUtteranceRef.current = null;
        if (onEnd) onEnd();
      };

      utterance.onerror = (e) => {
        // Interrupted or canceled is expected during barge-in
        setIsSpeaking(false);
        currentUtteranceRef.current = null;
      };

      window.speechSynthesis.speak(utterance);
    },
    [isMuted]
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  return {
    isSpeaking,
    isMuted,
    setIsMuted,
    speak,
    stop,
  };
}
