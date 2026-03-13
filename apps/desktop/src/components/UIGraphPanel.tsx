/**
 * TELOS UIGraph Panel — displays the current application context
 * from Windows UI Automation structured extraction.
 */

import { useTelosStore } from "../store";
import { Monitor, Layers } from "lucide-react";

export default function UIGraphPanel() {
  const { events } = useTelosStore();

  // Extract UIGraph events from the event stream
  const uigraphEvents = events
    .filter((e) => e.event_type === "uigraph_update" || e.event_type === "step_update")
    .slice(0, 10);

  return (
    <div className="bg-telos-surface border border-telos-border rounded-lg p-3 h-full flex flex-col">
      <div className="text-[10px] text-telos-text-muted font-mono uppercase tracking-wider mb-2 flex items-center gap-2">
        <Monitor size={12} />
        UIGRAPH — APP CONTEXT
      </div>
      <div className="flex-1 overflow-y-auto">
        {uigraphEvents.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-telos-text-muted">
            <Layers size={24} className="mb-2 opacity-30" />
            <span className="text-xs">No active UI context</span>
            <span className="text-[10px] mt-1">UIA snapshots will appear here during task execution</span>
          </div>
        ) : (
          uigraphEvents.map((event, i) => (
            <div
              key={i}
              className="bg-telos-bg border border-telos-border rounded p-2 mb-1 font-data"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] text-telos-accent">
                  {event.event_type.toUpperCase()}
                </span>
                <span className="text-[9px] text-telos-text-muted">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <div className="text-[10px] text-telos-text-dim truncate">
                {event.payload.agent ? (
                  <span className="text-telos-accent mr-1">
                    [{String(event.payload.agent).toUpperCase()}]
                  </span>
                ) : null}
                {event.payload.status ? String(event.payload.status) : null}
                {event.payload.result ? (
                  <span className="text-telos-text-muted ml-1">
                    {JSON.stringify(event.payload.result).slice(0, 80)}
                  </span>
                ) : null}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
