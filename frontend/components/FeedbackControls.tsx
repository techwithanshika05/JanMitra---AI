"use client";
import { useEffect, useState } from "react";
import { ThumbsDown, ThumbsUp } from "lucide-react";
import { api } from "@/lib/api";
import type { ChatFeedback } from "@/lib/chatTypes";
import StarRating from "./StarRating";

export default function FeedbackControls({ messageId }: { messageId: string }) {
  const [reaction, setReaction] = useState<"like" | "dislike" | "neutral">("neutral");
  const [rating, setRating] = useState<number | null>(null);
  const [text, setText] = useState("");
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState("");

  useEffect(() => {
    api.getFeedback(messageId)
      .then((feedback: ChatFeedback) => {
        setReaction(feedback.reaction);
        setRating(feedback.rating ?? null);
        setText(feedback.feedback_text || "");
      })
      .catch(() => undefined);
  }, [messageId]);

  const save = async () => {
    setSaving(true);
    setStatus("");
    try {
      await api.saveFeedback(messageId, {
        reaction,
        rating,
        feedback_text: text || null,
      });
      setStatus("Feedback saved.");
      setOpen(false);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Could not save feedback.");
    } finally {
      setSaving(false);
    }
  };

  const react = (next: "like" | "dislike") => {
    setReaction((current) => current === next ? "neutral" : next);
    setOpen(true);
  };

  return (
    <div className="mt-3 border-t border-indigo-100/70 pt-2 dark:border-white/10">
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          aria-label="Helpful"
          aria-pressed={reaction === "like"}
          onClick={() => react("like")}
          className={`rounded-full p-1.5 ${reaction === "like" ? "bg-teal text-white" : "hover:bg-white/70 dark:hover:bg-white/10"}`}
        >
          <ThumbsUp size={14} />
        </button>
        <button
          type="button"
          aria-label="Not helpful"
          aria-pressed={reaction === "dislike"}
          onClick={() => react("dislike")}
          className={`rounded-full p-1.5 ${reaction === "dislike" ? "bg-marigold text-white" : "hover:bg-white/70 dark:hover:bg-white/10"}`}
        >
          <ThumbsDown size={14} />
        </button>
        <StarRating value={rating} onChange={(value) => { setRating(value); setOpen(true); }} />
        <button type="button" onClick={() => setOpen((value) => !value)} className="text-xs underline">
          {reaction !== "neutral" || rating ? "Edit feedback" : "Add feedback"}
        </button>
      </div>
      {open && (
        <div className="mt-2 space-y-2">
          <textarea
            value={text}
            onChange={(event) => setText(event.target.value.slice(0, 1000))}
            maxLength={1000}
            rows={2}
            placeholder="Optional feedback"
            className="w-full rounded-lg border border-indigo-100 bg-white/70 p-2 text-xs text-indigo-900 outline-none dark:border-white/10 dark:bg-white/10 dark:text-white"
          />
          <button
            type="button"
            disabled={saving}
            onClick={save}
            className="rounded-full bg-indigo px-3 py-1.5 text-xs text-white disabled:opacity-50"
          >
            {saving ? "Saving…" : "Submit"}
          </button>
        </div>
      )}
      {status && <p className="mt-1 text-xs" role="status">{status}</p>}
    </div>
  );
}
