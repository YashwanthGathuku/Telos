/**
 * TELOS Mission Control — global state store (Zustand).
 *
 * Single source of truth for tasks, agents, privacy metrics,
 * system state, and SSE event stream data.
 */

import { create } from "zustand";

// ── Types ───────────────────────────────────────────────────────────────

export type TaskStatus =
  | "pending"
  | "routing"
  | "executing"
  | "completed"
  | "failed"
  | "cancelled";

export type AgentRole = "planner" | "reader" | "writer" | "verifier" | "privacy" | "vision";

export interface TaskStep {
  agent: AgentRole;
  action: string;
  status: TaskStatus;
  started_at?: string;
  completed_at?: string;
  detail: string;
}

export interface TaskRecord {
  id: string;
  task: string;
  status: TaskStatus;
  created_at: string;
  updated_at: string;
  result?: unknown;
  error?: string;
  steps: TaskStep[];
  privacy_summary?: PrivacySummary;
}

export interface PrivacySummary {
  local_operations: number;
  cloud_calls: number;
  bytes_sent: number;
  bytes_received: number;
  fields_masked: number;
  pii_blocked: number;
}

export interface SystemState {
  provider: string;
  provider_healthy: boolean;
  privacy_mode: string;
  active_tasks: number;
  total_tasks: number;
  egress: {
    total_calls: number;
    total_bytes_sent: number;
    total_bytes_received: number;
  };
  services: {
    orchestrator: boolean;
    scheduler: boolean;
    uigraph: boolean;
    capture_engine: boolean;
    delta_engine: boolean;
  };
}

export interface TelosEvent {
  event_type: string;
  task_id?: string;
  payload: Record<string, unknown>;
  timestamp: string;
}

interface TelosStore {
  // Tasks
  tasks: TaskRecord[];
  addTask: (task: TaskRecord) => void;
  updateTask: (id: string, update: Partial<TaskRecord>) => void;
  updateTaskStep: (taskId: string, stepIndex: number, update: Partial<TaskStep>) => void;

  // System state
  systemState: SystemState | null;
  setSystemState: (state: SystemState) => void;

  // Privacy
  privacySummary: PrivacySummary;
  updatePrivacy: (update: Partial<PrivacySummary>) => void;

  // Events
  events: TelosEvent[];
  addEvent: (event: TelosEvent) => void;

  // UI state
  commandInput: string;
  setCommandInput: (v: string) => void;
  isSubmitting: boolean;
  setIsSubmitting: (v: boolean) => void;

  // Connection
  connected: boolean;
  setConnected: (v: boolean) => void;
}

// ── Store ───────────────────────────────────────────────────────────────

export const useTelosStore = create<TelosStore>((set) => ({
  tasks: [],
  addTask: (task) =>
    set((state) => ({ tasks: [task, ...state.tasks].slice(0, 100) })),
  updateTask: (id, update) =>
    set((state) => ({
      tasks: state.tasks.map((t) => (t.id === id ? { ...t, ...update } : t)),
    })),
  updateTaskStep: (taskId, stepIndex, update) =>
    set((state) => ({
      tasks: state.tasks.map((t) => {
        if (t.id !== taskId) return t;
        const steps = [...t.steps];
        if (steps[stepIndex]) {
          steps[stepIndex] = { ...steps[stepIndex], ...update };
        } else if ("agent" in update && update.agent) {
          steps[stepIndex] = {
            agent: update.agent,
            action: "",
            detail: "",
            status: "pending",
            ...update,
          };
        }
        return { ...t, steps };
      }),
    })),

  systemState: null,
  setSystemState: (systemState) => set({ systemState }),

  privacySummary: {
    local_operations: 0,
    cloud_calls: 0,
    bytes_sent: 0,
    bytes_received: 0,
    fields_masked: 0,
    pii_blocked: 0,
  },
  updatePrivacy: (update) =>
    set((state) => ({
      privacySummary: { ...state.privacySummary, ...update },
    })),

  events: [],
  addEvent: (event) =>
    set((state) => ({ events: [event, ...state.events].slice(0, 200) })),

  commandInput: "",
  setCommandInput: (commandInput) => set({ commandInput }),
  isSubmitting: false,
  setIsSubmitting: (isSubmitting) => set({ isSubmitting }),

  connected: false,
  setConnected: (connected) => set({ connected }),
}));
