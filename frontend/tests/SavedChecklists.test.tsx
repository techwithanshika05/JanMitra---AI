import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ChecklistProgress from "@/components/checklists/ChecklistProgress";
import ChecklistItemRow from "@/components/checklists/ChecklistItemRow";
import SaveChecklistButton from "@/components/checklists/SaveChecklistButton";
import GuestChecklistImportPrompt from "@/components/checklists/GuestChecklistImportPrompt";
import { checklistsApi } from "@/lib/checklists/api";

const push = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

vi.mock("@/lib/i18n", () => ({
  useLanguage: () => ({ lang: "en" }),
}));

vi.mock("@/lib/checklists/api", () => ({
  checklistsApi: {
    create: vi.fn(),
    importGuest: vi.fn(),
  },
}));

describe("saved checklist UI", () => {
  beforeEach(() => {
    push.mockReset();
    window.localStorage.clear();
    vi.clearAllMocks();
  });

  it("renders accessible progress", () => {
    render(<ChecklistProgress value={62.5} />);
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "63");
  });

  it("saves a guest checklist and remembers that import is available", async () => {
    vi.mocked(checklistsApi.create).mockResolvedValue({
      storage_mode: "sqlite",
      sync_status: "pending",
      checklist: {
        id: "checklist-1",
        user_id: null,
        guest_session_id: "guest-1",
      },
    } as never);
    render(<SaveChecklistButton serviceId="ration" serviceName="Ration card" />);
    fireEvent.click(screen.getByRole("button", { name: "Save Checklist" }));

    await waitFor(() => expect(checklistsApi.create).toHaveBeenCalled());
    expect(window.localStorage.getItem("janmitra_guest_checklists")).toBe("true");
    expect(push).toHaveBeenCalledWith("/my-checklists/checklist-1");
  });

  it("updates completion and saves only a general note", async () => {
    const onUpdate = vi.fn().mockResolvedValue(undefined);
    render(
      <ChecklistItemRow
        item={{
          id: "item-1",
          checklist_id: "checklist-1",
          item_type: "document",
          title: "Residence proof",
          description: "Use an accepted residence document.",
          sequence_number: 1,
          is_required: true,
          is_completed: false,
          completed_at: null,
          user_note: null,
          source_item_key: "document:residence",
          source_state: "current",
          created_at: "2026-07-28T00:00:00",
          updated_at: "2026-07-28T00:00:00",
        }}
        labels={{
          required: "Required",
          optional: "Optional",
          note: "General note",
          noteWarning: "Do not enter sensitive numbers.",
        }}
        onUpdate={onUpdate}
      />,
    );
    fireEvent.click(screen.getByRole("checkbox", { name: "Residence proof" }));
    await waitFor(() =>
      expect(onUpdate).toHaveBeenCalledWith({ is_completed: true }),
    );
    const note = screen.getByRole("textbox");
    fireEvent.change(note, { target: { value: "Submitted at the office." } });
    fireEvent.blur(note);
    await waitFor(() =>
      expect(onUpdate).toHaveBeenCalledWith({
        user_note: "Submitted at the office.",
      }),
    );
  });

  it("imports guest checklists only after the approval button is used", async () => {
    vi.mocked(checklistsApi.importGuest).mockResolvedValue({
      imported_count: 2,
      skipped_count: 0,
    });
    const onDone = vi.fn();
    window.localStorage.setItem("janmitra_guest_checklists", "true");
    render(<GuestChecklistImportPrompt lang="en" onDone={onDone} />);

    expect(checklistsApi.importGuest).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Import checklists" }));
    await waitFor(() => expect(checklistsApi.importGuest).toHaveBeenCalledWith(true));
    expect(onDone).toHaveBeenCalledWith(2);
    expect(window.localStorage.getItem("janmitra_guest_checklists")).toBeNull();
  });
});
