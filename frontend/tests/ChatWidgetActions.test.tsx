import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ChatWidget from "@/components/ChatWidget";
import { api } from "@/lib/api";

vi.mock("@/lib/i18n", () => ({
  useLanguage: () => ({
    lang: "en",
    t: (key: string) => ({
      "chat.welcome": "Welcome",
      "chat.placeholder": "Ask a question",
      "chat.thinking": "Thinking",
      "chat.listening": "Listening",
      "chat.speak": "Listen to answer",
      "chat.mic": "Speak your question",
    }[key] || key),
  }),
}));

vi.mock("@/lib/api", () => ({
  api: {
    chat: vi.fn(),
  },
}));

describe("ChatWidget message actions", () => {
  beforeEach(() => {
    vi.mocked(api.chat).mockResolvedValue({
      answer: "A **grounded** response",
      confidence: 0.8,
      sources: [],
      disclaimer: "",
    });
  });

  it("shows retry, edit, and copy for users and copy for assistants", async () => {
    render(<ChatWidget />);

    const input = screen.getByPlaceholderText("Ask a question");
    fireEvent.change(input, { target: { value: "My welfare question" } });
    fireEvent.click(screen.getByRole("button", { name: "Send message" }));

    await waitFor(() => expect(api.chat).toHaveBeenCalledTimes(1));
    expect(screen.getByRole("button", { name: "Retry message" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Edit message" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy message" })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Copy response" })).toHaveLength(2);
    expect(screen.getByText("grounded")).toHaveClass("font-semibold");

    fireEvent.click(screen.getByRole("button", { name: "Edit message" }));
    expect(input).toHaveValue("My welfare question");
  });
});
