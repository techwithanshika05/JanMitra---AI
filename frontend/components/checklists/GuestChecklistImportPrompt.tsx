"use client";
import { useState } from "react";
import { checklistsApi } from "@/lib/checklists/api";
import { checklistCopy } from "@/lib/checklists/copy";
import type { Lang } from "@/lib/i18n";

export default function GuestChecklistImportPrompt({
  lang,
  onDone,
}: {
  lang: Lang;
  onDone: (imported: number) => void;
}) {
  const text = checklistCopy(lang);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const finish = async (approved: boolean) => {
    if (!approved) {
      onDone(0);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const result = await checklistsApi.importGuest(true);
      window.localStorage.removeItem("janmitra_guest_checklists");
      onDone(result.imported_count);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Import failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="rounded-card border border-gold/60 bg-gold/20 p-5" role="dialog">
      <h2 className="font-display text-lg font-semibold">{text.importTitle}</h2>
      <p className="mt-1 text-sm text-maroon-dark/65">{text.importBody}</p>
      <div className="mt-4 flex flex-wrap gap-3">
        <button className="btn-primary px-5 py-2" disabled={loading} onClick={() => finish(true)}>
          {loading ? text.saving : text.import}
        </button>
        <button className="btn-secondary px-5 py-2" disabled={loading} onClick={() => finish(false)}>
          {text.skip}
        </button>
      </div>
      {error && <p className="mt-2 text-xs text-red-600" role="alert">{error}</p>}
    </section>
  );
}
