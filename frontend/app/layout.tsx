import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";
import { LanguageProvider } from "@/lib/i18n";
import VoiceAssistant from "@/components/VoiceAssistant";

export const metadata: Metadata = {
  title: "JanMitra AI — Intelligent Welfare & Ration Assistant",
  description:
    "AI-powered citizen assistant for discovering welfare schemes, understanding PDS/ration services, and navigating government processes — with cited, explainable answers.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <LanguageProvider>
          <Navbar />
          <main className="min-h-screen">{children}</main>
          <VoiceAssistant />
        </LanguageProvider>
      </body>
    </html>
  );
}
