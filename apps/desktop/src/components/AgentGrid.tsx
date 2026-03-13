/**
 * TELOS Agent Status Grid — shows specialist agent states.
 */

import { useTelosStore } from "../store";
import { Brain, Eye, PenTool, ShieldCheck, Cpu } from "lucide-react";

const AGENTS = [
  { role: "planner", label: "PLANNER", icon: Brain, desc: "Task decomposition" },
  { role: "reader", label: "READER", icon: Eye, desc: "UIA extraction" },
  { role: "writer", label: "WRITER", icon: PenTool, desc: "Target execution" },
  { role: "verifier", label: "VERIFIER", icon: ShieldCheck, desc: "Result validation" },
  { role: "privacy", label: "PRIVACY", icon: Cpu, desc: "PII filter" },
];

export default function AgentGrid() {
  const { tasks } = useTelosStore();

  // Determine which agents are currently active
  const activeAgents = new Set<string>();
  for (const task of tasks) {
    if (task.status === "executing" || task.status === "routing") {
      for (const step of task.steps) {
        if (step.status === "executing") {
          activeAgents.add(step.agent);
        }
      }
    }
  }

  return (
    <div className="bg-telos-surface border border-telos-border rounded-lg p-3 h-full">
      <div className="text-[10px] text-telos-text-muted font-mono uppercase tracking-wider mb-2 flex items-center gap-2">
        <Cpu size={12} />
        AGENT STATUS
      </div>
      <div className="grid grid-cols-3 gap-2">
        {AGENTS.map(({ role, label, icon: Icon, desc }) => {
          const isActive = activeAgents.has(role);
          return (
            <div
              key={role}
              className={`border rounded-lg p-2 transition-all ${
                isActive
                  ? "border-telos-accent/50 bg-telos-accent/10 glow-blue"
                  : "border-telos-border bg-telos-bg"
              }`}
            >
              <div className="flex items-center gap-1.5 mb-1">
                <Icon
                  size={14}
                  className={isActive ? "text-telos-accent" : "text-telos-text-muted"}
                />
                <span
                  className={`text-[10px] font-mono font-bold ${
                    isActive ? "text-telos-accent" : "text-telos-text-muted"
                  }`}
                >
                  {label}
                </span>
              </div>
              <div className="text-[9px] text-telos-text-muted">{desc}</div>
              <div className="mt-1">
                {isActive ? (
                  <div className="flex items-center gap-1">
                    <div className="w-1.5 h-1.5 rounded-full bg-telos-accent animate-telos-pulse" />
                    <span className="text-[9px] text-telos-accent font-mono">ACTIVE</span>
                  </div>
                ) : (
                  <span className="text-[9px] text-telos-text-muted font-mono">IDLE</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
