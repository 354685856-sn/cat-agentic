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
fn app_server_transport_status(state: tauri::State<'_, transport::AppServerState>) -> transport::TransportStatus {
    transport::status(state)
}

#[tauri::command]
fn app_server_start(app: tauri::AppHandle, state: tauri::State<'_, transport::AppServerState>) -> Result<transport::TransportStatus, String> { transport::start(app, state) }

#[tauri::command]
fn app_server_send(state: tauri::State<'_, transport::AppServerState>, message: String) -> Result<(), String> { transport::send(state, message) }

#[tauri::command]
fn app_server_stop(state: tauri::State<'_, transport::AppServerState>) -> Result<transport::TransportStatus, String> { transport::stop(state) }

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(transport::AppServerState::default())
        .invoke_handler(tauri::generate_handler![platform_info, app_server_transport_status, app_server_start, app_server_send, app_server_stop])
        .run(tauri::generate_context!())
        .expect("error while running Cat Codex");
}
