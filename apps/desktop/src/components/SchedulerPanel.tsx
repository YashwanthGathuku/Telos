/**
 * TELOS Scheduler Panel — displays scheduled/queued missions.
 */

import { useEffect, useState } from "react";
import { getScheduledJobs } from "../api";
import { Calendar } from "lucide-react";

interface Job {
  id: string;
  name: string;
  cron: string;
  task: string;
  enabled: boolean;
  last_run?: string;
}

export default function SchedulerPanel() {
  const [jobs, setJobs] = useState<Job[]>([]);

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const data = (await getScheduledJobs()) as Job[];
        setJobs(data);
      } catch {
        // Scheduler may not be running yet
      }
    };
    fetchJobs();
    const interval = setInterval(fetchJobs, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-telos-surface border border-telos-border rounded-lg p-3 h-full flex flex-col">
      <div className="text-[10px] text-telos-text-muted font-mono uppercase tracking-wider mb-2 flex items-center gap-2">
        <Calendar size={12} />
        SCHEDULER
        {jobs.length > 0 && (
          <span className="text-telos-accent">({jobs.length})</span>
        )}
      </div>
      <div className="flex-1 overflow-y-auto">
        {jobs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-telos-text-muted">
            <Calendar size={24} className="mb-2 opacity-30" />
            <span className="text-xs">No scheduled missions</span>
          </div>
        ) : (
          jobs.map((job) => (
            <div
              key={job.id}
              className="bg-telos-bg border border-telos-border rounded p-2 mb-1"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs text-telos-text">{job.name}</span>
                <span
                  className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${
                    job.enabled
                      ? "bg-telos-success/20 text-telos-success"
                      : "bg-telos-border text-telos-text-muted"
                  }`}
                >
                  {job.enabled ? "ACTIVE" : "PAUSED"}
                </span>
              </div>
              <div className="text-[10px] font-mono text-telos-text-muted mt-0.5">
                CRON: {job.cron}
              </div>
              <div className="text-[10px] text-telos-text-dim truncate mt-0.5">
                {job.task}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
