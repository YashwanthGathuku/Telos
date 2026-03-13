/**
 * TELOS Privacy Monitor — real-time privacy metrics dashboard.
 * Shows local vs cloud processing, egress bytes, PII blocked.
 */

import { useTelosStore } from "../store";
import { Shield, Lock, Eye, Globe, AlertTriangle } from "lucide-react";

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export default function PrivacyMonitor() {
  const { privacySummary } = useTelosStore();

  const totalOps = privacySummary.local_operations + privacySummary.cloud_calls;
  const localPercent = totalOps > 0
    ? Math.round((privacySummary.local_operations / totalOps) * 100)
    : 100;

  return (
    <div className="bg-telos-surface border border-telos-border rounded-lg p-3 h-full flex flex-col">
      <div className="text-[10px] text-telos-text-muted font-mono uppercase tracking-wider mb-2 flex items-center gap-2">
        <Shield size={12} className="text-telos-success" />
        PRIVACY MONITOR
      </div>

      {/* Local vs Cloud gauge */}
      <div className="mb-3">
        <div className="flex justify-between text-[10px] font-mono mb-1">
          <span className="text-telos-success">LOCAL {localPercent}%</span>
          <span className="text-telos-warning">CLOUD {100 - localPercent}%</span>
        </div>
        <div className="h-2 bg-telos-bg rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-telos-success to-telos-success/70 transition-all"
            style={{ width: `${localPercent}%` }}
          />
        </div>
      </div>

      {/* Metrics */}
      <div className="space-y-2 flex-1">
        <MetricRow
          icon={<Lock size={12} className="text-telos-success" />}
          label="LOCAL OPS"
          value={String(privacySummary.local_operations)}
        />
        <MetricRow
          icon={<Globe size={12} className="text-telos-warning" />}
          label="CLOUD CALLS"
          value={String(privacySummary.cloud_calls)}
        />
        <MetricRow
          icon={<Eye size={12} className="text-telos-accent" />}
          label="FIELDS MASKED"
          value={String(privacySummary.fields_masked)}
        />
        <MetricRow
          icon={<AlertTriangle size={12} className="text-telos-danger" />}
          label="PII BLOCKED"
          value={String(privacySummary.pii_blocked)}
          highlight={privacySummary.pii_blocked > 0}
        />
        <div className="border-t border-telos-border pt-2 mt-2">
          <MetricRow
            icon={<Globe size={12} className="text-telos-text-muted" />}
            label="BYTES SENT"
            value={formatBytes(privacySummary.bytes_sent)}
          />
          <MetricRow
            icon={<Globe size={12} className="text-telos-text-muted" />}
            label="BYTES RECV"
            value={formatBytes(privacySummary.bytes_received)}
          />
        </div>
      </div>
    </div>
  );
}

function MetricRow({
  icon,
  label,
  value,
  highlight = false,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-1.5">
        {icon}
        <span className="text-[10px] font-mono text-telos-text-muted">{label}</span>
      </div>
      <span
        className={`text-xs font-mono font-bold ${
          highlight ? "text-telos-danger" : "text-telos-text"
        }`}
      >
        {value}
      </span>
    </div>
  );
}
