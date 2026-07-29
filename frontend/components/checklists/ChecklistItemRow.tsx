"use client";
import { useEffect, useState } from "react";
import type { ChecklistItem } from "@/lib/checklists/types";

function professionalDisplayParts(value: string) {
  return value
    .replace(/\u00e2\u20ac\u00a2/g, "\u2022")
    .split(/\s*[\u00b7\u2022\u25aa\u25cf\u25e6\u2713]\s*/)
    .map((part) => part.trim())
    .filter(Boolean);
}

export default function ChecklistItemRow({
  item,
  labels,
  disabled,
  onUpdate,
}: {
  item: ChecklistItem;
  labels: { required: string; optional: string; note: string; noteWarning: string };
  disabled?: boolean;
  onUpdate: (payload: { is_completed?: boolean; user_note?: string | null }) => Promise<void>;
}) {
  const [note, setNote] = useState(item.user_note || "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => setNote(item.user_note || ""), [item.user_note]);

  const update = async (payload: { is_completed?: boolean; user_note?: string | null }) => {
    setSaving(true);
    setError("");
    try {
      await onUpdate(payload);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Update failed.");
    } finally {
      setSaving(false);
    }
  };

  const removed = item.source_state === "removed" || item.source_state === "outdated";
  const titleParts = professionalDisplayParts(item.title);
  const descriptionParts = item.description
    ? professionalDisplayParts(item.description)
    : [];
  return (
    <article
      id={`checklist-item-${item.id}`}
      className={`rounded-xl border p-4 ${removed ? "border-gray-200 bg-gray-50 opacity-70" : "border-blush/50 bg-white/70"}`}
    >
      <div className="flex items-start gap-3">
        <input
          type="checkbox"
          className="mt-1 h-4 w-4 accent-rose"
          checked={item.is_completed}
          disabled={disabled || saving || removed}
          onChange={(event) => update({ is_completed: event.target.checked })}
          aria-label={item.title}
        />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className={`font-display text-base font-semibold leading-snug text-maroon-dark ${item.is_completed ? "line-through opacity-60" : ""}`}>
              {titleParts[0]}
            </h3>
            <span className="rounded-full bg-blush/50 px-2 py-0.5 text-[11px] text-maroon">
              {item.is_required ? labels.required : labels.optional}
            </span>
            {item.source_state !== "current" && (
              <span className="rounded-full bg-gold/40 px-2 py-0.5 text-[11px] uppercase">
                {item.source_state}
              </span>
            )}
          </div>
          {titleParts.length > 1 && (
            <ul className="mt-3 grid gap-2 text-sm text-maroon-dark/80 sm:grid-cols-2">
              {titleParts.slice(1).map((part) => (
                <li key={part} className="flex items-start gap-2 leading-5">
                  <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-marigold" />
                  <span>{part}</span>
                </li>
              ))}
            </ul>
          )}
          {descriptionParts.length > 0 && (
            <div className="mt-2 space-y-1 text-sm leading-6 text-maroon-dark/65">
              {descriptionParts.map((part) => <p key={part}>{part}</p>)}
            </div>
          )}
          {!removed && (
            <div className="mt-3">
              <label className="text-xs font-medium text-maroon-dark/70">{labels.note}</label>
              <textarea
                value={note}
                disabled={disabled || saving}
                maxLength={1000}
                rows={2}
                onChange={(event) => setNote(event.target.value)}
                onBlur={() => {
                  if (note !== (item.user_note || "")) update({ user_note: note || null });
                }}
                className="mt-1 w-full rounded-lg border border-blush/60 bg-transparent p-2 text-sm outline-none focus:border-rose"
              />
              <p className="mt-1 text-[11px] text-maroon-dark/45">{labels.noteWarning}</p>
            </div>
          )}
          {error && <p className="mt-2 text-xs text-red-600" role="alert">{error}</p>}
        </div>
      </div>
    </article>
  );
}
