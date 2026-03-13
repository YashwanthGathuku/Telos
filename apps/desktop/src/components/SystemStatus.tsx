/**
 * TELOS System Status — service health and provider info.
 */

import { useTelosStore } from "../store";
import { Activity, CheckCircle, XCircle } from "lucide-react";

export default function SystemStatus() {
  const { systemState } = useTelosStore();

  const services = [
    { name: "Orchestrator", port: 8080, up: systemState?.services.orchestrator ?? false },
    { name: "Scheduler", port: 8081, up: systemState?.services.scheduler ?? false },
    { name: "UIGraph", port: 8083, up: systemState?.services.uigraph ?? false },
  ];

  return (
    <div className="bg-telos-surface border border-telos-border rounded-lg p-3 h-full">
      <div className="text-[10px] text-telos-text-muted font-mono uppercase tracking-wider mb-2 flex items-center gap-2">
        <Activity size={12} />
        SYSTEM STATUS
      </div>
      <div className="flex gap-3">
        {services.map((svc) => (
          <div
            key={svc.name}
            className="flex items-center gap-1.5"
          >
            {svc.up ? (
              <CheckCircle size={12} className="text-telos-success" />
            ) : (
              <XCircle size={12} className="text-telos-danger" />
            )}
            <span className="text-[10px] font-mono text-telos-text-dim">
              {svc.name}
            </span>
            <span className="text-[9px] font-mono text-telos-text-muted">
              :{svc.port}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
