use telos_delta_engine::server::start_server;

#[tokio::main]
async fn main() {
    println!("Starting TELOS Delta Engine & Capture Service...");
    
    // In a real scenario we could read this from env vars, but hardcode 8084 for now
    let port_str = std::env::var("CAPTURE_ENGINE_PORT").unwrap_or_else(|_| "8084".to_string());
    let port: u16 = port_str.parse().unwrap_or(8084);

    start_server(port).await;
}
