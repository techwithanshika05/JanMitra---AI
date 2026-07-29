export type ChecklistStatus =
  | "not_started"
  | "in_progress"
  | "completed"
  | "archived"
  | "outdated";

export type ChecklistItemType =
  | "document"
  | "process_step"
  | "warning"
  | "important_note"
  | "timeline";

export type ChecklistItem = {
  id: string;
  checklist_id: string;
  item_type: ChecklistItemType;
  title: string;
  description: string | null;
  sequence_number: number;
  is_required: boolean;
  is_completed: boolean;
  completed_at: string | null;
  user_note: string | null;
  source_item_key: string;
  source_state: "current" | "new" | "changed" | "removed" | "outdated";
  created_at: string;
  updated_at: string;
};

export type SavedChecklist = {
  id: string;
  user_id: number | null;
  guest_session_id: string | null;
  service_id: string;
  service_name: string;
  language: string;
  status: ChecklistStatus;
  progress_percentage: number;
  source_version: string;
  source_citations: { title: string; snippet: string; score: number }[];
  knowledge_context: { state?: string | null; category?: string | null };
  storage_origin: "postgresql" | "sqlite";
  sync_status: "pending" | "synced" | "failed" | "conflict";
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  last_opened_at: string;
  items: ChecklistItem[];
};

export type ChecklistEnvelope = {
  storage_mode: "postgresql" | "sqlite";
  sync_status: SavedChecklist["sync_status"];
  checklist: SavedChecklist;
};

export type ChecklistGuidance = {
  progress_summary: string;
  next_steps: string[];
  missing_documents: string[];
  short_explanations: string[];
  alternative_actions: string[];
  reminders: string[];
};

export type ChecklistAnalytics = {
  active_storage_mode: "postgresql" | "sqlite";
  total_checklists: number;
  completion_rate: number;
  abandonment_rate: number;
  average_completion_hours: number;
  outdated_count: number;
  most_saved_checklists: { service_id: string; service_name: string; count: number }[];
  frequently_incomplete_steps: { title: string; count: number }[];
  storage_usage: { postgresql: number; sqlite: number };
};
