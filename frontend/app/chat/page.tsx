"use client";
import ChatWidget from "@/components/ChatWidget";
import { useLanguage } from "@/lib/i18n";

export default function ChatPage() {
  const { t } = useLanguage();
  return (
    <div className="max-w-3xl mx-auto px-5 md:px-8 py-14">
      <h1 className="font-display text-3xl font-semibold">{t("chat.title")}</h1>
      <p className="text-maroon-dark/60 mt-2 mb-8">{t("chat.subtitle")}</p>
      <ChatWidget />
    </div>
  );
}
