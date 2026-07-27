import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import FAQResponseCard from "@/components/FAQResponseCard";

describe("FAQResponseCard", () => {
  it("renders structured summaries, bullets, steps, and notes", () => {
    render(
      <FAQResponseCard
        content={{
          response_type: "faq",
          title: "Ration Card Application",
          summary: "Eligible residents can apply through their state portal.",
          sections: [{ heading: "Documents", points: ["Identity proof", "Address proof"] }],
          steps: ["Collect documents", "Submit the form"],
          note: "Keep the acknowledgement number.",
        }}
      />,
    );

    expect(screen.getByRole("heading", { name: "Ration Card Application" })).toBeInTheDocument();
    expect(screen.getByText("Identity proof")).toBeInTheDocument();
    expect(screen.getByText("Submit the form")).toBeInTheDocument();
    expect(screen.getByText("Keep the acknowledgement number.")).toBeInTheDocument();
  });

  it("renders inline bold and normalizes an older saved scheme list", () => {
    const { container } = render(
      <FAQResponseCard
        content={{
          response_type: "faq",
          title: "Here are the top 5 welfare schemes",
          summary: "**Pradhan Mantri Awas Yojana**: Housing assistance",
          sections: [],
          steps: [
            "**Pradhan Mantri Awas Yojana**: Housing assistance",
            "**Ayushman Bharat**: Health coverage",
          ],
          note: null,
        }}
      />,
    );

    expect(screen.getByText("Schemes")).toBeInTheDocument();
    expect(screen.getByText("Pradhan Mantri Awas Yojana").tagName).toBe("STRONG");
    expect(container.textContent).not.toContain("Summary");
    expect(container.textContent).not.toContain("**");
  });
});
