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
  return text.replace(/\*\*/g, "").trim();
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
    <article className="space-y-4" aria-label={content.title}>
      <header className="flex items-center gap-2">
        <ClipboardList size={18} className="shrink-0 text-marigold" />
        <h3 className="font-display text-base font-semibold">
          {renderInlineMarkdown(content.title)}
        </h3>
      </header>
      {!duplicateLegacySummary && (
        <section>
          <h4 className="text-xs font-semibold uppercase tracking-wide opacity-60">
            {hindi ? "सारांश" : "Summary"}
          </h4>
          <p className="mt-1.5 leading-relaxed">{renderInlineMarkdown(content.summary)}</p>
        </section>
      )}
      {content.sections.map((section, index) => (
        <section key={`${section.heading}-${index}`}>
          <h4 className="text-xs font-semibold uppercase tracking-wide opacity-60">
            {section.heading}
          </h4>
          <ul className="mt-1.5 list-disc space-y-1 pl-5">
            {section.points.map((point, pointIndex) => (
              <li key={pointIndex}>{renderInlineMarkdown(point)}</li>
            ))}
          </ul>
        </section>
      ))}
      {content.steps.length > 0 && (
        <section>
          <h4 className="text-xs font-semibold uppercase tracking-wide opacity-60">
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
