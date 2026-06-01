// Text-to-speech via the browser Web Speech API (speechSynthesis).
// Free, on-device, no extra model — keeps GPT-5.5 the only LLM in the system.

export function ttsSupported(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}

// Strip markdown so the voice doesn't read "asterisk asterisk" etc.
function clean(text: string): string {
  return text
    .replace(/```[\s\S]*?```/g, " code block ") // fenced code
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/\*([^*]+)\*/g, "$1")
    .replace(/__([^_]+)__/g, "$1")
    .replace(/[#>*_`|]/g, " ")
    .replace(/\[(.*?)\]\(.*?\)/g, "$1") // links -> label
    .replace(/\s+/g, " ")
    .trim();
}

let pickedVoice: SpeechSynthesisVoice | null = null;

function chooseVoice(): SpeechSynthesisVoice | null {
  if (!ttsSupported()) return null;
  if (pickedVoice) return pickedVoice;
  const voices = window.speechSynthesis.getVoices();
  if (!voices.length) return null;
  // Prefer a natural-sounding English voice when available.
  pickedVoice =
    voices.find((v) => /en-US/i.test(v.lang) && /natural|google|aria|jenny|zira/i.test(v.name)) ||
    voices.find((v) => /en-US/i.test(v.lang)) ||
    voices.find((v) => /^en/i.test(v.lang)) ||
    voices[0];
  return pickedVoice;
}

/** Speak the given text aloud (cancels anything currently speaking). */
export function speak(text: string, onEnd?: () => void): void {
  if (!ttsSupported()) return;
  const synth = window.speechSynthesis;
  synth.cancel();
  const body = clean(text);
  if (!body) {
    onEnd?.();
    return;
  }
  const utter = new SpeechSynthesisUtterance(body);
  const voice = chooseVoice();
  if (voice) utter.voice = voice;
  utter.rate = 1.0;
  utter.pitch = 1.0;
  utter.onend = () => onEnd?.();
  utter.onerror = () => onEnd?.();
  synth.speak(utter);
}

/** Stop any in-progress speech. */
export function stopSpeaking(): void {
  if (ttsSupported()) window.speechSynthesis.cancel();
}

export function isSpeaking(): boolean {
  return ttsSupported() && window.speechSynthesis.speaking;
}
