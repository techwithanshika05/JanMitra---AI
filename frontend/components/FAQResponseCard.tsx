import React from "react";
import { ClipboardList } from "lucide-react";
import type { StructuredFAQ } from "@/lib/chatTypes";

function renderInlineMarkdown(text: string) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    return <React.Fragment key={index}>{part}</React.Fragment>;
  });
}

function plainText(text: string) {
  return text.replace(/\*\*/g, "").replace(/^\s*#{1,6}\s+/, "").trim();
}

function stripHeadingMarker(text: string) {
  return text.replace(/^\s*#{1,6}\s+/, "").trim();
}

export default function FAQResponseCard({ content }: { content: StructuredFAQ }) {
  const hindi = /[\u0900-\u097f]/.test(content.title + content.summary);
  const listLike = /(?:top|list).*(?:scheme|benefit)|(?:scheme|benefit).*(?:top|list)/i.test(
    content.title,
  );
  const firstStep = content.steps[0] ? plainText(content.steps[0]) : "";
  const summary = plainText(content.summary);
  const summaryPrefix = summary.replace(/[.…]+$/, "").slice(0, 120);
  const duplicateLegacySummary =
    listLike && summaryPrefix.length > 0 && (
      firstStep === summary || firstStep.startsWith(summaryPrefix)
    );
  const stepsHeading = listLike
    ? (hindi ? "योजनाएं" : "Schemes")
    : (hindi ? "चरण" : "Steps");

  return (
    <article className="space-y-5" aria-label={plainText(content.title)}>
      <header className="flex items-start gap-3 border-b border-maroon-dark/10 pb-3">
        <span className="mt-0.5 rounded-lg bg-marigold/15 p-1.5">
          <ClipboardList size={17} className="shrink-0 text-marigold" />
        </span>
        <h3 className="font-display text-lg font-semibold leading-snug text-maroon-dark">
          {renderInlineMarkdown(stripHeadingMarker(content.title))}
        </h3>
      </header>
      {!duplicateLegacySummary && (
        <section>
          <h4 className="text-xs font-semibold uppercase tracking-[0.08em] text-maroon-dark/55">
            {hindi ? "सारांश" : "Summary"}
          </h4>
          <p className="mt-2 leading-7 text-maroon-dark/90">{renderInlineMarkdown(content.summary)}</p>
        </section>
      )}
      {content.sections.map((section, index) => (
        <section key={`${section.heading}-${index}`}>
          <h4 className="font-display text-[15px] font-semibold text-maroon-dark">
            {stripHeadingMarker(section.heading)}
          </h4>
          <ul className="mt-2.5 space-y-2.5">
            {section.points.map((point, pointIndex) => (
              <li key={pointIndex} className="flex items-start gap-2.5 leading-6 text-maroon-dark/90">
                <span className="mt-2.5 h-1.5 w-1.5 shrink-0 rounded-full bg-marigold" aria-hidden="true" />
                <span>{renderInlineMarkdown(stripHeadingMarker(point))}</span>
              </li>
            ))}
          </ul>
        </section>
      ))}
      {content.steps.length > 0 && (
        <section>
          <h4 className="font-display text-[15px] font-semibold text-maroon-dark">
            {stepsHeading}
          </h4>
          <ol className="mt-1.5 list-decimal space-y-1 pl-5">
            {content.steps.map((step, index) => (
              <li key={index}>{renderInlineMarkdown(step)}</li>
            ))}
          </ol>
        </section>
      )}
      {content.note && (
        <section>
          <h4 className="text-xs font-semibold uppercase tracking-wide opacity-60">
            {hindi ? "ध्यान दें" : "Note"}
          </h4>
          <p className="mt-1.5 border-l-2 border-marigold pl-3 text-xs opacity-75">
            {renderInlineMarkdown(content.note)}
          </p>
        </section>
      )}
    </article>
  );
}
