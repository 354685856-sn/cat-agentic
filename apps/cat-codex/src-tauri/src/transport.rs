use serde::Serialize;

/// Platform-neutral transport choices. Native stdio/Unix implementations can
/// be added without changing the React client contract.
#[derive(Debug, Serialize)]
#[serde(rename_all = "kebab-case")]
pub enum TransportStatus {
    NotConfigured,
}
