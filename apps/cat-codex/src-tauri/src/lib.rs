use serde::Serialize;
use std::path::{Path, PathBuf};
use std::process::Command;

mod transport;

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct PlatformInfo {
    os: String,
    arch: String,
    path_separator: String,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct WorkspaceSnapshot {
    root: String,
    files: Vec<String>,
    file_count: usize,
    directory_count: usize,
    branch: Option<String>,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct WorkspaceFileContent {
    path: String,
    content: String,
    truncated: bool,
}

fn workspace_file_path(workspace: &str, relative: &str) -> Result<(PathBuf, String), String> {
    let root = PathBuf::from(workspace).canonicalize().map_err(|error| format!("无法定位工作区：{error}"))?;
    let candidate = root.join(relative);
    let path = candidate.canonicalize().map_err(|error| format!("无法读取文件：{error}"))?;
    if !path.starts_with(&root) { return Err("只能读取工作区内的文件".to_owned()); }
    if !path.is_file() { return Err("目标不是文件".to_owned()); }
    let display = path.strip_prefix(&root).map_err(|_| "无法计算文件路径".to_owned())?.to_string_lossy().replace('\\', "/");
    Ok((path, display))
}

#[tauri::command]
fn read_workspace_file(workspace: String, relative: String) -> Result<WorkspaceFileContent, String> {
    let (path, display) = workspace_file_path(&workspace, &relative)?;
    let bytes = std::fs::read(&path).map_err(|error| format!("无法读取文件：{error}"))?;
    const MAX_BYTES: usize = 512 * 1024;
    let truncated = bytes.len() > MAX_BYTES;
    let content = String::from_utf8_lossy(&bytes[..bytes.len().min(MAX_BYTES)]).into_owned();
    Ok(WorkspaceFileContent { path: display, content, truncated })
}

fn collect_workspace(path: &Path, root: &Path, files: &mut Vec<String>, directories: &mut usize) -> Result<(), String> {
    let entries = std::fs::read_dir(path).map_err(|error| format!("无法读取工作区：{error}"))?;
    for entry in entries {
        let entry = entry.map_err(|error| format!("无法读取工作区条目：{error}"))?;
        let name = entry.file_name();
        if name == ".git" || name == "node_modules" || name == "target" || name == ".DS_Store" { continue; }
        let entry_path = entry.path();
        if entry_path.is_dir() {
            *directories += 1;
            collect_workspace(&entry_path, root, files, directories)?;
        } else if entry_path.is_file() {
            if let Ok(relative) = entry_path.strip_prefix(root) { files.push(relative.to_string_lossy().replace('\\', "/")); }
        }
    }
    Ok(())
}

#[tauri::command]
fn workspace_snapshot(path: String) -> Result<WorkspaceSnapshot, String> {
    let root = PathBuf::from(&path);
    if !root.is_dir() { return Err("工作区目录不存在".to_owned()); }
    let mut files = Vec::new();
    let mut directories = 0;
    collect_workspace(&root, &root, &mut files, &mut directories)?;
    files.sort();
    let branch = Command::new("git").args(["-C", &path, "branch", "--show-current"]).output().ok().and_then(|output| {
        let value = String::from_utf8_lossy(&output.stdout).trim().to_owned();
        (!value.is_empty()).then_some(value)
    });
    Ok(WorkspaceSnapshot { root: path, file_count: files.len(), directory_count: directories, files, branch })
}

#[tauri::command]
fn open_workspace(path: String) -> Result<(), String> {
    let root = PathBuf::from(&path);
    if !root.is_dir() { return Err("工作区目录不存在".to_owned()); }
    #[cfg(target_os = "macos")]
    let result = Command::new("open").arg(&root).status();
    #[cfg(target_os = "windows")]
    let result = Command::new("explorer").arg(&root).status();
    #[cfg(target_os = "linux")]
    let result = Command::new("xdg-open").arg(&root).status();
    result.map_err(|error| format!("无法打开工作区：{error}"))?.success().then_some(()).ok_or_else(|| "系统未能打开工作区".to_owned())
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
fn app_server_start(app: tauri::AppHandle, state: tauri::State<'_, transport::AppServerState>, cwd: Option<String>) -> Result<transport::TransportStatus, String> { transport::start(app, state, cwd) }

#[tauri::command]
fn pick_workspace() -> Option<String> {
    rfd::FileDialog::new().set_title("Choose a Cat Codex workspace").pick_folder().map(|path| path.to_string_lossy().into_owned())
}

#[tauri::command]
fn app_server_send(state: tauri::State<'_, transport::AppServerState>, message: String) -> Result<(), String> { transport::send(state, message) }

#[tauri::command]
fn app_server_stop(state: tauri::State<'_, transport::AppServerState>) -> Result<transport::TransportStatus, String> { transport::stop(state) }

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(transport::AppServerState::default())
        .invoke_handler(tauri::generate_handler![platform_info, pick_workspace, workspace_snapshot, read_workspace_file, open_workspace, app_server_transport_status, app_server_start, app_server_send, app_server_stop])
        .run(tauri::generate_context!())
        .expect("error while running Cat Codex");
}
