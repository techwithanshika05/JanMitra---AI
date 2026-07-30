"use client";

import { useEffect, useRef, useState } from "react";
import { AudioLines, Languages, Mic, PhoneOff, ShieldCheck, Sparkles } from "lucide-react";
import { Room, RoomEvent, Track } from "livekit-client";
import { api, type VoiceLanguage } from "@/lib/api";
import { useLanguage } from "@/lib/i18n";

type VoiceState = "idle" | "connecting" | "listening" | "ending" | "error";
type LanguageChoice = {
  label: string;
  helper: string;
  value: VoiceLanguage;
  accent: string;
};

const LANGUAGE_CHOICES: LanguageChoice[] = [
  {
    label: "हिंदी",
    helper: "बोलना शुरू करें",
    value: "hi-IN",
    accent: "from-indigo-100 via-white/70 to-marigold-50",
  },
  {
    label: "Hinglish",
    helper: "Start speaking",
    value: "hi-IN",
    accent: "from-marigold-50 via-white/70 to-orange-100",
  },
  {
    label: "English",
    helper: "Start speaking",
    value: "en-IN",
    accent: "from-teal-50 via-white/70 to-indigo-50",
  },
];

export default function ConversationalAICard() {
  const { lang } = useLanguage();
  const [selected, setSelected] = useState(lang === "hi" ? 0 : 1);
  const [state, setState] = useState<VoiceState>("idle");
  const [error, setError] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const roomRef = useRef<Room | null>(null);
  const audioRef = useRef<HTMLDivElement | null>(null);
  const selectedChoice = LANGUAGE_CHOICES[selected];
  const active = state === "connecting" || state === "listening" || state === "ending";

  useEffect(() => {
    return () => {
      roomRef.current?.disconnect();
      roomRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (state !== "listening") return;
    const timer = window.setInterval(() => {
      setElapsedSeconds((seconds) => seconds + 1);
    }, 1000);
    return () => window.clearInterval(timer);
  }, [state]);

  const elapsedTime = `${String(Math.floor(elapsedSeconds / 60)).padStart(2, "0")}:${String(
    elapsedSeconds % 60,
  ).padStart(2, "0")}`;

  async function startSpeaking() {
    if (active) return;
    setState("connecting");
    setElapsedSeconds(0);
    setError("");
    let createdSessionId: string | null = null;

    try {
      const voiceSession = await api.startVoiceSession(selectedChoice.value);
      createdSessionId = voiceSession.session_id;
      const room = new Room({ adaptiveStream: true, dynacast: true });
      roomRef.current = room;
      setSessionId(voiceSession.session_id);

      room.on(RoomEvent.Disconnected, () => {
        audioRef.current?.replaceChildren();
        roomRef.current = null;
        setState("idle");
        setSessionId(null);
        setElapsedSeconds(0);
      });
      room.on(RoomEvent.TrackSubscribed, (track) => {
        if (track.kind === Track.Kind.Audio) {
          audioRef.current?.appendChild(track.attach());
        }
      });
      room.on(RoomEvent.TrackUnsubscribed, (track) => {
        track.detach().forEach((element) => element.remove());
      });

      await room.connect(voiceSession.livekit_url, voiceSession.token);
      await room.startAudio();
      await room.localParticipant.setMicrophoneEnabled(true);
      setState("listening");
    } catch (caught) {
      roomRef.current?.disconnect();
      roomRef.current = null;
      if (createdSessionId) {
        await api.endVoiceSession(createdSessionId, "connection_failed").catch(() => undefined);
      }
      setState("error");
      setError(
        caught instanceof Error
          ? caught.message
          : "Could not start the voice assistant. Please try again.",
      );
    }
  }

  async function endSpeaking() {
    if (!sessionId) {
      roomRef.current?.disconnect();
      setState("idle");
      return;
    }

    setState("ending");
    roomRef.current?.disconnect();
    roomRef.current = null;
    try {
      await api.endVoiceSession(sessionId);
    } catch {
      // The citizen is already disconnected even if the server end event fails.
    } finally {
      setSessionId(null);
      setState("idle");
      setElapsedSeconds(0);
    }
  }

  const statusText =
    state === "connecting"
      ? lang === "hi"
        ? "सुरक्षित कनेक्शन बन रहा है…"
        : "Creating a secure connection…"
      : state === "listening"
        ? lang === "hi"
          ? "सुन रहा है — अपना सवाल पूछें"
          : "Listening — ask your question"
        : state === "ending"
          ? lang === "hi"
            ? "बातचीत समाप्त हो रही है…"
            : "Ending conversation…"
          : lang === "hi"
            ? "राशन और सरकारी योजनाओं के बारे में पूछें"
            : "Ask about ration and government schemes";

  return (
    <section
      aria-labelledby="conversational-ai-title"
      className="mt-7 overflow-hidden rounded-[28px] border border-white/60 bg-gradient-primary text-white shadow-glowLg"
    >
      <div className="relative isolate px-5 py-6 md:px-8 md:py-7">
        <div className="pointer-events-none absolute -right-16 -top-24 -z-10 h-64 w-64 rounded-full bg-marigold-400/35 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-28 left-1/4 -z-10 h-56 w-56 rounded-full bg-indigo-100/20 blur-3xl" />

        <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
          <div className="max-w-xl">
            <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-white/70">
              <Sparkles size={15} aria-hidden="true" />
              JanMitra Voice
            </div>
            <h2 id="conversational-ai-title" className="font-display text-2xl font-semibold md:text-3xl">
              {lang === "hi" ? "संवाद सहायक" : "Conversational AI Assistant"}
            </h2>
            <p className="mt-2 text-sm leading-6 text-white/75">
              {lang === "hi"
                ? "अपनी भाषा में बोलें। JanMitra सत्यापित दस्तावेज़ों और मौजूदा योजना रिकॉर्ड से जवाब देता है।"
                : "Speak naturally in your language. JanMitra answers from verified documents and existing scheme records."}
            </p>
          </div>

          <div className="flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-2 text-xs text-white/80 backdrop-blur">
            <ShieldCheck size={16} className="text-marigold-400" aria-hidden="true" />
            {lang === "hi" ? "ऑडियो सेव नहीं होता" : "Raw audio is not stored"}
          </div>
        </div>

        <div className="mt-6 grid gap-3 md:grid-cols-3" role="radiogroup" aria-label="Conversation language">
          {LANGUAGE_CHOICES.map((choice, index) => {
            const isSelected = selected === index;
            return (
              <button
                key={choice.label}
                type="button"
                role="radio"
                aria-checked={isSelected}
                disabled={active}
                onClick={() => setSelected(index)}
                className={`group relative min-h-24 overflow-hidden rounded-card border p-4 text-left transition-all ${
                  isSelected
                    ? "border-white bg-white text-indigo-950 shadow-card"
                    : "border-white/20 bg-white/10 text-white hover:bg-white/15"
                } disabled:cursor-not-allowed disabled:opacity-70`}
              >
                <span
                  className={`absolute inset-0 -z-10 bg-gradient-to-br ${choice.accent} ${
                    isSelected ? "opacity-100" : "opacity-0"
                  } transition-opacity`}
                />
                <span className="flex items-center justify-between">
                  <span className="font-display text-lg font-semibold">{choice.label}</span>
                  <Languages size={18} className={isSelected ? "text-marigold" : "text-white/60"} aria-hidden="true" />
                </span>
                <span className={`mt-3 block text-xs ${isSelected ? "text-indigo-600" : "text-white/65"}`}>
                  {choice.helper}
                </span>
              </button>
            );
          })}
        </div>

        <div className="mt-5 flex flex-col gap-3 rounded-card border border-white/15 bg-indigo-950/25 p-4 backdrop-blur md:flex-row md:items-center md:justify-between">
          <div className="flex min-w-0 items-center gap-3">
            <span
              className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full ${
                state === "listening" ? "animate-pulse bg-marigold text-indigo-950" : "bg-white/10 text-white"
              }`}
            >
              <AudioLines size={20} aria-hidden="true" />
            </span>
            <div>
              <p className="text-sm font-semibold">{statusText}</p>
              <p className="mt-0.5 text-xs text-white/55">
                {lang === "hi" ? "माइक्रोफ़ोन की अनुमति शुरू करने पर मांगी जाएगी" : "Microphone permission is requested only when you start"}
              </p>
            </div>
          </div>

          {state === "listening" || state === "ending" ? (
            <button
              type="button"
              onClick={endSpeaking}
              disabled={state === "ending"}
              aria-label={lang === "hi" ? "बातचीत समाप्त करें" : "End conversation"}
              className="inline-flex min-h-14 min-w-36 items-center justify-center gap-3 rounded-full border border-white/70 bg-white/80 px-5 text-base font-semibold text-indigo-950 shadow-card backdrop-blur transition hover:bg-white disabled:opacity-70"
            >
              <span className="tabular-nums text-indigo-900" aria-label={`Call duration ${elapsedTime}`}>
                {elapsedTime}
              </span>
              <PhoneOff size={22} className="text-red-500" strokeWidth={2.2} aria-hidden="true" />
            </button>
          ) : (
            <button
              type="button"
              onClick={startSpeaking}
              disabled={state === "connecting"}
              className="inline-flex min-h-11 items-center justify-center gap-2 rounded-full bg-marigold px-6 text-sm font-semibold text-indigo-950 shadow-glow transition hover:bg-marigold-400 disabled:cursor-wait disabled:opacity-70"
            >
              <Mic size={17} aria-hidden="true" />
              {state === "connecting"
                ? lang === "hi"
                  ? "कनेक्ट हो रहा है…"
                  : "Connecting…"
                : lang === "hi"
                  ? "बोलना शुरू करें"
                  : "Start speaking"}
            </button>
          )}
        </div>

        {error && (
          <p role="alert" className="mt-3 rounded-xl border border-red-200/30 bg-red-950/25 px-4 py-3 text-sm text-red-50">
            {error}
          </p>
        )}
        <div ref={audioRef} className="hidden" aria-hidden="true" />
      </div>
    </section>
  );
}
