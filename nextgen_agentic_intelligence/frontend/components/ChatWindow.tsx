"use client";

import { useEffect, useRef, useState } from "react";
import { resumeChat, streamChat, StreamCallbacks } from "@/lib/api";
import { speak, stopSpeaking, ttsSupported } from "@/lib/tts";
import MessageBubble, { Message } from "./MessageBubble";
import MicButton from "./MicButton";
import SqlApprovalCard from "./SqlApprovalCard";

const SUGGESTIONS = [
  "Is DRG 871 (Septicemia) shifting toward MCC since 2023?",
  "How many taxi trips are in the dataset?",
  "Which MS-DRGs did CMS add in 2026?",
  "Search the web: latest CMS IPPS final rule",
];

function newThreadId() {
  return `web-${Math.random().toString(36).slice(2)}-${Date.now()}`;
}

const DECISION_LABEL: Record<string, string> = {
  approve: "approved",
  edit: "edited & run",
  reject: "rejected",
};

export default function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [voiceReplies, setVoiceReplies] = useState(true);
  const threadId = useRef<string>(newThreadId());
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const patch = (id: string, p: Partial<Message>) =>
    setMessages((m) => m.map((msg) => (msg.id === id ? { ...msg, ...p } : msg)));

  // Drives one streamed turn (chat or resume) into the given assistant message.
  const pump = (assistantId: string, start: (cb: StreamCallbacks) => Promise<void>) => {
    let acc = "";
    return start({
      onToken: (t) => {
        acc += t;
        patch(assistantId, { content: acc });
      },
      onInterrupt: (ap) => {
        patch(assistantId, { streaming: false });
        // Append a SQL approval card to the conversation.
        setMessages((m) => [
          ...m,
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content: "",
            approval: { sql: ap.sql, question: ap.question, allowed: ap.allowed_decisions },
          },
        ]);
        setBusy(false);
      },
      onTrace: (tr) => patch(assistantId, { mermaid: tr.mermaid }),
      onError: (err) => {
        patch(assistantId, { content: err, error: true, streaming: false });
        setBusy(false);
      },
      onDone: () => {
        patch(assistantId, { streaming: false });
        setBusy(false);
        if (voiceReplies && acc.trim()) speak(acc);
      },
    });
  };

  const send = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    stopSpeaking();

    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content: trimmed };
    const assistantId = crypto.randomUUID();
    setMessages((m) => [
      ...m,
      userMsg,
      { id: assistantId, role: "assistant", content: "", streaming: true },
    ]);
    setInput("");
    setBusy(true);
    await pump(assistantId, (cb) => streamChat(trimmed, threadId.current, cb));
  };

  const decide = async (
    approvalId: string,
    decision: "approve" | "edit" | "reject",
    editedSql: string | null
  ) => {
    if (busy) return;
    stopSpeaking();
    patch(approvalId, {
      approval: {
        ...(messages.find((m) => m.id === approvalId)!.approval as NonNullable<Message["approval"]>),
        resolved: DECISION_LABEL[decision],
      },
    });
    const assistantId = crypto.randomUUID();
    setMessages((m) => [...m, { id: assistantId, role: "assistant", content: "", streaming: true }]);
    setBusy(true);
    await pump(assistantId, (cb) => resumeChat(threadId.current, decision, editedSql, cb));
  };

  const onMicTranscript = (text: string, isFinal: boolean) => {
    setInput(text);
    if (isFinal) send(text);
  };

  return (
    <div className="mx-auto flex h-[calc(100vh-72px)] max-w-4xl flex-col px-4">
      <div ref={scrollRef} className="chat-scroll flex-1 space-y-3 overflow-y-auto py-6">
        {messages.length === 0 ? (
          <Welcome onPick={send} />
        ) : (
          messages.map((m) =>
            m.approval ? (
              <SqlApprovalCard
                key={m.id}
                data={{ sql: m.approval.sql, question: m.approval.question, allowed: m.approval.allowed }}
                resolved={m.approval.resolved}
                onDecision={(d, sql) => decide(m.id, d, sql)}
              />
            ) : (
              <MessageBubble key={m.id} message={m} />
            )
          )
        )}
      </div>

      <div className="border-t border-uhc-blue-soft bg-white py-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send(input);
          }}
          className="flex items-end gap-2"
        >
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send(input);
              }
            }}
            rows={1}
            placeholder="Ask about DRG shifts, the taxi data, appeals, the call center, CMS changes, or search the web…"
            className="max-h-40 min-h-[44px] flex-1 resize-none rounded-2xl border border-uhc-blue-soft bg-white px-4 py-2.5 text-[15px] outline-none focus:border-uhc-blue-bright focus:ring-2 focus:ring-uhc-blue-bright/30"
          />
          {ttsSupported() && (
            <button
              type="button"
              onClick={() => {
                stopSpeaking();
                setVoiceReplies((v) => !v);
              }}
              title={voiceReplies ? "Voice replies on — click to mute" : "Voice replies off — click to enable"}
              className={`grid h-11 w-11 place-items-center rounded-full transition-colors ${
                voiceReplies
                  ? "bg-uhc-blue-soft text-uhc-blue hover:bg-uhc-blue-bright hover:text-white"
                  : "bg-gray-100 text-gray-400"
              }`}
            >
              {voiceReplies ? <SpeakerOnIcon /> : <SpeakerOffIcon />}
            </button>
          )}
          <MicButton onTranscript={onMicTranscript} disabled={busy} />
          <button
            type="submit"
            disabled={busy || !input.trim()}
            className="grid h-11 w-11 place-items-center rounded-full bg-uhc-blue text-white transition-colors hover:bg-uhc-blue-bright disabled:opacity-40"
            title="Send"
          >
            <SendIcon />
          </button>
        </form>
        <p className="mt-2 text-center text-[11px] text-gray-400">
          GPT-5.5 · DRG figures are illustrative mock data · taxi data is live Databricks via Genie (SQL needs your approval).
        </p>
      </div>
    </div>
  );
}

function Welcome({ onPick }: { onPick: (q: string) => void }) {
  return (
    <div className="flex h-full flex-col items-center justify-center text-center">
      <h1 className="text-2xl font-bold text-uhc-blue">NextGen Agentic Intelligence</h1>
      <p className="mt-1 text-xs uppercase tracking-[0.18em] text-gray-400">
        UnitedHealthcare · powered by Optum
      </p>
      <p className="mt-3 max-w-md text-sm text-gray-500">
        Ask about DRG coding shifts, live data (taxi), appeals, call-center metrics, CMS
        changes, or search the web. Type or tap the mic to speak.
      </p>
      <div className="mt-6 grid w-full max-w-xl grid-cols-1 gap-2 sm:grid-cols-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => onPick(s)}
            className="rounded-xl border border-uhc-blue-soft bg-uhc-blue-soft/40 px-4 py-3 text-left text-sm text-uhc-blue transition-colors hover:border-uhc-blue-bright hover:bg-uhc-blue-soft"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}

function SpeakerOnIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
      <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
      <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
    </svg>
  );
}

function SpeakerOffIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
      <line x1="23" y1="9" x2="17" y2="15" />
      <line x1="17" y1="9" x2="23" y2="15" />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}
