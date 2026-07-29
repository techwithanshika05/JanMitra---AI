"use client";
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Archive, Loader2, RefreshCw, RotateCcw, Trash2 } from "lucide-react";
import { checklistsApi } from "@/lib/checklists/api";
import type { ChecklistGuidance, SavedChecklist } from "@/lib/checklists/types";
import { useLanguage } from "@/lib/i18n";
import { checklistCopy } from "@/lib/checklists/copy";
import ChecklistProgress from "@/components/checklists/ChecklistProgress";
import ChecklistItemRow from "@/components/checklists/ChecklistItemRow";

export default function ChecklistDetailPage({
  params,
}: {
  params: { checklistId: string };
}) {
  const router = useRouter();
  const { lang } = useLanguage();
  const text = checklistCopy(lang);
  const [checklist, setChecklist] = useState<SavedChecklist | null>(null);
  const [guidance, setGuidance] = useState<ChecklistGuidance | null>(null);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await checklistsApi.get(params.checklistId);
      setChecklist(result.checklist);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not load checklist.");
    } finally {
      setLoading(false);
    }
  }, [params.checklistId]);

  useEffect(() => { load(); }, [load]);

  const updateItem = async (
    itemId: string,
    payload: { is_completed?: boolean; user_note?: string | null },
  ) => {
    const result = await checklistsApi.updateItem(params.checklistId, itemId, payload);
    setChecklist(result.checklist);
  };

  const action = async (kind: "archive" | "restore" | "refresh" | "delete") => {
    if (kind === "delete" && !window.confirm("Delete this saved checklist?")) return;
    setWorking(true);
    setError("");
    try {
      if (kind === "delete") {
        await checklistsApi.delete(params.checklistId);
        router.push("/my-checklists");
        return;
      }
      const result = kind === "archive"
        ? await checklistsApi.archive(params.checklistId)
        : kind === "restore"
          ? await checklistsApi.restore(params.checklistId)
          : await checklistsApi.refresh(params.checklistId);
      setChecklist(result.checklist);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Action failed.");
    } finally {
      setWorking(false);
    }
  };

  if (loading) {
    return <p className="mx-auto max-w-5xl px-5 py-16"><Loader2 className="inline animate-spin" /> {text.loading}</p>;
  }
  if (!checklist) {
    return <p className="mx-auto max-w-5xl px-5 py-16 text-red-600" role="alert">{error || "Checklist not found."}</p>;
  }

  const activeItems = checklist.items
    .slice()
    .sort((a, b) => a.sequence_number - b.sequence_number);
  const changed = activeItems.some((item) => item.source_state !== "current");
  const nextIncomplete = activeItems.find(
    (item) =>
      item.is_required
      && !item.is_completed
      && item.source_state !== "removed"
      && item.source_state !== "outdated",
  );

  return (
    <main className="mx-auto max-w-5xl px-5 py-14 md:px-8">
      <div className="flex flex-wrap items-start justify-between gap-5">
        <div className="min-w-0 flex-1">
          <h1 className="font-display text-3xl font-semibold">{checklist.service_name}</h1>
          <p className="mt-2 text-sm text-maroon-dark/55">
            {Math.round(checklist.progress_percentage)}% {text.completed}
          </p>
          <div className="mt-4 max-w-2xl"><ChecklistProgress value={checklist.progress_percentage} /></div>
        </div>
        <div className="flex flex-wrap gap-2">
          {nextIncomplete && (
            <button
              onClick={() =>
                document
                  .getElementById(`checklist-item-${nextIncomplete.id}`)
                  ?.scrollIntoView({ behavior: "smooth", block: "center" })
              }
              className="btn-primary px-4 py-2 text-sm"
            >
              {text.open}
            </button>
          )}
          <button disabled={working} onClick={() => action("refresh")} className="btn-secondary px-4 py-2 text-sm">
            <RefreshCw size={14} className="mr-1 inline" /> {text.refresh}
          </button>
          <button
            disabled={working}
            onClick={() => action(checklist.is_archived ? "restore" : "archive")}
            className="btn-secondary px-4 py-2 text-sm"
          >
            {checklist.is_archived ? <RotateCcw size={14} className="mr-1 inline" /> : <Archive size={14} className="mr-1 inline" />}
            {checklist.is_archived ? text.restore : text.archive}
          </button>
          <button disabled={working} onClick={() => action("delete")} className="rounded-full px-4 py-2 text-sm text-red-600 hover:bg-red-50">
            <Trash2 size={14} className="mr-1 inline" /> {text.delete}
          </button>
        </div>
      </div>

      {(checklist.status === "outdated" || changed) && (
        <div className="mt-6 rounded-card border border-gold bg-gold/20 p-4 text-sm">
          Official source information changed. New, changed and removed items are marked below; completed matching items were preserved.
        </div>
      )}
      {checklist.sync_status !== "synced" && (
        <div className="mt-3 rounded-lg bg-white/70 p-3 text-xs text-maroon-dark/60">
          Storage: {checklist.storage_origin} · Sync: {checklist.sync_status}
        </div>
      )}
      {error && <p className="mt-5 rounded-card bg-red-50 p-4 text-sm text-red-700" role="alert">{error}</p>}

      <section className="mt-8 space-y-4">
        {activeItems.map((item) => (
          <ChecklistItemRow
            key={item.id}
            item={item}
            disabled={checklist.is_archived}
            labels={text}
            onUpdate={(payload) => updateItem(item.id, payload)}
          />
        ))}
      </section>

      <section className="mt-8 rounded-card border border-blush/50 bg-white/70 p-5">
        <button
          className="font-semibold text-rose"
          onClick={async () => setGuidance(await checklistsApi.guidance(checklist.id, false))}
        >
          {text.guidance}
        </button>
        {guidance && (
          <div className="mt-4 text-sm">
            <p>{guidance.progress_summary}</p>
            <ol className="mt-3 list-decimal space-y-1 pl-5">
              {guidance.next_steps.map((step) => <li key={step}>{step}</li>)}
            </ol>
            {guidance.alternative_actions.map((item) => (
              <p key={item} className="mt-2 text-xs text-maroon-dark/55">{item}</p>
            ))}
          </div>
        )}
      </section>

      <details className="mt-6 rounded-card border border-blush/40 bg-white/60 p-5">
        <summary className="cursor-pointer font-semibold">{text.sources}</summary>
        <ul className="mt-3 space-y-3 text-sm">
          {checklist.source_citations.map((source) => (
            <li key={`${source.title}-${source.score}`}>
              <strong>{source.title}</strong> ({Math.round(source.score * 100)}%)
              <p className="text-xs text-maroon-dark/55">{source.snippet}</p>
            </li>
          ))}
        </ul>
      </details>
    </main>
  );
}
