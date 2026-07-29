import { request } from "@/lib/api";
import type {
  ChecklistAnalytics,
  ChecklistEnvelope,
  ChecklistGuidance,
  SavedChecklist,
} from "./types";

export const checklistsApi = {
  create: (payload: {
    service_id: string;
    service_name: string;
    language: string;
    state?: string;
    category?: string;
  }): Promise<ChecklistEnvelope> =>
    request("/api/checklists", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  list: (archived = false): Promise<{
    storage_mode: string;
    sync_status: string;
    checklists: SavedChecklist[];
  }> => request(`/api/checklists${archived ? "?archived=true" : ""}`),

  get: (id: string): Promise<ChecklistEnvelope> =>
    request(`/api/checklists/${id}`),

  updateItem: (
    checklistId: string,
    itemId: string,
    payload: { is_completed?: boolean; user_note?: string | null },
  ): Promise<ChecklistEnvelope> =>
    request(`/api/checklists/${checklistId}/items/${itemId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  refresh: (id: string): Promise<ChecklistEnvelope & {
    new_items: number;
    changed_items: number;
    removed_items: number;
    source_version_changed: boolean;
  }> => request(`/api/checklists/${id}/refresh`, { method: "POST" }),

  archive: (id: string): Promise<ChecklistEnvelope> =>
    request(`/api/checklists/${id}/archive`, { method: "POST" }),

  restore: (id: string): Promise<ChecklistEnvelope> =>
    request(`/api/checklists/${id}/restore`, { method: "POST" }),

  delete: (id: string): Promise<void> =>
    request(`/api/checklists/${id}`, { method: "DELETE" }),

  importGuest: (approved: boolean): Promise<{
    imported_count: number;
    skipped_count: number;
  }> =>
    request("/api/checklists/import-guest", {
      method: "POST",
      body: JSON.stringify({ approved }),
    }),

  guidance: (id: string, remindersConsented = false): Promise<ChecklistGuidance> =>
    request(
      `/api/checklists/${id}/guidance?reminders_consented=${remindersConsented}`,
    ),

  analytics: (): Promise<ChecklistAnalytics> =>
    request("/api/checklists/admin/analytics"),
};
