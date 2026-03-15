/**
 * TELOS — API client and SSE connection manager.
 *
 * Handles communication with the orchestrator (port 8080)
 * and scheduler (port 8081) via the Tauri IPC bridge.
 * Falls back to direct HTTP when running in dev mode.
 */

const ORCHESTRATOR_URL = "http://127.0.0.1:8080";
const SCHEDULER_URL = "http://127.0.0.1:8081";

// Check if we're running inside Tauri
const isTauri = () => "__TAURI_INTERNALS__" in window;

async function tauriInvoke<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  if (isTauri()) {
    const { invoke } = await import("@tauri-apps/api/core");
    return invoke<T>(cmd, args);
  }
  throw new Error("Not in Tauri context");
}

function getSelectedProvider(): string | null {
  return sessionStorage.getItem("telos_provider");
}

function getApiToken(): string | null {
  const token = sessionStorage.getItem("telos_api_token");
  return token?.trim() ? token.trim() : null;
}

function authHeaders(): HeadersInit {
  const token = getApiToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function orchestratorHeaders(): HeadersInit {
  const provider = getSelectedProvider();
  return {
    ...authHeaders(),
    ...(provider ? { "X-Telos-Provider": provider } : {}),
  };
}

function schedulerHeaders(): HeadersInit {
  return authHeaders();
}

async function readJsonResponse<T>(resp: Response): Promise<T> {
  const body = (await resp.json().catch(() => null)) as Record<string, unknown> | null;
  if (!resp.ok) {
    const message = typeof body?.error === "string"
      ? body.error
      : typeof body?.detail === "string"
        ? body.detail
        : `HTTP ${resp.status}`;
    throw new Error(message);
  }
  return body as T;
}

// ── Orchestrator API ────────────────────────────────────────────────────

export async function submitTask(task: string): Promise<{
  task_id: string;
  status: string;
  task: string;
}> {
  const provider = getSelectedProvider();

  if (isTauri()) {
    const result = await tauriInvoke<{ task_id: string; status: string; task: string }>(
      "submit_task",
      { task, provider, token: getApiToken() }
    );
    return result;
  }

  const resp = await fetch(`${ORCHESTRATOR_URL}/task`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...orchestratorHeaders(),
    },
    body: JSON.stringify({ task }),
  });
  return readJsonResponse(resp);
}

export async function getTasks(): Promise<unknown[]> {
  if (isTauri()) {
    return tauriInvoke<unknown[]>("get_tasks", { token: getApiToken() });
  }
  const resp = await fetch(`${ORCHESTRATOR_URL}/tasks`, {
    headers: orchestratorHeaders(),
  });
  return readJsonResponse(resp);
}

export async function getSystemState(): Promise<unknown> {
  if (isTauri()) {
    return tauriInvoke("get_system_state", { provider: getSelectedProvider(), token: getApiToken() });
  }
  const resp = await fetch(`${ORCHESTRATOR_URL}/system/state`, {
    headers: orchestratorHeaders(),
  });
  return readJsonResponse(resp);
}

export async function getPrivacySummary(): Promise<unknown> {
  if (isTauri()) {
    return tauriInvoke("get_privacy_summary", { provider: getSelectedProvider(), token: getApiToken() });
  }
  const resp = await fetch(`${ORCHESTRATOR_URL}/privacy/summary`, {
    headers: orchestratorHeaders(),
  });
  return readJsonResponse(resp);
}

// ── Scheduler API ───────────────────────────────────────────────────────

export async function getScheduledJobs(): Promise<unknown[]> {
  if (isTauri()) {
    return tauriInvoke<unknown[]>("get_scheduled_jobs", { token: getApiToken() });
  }
  const resp = await fetch(`${SCHEDULER_URL}/jobs`, {
    headers: schedulerHeaders(),
  });
  return readJsonResponse(resp);
}

// ── SSE Event Stream ────────────────────────────────────────────────────

export type EventHandler = (event: {
  event_type: string;
  task_id?: string;
  payload: Record<string, unknown>;
  timestamp: string;
}) => void;

export function connectEventStream(onEvent: EventHandler, onStatus: (connected: boolean) => void): () => void {
  let es: EventSource | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let backoffMs = 1000;
  const MAX_BACKOFF_MS = 30000;

  function connect() {
    const url = new URL(`${ORCHESTRATOR_URL}/events`);
    const token = getApiToken();
    if (token) {
      url.searchParams.set("access_token", token);
    }
    es = new EventSource(url.toString());

    es.onopen = () => {
      backoffMs = 1000; // reset on successful connection
      onStatus(true);
    };

    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        onEvent(data);
      } catch {
        // ignore parse errors
      }
    };

    // Named event types
    for (const type of [
      "task_created",
      "task_status",
      "step_update",
      "privacy_update",
      "agent_status",
      "system_state",
      "uigraph_update",
      "error",
    ]) {
      es.addEventListener(type, (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          onEvent(data);
        } catch {
          // ignore
        }
      });
    }

    es.onerror = () => {
      onStatus(false);
      es?.close();
      // Reconnect with exponential backoff (1s → 2s → 4s → ... → 30s max)
      reconnectTimer = setTimeout(connect, backoffMs);
      backoffMs = Math.min(backoffMs * 2, MAX_BACKOFF_MS);
    };
  }

  connect();

  return () => {
    es?.close();
    if (reconnectTimer) clearTimeout(reconnectTimer);
  };
}
