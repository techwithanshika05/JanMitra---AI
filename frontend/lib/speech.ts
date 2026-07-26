/**
 * Shared voice helpers for ChatWidget + VoiceAssistant.
 *
 * The core bug being fixed here: browsers (especially Chrome) load their
 * available speechSynthesis voices ASYNCHRONOUSLY. If you call
 * speechSynthesis.speak() before voices have finished loading -- which
 * happens very often on the FIRST attempt right after a page loads --
 * the browser can silently produce no audio at all, or fall back to a
 * default (English) voice even when a Hindi voice exists on the system.
 * This is the most common reason "Hindi voice doesn't work" while English
 * seems fine: English almost always has a voice ready immediately, Hindi
 * voice packs take longer to enumerate or may need to be selected explicitly.
 */

export function waitForVoices(): Promise<SpeechSynthesisVoice[]> {
  return new Promise((resolve) => {
    if (!("speechSynthesis" in window)) {
      resolve([]);
      return;
    }
    const synth = window.speechSynthesis;
    const existing = synth.getVoices();
    if (existing.length > 0) {
      resolve(existing);
      return;
    }
    const onVoicesChanged = () => {
      resolve(synth.getVoices());
      synth.removeEventListener("voiceschanged", onVoicesChanged);
    };
    synth.addEventListener("voiceschanged", onVoicesChanged);
    // Safety net: some browsers never fire voiceschanged reliably.
    setTimeout(() => {
      synth.removeEventListener("voiceschanged", onVoicesChanged);
      resolve(synth.getVoices());
    }, 1200);
  });
}

/** Picks the best matching voice for a given BCP-47 language code, e.g. "hi-IN". */
export function pickVoice(voices: SpeechSynthesisVoice[], langCode: string): SpeechSynthesisVoice | undefined {
  const exact = voices.find((v) => v.lang.toLowerCase() === langCode.toLowerCase());
  if (exact) return exact;
  const base = langCode.split("-")[0].toLowerCase();
  return voices.find((v) => v.lang.toLowerCase().startsWith(base));
}

/**
 * Maps our 3 UI languages to a speech (STT/TTS) locale. Hinglish has no
 * dedicated browser locale, so it uses Hindi recognition/voice -- this is
 * also intentional: browser Hindi STT already transcribes romanized/mixed
 * speech reasonably, and Hindi TTS is closer to Hinglish's spoken cadence
 * than English TTS would be.
 */
export function speechLangCode(lang: "en" | "hi" | "hinglish"): string {
  return lang === "en" ? "en-IN" : "hi-IN";
}

/** Human-readable STT error messages, in the current UI language. */
export function speechRecognitionErrorMessage(errorCode: string, lang: "en" | "hi" | "hinglish"): string {
  const messages: Record<string, Record<string, string>> = {
    "not-allowed": {
      en: "Microphone permission was denied. Please allow microphone access in your browser settings and try again.",
      hi: "माइक्रोफ़ोन की अनुमति नहीं मिली। कृपया ब्राउज़र सेटिंग्स में माइक्रोफ़ोन की अनुमति दें और दोबारा कोशिश करें।",
      hinglish: "Microphone ki permission nahi mili. Kripya browser settings mein microphone allow karo aur dobara try karo.",
    },
    "no-speech": {
      en: "No speech was detected. Please try speaking again.",
      hi: "कोई आवाज़ नहीं मिली। कृपया दोबारा बोलें।",
      hinglish: "Koi awaaz nahi mili. Kripya dobara bolo.",
    },
    "audio-capture": {
      en: "No microphone was found on this device.",
      hi: "इस डिवाइस पर कोई माइक्रोफ़ोन नहीं मिला।",
      hinglish: "Is device par koi microphone nahi mila.",
    },
    "language-not-supported": {
      en: "This browser doesn't support speech recognition in the selected language.",
      hi: "यह ब्राउज़र चुनी गई भाषा में आवाज़ पहचान समर्थित नहीं करता।",
      hinglish: "Ye browser selected language mein speech recognition support nahi karta.",
    },
  };
  const fallback = {
    en: "Voice recognition ran into an error. Please try again.",
    hi: "आवाज़ पहचानने में समस्या हुई। कृपया दोबारा कोशिश करें।",
    hinglish: "Voice recognition mein problem hui. Kripya dobara try karo.",
  };
  return (messages[errorCode] || fallback)[lang] || fallback.en;
}
