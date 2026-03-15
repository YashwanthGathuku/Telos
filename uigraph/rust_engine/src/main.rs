use telos_delta_engine::server::start_server;

#[tokio::main]
async fn main() {
    println!("Starting TELOS Delta Engine & Capture Service...");

    // Delta Engine port — configurable via DELTA_ENGINE_PORT env var
    let port_str = std::env::var("DELTA_ENGINE_PORT").unwrap_or_else(|_| "8084".to_string());
    let port: u16 = port_str.parse().unwrap_or(8084);

    start_server(port).await;
}
