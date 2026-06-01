"use client";

import { useEffect, useRef, useState } from "react";

/* Voice input via the browser Web Speech API (Chrome/Edge).
 * Push-to-talk: click to start, click to stop. Final transcript is pushed up
 * via onTranscript; interim results update live. No external model/API — keeps
 * GPT-5.5 as the only LLM in the system. */
interface Props {
  onTranscript: (text: string, isFinal: boolean) => void;
  disabled?: boolean;
}

export default function MicButton({ onTranscript, disabled }: Props) {
  const [supported, setSupported] = useState(true);
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    const SR =
      (typeof window !== "undefined" &&
        ((window as any).SpeechRecognition ||
          (window as any).webkitSpeechRecognition)) ||
      null;
    if (!SR) {
      setSupported(false);
      return;
    }
    const recognition = new SR();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onresult = (event: any) => {
      let interim = "";
      let final = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) final += transcript;
        else interim += transcript;
      }
      if (final) onTranscript(final, true);
      else if (interim) onTranscript(interim, false);
    };
    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);

    recognitionRef.current = recognition;
    return () => {
      try {
        recognition.stop();
      } catch {
        /* noop */
      }
    };
    // onTranscript is stable enough for this demo; intentionally run once.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggle = () => {
    const rec = recognitionRef.current;
    if (!rec) return;
    if (listening) {
      rec.stop();
      setListening(false);
    } else {
      try {
        rec.start();
        setListening(true);
      } catch {
        /* already started */
      }
    }
  };

  if (!supported) {
    return (
      <button
        type="button"
        title="Voice input needs Chrome or Edge"
        disabled
        className="grid h-11 w-11 place-items-center rounded-full bg-gray-100 text-gray-400"
      >
        <MicIcon />
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={toggle}
      disabled={disabled}
      title={listening ? "Stop listening" : "Speak your question"}
      className={`grid h-11 w-11 place-items-center rounded-full transition-colors ${
        listening
          ? "animate-pulse bg-optum-orange text-white"
          : "bg-uhc-blue-soft text-uhc-blue hover:bg-uhc-blue-bright hover:text-white"
      } disabled:opacity-50`}
    >
      <MicIcon />
    </button>
  );
}

function MicIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" y1="19" x2="12" y2="23" />
      <line x1="8" y1="23" x2="16" y2="23" />
    </svg>
  );
}
