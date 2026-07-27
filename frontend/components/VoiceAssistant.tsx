"use client";
import { useState, useRef, useEffect } from "react";
import { Mic, X, Loader2, Volume2, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";
import { useLanguage } from "@/lib/i18n";
import { waitForVoices, pickVoice, speechLangCode, speechRecognitionErrorMessage } from "@/lib/speech";

type Turn = { role: "user" | "assistant"; text: string };

/**
 * Global floating Voice Assistant.
 *
 * Why a separate widget from the chat page's inline mic/speaker buttons:
 * this one is reachable from ANY page (dashboard, schemes, checklist,
 * grievance...) and runs a hands-free loop -- tap once, speak, get a
 * spoken answer back -- without navigating to /chat or touching the
 * keyboard.
 *
 * Voice fix: speechSynthesis voices load asynchronously in the browser.
 * Speaking immediately (the old behavior) silently failed for Hindi far
 * more often than English, since Hindi voice packs take longer to become
 * available. We now wait for voices and explicitly pick a matching one
 * (see lib/speech.ts), and surface a real error message instead of just
 * going back to idle when something fails.
 */
export default function VoiceAssistant() {
  const { lang, t } = useLanguage();
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState<"idle" | "listening" | "thinking" | "speaking">("idle");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [supported, setSupported] = useState(true);
  const [error, setError] = useState("");

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
          : lang === "hinglish"
          ? "Sorry, server se connect nahi ho pa raha. Kripya check karo ki backend chalu hai ya nahi."
          : "Sorry, I couldn't reach the server. Please check the backend is running.";
      setTurns((t) => [...t, { role: "assistant", text: fallback }]);
      speakReply(fallback);
    }
  };

  const speakReply = async (text: string) => {
    if (!("speechSynthesis" in window)) {
      setStatus("idle");
      return;
    }
    window.speechSynthesis.cancel();

    const langCode = speechLangCode(lang);
    const voices = await waitForVoices();
    const matchedVoice = pickVoice(voices, langCode);

    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = langCode;
    if (matchedVoice) utter.voice = matchedVoice;
    utter.onstart = () => setStatus("speaking");
    utter.onend = () => setStatus("idle");
    utter.onerror = () => {
      setStatus("idle");
      if (lang !== "en" && !matchedVoice) {
        setError(
          lang === "hi"
            ? "इस डिवाइस पर हिंदी आवाज़ उपलब्ध नहीं है। अपने डिवाइस/ब्राउज़र में हिंदी टेक्स्ट-टू-स्पीच वॉइस इंस्टॉल करें।"
            : "Is device par Hindi voice available nahi hai. Apne device/browser mein Hindi text-to-speech voice install karo."
        );
      }
    };
    window.speechSynthesis.speak(utter);
  };

  const startListening = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    setError("");
    window.speechSynthesis.cancel(); // don't listen over our own voice

    const recognition = new SpeechRecognition();
    recognition.lang = speechLangCode(lang);
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      handleUserSpeech(transcript);
    };
    recognition.onerror = (event: any) => {
      setStatus("idle");
      setError(speechRecognitionErrorMessage(event.error, lang));
    };
    recognition.onend = () => {
      setStatus((s) => (s === "listening" ? "idle" : s));
    };

    recognitionRef.current = recognition;
    setStatus("listening");
    try {
      recognition.start();
    } catch {
      setStatus("idle");
      setError(speechRecognitionErrorMessage("generic", lang));
    }
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

  if (!supported) return null; // graceful no-op on unsupported browsers (e.g. Firefox STT)

  return (
    <>
      {/* Floating trigger button */}
      {!open && (
        <button
          onClick={() => setOpen(true)}
          aria-label="Open voice assistant"
          className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-rose text-white shadow-lg flex items-center justify-center hover:brightness-110 transition-colors animate-[pulse_3s_ease-in-out_infinite]"
        >
          <Mic size={22} />
        </button>
      )}

      {/* Expanded voice panel */}
      {open && (
        <div className="fixed bottom-6 right-6 z-50 w-[340px] max-w-[90vw] rounded-card shadow-card border border-blush/40 bg-white/95 backdrop-blur overflow-hidden flex flex-col">
          <div className="flex items-center justify-between px-4 py-3 border-b border-blush/40">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <span className="w-2 h-2 rounded-full bg-maroon" />
              JanMitra Voice
            </div>
            <button onClick={closeWidget} aria-label="Close voice assistant">
              <X size={16} />
            </button>
          </div>

          <div ref={scrollRef} className="max-h-64 overflow-y-auto px-4 py-3 space-y-3">
            {turns.length === 0 && (
              <p className="text-xs text-maroon-dark/50">
                {lang === "hi"
                  ? "माइक दबाकर बोलिए — मैं सुनकर जवाब दूंगा।"
                  : lang === "hinglish"
                  ? "Mic dabakar boliye — main sunkar jawab dunga."
                  : "Tap the mic and speak — I'll listen and answer out loud."}
              </p>
            )}
            {turns.map((turn, i) => (
              <div
                key={i}
                className={`text-sm px-3 py-2 rounded-xl max-w-[85%] ${
                  turn.role === "user"
                    ? "bg-maroon text-white ml-auto rounded-br-sm"
                    : "bg-blush/30 rounded-bl-sm"
                }`}
              >
                {turn.text}
              </div>
            ))}
            {error && (
              <div className="flex items-start gap-1.5 text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">
                <AlertTriangle size={12} className="mt-0.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}
          </div>

          <div className="p-4 flex flex-col items-center gap-2 border-t border-blush/40">
            <button
              onClick={status === "listening" ? stopListening : startListening}
              disabled={status === "thinking" || status === "speaking"}
              aria-label={status === "listening" ? "Stop listening" : "Start speaking"}
              className={`w-16 h-16 rounded-full flex items-center justify-center transition-colors disabled:opacity-50 ${
                status === "listening" ? "bg-red-500 text-white" : "bg-rose text-white hover:brightness-110"
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
            <p className="text-xs text-maroon-dark/60 h-4">
              {status === "listening" && (lang === "hi" ? "सुन रहा हूं…" : lang === "hinglish" ? "Sun raha hoon…" : "Listening…")}
              {status === "thinking" && (lang === "hi" ? "सोच रहा हूं…" : lang === "hinglish" ? "Soch raha hoon…" : "Thinking…")}
              {status === "speaking" && (lang === "hi" ? "बोल रहा हूं…" : lang === "hinglish" ? "Bol raha hoon…" : "Speaking…")}
              {status === "idle" && turns.length === 0 && (lang === "hi" ? "बोलने के लिए टैप करें" : lang === "hinglish" ? "Bolne ke liye tap karo" : "Tap to speak")}
            </p>
          </div>
        </div>
      )}
    </>
  );
}
