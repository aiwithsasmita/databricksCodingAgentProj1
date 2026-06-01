"use client";

import { useEffect, useState } from "react";
import { speak, stopSpeaking, ttsSupported } from "@/lib/tts";
import FlowDiagram from "./FlowDiagram";

export type Role = "user" | "assistant";

export interface Message {
  id: string;
  role: Role;
  content: string;
  streaming?: boolean;
  error?: boolean;
  // When set, this message is a human-in-the-loop SQL approval card.
  approval?: { sql: string; question: string; allowed: string[]; resolved?: string };
  // Mermaid flow diagram of how this answer was generated.
  mermaid?: string;
}

export default function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const [speaking, setSpeaking] = useState(false);
  const [showFlow, setShowFlow] = useState(false);
  const canSpeak = !isUser && !message.error && ttsSupported();
  const hasFlow = !isUser && !!message.mermaid && !message.streaming;

  // Stop speaking this message if it unmounts.
  useEffect(() => () => stopSpeaking(), []);

  const toggleSpeak = () => {
    if (speaking) {
      stopSpeaking();
      setSpeaking(false);
    } else {
      setSpeaking(true);
      speak(message.content, () => setSpeaking(false));
    }
  };

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-[15px] leading-relaxed ${
          isUser
            ? "rounded-br-sm bg-uhc-blue text-white"
            : message.error
            ? "rounded-bl-sm border border-red-200 bg-red-50 text-red-700"
            : "rounded-bl-sm border border-uhc-blue-soft bg-white text-gray-800"
        }`}
      >
        {!isUser && (
          <div className="mb-1 flex items-center justify-between gap-3">
            <span className="text-xs font-semibold text-optum-orange">DRG Assistant</span>
            {canSpeak && !message.streaming && (
              <button
                type="button"
                onClick={toggleSpeak}
                title={speaking ? "Stop reading" : "Read aloud"}
                className={`grid h-6 w-6 place-items-center rounded-full transition-colors ${
                  speaking
                    ? "bg-optum-orange text-white"
                    : "text-uhc-blue-bright hover:bg-uhc-blue-soft"
                }`}
              >
                {speaking ? <StopIcon /> : <SpeakerIcon />}
              </button>
            )}
          </div>
        )}
        <span className={message.streaming ? "streaming-caret" : ""}>{message.content}</span>

        {hasFlow && (
          <div className="mt-2 border-t border-uhc-blue-soft pt-2">
            <button
              type="button"
              onClick={() => setShowFlow((v) => !v)}
              className="flex items-center gap-1 text-xs font-semibold text-uhc-blue-bright hover:text-uhc-blue"
            >
              <FlowIcon />
              {showFlow ? "Hide flow" : "Show flow"}
            </button>
            {showFlow && <FlowDiagram code={message.mermaid as string} />}
          </div>
        )}
      </div>
    </div>
  );
}

function FlowIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="4" y="3" width="6" height="4" rx="1" />
      <rect x="14" y="10" width="6" height="4" rx="1" />
      <rect x="4" y="17" width="6" height="4" rx="1" />
      <path d="M10 5h3a2 2 0 0 1 2 2v3M10 19h3a2 2 0 0 0 2-2v-3" />
    </svg>
  );
}

function SpeakerIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
      <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
      <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
    </svg>
  );
}

function StopIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
      <rect x="5" y="5" width="14" height="14" rx="2" />
    </svg>
  );
}
