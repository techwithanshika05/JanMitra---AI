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

  login: (payload: { email: string; password: string }) =>
    request("/auth/login", { method: "POST", body: JSON.stringify(payload) }),

  register: (payload: Record<string, unknown>) =>
    request("/auth/register", { method: "POST", body: JSON.stringify(payload) }),

  adminSummary: () => request("/admin/summary"),
};

export { API_URL };
