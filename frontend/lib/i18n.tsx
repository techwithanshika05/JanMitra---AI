"use client";
import { createContext, useContext, useState, ReactNode, useEffect } from "react";

export type Lang = "en" | "hi" | "hinglish";

/**
 * Central translation dictionary. Keep keys flat and short so any component
 * can call t("chat.placeholder") etc. Add new keys here as new pages adopt
 * translation -- this is the single source of truth for UI copy in all
 * languages, kept separate from the AI's own (dynamically generated)
 * answers, which are translated server-side by the LLM/prompt instead.
 */
const dict = {
  en: {
    "nav.dashboard": "Dashboard",
    "nav.schemes": "Scheme Finder",
    "nav.chat": "Ask JanMitra",
    "nav.checklist": "Checklist",
    "nav.myChecklists": "My Checklists",
    "nav.grievance": "Grievance",
    "nav.documents": "My Documents",
    "nav.faq": "FAQ",
    "nav.helpline": "Helpline",
    "nav.admin": "Admin",
    "hero.tag": "A citizen assistant, not a chatbot",
    "hero.title1": "Every Indian's path through",
    "hero.title2": "welfare & ration",
    "hero.title3": "services, made clear.",
    "hero.desc":
      "JanMitra AI explains schemes, ration processes, and grievance routes in your language — every answer grounded in official sources, with visible confidence, never a false promise of eligibility.",
    "hero.cta1": "Ask JanMitra",
    "hero.cta2": "Find schemes for me",
    "chat.title": "Ask JanMitra AI",
    "chat.subtitle": "Grounded in official scheme & PDS data. Every answer shows a confidence score and its sources.",
    "chat.placeholder": "Ask about a scheme, ration process, or document…",
    "chat.welcome":
      "Namaste! I'm JanMitra AI. Ask me about ration cards, welfare schemes, required documents, or how to file a grievance. Every answer I give is grounded in official scheme data and shows its sources.",
    "chat.thinking": "JanMitra is thinking…",
    "chat.listening": "Listening…",
    "chat.speak": "Listen to answer",
    "chat.mic": "Speak your question",
  },
  hi: {
    "nav.dashboard": "डैशबोर्ड",
    "nav.schemes": "योजना खोजें",
    "nav.chat": "JanMitra से पूछें",
    "nav.checklist": "चेकलिस्ट",
    "nav.myChecklists": "मेरी चेकलिस्ट",
    "nav.grievance": "शिकायत",
    "nav.documents": "मेरे दस्तावेज़",
    "nav.faq": "सामान्य प्रश्न",
    "nav.helpline": "हेल्पलाइन",
    "nav.admin": "एडमिन",
    "hero.tag": "एक नागरिक सहायक, सिर्फ चैटबॉट नहीं",
    "hero.title1": "हर भारतीय का",
    "hero.title2": "कल्याण व राशन",
    "hero.title3": "सेवाओं का रास्ता, अब स्पष्ट।",
    "hero.desc":
      "JanMitra AI आपकी भाषा में योजनाओं, राशन प्रक्रियाओं और शिकायत के तरीकों को समझाता है — हर जवाब आधिकारिक स्रोतों पर आधारित है, विश्वास स्तर के साथ, कभी भी पात्रता का झूठा वादा नहीं करता।",
    "hero.cta1": "JanMitra से पूछें",
    "hero.cta2": "मेरे लिए योजनाएं खोजें",
    "chat.title": "JanMitra AI से पूछें",
    "chat.subtitle": "आधिकारिक योजना व राशन डेटा पर आधारित। हर जवाब में विश्वास स्तर और स्रोत दिखते हैं।",
    "chat.placeholder": "किसी योजना, राशन प्रक्रिया या दस्तावेज़ के बारे में पूछें…",
    "chat.welcome":
      "नमस्ते! मैं JanMitra AI हूं। मुझसे राशन कार्ड, कल्याण योजनाओं, ज़रूरी दस्तावेज़ों या शिकायत दर्ज करने के बारे में पूछें। मेरा हर जवाब आधिकारिक डेटा पर आधारित होता है और स्रोत दिखाता है।",
    "chat.thinking": "JanMitra सोच रहा है…",
    "chat.listening": "सुन रहा हूं…",
    "chat.speak": "जवाब सुनें",
    "chat.mic": "बोलकर पूछें",
  },
  hinglish: {
    "nav.dashboard": "Dashboard",
    "nav.schemes": "Scheme Khojo",
    "nav.chat": "JanMitra se Pucho",
    "nav.checklist": "Checklist",
    "nav.myChecklists": "Meri Checklists",
    "nav.grievance": "Shikayat",
    "nav.documents": "Mere Documents",
    "nav.faq": "FAQ",
    "nav.helpline": "Helpline",
    "nav.admin": "Admin",
    "hero.tag": "Ek citizen assistant, chatbot nahi",
    "hero.title1": "Har Indian ka",
    "hero.title2": "welfare aur ration",
    "hero.title3": "services ka raasta, ab clear.",
    "hero.desc":
      "JanMitra AI aapki bhasha mein schemes, ration processes, aur shikayat ke tareeke samjhata hai — har jawab official sources par based hai, confidence ke saath, kabhi bhi eligibility ka jhoota vaada nahi karta.",
    "hero.cta1": "JanMitra se Pucho",
    "hero.cta2": "Mere liye schemes khojo",
    "chat.title": "JanMitra AI se Pucho",
    "chat.subtitle": "Official scheme aur PDS data par based. Har jawab confidence score aur sources dikhata hai.",
    "chat.placeholder": "Kisi scheme, ration process, ya document ke baare mein pucho…",
    "chat.welcome":
      "Namaste! Main JanMitra AI hoon. Mujhse ration card, welfare schemes, zaroori documents, ya shikayat darj karne ke baare mein pucho. Mera har jawab official scheme data par based hota hai aur sources dikhata hai.",
    "chat.thinking": "JanMitra soch raha hai…",
    "chat.listening": "Sun raha hoon…",
    "chat.speak": "Jawab suno",
    "chat.mic": "Bolkar pucho",
  },
} as const;

type DictKey = keyof typeof dict["en"];

type LanguageContextType = {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: DictKey) => string;
};

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");

  // Persist choice across page loads within the browser session (not
  // localStorage-in-artifacts restricted here since this is a real Next.js
  // app running in the user's own browser, not the Claude artifact sandbox).
  useEffect(() => {
    const saved = window.localStorage.getItem("janmitra_lang") as Lang | null;
    if (saved === "en" || saved === "hi" || saved === "hinglish") setLangState(saved);
  }, []);

  const setLang = (l: Lang) => {
    setLangState(l);
    window.localStorage.setItem("janmitra_lang", l);
  };

  const t = (key: DictKey) => dict[lang][key] || dict.en[key] || key;

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within LanguageProvider");
  return ctx;
}
