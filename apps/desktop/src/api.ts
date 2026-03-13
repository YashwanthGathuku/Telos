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

// ── Orchestrator API ────────────────────────────────────────────────────

export async function submitTask(task: string): Promise<{
  task_id: string;
  status: string;
  task: string;
}> {
  if (isTauri()) {
    const result = await tauriInvoke<{ task_id: string; status: string; task: string }>(
      "submit_task",
      { task }
    );
    return result;
  }

  const resp = await fetch(`${ORCHESTRATOR_URL}/task`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task }),
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

export async function getTasks(): Promise<unknown[]> {
  if (isTauri()) {
    return tauriInvoke<unknown[]>("get_tasks");
  }
  const resp = await fetch(`${ORCHESTRATOR_URL}/tasks`);
  return resp.json();
}

export async function getSystemState(): Promise<unknown> {
  if (isTauri()) {
    return tauriInvoke("get_system_state");
  }
  const resp = await fetch(`${ORCHESTRATOR_URL}/system/state`);
  return resp.json();
}

export async function getPrivacySummary(): Promise<unknown> {
  if (isTauri()) {
    return tauriInvoke("get_privacy_summary");
  }
  const resp = await fetch(`${ORCHESTRATOR_URL}/privacy/summary`);
  return resp.json();
}

// ── Scheduler API ───────────────────────────────────────────────────────

export async function getScheduledJobs(): Promise<unknown[]> {
  if (isTauri()) {
    return tauriInvoke<unknown[]>("get_scheduled_jobs");
  }
  const resp = await fetch(`${SCHEDULER_URL}/jobs`);
  return resp.json();
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
    es = new EventSource(`${ORCHESTRATOR_URL}/events`);

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
