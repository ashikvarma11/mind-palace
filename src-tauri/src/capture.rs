//! Fixed capture executable/root only. Source scopes require explicit user input.
use crate::worker::{self, Error};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{path::PathBuf, process::Stdio, time::Duration};
use tauri::Manager;
use tokio::{io::{AsyncBufReadExt, AsyncReadExt, AsyncWriteExt, BufReader}, process::{Child, Command}, time::timeout};

const MANIFEST: &str = include_str!("../resources/memory-capture/worker-manifest.json");
#[derive(Default)]
pub(crate) struct CaptureState(tokio::sync::Mutex<()>);
fn invalid() -> Error { Error { code: "CAPTURE_UNAVAILABLE", message: "Capture setup is unavailable or invalid. Existing files were preserved.", retryable: false } }
fn busy() -> Error { Error { code: "BUSY", message: "Another capture operation is running. Existing files were preserved.", retryable: false } }
fn timed_out() -> Error { Error { code: "CAPTURE_TIMEOUT", message: "The capture operation exceeded its deadline. A write may have completed; inspect status before retrying.", retryable: false } }
fn process_failed() -> Error { Error { code: "CAPTURE_PROCESS_FAILED", message: "The capture receiver failed. Existing files were preserved; inspect status before retrying.", retryable: false } }

// Diagnostics are opt-in and restricted to an isolated debug probe. Never log
// request arguments, paths, source text or model output.
fn trace_stage(stage: &str, started: std::time::Instant) {
    #[cfg(debug_assertions)]
    if std::env::var("MP_CAPTURE_TIMING").as_deref() == Ok("1")
        && std::env::var("MP_NATIVE_PROBE_ID").ok().is_some_and(|value| uuid::Uuid::parse_str(&value).is_ok()) {
        eprintln!("MP_CAPTURE_STAGE {stage} {}", started.elapsed().as_millis());
    }
    #[cfg(not(debug_assertions))]
    let _ = (stage, started);
}

const OUTPUT_LIMIT: u64 = 64 * 1024 * 1024;

#[derive(Clone, Copy, Deserialize, Serialize)]
#[serde(rename_all = "kebab-case")]
pub(crate) enum Provider { ClaudeCode, Codex }
impl Provider { fn name(&self) -> &str { match self { Self::ClaudeCode => "claude-code", Self::Codex => "codex" } } }
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct Scope {
    provider: Provider, source_root: String, memory_roots: Vec<String>,
    enabled: bool, memory_enabled: bool, revision: String,
}
impl Scope {
    fn valid(&self) -> bool {
        let path = |value: &str| value.len() <= 4096 && PathBuf::from(value).is_absolute()
            && !value.chars().any(char::is_control);
        path(&self.source_root) && self.memory_roots.len() <= 32
            && self.memory_roots.iter().all(|value| path(value))
            && (!self.memory_enabled || !self.memory_roots.is_empty())
            && self.revision.len() == 64 && self.revision.bytes().all(|b| b.is_ascii_digit() || matches!(b, b'a'..=b'f'))
    }
}

fn resolve(app: &tauri::AppHandle) -> Result<(PathBuf, PathBuf), Error> {
    #[cfg(debug_assertions)]
    let bundle = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("resources/memory-capture");
    #[cfg(not(debug_assertions))]
    let bundle = app.path().resource_dir().map_err(|_| invalid())?.join("memory-capture");
    let mut root = app.path().local_data_dir().map_err(|_| invalid())?.join("MindPalace/capture");
    #[cfg(debug_assertions)]
    if let Some(value) = std::env::var_os("MP_NATIVE_PROBE_ID") {
        let value = value.to_str().ok_or_else(invalid)?;
        if uuid::Uuid::parse_str(value).map_err(|_| invalid())?.to_string() != value { return Err(invalid()); }
        root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).parent().ok_or_else(invalid)?
            .join(".tools/native/verification").join(format!("capture-{value}"));
    }
    worker::no_links(&root)?;
    Ok((bundle, root))
}

async fn prepare(app: tauri::AppHandle) -> Result<Child, Error> {
    // Filesystem checks and Windows CreateProcess can block. Keep them off the
    // command executor so the outer deadline and WebView stay responsive.
    // A late detached task result drops its kill-on-drop child without input.
    tokio::task::spawn_blocking(move || {
        let started = std::time::Instant::now();
        let (bundle, root) = resolve(&app)?;
        trace_stage("resolve", started);
        let started = std::time::Instant::now();
        let executable = worker::verify_resources(&bundle, MANIFEST, "memory-capture.exe")
            .map_err(|_| Error { code: "CAPTURE_RESOURCES_INVALID", message: "The bundled capture receiver is missing or changed.", retryable: false })?;
        trace_stage("resources", started);
        let started = std::time::Instant::now();
        let mut command = Command::new(executable);
        command.arg("--app-control-root").arg(root).current_dir(&bundle)
            .kill_on_drop(true).env_clear().stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::null());
        #[cfg(windows)]
        command.creation_flags(0x08000000);
        for name in ["SystemRoot", "WINDIR", "TEMP", "TMP"] {
            if let Some(value) = std::env::var_os(name) { command.env(name, value); }
        }
        let result = command.spawn().map_err(|_| process_failed());
        trace_stage("spawn", started);
        result
    }).await.map_err(|_| invalid())?
}

async fn call(app: &tauri::AppHandle, request: Value) -> Result<Value, Error> {
    let mut request_bytes = serde_json::to_vec(&request).map_err(|_| invalid())?;
    if request_bytes.len() >= 65536 { return Err(invalid()); }
    request_bytes.push(b'\n');
    let operation = async {
        let started = std::time::Instant::now();
        let mut child = prepare(app.clone()).await?;
        trace_stage("prepare", started);
        let started = std::time::Instant::now();
        let mut input = child.stdin.take().ok_or_else(invalid)?;
        input.write_all(&request_bytes).await.map_err(|_| invalid())?;
        input.shutdown().await.map_err(|_| invalid())?;
        drop(input);
        trace_stage("write", started);
        let started = std::time::Instant::now();
        let output = child.stdout.take().ok_or_else(invalid)?;
        let mut data = Vec::new();
        BufReader::new(output).take(OUTPUT_LIMIT + 1).read_until(b'\n', &mut data).await.map_err(|_| invalid())?;
        trace_stage("frame", started);
        if data.len() as u64 > OUTPUT_LIMIT || !data.ends_with(b"\n") { return Err(invalid()); }
        let started = std::time::Instant::now();
        if !child.wait().await.map_err(|_| process_failed())?.success() { return Err(process_failed()); }
        trace_stage("exit", started);
        serde_json::from_slice(&data).map_err(|_| Error { code: "CAPTURE_RESPONSE_INVALID", message: "The capture receiver returned invalid data.", retryable: false })
    };
    match timeout(Duration::from_secs(30), operation).await {
        Ok(result) => result,
        Err(_) => Err(timed_out()),
    }
}

#[tauri::command]
pub(crate) async fn capture_status(app: tauri::AppHandle, state: tauri::State<'_, CaptureState>) -> Result<Value, Error> {
    // Connections can open while automatic vault sync reads the same status.
    // This read may wait; no uncertain mutation is repeated or enqueued.
    let read = async {
        let _lock = state.0.lock().await;
        call(&app, json!({"method":"status"})).await
    };
    timeout(Duration::from_secs(30), read).await.map_err(|_| timed_out())?
}
#[tauri::command]
pub(crate) async fn capture_configure(app: tauri::AppHandle, state: tauri::State<'_, CaptureState>, input: Scope) -> Result<Value, Error> {
    if !input.valid() { return Err(invalid()); }
    let _lock = state.0.try_lock().map_err(|_| busy())?;
    call(&app, json!({"method":"configure","provider":input.provider.name(),"source_root":input.source_root,
        "memory_roots":input.memory_roots,"enabled":input.enabled,"memory_enabled":input.memory_enabled,"revision":input.revision})).await
}
#[tauri::command]
pub(crate) async fn capture_index(app: tauri::AppHandle, state: tauri::State<'_, CaptureState>) -> Result<Value, Error> {
    let _lock = state.0.try_lock().map_err(|_| busy())?;
    call(&app, json!({"method":"index"})).await
}

#[tauri::command]
pub(crate) async fn capture_recover(app: tauri::AppHandle, state: tauri::State<'_, CaptureState>) -> Result<Value, Error> {
    let _lock = state.0.try_lock().map_err(|_| busy())?;
    call(&app, json!({"method":"recover"})).await
}
#[tauri::command]
pub(crate) async fn capture_cleanup(app: tauri::AppHandle, state: tauri::State<'_, CaptureState>) -> Result<Value, Error> {
    let _lock = state.0.try_lock().map_err(|_| busy())?;
    call(&app, json!({"method":"cleanup"})).await
}
#[tauri::command]
pub(crate) async fn capture_history_preview(app: tauri::AppHandle, state: tauri::State<'_, CaptureState>) -> Result<Value, Error> {
    let _lock = state.0.try_lock().map_err(|_| busy())?;
    call(&app, json!({"method":"history-preview"})).await
}
#[tauri::command]
pub(crate) async fn capture_history_import(app: tauri::AppHandle, state: tauri::State<'_, CaptureState>, preview_id: String, offset: u32) -> Result<Value, Error> {
    if offset > 1000 || !uuid::Uuid::parse_str(&preview_id).is_ok_and(|value| value.to_string() == preview_id) { return Err(invalid()); }
    let _lock = state.0.try_lock().map_err(|_| busy())?;
    call(&app, json!({"method":"history-import","preview_id":preview_id,"offset":offset})).await
}

#[derive(Deserialize)]
#[serde(rename_all = "kebab-case")]
pub(crate) enum HookAction { Status, Install, Remove }
impl HookAction { fn name(&self) -> &str { match self { Self::Status => "status", Self::Install => "install", Self::Remove => "remove" } } }
#[tauri::command]
pub(crate) async fn capture_codex_hook(app: tauri::AppHandle, state: tauri::State<'_, CaptureState>, action: HookAction) -> Result<Value, Error> {
    let _lock = state.0.try_lock().map_err(|_| busy())?;
    let home = match std::env::var_os("CODEX_HOME") {
        Some(value) => PathBuf::from(value),
        None => app.path().home_dir().map_err(|_| invalid())?.join(".codex"),
    };
    if !home.is_absolute() { return Err(invalid()); }
    worker::no_links(&home)?;
    call(&app, json!({"method":"codex-hook","action":action.name(),"codex_home":home})).await
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Candidate {
    op_id: String, provider: Provider, session_key: String, session_id: String,
    title: String, source_text: String, selected_sha256: String, revisions: Vec<String>,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Plan { schema_version: u32, candidates: Vec<Candidate>, skipped: u32, memories_pending: u32, next_offset: Option<u32> }
#[derive(Serialize)]
pub(crate) struct ImportResult {
    schema_version: u32, created: u32, updated: u32, unchanged: u32,
    acknowledged: u32, skipped: u32, memories_pending: u32, next_offset: Option<u32>,
}
fn hex(value: &str) -> bool {
    value.len() == 64 && value.bytes().all(|b| b.is_ascii_digit() || matches!(b, b'a'..=b'f'))
}
impl Candidate {
    fn valid(&self) -> bool {
        let selected = format!("{:x}", Sha256::digest(self.source_text.as_bytes()));
        let key = format!("{:x}", Sha256::digest(format!("{}\0{}", self.provider.name(), self.session_id).as_bytes()));
        uuid::Uuid::parse_str(&self.op_id).is_ok_and(|value| value.to_string() == self.op_id)
            && self.session_key == key && hex(&self.session_key)
            && (1..=128).contains(&self.session_id.len())
            && self.session_id.bytes().all(|b| b.is_ascii_alphanumeric() || matches!(b, b'_' | b'-'))
            && (1..=200).contains(&self.title.chars().count()) && self.source_text.len() <= 20 * 1024 * 1024
            && self.selected_sha256 == selected && hex(&self.selected_sha256)
            && (1..=5000).contains(&self.revisions.len())
            && self.revisions.iter().all(|value| hex(value))
            && self.revisions.iter().any(|value| value == &self.selected_sha256)
            && self.revisions.iter().collect::<std::collections::BTreeSet<_>>().len() == self.revisions.len()
    }
}

#[tauri::command]
pub(crate) async fn capture_import(
    app: tauri::AppHandle, capture: tauri::State<'_, CaptureState>,
    vault: tauri::State<'_, crate::commands::VaultState>, offset: u32,
) -> Result<ImportResult, Error> {
    if offset > 5000 { return Err(invalid()); }
    let _lock = capture.0.try_lock().map_err(|_| busy())?;
    let value = call(&app, json!({"method":"import-plan","offset":offset})).await?;
    let plan: Plan = serde_json::from_value(value).map_err(|_| invalid())?;
    if plan.schema_version != 1 || plan.candidates.len() > 10 || plan.skipped > 5000
        || plan.memories_pending > 5000 || plan.next_offset.is_some_and(|next| next <= offset || next > 5000)
        || plan.candidates.iter().any(|candidate| !candidate.valid()) { return Err(invalid()); }
    let mut result = ImportResult { schema_version: 1, created: 0, updated: 0, unchanged: 0, acknowledged: 0,
        skipped: plan.skipped, memories_pending: plan.memories_pending, next_offset: plan.next_offset };
    for candidate in plan.candidates {
        let receipt = match vault.call("captures.ingest", serde_json::to_value(&candidate).map_err(|_| invalid())?).await {
            Ok(value) => value,
            Err(error) if matches!(error.code, "CONFLICT" | "VALIDATION_ERROR" | "LIMIT_EXCEEDED") => {
                result.skipped += 1;
                continue;
            }
            Err(error) => return Err(error),
        };
        match receipt.get("status").and_then(Value::as_str) {
            Some("created") => result.created += 1,
            Some("updated") => result.updated += 1,
            Some("unchanged") => result.unchanged += 1,
            _ => return Err(invalid()),
        }
        let canonical_session_id = receipt.get("id").and_then(Value::as_str).ok_or_else(invalid)?;
        if uuid::Uuid::parse_str(canonical_session_id).is_err() { return Err(invalid()); }
        let ack = call(&app, json!({"method":"acknowledge","provider":candidate.provider.name(),
            "session_key":candidate.session_key,"selected_sha256":candidate.selected_sha256,
            "canonical_session_id":canonical_session_id})).await?;
        if !matches!(ack.get("status").and_then(Value::as_str), Some("acknowledged" | "unchanged")) {
            return Err(invalid());
        }
        result.acknowledged += 1;
    }
    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn scopes_reject_unknown_fields_relative_paths_and_missing_memory_consent() {
        let value = json!({"provider":"codex","source_root":"C:/synthetic/source","memory_roots":[],
            "enabled":false,"memory_enabled":false,"revision":"a".repeat(64)});
        assert!(serde_json::from_value::<Scope>(value.clone()).unwrap().valid());
        for field in ["executable", "inbox_root", "endpoint"] {
            let mut bad = value.clone(); bad[field] = json!("private");
            assert!(serde_json::from_value::<Scope>(bad).is_err());
        }
        let mut bad = value.clone(); bad["source_root"] = json!("relative");
        assert!(!serde_json::from_value::<Scope>(bad).unwrap().valid());
        let mut bad = value; bad["memory_enabled"] = json!(true);
        assert!(!serde_json::from_value::<Scope>(bad).unwrap().valid());
    }
    #[test]
    fn import_candidates_reject_spoofed_identity_and_hashes() {
        let provider = Provider::Codex;
        let session_id = "synthetic".to_string();
        let source_text = "{\"type\":\"synthetic\"}\n".to_string();
        let selected_sha256 = format!("{:x}", Sha256::digest(source_text.as_bytes()));
        let session_key = format!("{:x}", Sha256::digest(b"codex\0synthetic"));
        let mut candidate = Candidate { op_id: uuid::Uuid::new_v4().to_string(), provider, session_key,
            session_id, title: "Codex session synthetic".into(), source_text,
            selected_sha256: selected_sha256.clone(), revisions: vec![selected_sha256] };
        assert!(candidate.valid());
        candidate.session_id = "different".into();
        assert!(!candidate.valid());
    }
}
