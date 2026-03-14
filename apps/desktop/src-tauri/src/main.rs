//! TELOS Desktop Shell — Tauri 2 backend.
//!
//! Provides IPC commands for the React frontend to communicate
//! with local services (orchestrator, scheduler, UIGraph).

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use reqwest::RequestBuilder;
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
    capture_engine: bool,
}

fn apply_auth(request: RequestBuilder, token: Option<String>) -> RequestBuilder {
    if let Some(token) = token.filter(|value| !value.trim().is_empty()) {
        request.bearer_auth(token)
    } else {
        request
    }
}

fn apply_provider(request: RequestBuilder, provider: Option<String>) -> RequestBuilder {
    if let Some(provider) = provider.filter(|value| !value.trim().is_empty()) {
        request.header("X-Telos-Provider", provider)
    } else {
        request
    }
}

async fn read_json_response(resp: reqwest::Response) -> Result<serde_json::Value, String> {
    let status = resp.status();
    let json: serde_json::Value = resp.json().await.map_err(|e| e.to_string())?;
    if status.is_success() {
        return Ok(json);
    }

    let message = json
        .get("error")
        .and_then(|value| value.as_str())
        .or_else(|| json.get("detail").and_then(|value| value.as_str()))
        .map(str::to_owned)
        .unwrap_or_else(|| format!("HTTP {}", status.as_u16()));
    Err(message)
}

/// IPC: Get current system state.
#[tauri::command]
async fn get_system_state(
    provider: Option<String>,
    token: Option<String>,
) -> Result<serde_json::Value, String> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(5))
        .build()
        .map_err(|e| e.to_string())?;

    let request = apply_auth(
        apply_provider(client.get("http://127.0.0.1:8080/system/state"), provider),
        token,
    );

    match request.send().await {
        Ok(resp) => read_json_response(resp).await,
        Err(e) => Err(format!("Orchestrator unreachable: {}", e)),
    }
}

/// IPC: Submit a task.
#[tauri::command]
async fn submit_task(
    task: String,
    provider: Option<String>,
    token: Option<String>,
) -> Result<serde_json::Value, String> {
    if task.is_empty() || task.len() > 10_000 {
        return Err("Task must be 1-10000 characters".into());
    }

    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(30))
        .build()
        .map_err(|e| e.to_string())?;

    let body = serde_json::json!({"task": task});
    let request = apply_auth(
        apply_provider(
            client.post("http://127.0.0.1:8080/task").json(&body),
            provider,
        ),
        token,
    );

    match request.send().await {
        Ok(resp) => read_json_response(resp).await,
        Err(e) => Err(format!("Failed to submit task: {}", e)),
    }
}

/// IPC: Get task list.
#[tauri::command]
async fn get_tasks(token: Option<String>) -> Result<serde_json::Value, String> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(5))
        .build()
        .map_err(|e| e.to_string())?;

    match apply_auth(client.get("http://127.0.0.1:8080/tasks"), token)
        .send()
        .await
    {
        Ok(resp) => read_json_response(resp).await,
        Err(e) => Err(format!("Failed to get tasks: {}", e)),
    }
}

/// IPC: Get privacy summary.
#[tauri::command]
async fn get_privacy_summary(
    provider: Option<String>,
    token: Option<String>,
) -> Result<serde_json::Value, String> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(5))
        .build()
        .map_err(|e| e.to_string())?;

    let request = apply_auth(
        apply_provider(
            client.get("http://127.0.0.1:8080/privacy/summary"),
            provider,
        ),
        token,
    );

    match request.send().await {
        Ok(resp) => read_json_response(resp).await,
        Err(e) => Err(format!("Failed to get privacy summary: {}", e)),
    }
}

/// IPC: Get scheduled jobs.
#[tauri::command]
async fn get_scheduled_jobs(token: Option<String>) -> Result<serde_json::Value, String> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(5))
        .build()
        .map_err(|e| e.to_string())?;

    match apply_auth(client.get("http://127.0.0.1:8081/jobs"), token)
        .send()
        .await
    {
        Ok(resp) => read_json_response(resp).await,
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
