"use client";
import React, { useState, useRef, useEffect } from "react";
import type { ReactNode } from "react";
import {
  AlertTriangle,
  Check,
  ChevronDown,
  ChevronUp,
  Copy,
  FileText,
  Mic,
  Pencil,
  RotateCcw,
  Send,
  Square,
  Volume2,
} from "lucide-react";
import { api } from "@/lib/api";
import { useLanguage } from "@/lib/i18n";
import type { ChatMessage, ChatSession } from "@/lib/chatTypes";
import ConfidenceMeter from "./ConfidenceMeter";
import FAQResponseCard from "./FAQResponseCard";
import FeedbackControls from "./FeedbackControls";

type Message = {
  id?: string;
  role: "user" | "assistant";
  text: string;
  responseType?: string;
  structuredContent?: ChatMessage["structured_content"];
  confidence?: number;
  sources?: { title: string; snippet: string; score: number }[];
  disclaimer?: string;
};

function renderInlineMarkdown(text: string): ReactNode[] {
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts.filter(Boolean).map((part, index) =>
    part.startsWith("**") && part.endsWith("**") ? (
      <strong key={index} className="font-semibold">{part.slice(2, -2)}</strong>
    ) : part
  );
}

function AnswerText({ text }: { text: string }) {
  const blocks: ReactNode[] = [];
  let listItems: string[] = [];

  const flushList = () => {
    if (!listItems.length) return;
    const items = listItems;
    listItems = [];
    blocks.push(
      <ul key={`list-${blocks.length}`} className="list-disc space-y-1.5 pl-5">
        {items.map((item, index) => (
          <li key={index}>{renderInlineMarkdown(item)}</li>
        ))}
      </ul>
    );
  };

  text.split("\n").forEach((line) => {
    const trimmed = line.trim();
    const listMatch = trimmed.match(/^[-*]\s+(.+)$/);
    if (listMatch) {
      listItems.push(
        listMatch[1].replace(/\s*\(Source:\s*[^)]+\)\s*$/i, "")
      );
      return;
    }

    flushList();
    if (!trimmed) return;

    const headingMatch = trimmed.match(/^#{1,4}\s+(.+)$/) ||
      trimmed.match(/^\*\*(.+)\*\*$/);
    if (headingMatch) {
      blocks.push(
        <h3
          key={`heading-${blocks.length}`}
          className="pt-1 font-display text-base font-semibold leading-snug text-indigo-950 dark:text-white"
        >
          {headingMatch[1]}
        </h3>
      );
      return;
    }

    blocks.push(
      <p key={`paragraph-${blocks.length}`} className="leading-relaxed">
        {renderInlineMarkdown(trimmed)}
      </p>
    );
  });

  flushList();
  return <div className="space-y-3">{blocks}</div>;
}

/**
 * Voice guidance uses the browser's native Web Speech API:
 * - SpeechRecognition for Speech-to-Text (mic button)
 * - speechSynthesis for Text-to-Speech (speaker button on AI replies)
 * No external service, no API cost, works once the page is loaded.
 * Support varies by browser (best in Chrome/Edge); we feature-detect and
 * simply hide the buttons if unsupported instead of erroring.
 */
export default function ChatWidget({
  sessionId,
  onSessionCreated,
  onSessionChanged,
}: {
  sessionId?: string | null;
  onSessionCreated?: (session: ChatSession) => void;
  onSessionChanged?: () => void | Promise<void>;
} = {}) {
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
  const [historyLoading, setHistoryLoading] = useState(false);
  const [error, setError] = useState("");
  const [copiedMessage, setCopiedMessage] = useState<string | null>(null);
  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());

  const legacySessionId = useRef(`session-${Math.random().toString(36).slice(2)}`);
  const bottomRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const welcomeMessage = (): Message => ({
    role: "assistant",
    text: t("chat.welcome"),
  });

  useEffect(() => {
    if (sessionId === undefined) return;
    if (!sessionId) {
      setMessages([welcomeMessage()]);
      setError("");
      return;
    }

    let active = true;
    setHistoryLoading(true);
    setError("");
    api.getChatSession(sessionId)
      .then((session) => {
        if (!active) return;
        const stored = session.messages
          .filter((message) => message.role === "user" || message.role === "assistant")
          .map((message): Message => ({
            id: message.id,
            role: message.role as "user" | "assistant",
            text: message.content,
            responseType: message.response_type,
            structuredContent: message.structured_content,
            confidence: message.confidence ?? undefined,
            sources: message.sources,
            disclaimer: message.disclaimer ?? undefined,
          }));
        setMessages(stored.length ? stored : [welcomeMessage()]);
      })
      .catch((err) => {
        if (!active) return;
        setMessages([welcomeMessage()]);
        setError(err instanceof Error ? err.message : "Could not load this conversation.");
      })
      .finally(() => {
        if (active) setHistoryLoading(false);
      });
    return () => { active = false; };
    // The language-specific welcome is refreshed by the existing language effect.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

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

  const copyMessage = async (text: string, messageKey: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedMessage(messageKey);
      window.setTimeout(() => {
        setCopiedMessage((current) => current === messageKey ? null : current);
      }, 1600);
    } catch {
      setCopiedMessage(null);
    }
  };

  const editMessage = (text: string) => {
    setInput(text);
    window.requestAnimationFrame(() => {
      inputRef.current?.focus();
      inputRef.current?.setSelectionRange(text.length, text.length);
    });
  };

  const send = async (messageOverride?: string) => {
    const messageText = (messageOverride ?? input).trim();
    if (!messageText || loading) return;
    const userMsg: Message = { role: "user", text: messageText };
    setMessages((m) => [...m, userMsg]);
    if (messageOverride === undefined) setInput("");
    setLoading(true);
    setError("");
    try {
      if (sessionId !== undefined) {
        let targetSessionId = sessionId;
        if (!targetSessionId) {
          const session = await api.createChatSession({});
          targetSessionId = session.id;
          onSessionCreated?.(session);
        }
        const res = await api.sendChatMessage(targetSessionId, {
          message: userMsg.text,
          language: lang,
          client_message_id: crypto.randomUUID(),
        });
        const assistant = res.assistant_message;
        setMessages((m) => [
          ...m,
          {
            id: assistant.id,
            role: "assistant",
            text: assistant.content,
            responseType: assistant.response_type,
            structuredContent: assistant.structured_content,
            confidence: assistant.confidence ?? undefined,
            sources: assistant.sources,
            disclaimer: assistant.disclaimer ?? undefined,
          },
        ]);
        await onSessionChanged?.();
        return;
      }

      const res = await api.chat({
        session_id: legacySessionId.current,
        message: userMsg.text,
        language: lang,
      });
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
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Sorry, I couldn't reach the JanMitra backend. Is the API server running?"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`flex h-full min-h-0 flex-col overflow-hidden ${
      sessionId === undefined
        ? "h-[70vh] rounded-card border border-indigo-50 bg-white/70 shadow-card dark:border-white/10 dark:bg-white/5"
        : ""
    }`}>
      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {historyLoading && (
          <div className="text-xs text-indigo-900/50 dark:text-white/40">
            Loading conversation...
          </div>
        )}
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
                {m.role === "assistant" &&
                m.responseType === "faq" &&
                m.structuredContent ? (
                  <FAQResponseCard content={m.structuredContent} />
                ) : (
                  <AnswerText text={m.text} />
                )}
                {m.role === "assistant" && (
                  <div className="flex shrink-0 items-center gap-1">
                    <button
                      type="button"
                      aria-label={lang === "hi" ? "उत्तर कॉपी करें" : "Copy response"}
                      title={lang === "hi" ? "कॉपी करें" : "Copy"}
                      onClick={() => copyMessage(m.text, `assistant-${m.id || i}`)}
                      className="mt-0.5 rounded-md p-1 text-indigo-900/40 transition-colors hover:bg-white/70 hover:text-marigold dark:text-white/40 dark:hover:bg-white/10"
                    >
                      {copiedMessage === `assistant-${m.id || i}` ? <Check size={14} /> : <Copy size={14} />}
                    </button>
                    {ttsSupported && (
                      <button
                        type="button"
                        aria-label={t("chat.speak")}
                        title={t("chat.speak")}
                        onClick={() => speak(m.text, i)}
                        className="mt-0.5 rounded-md p-1 text-indigo-900/40 transition-colors hover:bg-white/70 hover:text-marigold dark:text-white/40 dark:hover:bg-white/10"
                      >
                        {speakingIndex === i ? <Square size={14} /> : <Volume2 size={14} />}
                      </button>
                    )}
                  </div>
                )}
              </div>

              {m.role === "user" && (
                <div className="mt-2 flex justify-end gap-1 border-t border-white/15 pt-1.5">
                  <button
                    type="button"
                    disabled={loading}
                    aria-label={lang === "hi" ? "संदेश फिर भेजें" : "Retry message"}
                    title={lang === "hi" ? "फिर भेजें" : "Retry"}
                    onClick={() => send(m.text)}
                    className="rounded-md p-1 text-white/65 transition-colors hover:bg-white/10 hover:text-white disabled:opacity-40"
                  >
                    <RotateCcw size={13} />
                  </button>
                  <button
                    type="button"
                    aria-label={lang === "hi" ? "संदेश संपादित करें" : "Edit message"}
                    title={lang === "hi" ? "संपादित करें" : "Edit"}
                    onClick={() => editMessage(m.text)}
                    className="rounded-md p-1 text-white/65 transition-colors hover:bg-white/10 hover:text-white"
                  >
                    <Pencil size={13} />
                  </button>
                  <button
                    type="button"
                    aria-label={lang === "hi" ? "संदेश कॉपी करें" : "Copy message"}
                    title={lang === "hi" ? "कॉपी करें" : "Copy"}
                    onClick={() => copyMessage(m.text, `user-${m.id || i}`)}
                    className="rounded-md p-1 text-white/65 transition-colors hover:bg-white/10 hover:text-white"
                  >
                    {copiedMessage === `user-${m.id || i}` ? <Check size={13} /> : <Copy size={13} />}
                  </button>
                </div>
              )}

              {m.role === "assistant" && typeof m.confidence === "number" && (
                <div className="mt-3 space-y-3">
                  <ConfidenceMeter score={m.confidence} />

                  {m.sources && m.sources.length > 0 && (
                    <div className="space-y-1.5">
                      <p className="text-xs font-semibold uppercase tracking-wide text-indigo-900/50 dark:text-white/40">
                        Sources
                      </p>
                      {m.sources
                        .slice(0, expandedSources.has(m.id || String(i)) ? undefined : 1)
                        .map((s, si) => (
                        <div key={si} className="flex items-start gap-1.5 text-xs text-indigo-900/70 dark:text-white/60">
                          <FileText size={12} className="mt-0.5 shrink-0" />
                          <span>
                            <strong>{s.title}</strong> — {s.snippet}...
                          </span>
                        </div>
                      ))}
                      {m.sources.length > 1 && (
                        <button
                          type="button"
                          onClick={() => {
                            const key = m.id || String(i);
                            setExpandedSources((current) => {
                              const next = new Set(current);
                              next.has(key) ? next.delete(key) : next.add(key);
                              return next;
                            });
                          }}
                          className="inline-flex items-center gap-1 text-xs font-medium text-indigo-700 hover:text-marigold dark:text-white/70"
                        >
                          {expandedSources.has(m.id || String(i)) ? (
                            <><ChevronUp size={13} /> {lang === "hi" ? "कम दिखाएं" : "Show less"}</>
                          ) : (
                            <><ChevronDown size={13} /> {lang === "hi" ? `${m.sources.length - 1} और दिखाएं` : `Show ${m.sources.length - 1} more`}</>
                          )}
                        </button>
                      )}
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
              {m.role === "assistant" && m.id && (
                <FeedbackControls messageId={m.id} />
              )}
            </div>
          </div>
        ))}
        {loading && <div className="text-xs text-indigo-900/50 dark:text-white/40">{t("chat.thinking")}</div>}
        {error && <div className="text-xs text-red-600" role="alert">{error}</div>}
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
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder={t("chat.placeholder")}
          className="flex-1 bg-transparent border border-indigo-100 dark:border-white/10 rounded-full px-4 py-2 text-sm outline-none focus-visible:border-marigold"
        />
        <button
          onClick={() => send()}
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
