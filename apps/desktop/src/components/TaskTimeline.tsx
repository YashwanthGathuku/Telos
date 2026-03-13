/**
 * TELOS Task Timeline — live execution feed.
 * Shows all tasks with their status, steps, and progression.
 */

import { useTelosStore } from "../store";
import type { TaskRecord, TaskStatus } from "../store";
import { Clock, CheckCircle, XCircle, Loader2, ArrowRight } from "lucide-react";

const STATUS_STYLES: Record<TaskStatus, { color: string; icon: typeof Clock }> = {
  pending: { color: "text-telos-text-muted", icon: Clock },
  routing: { color: "text-telos-accent", icon: Loader2 },
  executing: { color: "text-telos-warning", icon: Loader2 },
  completed: { color: "text-telos-success", icon: CheckCircle },
  failed: { color: "text-telos-danger", icon: XCircle },
  cancelled: { color: "text-telos-text-muted", icon: XCircle },
};

function TaskCard({ task }: { task: TaskRecord }) {
  const style = STATUS_STYLES[task.status] ?? STATUS_STYLES.pending;
  const Icon = style.icon;

  return (
    <div className="bg-telos-bg border border-telos-border rounded-lg p-3 mb-2">
      {/* Header */}
      <div className="flex items-start gap-2 mb-2">
        <Icon
          size={16}
          className={`${style.color} mt-0.5 shrink-0 ${
            task.status === "executing" || task.status === "routing"
              ? "animate-spin"
              : ""
          }`}
        />
        <div className="flex-1 min-w-0">
          <div className="text-sm text-telos-text truncate">{task.task}</div>
          <div className="text-[10px] text-telos-text-muted font-mono mt-0.5">
            {task.id} · {new Date(task.created_at).toLocaleTimeString()}
          </div>
        </div>
        <span
          className={`text-[10px] font-mono px-2 py-0.5 rounded ${style.color} bg-current/10`}
          style={{ backgroundColor: "rgba(255,255,255,0.05)" }}
        >
          {task.status.toUpperCase()}
        </span>
      </div>

      {/* Steps */}
      {task.steps.length > 0 && (
        <div className="flex items-center gap-1 mt-2 overflow-x-auto">
          {task.steps.map((step, i) => {
            return (
              <div key={i} className="flex items-center gap-1">
                {i > 0 && <ArrowRight size={10} className="text-telos-text-muted shrink-0" />}
                <div
                  className={`text-[10px] font-mono px-2 py-0.5 rounded border shrink-0 ${
                    step.status === "completed"
                      ? "border-telos-success/30 text-telos-success"
                      : step.status === "executing"
                      ? "border-telos-warning/30 text-telos-warning"
                      : "border-telos-border text-telos-text-muted"
                  }`}
                >
                  {step.agent.toUpperCase()}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Privacy summary */}
      {task.privacy_summary && (
        <div className="flex gap-3 mt-2 text-[10px] font-mono text-telos-text-muted">
          <span>LOCAL: {task.privacy_summary.local_operations}</span>
          <span>CLOUD: {task.privacy_summary.cloud_calls}</span>
          <span>MASKED: {task.privacy_summary.fields_masked}</span>
          <span>PII: {task.privacy_summary.pii_blocked}</span>
        </div>
      )}

      {/* Error */}
      {task.error && (
        <div className="text-xs text-telos-danger mt-2 font-mono truncate">
          {task.error}
        </div>
      )}
    </div>
  );
}

export default function TaskTimeline() {
  const { tasks } = useTelosStore();

  return (
    <div className="bg-telos-surface border border-telos-border rounded-lg p-3 h-full flex flex-col">
      <div className="text-[10px] text-telos-text-muted font-mono uppercase tracking-wider mb-2 flex items-center gap-2">
        <Clock size={12} />
        TASK TIMELINE
        {tasks.length > 0 && (
          <span className="text-telos-accent">({tasks.length})</span>
        )}
      </div>
      <div className="flex-1 overflow-y-auto">
        {tasks.length === 0 ? (
          <div className="flex items-center justify-center h-full text-sm text-telos-text-muted">
            No tasks yet. Enter a command above.
          </div>
        ) : (
          tasks.map((task) => <TaskCard key={task.id} task={task} />)
        )}
      </div>
    </div>
  );
}
