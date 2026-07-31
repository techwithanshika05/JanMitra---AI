const TOKEN_KEY = 'janmitra_token'

export const getToken = () =>
  typeof window === 'undefined' ? null : localStorage.getItem(TOKEN_KEY)

export const setToken = (token) => {
  if (typeof window === 'undefined') return
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
  window.dispatchEvent(new CustomEvent('janmitra-auth-changed', {
    detail: { authenticated: Boolean(token) }
  }))
}

const headers = (extra = {}) => {
  const token = getToken()
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extra
  }
}

export async function request(path, options = {}) {
  const response = await fetch(path, {
    credentials: 'include',
    ...options,
    headers: headers(options.headers)
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const detail = Array.isArray(body.detail)
      ? body.detail.map(item => item.msg).join(', ')
      : body.detail
    const error = new Error(detail || `Request failed (${response.status})`)
    error.status = response.status
    throw error
  }
  if (response.status === 204) return null
  return response.json()
}

export async function upload(path, file) {
  const formData = new FormData()
  formData.append('file', file)
  const token = getToken()
  const response = await fetch(path, {
    method: 'POST',
    credentials: 'include',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || `Upload failed (${response.status})`)
  }
  return response.json()
}

async function download(path, options = {}) {
  const token = getToken()
  const response = await fetch(path, {
    credentials: 'include',
    ...options,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {})
    }
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || `Download failed (${response.status})`)
  }
  return response.blob()
}

const json = (method, body) => ({
  method,
  body: body === undefined ? undefined : JSON.stringify(body)
})

export const api = {
  health: () => request('/api/health'),
  login: payload => request('/api/auth/login', json('POST', payload)),
  adminLogin: payload => request('/api/auth/admin-login', json('POST', payload)),
  register: payload => request('/api/auth/register', json('POST', payload)),
  me: () => request('/api/auth/me'),

  chat: payload => request('/api/chat', json('POST', payload)),
  chatHistory: sessionId => request(`/api/chat/history/${encodeURIComponent(sessionId)}`),
  chatSessions: () => request('/backend-api/chat/sessions'),
  createChatSession: title => request('/backend-api/chat/sessions', json('POST', { title })),
  chatSession: id => request(`/backend-api/chat/sessions/${id}`),
  renameChatSession: (id, title) => request(`/backend-api/chat/sessions/${id}`, json('PATCH', { title })),
  deleteChatSession: id => request(`/backend-api/chat/sessions/${id}`, { method: 'DELETE' }),
  chatMessages: (id, cursor) => request(`/backend-api/chat/sessions/${id}/messages${cursor ? `?cursor=${encodeURIComponent(cursor)}` : ''}`),
  sendChatMessage: (id, payload) => request(`/backend-api/chat/sessions/${id}/messages`, json('POST', payload)),
  saveChatFeedback: (messageId, payload) => request(`/backend-api/chat/messages/${messageId}/feedback`, json('POST', payload)),
  chatFeedback: messageId => request(`/backend-api/chat/messages/${messageId}/feedback`),
  deleteChatFeedback: messageId => request(`/backend-api/chat/messages/${messageId}/feedback`, { method: 'DELETE' }),
  migrateGuestChat: () => request('/backend-api/chat/migrate-guest', json('POST')),

  schemes: () => request('/api/schemes'),
  findSchemes: payload => request('/api/schemes/find-hybrid', json('POST', payload)),
  scheme: id => request(`/api/schemes/${id}`),
  faqs: (filters = {}) => {
    const params = new URLSearchParams(Object.entries(filters).filter(([, value]) => value))
    return request(`/api/faqs${params.size ? `?${params}` : ''}`)
  },
  rationProcesses: () => request('/api/ration/processes'),
  rationProcess: key => request(`/api/ration/processes/${encodeURIComponent(key)}`),
  generateChecklist: payload => request('/api/checklist/generate', json('POST', payload)),
  downloadChecklistPdf: payload => download('/api/checklist/generate/pdf', {
    ...json('POST', payload),
    headers: { 'Content-Type': 'application/json' }
  }),
  grievanceGuide: payload => request('/api/grievance/guide', json('POST', payload)),
  submitFeedback: payload => request('/api/analytics/feedback', json('POST', payload)),

  uploadDocument: file => upload('/api/documents/upload', file),
  askDocument: payload => request('/api/documents/ask', json('POST', payload)),

  voiceHealth: () => request('/backend-api/voice/health'),
  startVoice: language => request('/backend-api/voice/sessions', json('POST', { language })),
  endVoice: (id, reason = 'user_ended') =>
    request(`/backend-api/voice/sessions/${id}/end`, json('POST', { reason })),
  voiceSessions: () => request('/backend-api/voice/sessions'),
  voiceSession: id => request(`/backend-api/voice/sessions/${id}`),

  createSavedChecklist: payload => request('/backend-api/checklists', json('POST', payload)),
  savedChecklists: (archived = false) => request(`/backend-api/checklists?archived=${archived}`),
  savedChecklist: id => request(`/backend-api/checklists/${id}`),
  updateSavedChecklist: (id, payload) => request(`/backend-api/checklists/${id}`, json('PATCH', payload)),
  updateChecklistItem: (checklistId, itemId, payload) =>
    request(`/backend-api/checklists/${checklistId}/items/${itemId}`, json('PATCH', payload)),
  importGuestChecklists: approved => request('/backend-api/checklists/import-guest', json('POST', { approved })),
  refreshChecklist: id => request(`/backend-api/checklists/${id}/refresh`, json('POST')),
  archiveChecklist: id => request(`/backend-api/checklists/${id}/archive`, json('POST')),
  restoreChecklist: id => request(`/backend-api/checklists/${id}/restore`, json('POST')),
  deleteChecklist: id => request(`/backend-api/checklists/${id}`, { method: 'DELETE' }),
  checklistGuidance: (id, remindersConsented = false) =>
    request(`/backend-api/checklists/${id}/guidance?reminders_consented=${remindersConsented}`),

  guestSession: () => request('/backend-api/guest/session', json('POST')),
  claimGuestData: () => request('/backend-api/auth/claim-guest-data', json('POST')),
  identityHistory: () => request('/backend-api/me/history'),
  identityActivity: () => request('/backend-api/me/activity'),
  preferences: () => request('/backend-api/me/preferences'),
  updatePreferences: payload => request('/backend-api/me/preferences', json('PATCH', payload)),

  adminSummary: () => request('/api/admin/summary'),
  adminFeedback: () => request('/api/admin/feedback'),
  eventsByType: () => request('/api/analytics/events-by-type'),
  missingKnowledge: () => request('/api/admin/missing-knowledge'),
  checklistAnalytics: () => request('/backend-api/checklists/admin/analytics'),
  uploadKnowledgeDocument: file => upload('/api/upload/document', file),
  knowledgeDocuments: () => request('/api/upload/documents')
}
