"use client";
import React from "react";
import { Star } from "lucide-react";

export default function StarRating({
  value,
  onChange,
  disabled = false,
}: {
  value: number | null;
  onChange: (value: number) => void;
  disabled?: boolean;
}) {
  return (
    <div className="flex gap-0.5" role="radiogroup" aria-label="Rate this response">
      {[1, 2, 3, 4, 5].map((rating) => (
        <button
          key={rating}
          type="button"
          role="radio"
          aria-checked={value === rating}
          aria-label={`${rating} star${rating === 1 ? "" : "s"}`}
          disabled={disabled}
          onClick={() => onChange(rating)}
          className="rounded p-0.5 disabled:opacity-50"
        >
          <Star
            size={16}
            className={rating <= (value || 0) ? "fill-marigold text-marigold" : "text-indigo-900/30 dark:text-white/30"}
          />
        </button>
      ))}
    </div>
  );
}
