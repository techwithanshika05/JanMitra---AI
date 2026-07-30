"use client";
import { useState, useRef, useEffect } from "react";
import { Send, FileText, AlertTriangle, Mic, Volume2, Square } from "lucide-react";
import { api } from "@/lib/api";
import { useLanguage } from "@/lib/i18n";
import ConfidenceMeter from "./ConfidenceMeter";

type Message = {
  role: "user" | "assistant";
  text: string;
  confidence?: number;
  sources?: { title: string; snippet: string; score: number }[];
  disclaimer?: string;
};

/**
 * Voice guidance uses the browser's native Web Speech API:
 * - SpeechRecognition for Speech-to-Text (mic button)
 * - speechSynthesis for Text-to-Speech (speaker button on AI replies)
 * No external service, no API cost, works once the page is loaded.
 * Support varies by browser (best in Chrome/Edge); we feature-detect and
 * simply hide the buttons if unsupported instead of erroring.
 */
export default function ChatWidget() {
  const { lang, t } = useLanguage();
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", text: t("chat.welcome") },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [speakingIndex, setSpeakingIndex] = useState<number | null>(null);
  const [voiceSupported, setVoiceSupported] = useState(false);
  const [ttsSupported, setTtsSupported] = useState(false);

  const sessionId = useRef(`session-${Math.random().toString(36).slice(2)}`);
  const bottomRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    setTtsSupported(typeof window !== "undefined" && "speechSynthesis" in window);
  }, []);

  // Reset the greeting message when language changes, so a fresh visitor
  // switching language before chatting sees it in the right language.
  useEffect(() => {
    setMessages((m) =>
      m.length === 1 && m[0].role === "assistant" && !m[0].confidence
        ? [{ role: "assistant", text: t("chat.welcome") }]
        : m
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lang]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Set up SpeechRecognition once, feature-detected.
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setVoiceSupported(false);
      return;
    }
    setVoiceSupported(true);
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setInput(transcript);
    };
    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);
    recognitionRef.current = recognition;
  }, []);

  // Keep recognition language in sync with the selected UI language.
  useEffect(() => {
    if (recognitionRef.current) {
      recognitionRef.current.lang = lang === "hi" ? "hi-IN" : "en-IN";
    }
  }, [lang]);

  const toggleListening = () => {
    if (!recognitionRef.current) return;
    if (listening) {
      recognitionRef.current.stop();
      setListening(false);
    } else {
      setInput("");
      recognitionRef.current.start();
      setListening(true);
    }
  };

  const speak = (text: string, index: number) => {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel(); // stop any ongoing speech first
    if (speakingIndex === index) {
      setSpeakingIndex(null);
      return;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang === "hi" ? "hi-IN" : "en-IN";
    utterance.onend = () => setSpeakingIndex(null);
    utterance.onerror = () => setSpeakingIndex(null);
    setSpeakingIndex(index);
    window.speechSynthesis.speak(utterance);
  };

  const send = async () => {
    if (!input.trim() || loading) return;
    const userMsg: Message = { role: "user", text: input };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const res = await api.chat({ session_id: sessionId.current, message: userMsg.text, language: lang });
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          text: res.answer,
          confidence: res.confidence,
          sources: res.sources,
          disclaimer: res.disclaimer,
        },
      ]);
    } catch {
      setMessages((m) => [
        ...m,
        { role: "assistant", text: "Sorry, I couldn't reach the JanMitra backend. Is the API server running?" },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[70vh] rounded-card border border-indigo-50 dark:border-white/10 bg-white/70 dark:bg-white/5 shadow-card overflow-hidden">
      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm ${
                m.role === "user"
                  ? "bg-indigo text-white rounded-br-sm"
                  : "bg-indigo-50 dark:bg-white/10 rounded-bl-sm"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <p className="whitespace-pre-line">{m.text}</p>
                {m.role === "assistant" && ttsSupported && (
                  <button
                    aria-label={t("chat.speak")}
                    onClick={() => speak(m.text, i)}
                    className="shrink-0 mt-0.5 text-indigo-900/40 dark:text-white/40 hover:text-marigold transition-colors"
                  >
                    {speakingIndex === i ? <Square size={14} /> : <Volume2 size={14} />}
                  </button>
                )}
              </div>

              {m.role === "assistant" && typeof m.confidence === "number" && (
                <div className="mt-3 space-y-3">
                  <ConfidenceMeter score={m.confidence} />

                  {m.sources && m.sources.length > 0 && (
                    <div className="space-y-1.5">
                      <p className="text-xs font-semibold uppercase tracking-wide text-indigo-900/50 dark:text-white/40">
                        Sources
                      </p>
                      {m.sources.map((s, si) => (
                        <div key={si} className="flex items-start gap-1.5 text-xs text-indigo-900/70 dark:text-white/60">
                          <FileText size={12} className="mt-0.5 shrink-0" />
                          <span>
                            <strong>{s.title}</strong> — {s.snippet}...
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                  {m.disclaimer && (
                    <div className="flex items-start gap-1.5 text-xs text-marigold-600">
                      <AlertTriangle size={12} className="mt-0.5 shrink-0" />
                      <span>{m.disclaimer}</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && <div className="text-xs text-indigo-900/50 dark:text-white/40">{t("chat.thinking")}</div>}
        {listening && <div className="text-xs text-marigold font-medium">🎙 {t("chat.listening")}</div>}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-indigo-50 dark:border-white/10 p-3 flex gap-2">
        {voiceSupported && (
          <button
            onClick={toggleListening}
            aria-label={t("chat.mic")}
            className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 transition-colors ${
              listening ? "bg-red-500 text-white" : "border border-indigo-100 dark:border-white/10 hover:border-marigold"
            }`}
          >
            <Mic size={16} />
          </button>
        )}
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder={t("chat.placeholder")}
          className="flex-1 bg-transparent border border-indigo-100 dark:border-white/10 rounded-full px-4 py-2 text-sm outline-none focus-visible:border-marigold"
        />
        <button
          onClick={send}
          disabled={loading}
          aria-label="Send message"
          className="w-10 h-10 rounded-full bg-marigold text-white flex items-center justify-center hover:bg-marigold-600 transition-colors disabled:opacity-50"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}
