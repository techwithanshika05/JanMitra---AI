"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Archive, ClipboardList, Loader2 } from "lucide-react";
import { checklistsApi } from "@/lib/checklists/api";
import type { SavedChecklist } from "@/lib/checklists/types";
import { useLanguage } from "@/lib/i18n";
import { checklistCopy } from "@/lib/checklists/copy";
import SavedChecklistCard from "@/components/checklists/SavedChecklistCard";
import GuestChecklistImportPrompt from "@/components/checklists/GuestChecklistImportPrompt";

export default function MyChecklistsPage() {
  const { lang } = useLanguage();
  const text = checklistCopy(lang);
  const [archived, setArchived] = useState(false);
  const [rows, setRows] = useState<SavedChecklist[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showImport, setShowImport] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await checklistsApi.list(archived);
      setRows(result.checklists);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not load checklists.");
    } finally {
      setLoading(false);
    }
  }, [archived]);

  useEffect(() => {
    setShowImport(
      !!window.localStorage.getItem("janmitra_token")
      && window.localStorage.getItem("janmitra_guest_checklists") === "true",
    );
  }, []);
  useEffect(() => { load(); }, [load]);

  return (
    <main className="mx-auto max-w-6xl px-5 py-14 md:px-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-semibold">{text.my}</h1>
          <p className="mt-2 text-sm text-maroon-dark/60">
            Track required documents and process steps without storing sensitive numbers.
          </p>
        </div>
        <Link href="/checklist" className="btn-primary px-5 py-2.5">
          + {text.save}
        </Link>
      </div>

      {showImport && (
        <div className="mt-7">
          <GuestChecklistImportPrompt
            lang={lang}
            onDone={() => { setShowImport(false); load(); }}
          />
        </div>
      )}

      <div className="mt-8 flex gap-2">
        <button
          onClick={() => setArchived(false)}
          className={`rounded-full px-4 py-2 text-sm ${!archived ? "bg-maroon text-white" : "bg-white/70"}`}
        >
          <ClipboardList size={14} className="mr-1 inline" /> {text.active}
        </button>
        <button
          onClick={() => setArchived(true)}
          className={`rounded-full px-4 py-2 text-sm ${archived ? "bg-maroon text-white" : "bg-white/70"}`}
        >
          <Archive size={14} className="mr-1 inline" /> {text.archived}
        </button>
      </div>

      {loading && (
        <p className="mt-10 flex items-center gap-2 text-sm text-maroon-dark/60">
          <Loader2 size={16} className="animate-spin" /> {text.loading}
        </p>
      )}
      {error && <p className="mt-8 rounded-card bg-red-50 p-4 text-sm text-red-700" role="alert">{error}</p>}
      {!loading && !error && rows.length === 0 && (
        <section className="mt-10 rounded-card border border-dashed border-blush bg-white/60 p-10 text-center">
          <ClipboardList className="mx-auto text-rose" />
          <h2 className="mt-3 font-display text-xl font-semibold">{text.empty}</h2>
          <p className="mt-1 text-sm text-maroon-dark/55">{text.emptyHelp}</p>
        </section>
      )}
      <div className="mt-8 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        {rows.map((checklist) => (
          <SavedChecklistCard key={checklist.id} checklist={checklist} copy={text} />
        ))}
      </div>
    </main>
  );
}
