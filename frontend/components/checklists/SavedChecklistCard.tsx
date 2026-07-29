"use client";
import Link from "next/link";
import { ArrowRight, Clock3 } from "lucide-react";
import type { SavedChecklist } from "@/lib/checklists/types";
import ChecklistProgress from "./ChecklistProgress";

export default function SavedChecklistCard({
  checklist,
  copy,
}: {
  checklist: SavedChecklist;
  copy: { completed: string; updated: string; open: string };
}) {
  const completed = checklist.items.filter((item) => item.is_completed).length;
  const total = checklist.items.filter(
    (item) => item.source_state !== "removed",
  ).length;
  return (
    <article className="rounded-card border border-blush/50 bg-white/80 p-5 shadow-card">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="font-display text-lg font-semibold">{checklist.service_name}</h2>
          <span className="mt-1 inline-flex rounded-full bg-blush/50 px-2.5 py-1 text-xs text-maroon">
            {checklist.status.replaceAll("_", " ")}
          </span>
        </div>
        <strong className="text-lg text-rose">{Math.round(checklist.progress_percentage)}%</strong>
      </div>
      <div className="mt-4">
        <ChecklistProgress value={checklist.progress_percentage} />
      </div>
      <p className="mt-2 text-xs text-maroon-dark/60">
        {completed}/{total} {copy.completed}
      </p>
      <div className="mt-5 flex items-center justify-between border-t border-blush/40 pt-4">
        <span className="flex items-center gap-1 text-xs text-maroon-dark/50">
          <Clock3 size={13} /> {copy.updated}:{" "}
          {new Date(checklist.updated_at).toLocaleDateString()}
        </span>
        <Link
          href={`/my-checklists/${checklist.id}`}
          className="inline-flex items-center gap-1 text-sm font-semibold text-rose"
        >
          {copy.open} <ArrowRight size={14} />
        </Link>
      </div>
    </article>
  );
}
