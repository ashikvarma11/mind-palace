//! Narrow local-only commands. The WebView never supplies file or executable paths.
use crate::{paths, worker::{Error, Worker}};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::sync::{Arc, Mutex};
use tokio::process::Child;

#[derive(Default)]
struct Supervisor { exiting: bool, child: Option<Arc<Mutex<Child>>> }
#[derive(Default)]
pub(crate) struct VaultState {
    worker: tokio::sync::Mutex<Option<Worker>>,
    supervisor: Mutex<Supervisor>,
}
#[derive(Serialize)]
pub(crate) struct Status { connected: bool, ai_enabled: bool }
fn unavailable() -> Error { Error { code: "VAULT_CLOSED", message: "Open the local vault first.", retryable: false } }
fn busy() -> Error { Error { code: "BUSY", message: "Another local operation is running. Wait for it to finish.", retryable: true } }
fn invalid() -> Error { Error { code: "VALIDATION_ERROR", message: "The conversation request is invalid or too large.", retryable: false } }

impl VaultState {
    pub(crate) fn shutdown(&self) {
        // This lock is independent of asynchronous request IO. Exit never waits
        // for a save or startup timeout, and can kill only this app's owned child.
        let mut state = self.supervisor.lock().unwrap_or_else(|e| e.into_inner());
        state.exiting = true;
        if let Some(child) = state.child.as_ref() {
            let mut child = child.lock().unwrap_or_else(|e| e.into_inner());
            let _ = child.start_kill();
        }
    }
    async fn call(&self, method: &str, params: Value) -> Result<Value, Error> {
        let mut worker = self.worker.try_lock().map_err(|_| busy())?;
        let result = worker.as_mut().ok_or_else(unavailable)?.request(method, params).await;
        if result.as_ref().is_err_and(|e| e.code == "WORKER_DISCONNECTED") { *worker = None; }
        result
    }
}

#[tauri::command]
pub(crate) async fn vault_status(state: tauri::State<'_, VaultState>) -> Result<Status, Error> {
    let worker = state.worker.try_lock().map_err(|_| busy())?;
    Ok(Status { connected: worker.as_ref().is_some_and(Worker::is_usable), ai_enabled: false })
}
#[tauri::command]
pub(crate) async fn vault_open(app: tauri::AppHandle, state: tauri::State<'_, VaultState>, create: bool) -> Result<Status, Error> {
    let mut worker = state.worker.try_lock().map_err(|_| busy())?;
    if worker.is_some() { return Err(Error { code: "CONFLICT", message: "A local vault is already open.", retryable: false }); }
    {
        let mut supervisor = state.supervisor.lock().map_err(|_| unavailable())?;
        if supervisor.exiting { return Err(unavailable()); }
        if let Some(child) = supervisor.child.as_ref() {
            if child.lock().map_err(|_| unavailable())?.try_wait().map_err(|_| unavailable())?.is_none() {
                return Err(Error { code: "WORKER_SHUTDOWN_FAILED", message: "Close the previous worker before opening a vault.", retryable: false });
            }
        }
        supervisor.child = None;
    }
    let (bundle, vault) = paths::resolve(&app)?;
    if create {
        let parent = vault.parent().ok_or_else(invalid)?;
        std::fs::create_dir_all(parent).map_err(|_| invalid())?;
        crate::worker::no_links(parent)?;
    }
    let opened = Worker::start_supervised(&bundle, &vault, create, |child| {
        let mut supervisor = state.supervisor.lock().map_err(|_| unavailable())?;
        if supervisor.exiting { return Err(unavailable()); }
        supervisor.child = Some(child);
        Ok(())
    }).await?;
    *worker = Some(opened);
    Ok(Status { connected: true, ai_enabled: false })
}
#[tauri::command]
pub(crate) async fn vault_close(state: tauri::State<'_, VaultState>) -> Result<Status, Error> {
    let mut worker = state.worker.try_lock().map_err(|_| busy())?;
    if let Some(owned) = worker.as_mut() { owned.stop().await?; }
    // Startup can fail before a Worker reaches managed state. Retain and
    // confirm that registered child too, rather than silently dropping it.
    let registered = state.supervisor.lock().map_err(|_| unavailable())?.child.clone();
    if let Some(child) = registered { crate::worker::stop_owned(&child).await?; }
    *worker = None;
    state.supervisor.lock().map_err(|_| unavailable())?.child = None;
    Ok(Status { connected: false, ai_enabled: false })
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct Conversation { op_id: String, title: String, body: String, source_text: String }
fn identifier(value: &str) -> bool { uuid::Uuid::parse_str(value).is_ok_and(|id| id.to_string() == value) }
#[tauri::command]
pub(crate) async fn sessions_create(state: tauri::State<'_, VaultState>, input: Conversation) -> Result<Value, Error> {
    if !identifier(&input.op_id) || !(1..=200).contains(&input.title.chars().count())
        || input.body.chars().count() > 32768 || input.source_text.chars().count() > 65536 { return Err(invalid()); }
    state.call("sessions.create", serde_json::to_value(input).map_err(|_| invalid())?).await
}
#[tauri::command]
pub(crate) async fn sessions_list(state: tauri::State<'_, VaultState>, limit: u32, offset: u32) -> Result<Value, Error> {
    if !(1..=50).contains(&limit) || offset > 1000 { return Err(invalid()); }
    state.call("sessions.list", json!({"limit":limit,"offset":offset})).await
}
#[tauri::command]
pub(crate) async fn sessions_read(state: tauri::State<'_, VaultState>, id: String) -> Result<Value, Error> {
    if !identifier(&id) { return Err(invalid()); }
    state.call("sessions.read", json!({"id":id})).await
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn rejects_unknown_fields_and_noncanonical_identifiers() {
        assert!(!identifier("../secret"));
        assert!(!identifier("AABBCCDD-0000-0000-0000-000000000000"));
        assert!(identifier("aabbccdd-0000-0000-0000-000000000000"));
        assert!(serde_json::from_value::<Conversation>(json!({"op_id":"x","title":"t","body":"","source_text":"","path":"secret"})).is_err());
    }
    #[test]
    fn single_flight_and_exit_flag() {
        let state = VaultState::default();
        let _held = state.worker.try_lock().unwrap();
        assert!(state.worker.try_lock().is_err());
        state.shutdown();
        assert!(state.supervisor.lock().unwrap().exiting);
    }
}
