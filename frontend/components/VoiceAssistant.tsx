"use client";
import { useState, useRef, useEffect } from "react";
import { Mic, X, Loader2, Volume2 } from "lucide-react";
import { api } from "@/lib/api";
import { useLanguage } from "@/lib/i18n";

type Turn = { role: "user" | "assistant"; text: string };

export default function VoiceAssistant() {
  const { lang } = useLanguage();
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState<"idle" | "listening" | "thinking" | "speaking">("idle");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [supported, setSupported] = useState(true);

  const recognitionRef = useRef<any>(null);
  const sessionId = useRef(`voice-${Math.random().toString(36).slice(2)}`);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const hasTTS = "speechSynthesis" in window;
    setSupported(!!SpeechRecognition && hasTTS);
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [turns, status]);

  const handleUserSpeech = async (transcript: string) => {
    setTurns((t) => [...t, { role: "user", text: transcript }]);
    setStatus("thinking");
    try {
      const res = await api.chat({ session_id: sessionId.current, message: transcript, language: lang });
      setTurns((t) => [...t, { role: "assistant", text: res.answer }]);
      speakReply(res.answer);
    } catch {
      const fallback =
        lang === "hi"
          ? "माफ़ कीजिए, सर्वर से जुड़ नहीं पा रहा। कृपया बैकएंड चालू है या नहीं जांचें।"
          : "Sorry, I couldn't reach the server. Please check the backend is running.";
      setTurns((t) => [...t, { role: "assistant", text: fallback }]);
      speakReply(fallback);
    }
  };

  const speakReply = (text: string) => {
    if (!("speechSynthesis" in window)) {
      setStatus("idle");
      return;
    }
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = lang === "hi" ? "hi-IN" : "en-IN";
    utter.onstart = () => setStatus("speaking");
    utter.onend = () => setStatus("idle");
    utter.onerror = () => setStatus("idle");
    window.speechSynthesis.speak(utter);
  };

  const startListening = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    window.speechSynthesis.cancel();

    const recognition = new SpeechRecognition();
    recognition.lang = lang === "hi" ? "hi-IN" : "en-IN";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      handleUserSpeech(transcript);
    };
    recognition.onerror = () => setStatus("idle");
    recognition.onend = () => {
      setStatus((s) => (s === "listening" ? "idle" : s));
    };

    recognitionRef.current = recognition;
    setStatus("listening");
    recognition.start();
  };

  const stopListening = () => {
    recognitionRef.current?.stop();
    setStatus("idle");
  };

  const closeWidget = () => {
    recognitionRef.current?.stop();
    window.speechSynthesis.cancel();
    setStatus("idle");
    setOpen(false);
  };

  if (!supported) return null;

  return (
    <>
      {!open && (
        <button
          onClick={() => setOpen(true)}
          aria-label="Open voice assistant"
          className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-marigold text-white shadow-lg flex items-center justify-center hover:bg-marigold-600 transition-colors animate-[pulse_3s_ease-in-out_infinite]"
        >
          <Mic size={22} />
        </button>
      )}

      {open && (
        <div className="fixed bottom-6 right-6 z-50 w-[340px] max-w-[90vw] rounded-card shadow-card border border-indigo-50 dark:border-white/10 bg-white/95 dark:bg-indigo-900/95 backdrop-blur overflow-hidden flex flex-col">
          <div className="flex items-center justify-between px-4 py-3 border-b border-indigo-50 dark:border-white/10">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <span className="w-2 h-2 rounded-full bg-teal" />
              JanMitra Voice
            </div>
            <button onClick={closeWidget} aria-label="Close voice assistant">
              <X size={16} />
            </button>
          </div>

          <div ref={scrollRef} className="max-h-64 overflow-y-auto px-4 py-3 space-y-3">
            {turns.length === 0 && (
              <p className="text-xs text-indigo-900/50 dark:text-white/40">
                {lang === "hi"
                  ? "माइक दबाकर बोलिए — मैं सुनकर जवाब दूंगा।"
                  : "Tap the mic and speak — I'll listen and answer out loud."}
              </p>
            )}
            {turns.map((turn, i) => (
              <div
                key={i}
                className={`text-sm px-3 py-2 rounded-xl max-w-[85%] ${
                  turn.role === "user"
                    ? "bg-indigo text-white ml-auto rounded-br-sm"
                    : "bg-indigo-50 dark:bg-white/10 rounded-bl-sm"
                }`}
              >
                {turn.text}
              </div>
            ))}
          </div>

          <div className="p-4 flex flex-col items-center gap-2 border-t border-indigo-50 dark:border-white/10">
            <button
              onClick={status === "listening" ? stopListening : startListening}
              disabled={status === "thinking" || status === "speaking"}
              aria-label={status === "listening" ? "Stop listening" : "Start speaking"}
              className={`w-16 h-16 rounded-full flex items-center justify-center transition-colors disabled:opacity-50 ${
                status === "listening" ? "bg-red-500 text-white" : "bg-marigold text-white hover:bg-marigold-600"
              }`}
            >
              {status === "thinking" ? (
                <Loader2 size={24} className="animate-spin" />
              ) : status === "speaking" ? (
                <Volume2 size={24} />
              ) : (
                <Mic size={24} />
              )}
            </button>
            <p className="text-xs text-indigo-900/60 dark:text-white/50 h-4">
              {status === "listening" && (lang === "hi" ? "सुन रहा हूं…" : "Listening…")}
              {status === "thinking" && (lang === "hi" ? "सोच रहा हूं…" : "Thinking…")}
              {status === "speaking" && (lang === "hi" ? "बोल रहा हूं…" : "Speaking…")}
              {status === "idle" && turns.length === 0 && (lang === "hi" ? "बोलने के लिए टैप करें" : "Tap to speak")}
            </p>
          </div>
        </div>
      )}
    </>
  );
}