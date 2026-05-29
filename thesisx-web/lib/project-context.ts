const STORAGE_KEY = "thesisx.active_project_id";
const HISTORY_SESSION_KEY = "thesisx.history_session_id";

export function getActiveProjectId() {
  if (typeof window === "undefined") {
    return "";
  }
  return window.localStorage.getItem(STORAGE_KEY) ?? "";
}

export function setActiveProjectId(projectId: string) {
  if (typeof window === "undefined") {
    return;
  }
  if (!projectId) {
    window.localStorage.removeItem(STORAGE_KEY);
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, projectId);
}

export function getHistorySessionId() {
  if (typeof window === "undefined") {
    return "";
  }
  return window.localStorage.getItem(HISTORY_SESSION_KEY) ?? "";
}

export function setHistorySessionId(sessionId: string) {
  if (typeof window === "undefined") {
    return;
  }
  if (!sessionId) {
    window.localStorage.removeItem(HISTORY_SESSION_KEY);
    return;
  }
  window.localStorage.setItem(HISTORY_SESSION_KEY, sessionId);
}
