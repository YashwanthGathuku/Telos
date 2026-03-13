/**
 * TELOS Mission Control — main application shell.
 *
 * Premium operations dashboard layout:
 * ┌─────────────────────────────────────────┐
 * │  Top Bar (TELOS branding + status)       │
 * ├──────────────────┬──────────────────────┤
 * │  Command Bar     │  System Status       │
 * ├──────────────────┼──────────────────────┤
 * │  Task Timeline   │  Agent Status Grid   │
 * │                  ├──────────────────────┤
 * │                  │  Privacy Monitor     │
 * ├──────────────────┼──────────────────────┤
 * │  UIGraph Panel   │  Scheduler Panel     │
 * └──────────────────┴──────────────────────┘
 */

import { useState, useEffect } from "react";
import { useTelosStore } from "./store";
import { connectEventStream, getSystemState } from "./api";
import TopBar from "./components/TopBar";
import CommandBar from "./components/CommandBar";
import TaskTimeline from "./components/TaskTimeline";
import AgentGrid from "./components/AgentGrid";
import PrivacyMonitor from "./components/PrivacyMonitor";
import SystemStatus from "./components/SystemStatus";
import UIGraphPanel from "./components/UIGraphPanel";
import SchedulerPanel from "./components/SchedulerPanel";
import SettingsModal from "./components/SettingsModal";
import OnboardingWizard from "./components/OnboardingWizard";

import type { TaskRecord, TaskStep, SystemState, PrivacySummary, TelosEvent } from "./store";

function App() {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const {
    setConnected,
    addEvent,
    addTask,
    updateTask,
    updateTaskStep,
    updatePrivacy,
    setSystemState,
  } = useTelosStore();

  useEffect(() => {
    // ... preexisting effect logic unchanged...
    const disconnect = connectEventStream(
      (event) => {
        addEvent(event as TelosEvent);

        switch (event.event_type) {
          case "task_created":
            addTask({
              id: event.task_id ?? "",
              task: (event.payload.task as string) ?? "",
              status: (event.payload.status as TaskRecord["status"]) ?? "pending",
              created_at: event.timestamp,
              updated_at: event.timestamp,
              steps: [],
            });
            break;
          case "task_status":
            if (event.task_id) {
              updateTask(event.task_id, {
                status: event.payload.status as TaskRecord["status"],
                error: event.payload.error as string | undefined,
                updated_at: event.timestamp,
              });
            }
            break;
          case "step_update":
            if (event.task_id && typeof event.payload.step_index === "number") {
              updateTaskStep(
                event.task_id,
                event.payload.step_index as number,
                {
                  status: (event.payload.status as TaskStep["status"]) ?? "executing",
                  ...(event.payload.status === "completed" && { completed_at: event.timestamp }),
                  ...(event.payload.status === "executing" && { started_at: event.timestamp }),
                },
              );
            }
            break;
          case "privacy_update":
            updatePrivacy(event.payload as unknown as Partial<PrivacySummary>);
            break;
          case "system_state":
            setSystemState(event.payload as unknown as SystemState);
            break;
        }
      },
      setConnected
    );

    // Poll system state every 5 seconds
    const pollState = async () => {
      try {
        const state = (await getSystemState()) as SystemState;
        setSystemState(state);
        setConnected(true);
      } catch {
        setConnected(false);
      }
    };
    pollState();
    const interval = setInterval(pollState, 5000);

    return () => {
      disconnect();
      clearInterval(interval);
    };
  }, [addEvent, addTask, updateTask, updateTaskStep, updatePrivacy, setSystemState, setConnected]);

  return (
    <div className="h-screen w-screen overflow-hidden bg-telos-bg flex flex-col">
      <OnboardingWizard />
      <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
      <TopBar onOpenSettings={() => setIsSettingsOpen(true)} />
      <div className="flex-1 grid grid-cols-12 grid-rows-[auto_1fr_1fr] gap-2 p-2 overflow-hidden">
        {/* Row 1: Command + System Status */}
        <div className="col-span-8">
          <CommandBar />
        </div>
        <div className="col-span-4">
          <SystemStatus />
        </div>

        {/* Row 2: Timeline + Agent Grid & Privacy */}
        <div className="col-span-5 row-span-2 overflow-hidden">
          <TaskTimeline />
        </div>
        <div className="col-span-4">
          <AgentGrid />
        </div>
        <div className="col-span-3">
          <PrivacyMonitor />
        </div>

        {/* Row 3: UIGraph + Scheduler */}
        <div className="col-span-4">
          <UIGraphPanel />
        </div>
        <div className="col-span-3">
          <SchedulerPanel />
        </div>
      </div>
    </div>
  );
}

export default App;
