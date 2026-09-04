use serde::Serialize;
use std::io::{BufRead, BufReader, Write};
use std::process::{Child, ChildStdin, Command, Stdio};
use std::sync::Mutex;
use tauri::{AppHandle, Emitter, Manager, State};

/// Platform-neutral transport choices. Native stdio/Unix implementations can
/// be added without changing the React client contract.
#[derive(Debug, Serialize)]
#[serde(rename_all = "kebab-case")]
pub enum TransportStatus {
    NotConfigured,
    Running,
    Stopped,
}

struct RunningProcess {
    child: Child,
    stdin: ChildStdin,
}

pub struct AppServerState {
    process: Mutex<Option<RunningProcess>>,
}

impl Default for AppServerState {
    fn default() -> Self { Self { process: Mutex::new(None) } }
}

pub fn start(app: AppHandle, state: State<'_, AppServerState>) -> Result<TransportStatus, String> {
    let mut process = state.process.lock().map_err(|_| "App Server 状态锁不可用".to_owned())?;
    if process.is_some() { return Ok(TransportStatus::Running); }

    let codex = app.path().resource_dir().ok()
        .map(|directory| directory.join(if cfg!(windows) { "codex.exe" } else { "codex" }))
        .filter(|path| path.is_file());
    let mut command = codex.map(Command::new).unwrap_or_else(|| Command::new("codex"));
    let mut child = command
        .args(["app-server", "--stdio"])
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::inherit())
        .spawn()
        .map_err(|error| format!("无法启动 codex app-server: {error}"))?;
    let stdin = child.stdin.take().ok_or_else(|| "无法打开 App Server stdin".to_owned())?;
    let stdout = child.stdout.take().ok_or_else(|| "无法打开 App Server stdout".to_owned())?;
    let reader_app = app.clone();
    std::thread::spawn(move || {
        for line in BufReader::new(stdout).lines() {
            match line {
                Ok(message) if !message.trim().is_empty() => { let _ = reader_app.emit("app-server-message", message); }
                Ok(_) => {}
                Err(error) => { let _ = reader_app.emit("app-server-error", error.to_string()); break; }
            }
        }
        let _ = reader_app.emit("app-server-stopped", ());
    });
    *process = Some(RunningProcess { child, stdin });
    Ok(TransportStatus::Running)
}

pub fn status(state: State<'_, AppServerState>) -> TransportStatus {
    if state.process.lock().map(|process| process.is_some()).unwrap_or(false) { TransportStatus::Running } else { TransportStatus::NotConfigured }
}

pub fn send(state: State<'_, AppServerState>, message: String) -> Result<(), String> {
    serde_json::from_str::<serde_json::Value>(&message).map_err(|error| format!("非法 App Server JSON: {error}"))?;
    let mut process = state.process.lock().map_err(|_| "App Server 状态锁不可用".to_owned())?;
    let running = process.as_mut().ok_or_else(|| "App Server 尚未启动".to_owned())?;
    writeln!(running.stdin, "{message}").map_err(|error| format!("写入 App Server 失败: {error}"))?;
    running.stdin.flush().map_err(|error| format!("刷新 App Server 失败: {error}"))
}

pub fn stop(state: State<'_, AppServerState>) -> Result<TransportStatus, String> {
    let mut process = state.process.lock().map_err(|_| "App Server 状态锁不可用".to_owned())?;
    if let Some(mut running) = process.take() { let _ = running.child.kill(); let _ = running.child.wait(); }
    Ok(TransportStatus::Stopped)
}
