"use client";
import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Menu, MessageSquarePlus, Pencil, Trash2, X } from "lucide-react";
import type { ChatSession } from "@/lib/chatTypes";

export default function ChatHistorySidebar({
  sessions,
  activeId,
  loading,
  error,
  onSelect,
  onNew,
  onRename,
  onDelete,
}: {
  sessions: ChatSession[];
  activeId: string | null;
  loading: boolean;
  error: string;
  onSelect: (id: string) => void;
  onNew: () => void;
  onRename: (id: string, title: string) => void;
  onDelete: (id: string) => void;
}) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    setOpen(window.localStorage.getItem("janmitra_history_open") === "true");
  }, []);

  const setHistoryOpen = (next: boolean) => {
    setOpen(next);
    window.localStorage.setItem("janmitra_history_open", String(next));
  };

  const content = (
    <aside className="flex h-full w-72 flex-col border-r border-indigo-50 bg-white/60 p-3 dark:border-white/10 dark:bg-white/5">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-semibold">Conversations</h2>
        <button aria-label="Close history" onClick={() => setHistoryOpen(false)}>
          <X size={18} />
        </button>
      </div>
      <button
        type="button"
        onClick={() => { onNew(); setHistoryOpen(false); }}
        className="mb-3 flex items-center justify-center gap-2 rounded-lg bg-indigo px-3 py-2 text-sm text-white"
      >
        <MessageSquarePlus size={16} /> New conversation
      </button>
      {loading && <p className="p-2 text-xs opacity-60">Loading history…</p>}
      {error && <p className="p-2 text-xs text-red-600" role="alert">{error}</p>}
      {!loading && !error && sessions.length === 0 && (
        <p className="p-2 text-xs opacity-60">No saved conversations yet.</p>
      )}
      <div className="flex-1 space-y-1 overflow-y-auto">
        {sessions.map((session) => (
          <div
            key={session.id}
            className={`group flex items-center rounded-lg ${activeId === session.id ? "bg-marigold-50 dark:bg-white/10" : "hover:bg-indigo-50 dark:hover:bg-white/5"}`}
          >
            <button
              type="button"
              onClick={() => { onSelect(session.id); setHistoryOpen(false); }}
              className="min-w-0 flex-1 truncate px-3 py-2 text-left text-sm"
            >
              {session.title || "New conversation"}
            </button>
            <button
              type="button"
              aria-label="Rename conversation"
              onClick={() => {
                const title = window.prompt("Conversation title", session.title || "");
                if (title?.trim()) onRename(session.id, title.trim());
              }}
              className="p-1 opacity-60 hover:opacity-100"
            >
              <Pencil size={13} />
            </button>
            <button
              type="button"
              aria-label="Delete conversation"
              onClick={() => {
                if (window.confirm("Delete this conversation?")) onDelete(session.id);
              }}
              className="mr-1 p-1 opacity-60 hover:text-red-600 hover:opacity-100"
            >
              <Trash2 size={13} />
            </button>
          </div>
        ))}
      </div>
    </aside>
  );

  return (
    <>
      {!open && (
        <motion.div
          initial={{ opacity: 0, scale: 0.85 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex h-full w-12 shrink-0 justify-center border-r border-indigo-50 bg-white/50 pt-3 dark:border-white/10 dark:bg-white/[0.03]"
        >
          <button
            type="button"
            className="flex h-9 w-9 items-center justify-center rounded-lg text-indigo-700 transition-colors hover:bg-indigo-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo dark:text-white/80 dark:hover:bg-white/10"
            aria-label="Open conversations"
            title="Open conversations"
            onClick={() => setHistoryOpen(true)}
          >
            <Menu size={18} />
          </button>
        </motion.div>
      )}

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            className="hidden h-full shrink-0 overflow-hidden md:block"
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 288, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.24, ease: "easeOut" }}
          >
            {content}
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {open && (
          <motion.div
            className="fixed inset-0 z-50 bg-black/30 md:hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setHistoryOpen(false)}
          >
            <motion.div
              className="h-full"
              initial={{ x: -288 }}
              animate={{ x: 0 }}
              exit={{ x: -288 }}
              transition={{ duration: 0.24, ease: "easeOut" }}
              onClick={(event) => event.stopPropagation()}
            >
              {content}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
