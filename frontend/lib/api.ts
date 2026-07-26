const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function authHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = window.localStorage.getItem("janmitra_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request(path: string, options: RequestInit = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  chat: (payload: { session_id: string; message: string; language?: string }) =>
    request("/chat", { method: "POST", body: JSON.stringify(payload) }),

  findSchemes: (payload: Record<string, unknown>) =>
    request("/schemes/find", { method: "POST", body: JSON.stringify(payload) }),

  listSchemes: () => request("/schemes"),

  generateChecklist: (payload: { service_type: string; state?: string; category?: string }) =>
    request("/checklist/generate", { method: "POST", body: JSON.stringify(payload) }),

  rationProcesses: () => request("/ration/processes"),
  rationProcess: (key: string) => request(`/ration/processes/${key}`),

  guideGrievance: (payload: { category: string; description: string; state?: string }) =>
    request("/grievance/guide", { method: "POST", body: JSON.stringify(payload) }),

  login: (payload: { mobile: string; password: string }) =>
    request("/auth/login", { method: "POST", body: JSON.stringify(payload) }),

  register: (payload: Record<string, unknown>) =>
    request("/auth/register", { method: "POST", body: JSON.stringify(payload) }),

  adminSummary: () => request("/admin/summary"),

  uploadDocument: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_URL}/documents/upload`, { method: "POST", body: formData });
    if (!res.ok) throw new Error("Upload failed");
    return res.json();
  },

  askDocument: (payload: { doc_id: string; question: string; language?: string }) =>
    request("/documents/ask", { method: "POST", body: JSON.stringify(payload) }),

  listFaqs: (params?: { category?: string; language?: string }) => {
    const qs = new URLSearchParams();
    if (params?.category) qs.set("category", params.category);
    if (params?.language) qs.set("language", params.language);
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return request(`/faqs${suffix}`);
  },

  submitFeedback: (payload: { chat_id?: number; rating: number; comment?: string }) =>
    request("/analytics/feedback", { method: "POST", body: JSON.stringify(payload) }),
};

export { API_URL };
