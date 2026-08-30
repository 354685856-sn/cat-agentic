use serde::Serialize;

mod transport;

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct PlatformInfo {
    os: String,
    arch: String,
    path_separator: String,
}

#[tauri::command]
fn platform_info() -> PlatformInfo {
    PlatformInfo {
        os: std::env::consts::OS.to_owned(),
        arch: std::env::consts::ARCH.to_owned(),
        path_separator: std::path::MAIN_SEPARATOR.to_string(),
    }
}

#[tauri::command]
fn app_server_transport_status() -> transport::TransportStatus {
    transport::TransportStatus::NotConfigured
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![platform_info, app_server_transport_status])
        .run(tauri::generate_context!())
        .expect("error while running Cat Codex");
}
