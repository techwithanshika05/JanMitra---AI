export type StructuredFAQ = {
  response_type: "faq";
  title: string;
  summary: string;
  sections: { heading: string; points: string[] }[];
  steps: string[];
  note?: string | null;
};

export type ChatMessage = {
  id?: string;
  session_id?: string;
  role: "user" | "assistant" | "system";
  content: string;
  language?: string;
  response_type?: string;
  structured_content?: StructuredFAQ | null;
  confidence?: number | null;
  sources?: { title: string; snippet: string; score: number }[];
  disclaimer?: string | null;
  created_at?: string;
};

export type ChatSession = {
  id: string;
  title?: string | null;
  created_at: string;
  updated_at: string;
  last_message_at: string;
};

export type ChatFeedback = {
  id: string;
  session_id: string;
  message_id: string;
  reaction: "like" | "dislike" | "neutral";
  rating?: number | null;
  feedback_text?: string | null;
};
