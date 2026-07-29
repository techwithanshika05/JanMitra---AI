export default function ChecklistProgress({ value }: { value: number }) {
  const safeValue = Math.max(0, Math.min(100, value));
  return (
    <div
      className="h-2.5 overflow-hidden rounded-full bg-blush/60"
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(safeValue)}
    >
      <div
        className="h-full rounded-full bg-gradient-primary transition-all"
        style={{ width: `${safeValue}%` }}
      />
    </div>
  );
}
