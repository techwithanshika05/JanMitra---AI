"use client";
import { useState, useRef } from "react";
import { Upload, FileText, Send, Loader2, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";
import { useLanguage } from "@/lib/i18n";
import ConfidenceMeter from "@/components/ConfidenceMeter";

type Answer = {
  question: string;
  answer: string;
  confidence: number;
  sources: { title: string; snippet: string; score: number }[];
};

export default function DocumentsPage() {
  const { lang } = useLanguage();
  const [docId, setDocId] = useState<string | null>(null);
  const [fileName, setFileName] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadWarning, setUploadWarning] = useState("");
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [answers, setAnswers] = useState<Answer[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (file: File) => {
    setUploading(true);
    setUploadWarning("");
    setAnswers([]);
    try {
      const res = await api.uploadDocument(file);
      setDocId(res.doc_id);
      setFileName(res.filename);
      if (res.warning) setUploadWarning(res.warning);
    } catch {
      setUploadWarning(lang === "hi" ? "अपलोड विफल रहा। कृपया दोबारा कोशिश करें।" : "Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  const askQuestion = async () => {
    if (!docId || !question.trim() || asking) return;
    setAsking(true);
    const q = question;
    setQuestion("");
    try {
      const res = await api.askDocument({ doc_id: docId, question: q, language: lang });
      setAnswers((a) => [...a, { question: q, answer: res.answer, confidence: res.confidence, sources: res.sources }]);
    } catch {
      setAnswers((a) => [...a, {
        question: q,
        answer: lang === "hi" ? "क्षमा करें, कुछ गलत हो गया।" : "Sorry, something went wrong.",
        confidence: 0, sources: [],
      }]);
    } finally {
      setAsking(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-5 md:px-8 py-14">
      <h1 className="font-display text-3xl font-semibold">
        {lang === "hi" ? "दस्तावेज़ अपलोड करें व सवाल पूछें" : "Upload a Document & Ask Questions"}
      </h1>
      <p className="text-maroon-dark/60 mt-2 max-w-2xl">
        {lang === "hi"
          ? "अपना कोई भी दस्तावेज़ (जैसे सूचना पत्र, आवेदन की प्रति) अपलोड करें और उसके बारे में सीधे सवाल पूछें। उत्तर केवल आपके दस्तावेज़ पर आधारित होंगे — किसी और के डेटा से मिश्रित नहीं।"
          : "Upload any document of yours (e.g. a notice, an application copy) and ask questions about it directly. Answers are grounded only in your uploaded document — never mixed with anyone else's data."}
      </p>

      {!docId && (
        <div
          className="mt-8 rounded-card border-2 border-dashed border-blush/60 p-10 text-center cursor-pointer hover:border-rose transition-colors"
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])}
          />
          {uploading ? (
            <Loader2 size={28} className="mx-auto animate-spin text-rose" />
          ) : (
            <Upload size={28} className="mx-auto text-rose" />
          )}
          <p className="mt-3 text-sm text-maroon-dark/60">
            {uploading
              ? lang === "hi" ? "अपलोड हो रहा है…" : "Uploading…"
              : lang === "hi" ? "क्लिक करके .txt फाइल चुनें" : "Click to select a .txt file"}
          </p>
          <p className="text-xs text-maroon-dark/40 mt-1">
            {lang === "hi" ? "अभी केवल .txt समर्थित है" : "Currently .txt files are supported best"}
          </p>
        </div>
      )}

      {uploadWarning && (
        <div className="mt-4 flex items-start gap-2 text-sm text-rose bg-gold/30 rounded-lg p-3">
          <AlertTriangle size={16} className="mt-0.5 shrink-0" />
          <span>{uploadWarning}</span>
        </div>
      )}

      {docId && (
        <>
          <div className="mt-8 flex items-center gap-2 text-sm rounded-full bg-blush/30 px-4 py-2 w-fit">
            <FileText size={14} className="text-rose" />
            <span className="font-medium">{fileName}</span>
            <button
              onClick={() => { setDocId(null); setFileName(""); setAnswers([]); }}
              className="text-xs text-maroon-dark/50 hover:text-rose ml-2"
            >
              {lang === "hi" ? "बदलें" : "change"}
            </button>
          </div>

          <div className="mt-6 space-y-4">
            {answers.map((a, i) => (
              <div key={i} className="space-y-2">
                <div className="ml-auto max-w-[85%] bg-maroon text-white rounded-2xl rounded-br-sm px-4 py-2 text-sm w-fit">
                  {a.question}
                </div>
                <div className="max-w-[85%] bg-blush/30 rounded-2xl rounded-bl-sm px-4 py-3 text-sm space-y-2">
                  <p>{a.answer}</p>
                  <ConfidenceMeter score={a.confidence} />
                  {a.sources.length > 0 && (
                    <p className="text-xs text-maroon-dark/50">
                      {lang === "hi" ? "स्रोत: आपका अपलोड किया गया दस्तावेज़" : "Source: your uploaded document"}
                    </p>
                  )}
                </div>
              </div>
            ))}
            {asking && <p className="text-xs text-maroon-dark/50">{lang === "hi" ? "सोच रहा हूं…" : "Thinking…"}</p>}
          </div>

          <div className="mt-6 flex gap-2">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && askQuestion()}
              placeholder={lang === "hi" ? "इस दस्तावेज़ के बारे में पूछें…" : "Ask about this document…"}
              className="flex-1 border border-blush/60 rounded-full px-4 py-2 text-sm bg-transparent outline-none focus-visible:border-rose"
            />
            <button
              onClick={askQuestion}
              disabled={asking}
              className="w-10 h-10 rounded-full bg-rose text-white flex items-center justify-center hover:brightness-110 transition-colors disabled:opacity-50"
            >
              <Send size={16} />
            </button>
          </div>
        </>
      )}
    </div>
  );
}
