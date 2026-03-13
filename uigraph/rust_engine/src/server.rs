use axum::{
    routing::post,
    Router, Json,
};
use serde::Serialize;
use std::net::SocketAddr;
use base64::{Engine as _, engine::general_purpose::STANDARD};

use crate::capture::capture_primary_screen;

#[derive(Serialize)]
struct CaptureResponse {
    image: String, // Base64 encoded PNG
}

#[derive(Serialize)]
struct ErrorResponse {
    error: String,
}

/// Start the Axum HTTP server on the given port.
pub async fn start_server(port: u16) {
    let app = Router::new()
        .route("/capture/screen", post(handle_capture))
        .route("/delta", post(handle_delta));

    let addr = SocketAddr::from(([127, 0, 0, 1], port));
    println!("Starting Rust capture engine at http://{}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

async fn handle_capture() -> Result<Json<CaptureResponse>, Json<ErrorResponse>> {
    println!("Received request to capture screen...");
    match capture_primary_screen() {
        Ok(png_bytes) => {
            let encoded = STANDARD.encode(&png_bytes);
            Ok(Json(CaptureResponse { image: encoded }))
        }
        Err(e) => {
            eprintln!("Capture failed: {}", e);
            Err(Json(ErrorResponse { error: e }))
        }
    }
}

use crate::{DeltaEngine, UISnapshot, UIChange};
use serde::Deserialize;

#[derive(Deserialize)]
struct DeltaRequest {
    old_snapshot: UISnapshot,
    new_snapshot: UISnapshot,
}

#[derive(Serialize)]
struct DeltaResponse {
    changes: Vec<UIChange>,
}

async fn handle_delta(Json(payload): Json<DeltaRequest>) -> Result<Json<DeltaResponse>, Json<ErrorResponse>> {
    println!("Received request to compute UI delta...");
    let mut engine = DeltaEngine::new();
    let changes = engine.compute_delta(&payload.old_snapshot, &payload.new_snapshot);
    Ok(Json(DeltaResponse { changes }))
}

