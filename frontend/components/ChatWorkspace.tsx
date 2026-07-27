"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ChatSession } from "@/lib/chatTypes";
import ChatHistorySidebar from "./ChatHistorySidebar";
import ChatWidget from "./ChatWidget";

export default function ChatWorkspace() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const items = await api.listChatSessions();
      setSessions(items);
      setActiveId((current) =>
        current && items.some((item) => item.id === current)
          ? current
          : items[0]?.id || null
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load chat history.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const create = async () => {
    try {
      const session = await api.createChatSession({});
      setSessions((items) => [session, ...items]);
      setActiveId(session.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create conversation.");
    }
  };

  const rename = async (id: string, title: string) => {
    const updated = await api.renameChatSession(id, title);
    setSessions((items) => items.map((item) => item.id === id ? updated : item));
  };

  const remove = async (id: string) => {
    await api.deleteChatSession(id);
    setSessions((items) => {
      const remaining = items.filter((item) => item.id !== id);
      if (activeId === id) setActiveId(remaining[0]?.id || null);
      return remaining;
    });
  };

  return (
    <div className="relative flex h-[72vh] min-h-[34rem] overflow-hidden rounded-card border border-indigo-50 bg-white/70 shadow-card dark:border-white/10 dark:bg-white/5">
      <ChatHistorySidebar
        sessions={sessions}
        activeId={activeId}
        loading={loading}
        error={error}
        onSelect={setActiveId}
        onNew={create}
        onRename={rename}
        onDelete={remove}
      />
      <div className="min-w-0 flex-1">
        <ChatWidget
          sessionId={activeId}
          onSessionCreated={(session) => {
            setSessions((items) => [session, ...items]);
            setActiveId(session.id);
          }}
          onSessionChanged={load}
        />
      </div>
    </div>
  );
}
