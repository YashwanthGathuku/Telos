//! TELOS Desktop Shell — Tauri 2 backend.
//!
//! Provides IPC commands for the React frontend to communicate
//! with local services (orchestrator, scheduler, UIGraph).

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
struct SystemState {
    provider: String,
    provider_healthy: bool,
    privacy_mode: String,
    active_tasks: u32,
    services: ServiceState,
}

#[derive(Debug, Serialize, Deserialize)]
struct ServiceState {
    orchestrator: bool,
    scheduler: bool,
    uigraph: bool,
}

/// IPC: Get current system state.
#[tauri::command]
async fn get_system_state() -> Result<serde_json::Value, String> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(5))
        .build()
        .map_err(|e| e.to_string())?;

    match client.get("http://127.0.0.1:8080/system/state").send().await {
        Ok(resp) => {
            let json: serde_json::Value = resp.json().await.map_err(|e| e.to_string())?;
            Ok(json)
        }
        Err(e) => Err(format!("Orchestrator unreachable: {}", e)),
    }
}

/// IPC: Submit a task.
#[tauri::command]
async fn submit_task(task: String) -> Result<serde_json::Value, String> {
    if task.is_empty() || task.len() > 10_000 {
        return Err("Task must be 1-10000 characters".into());
    }

    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(30))
        .build()
        .map_err(|e| e.to_string())?;

    let body = serde_json::json!({"task": task});
    match client.post("http://127.0.0.1:8080/task").json(&body).send().await {
        Ok(resp) => {
            let json: serde_json::Value = resp.json().await.map_err(|e| e.to_string())?;
            Ok(json)
        }
        Err(e) => Err(format!("Failed to submit task: {}", e)),
    }
}

/// IPC: Get task list.
#[tauri::command]
async fn get_tasks() -> Result<serde_json::Value, String> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(5))
        .build()
        .map_err(|e| e.to_string())?;

    match client.get("http://127.0.0.1:8080/tasks").send().await {
        Ok(resp) => {
            let json: serde_json::Value = resp.json().await.map_err(|e| e.to_string())?;
            Ok(json)
        }
        Err(e) => Err(format!("Failed to get tasks: {}", e)),
    }
}

/// IPC: Get privacy summary.
#[tauri::command]
async fn get_privacy_summary() -> Result<serde_json::Value, String> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(5))
        .build()
        .map_err(|e| e.to_string())?;

    match client.get("http://127.0.0.1:8080/privacy/summary").send().await {
        Ok(resp) => {
            let json: serde_json::Value = resp.json().await.map_err(|e| e.to_string())?;
            Ok(json)
        }
        Err(e) => Err(format!("Failed to get privacy summary: {}", e)),
    }
}

/// IPC: Get scheduled jobs.
#[tauri::command]
async fn get_scheduled_jobs() -> Result<serde_json::Value, String> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(5))
        .build()
        .map_err(|e| e.to_string())?;

    match client.get("http://127.0.0.1:8081/jobs").send().await {
        Ok(resp) => {
            let json: serde_json::Value = resp.json().await.map_err(|e| e.to_string())?;
            Ok(json)
        }
        Err(e) => Err(format!("Scheduler unreachable: {}", e)),
    }
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            get_system_state,
            submit_task,
            get_tasks,
            get_privacy_summary,
            get_scheduled_jobs,
        ])
        .run(tauri::generate_context!())
        .expect("error while running TELOS");
}
