"use client";
import { useState, useRef, useEffect } from "react";
import { Send, FileText, AlertTriangle, Mic, Volume2, Square, ThumbsUp, ThumbsDown } from "lucide-react";
import { api } from "@/lib/api";
import { useLanguage } from "@/lib/i18n";
import { waitForVoices, pickVoice, speechLangCode, speechRecognitionErrorMessage } from "@/lib/speech";
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
  const [feedbackGiven, setFeedbackGiven] = useState<Record<number, "up" | "down">>({});
  const [voiceError, setVoiceError] = useState("");

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
      setVoiceError("");
    };
    recognition.onend = () => setListening(false);
    recognition.onerror = (event: any) => {
      setListening(false);
      setVoiceError(speechRecognitionErrorMessage(event.error, lang));
    };
    recognitionRef.current = recognition;
  }, []);

  // Keep recognition language in sync with the selected UI language.
  // Fix: hinglish now correctly maps to hi-IN recognition instead of
  // silently falling through to English (the bug behind "Hindi doesn't work"
  // when the UI language was actually set to Hinglish).
  useEffect(() => {
    if (recognitionRef.current) {
      recognitionRef.current.lang = speechLangCode(lang);
    }
  }, [lang]);

  const toggleListening = () => {
    if (!recognitionRef.current) return;
    setVoiceError("");
    if (listening) {
      recognitionRef.current.stop();
      setListening(false);
    } else {
      setInput("");
      try {
        recognitionRef.current.start();
        setListening(true);
      } catch {
        // start() throws if a recognition session is already active;
        // surfacing this beats a silent no-op.
        setVoiceError(speechRecognitionErrorMessage("generic", lang));
      }
    }
  };

  // Fix: previously called speechSynthesis.speak() immediately, before the
  // browser had finished loading its voice list. On first use this silently
  // produced no audio (or fell back to a default English-sounding voice)
  // for Hindi far more often than for English, since English voices are
  // almost always ready immediately while Hindi voices load asynchronously.
  // Explicitly waiting for voices + picking a matching one fixes this.
  const speak = async (text: string, index: number) => {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel(); // stop any ongoing speech first
    if (speakingIndex === index) {
      setSpeakingIndex(null);
      return;
    }
    const langCode = speechLangCode(lang);
    const voices = await waitForVoices();
    const matchedVoice = pickVoice(voices, langCode);

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = langCode;
    if (matchedVoice) utterance.voice = matchedVoice;
    utterance.onend = () => setSpeakingIndex(null);
    utterance.onerror = () => {
      setSpeakingIndex(null);
      if (lang !== "en" && !matchedVoice) {
        setVoiceError(
          lang === "hi"
            ? "इस डिवाइस पर हिंदी आवाज़ उपलब्ध नहीं है। कृपया अपने डिवाइस/ब्राउज़र में हिंदी टेक्स्ट-टू-स्पीच वॉइस इंस्टॉल करें।"
            : "Is device par Hindi voice available nahi hai. Kripya apne device/browser mein Hindi text-to-speech voice install karo."
        );
      }
    };
    setSpeakingIndex(index);
    window.speechSynthesis.speak(utterance);
  };

  const rateAnswer = async (index: number, rating: "up" | "down") => {
    if (feedbackGiven[index]) return; // one rating per answer
    setFeedbackGiven((f) => ({ ...f, [index]: rating }));
    try {
      await api.submitFeedback({ rating: rating === "up" ? 5 : 1 });
    } catch {
      // feedback is best-effort; don't disrupt the chat experience on failure
    }
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
    <div className="flex flex-col h-[70vh] rounded-card border border-blush/40 bg-white/70 shadow-card overflow-hidden">
      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm ${
                m.role === "user"
                  ? "bg-maroon text-white rounded-br-sm"
                  : "bg-blush/30 rounded-bl-sm"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <p className="whitespace-pre-line">{m.text}</p>
                {m.role === "assistant" && ttsSupported && (
                  <button
                    aria-label={t("chat.speak")}
                    onClick={() => speak(m.text, i)}
                    className="shrink-0 mt-0.5 text-maroon-dark/40 hover:text-rose transition-colors"
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
                      <p className="text-xs font-semibold uppercase tracking-wide text-maroon-dark/50">
                        Sources
                      </p>
                      {m.sources.map((s, si) => (
                        <div key={si} className="flex items-start gap-1.5 text-xs text-maroon-dark/70">
                          <FileText size={12} className="mt-0.5 shrink-0" />
                          <span>
                            <strong>{s.title}</strong> — {s.snippet}...
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                  {m.disclaimer && (
                    <div className="flex items-start gap-1.5 text-xs text-rose">
                      <AlertTriangle size={12} className="mt-0.5 shrink-0" />
                      <span>{m.disclaimer}</span>
                    </div>
                  )}

                  <div className="flex items-center gap-2 pt-1">
                    <span className="text-xs text-maroon-dark/40">Was this helpful?</span>
                    <button
                      onClick={() => rateAnswer(i, "up")}
                      disabled={!!feedbackGiven[i]}
                      aria-label="Helpful"
                      className={`p-1 rounded-full transition-colors ${
                        feedbackGiven[i] === "up" ? "text-rose" : "text-maroon-dark/30 hover:text-rose disabled:hover:text-maroon-dark/30"
                      }`}
                    >
                      <ThumbsUp size={14} />
                    </button>
                    <button
                      onClick={() => rateAnswer(i, "down")}
                      disabled={!!feedbackGiven[i]}
                      aria-label="Not helpful"
                      className={`p-1 rounded-full transition-colors ${
                        feedbackGiven[i] === "down" ? "text-rose" : "text-maroon-dark/30 hover:text-rose disabled:hover:text-maroon-dark/30"
                      }`}
                    >
                      <ThumbsDown size={14} />
                    </button>
                    {feedbackGiven[i] && <span className="text-xs text-maroon-dark/40">Thanks for the feedback!</span>}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && <div className="text-xs text-maroon-dark/50">{t("chat.thinking")}</div>}
        {listening && <div className="text-xs text-rose font-medium">🎙 {t("chat.listening")}</div>}
        {voiceError && (
          <div className="flex items-start gap-1.5 text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">
            <AlertTriangle size={12} className="mt-0.5 shrink-0" />
            <span>{voiceError}</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-blush/40 p-3 flex gap-2">
        {voiceSupported && (
          <button
            onClick={toggleListening}
            aria-label={t("chat.mic")}
            className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 transition-colors ${
              listening ? "bg-red-500 text-white" : "border border-blush/60 hover:border-rose"
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
          className="flex-1 bg-transparent border border-blush/60 rounded-full px-4 py-2 text-sm outline-none focus-visible:border-rose"
        />
        <button
          onClick={send}
          disabled={loading}
          aria-label="Send message"
          className="w-10 h-10 rounded-full bg-rose text-white flex items-center justify-center hover:brightness-110 transition-colors disabled:opacity-50"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}
