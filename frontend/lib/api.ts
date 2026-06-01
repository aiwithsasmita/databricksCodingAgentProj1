// SSE client for the FastAPI backend.
// Streams assistant token deltas; also surfaces human-in-the-loop SQL approval
// interrupts and lets the UI resume the paused run with a decision.

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export interface SqlApproval {
  type: "sql_approval";
  tool: string;
  sql: string;
  question: string;
  allowed_decisions: string[];
}

export interface FlowTrace {
  mermaid: string;
  steps: unknown[];
}

export interface StreamCallbacks {
  onToken: (text: string) => void;
  onInterrupt?: (approval: SqlApproval) => void;
  onTrace?: (trace: FlowTrace) => void;
  onError: (message: string) => void;
  onDone: () => void;
}

async function streamSSE(
  path: string,
  body: unknown,
  cb: StreamCallbacks,
  signal?: AbortSignal
): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    });
  } catch {
    cb.onError(`Cannot reach the agent backend at ${API_URL}. Is it running?`);
    cb.onDone();
    return;
  }

  if (!res.ok || !res.body) {
    cb.onError(`Backend returned ${res.status} ${res.statusText}.`);
    cb.onDone();
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let doneCalled = false;
  const finish = () => {
    if (!doneCalled) {
      doneCalled = true;
      cb.onDone();
    }
  };

  const handleFrame = (frame: string) => {
    let event = "message";
    const dataLines: string[] = [];
    for (const line of frame.split("\n")) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
    }
    const data = dataLines.join("\n");
    if (event === "token") {
      try {
        cb.onToken(JSON.parse(data).text ?? "");
      } catch {
        /* ignore */
      }
    } else if (event === "interrupt") {
      try {
        cb.onInterrupt?.(JSON.parse(data) as SqlApproval);
      } catch {
        /* ignore */
      }
    } else if (event === "trace") {
      try {
        cb.onTrace?.(JSON.parse(data) as FlowTrace);
      } catch {
        /* ignore */
      }
    } else if (event === "error") {
      try {
        cb.onError(JSON.parse(data).error ?? "Unknown error");
      } catch {
        cb.onError("Unknown error");
      }
    } else if (event === "done") {
      finish();
    }
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    // Strip CR so frame-splitting on "\n\n" works regardless of newline style.
    buffer += decoder.decode(value, { stream: true }).replace(/\r/g, "");
    let idx;
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      if (frame.trim()) handleFrame(frame);
    }
  }
  finish();
}

/** Send a chat message and stream the reply (may end in an SQL approval). */
export function streamChat(
  message: string,
  threadId: string,
  cb: StreamCallbacks,
  signal?: AbortSignal
): Promise<void> {
  return streamSSE("/api/chat", { message, thread_id: threadId }, cb, signal);
}

/** Resume a paused human-in-the-loop run with a decision. */
export function resumeChat(
  threadId: string,
  decision: "approve" | "edit" | "reject",
  editedSql: string | null,
  cb: StreamCallbacks,
  signal?: AbortSignal
): Promise<void> {
  return streamSSE(
    "/api/resume",
    { thread_id: threadId, decision, edited_sql: editedSql },
    cb,
    signal
  );
}
