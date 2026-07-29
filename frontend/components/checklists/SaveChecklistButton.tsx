"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { BookmarkPlus, Loader2 } from "lucide-react";
import { checklistsApi } from "@/lib/checklists/api";
import { useLanguage } from "@/lib/i18n";
import { checklistCopy } from "@/lib/checklists/copy";

export default function SaveChecklistButton({
  serviceId,
  serviceName,
}: {
  serviceId: string;
  serviceName: string;
}) {
  const { lang } = useLanguage();
  const text = checklistCopy(lang);
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const save = async () => {
    setSaving(true);
    setError("");
    try {
      const result = await checklistsApi.create({
        service_id: serviceId,
        service_name: serviceName,
        language: lang,
      });
      if (result.checklist.user_id === null) {
        window.localStorage.setItem("janmitra_guest_checklists", "true");
      }
      router.push(`/my-checklists/${result.checklist.id}`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not save checklist.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <button
        type="button"
        onClick={save}
        disabled={saving}
        className="btn-primary inline-flex items-center gap-2 px-5 py-2.5 disabled:opacity-60"
      >
        {saving ? <Loader2 size={15} className="animate-spin" /> : <BookmarkPlus size={15} />}
        {saving ? text.saving : text.save}
      </button>
      {error && <p className="mt-2 text-xs text-red-600" role="alert">{error}</p>}
    </div>
  );
}
