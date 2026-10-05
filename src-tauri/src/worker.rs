//! Private supervised transport. No generic executable/worker command is exposed.
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, io::Read, path::{Component, Path, PathBuf}, process::Stdio, time::Duration};
use tokio::{io::{AsyncBufReadExt, AsyncReadExt, AsyncWriteExt, BufReader}, process::{Child, ChildStdin, ChildStdout, Command}, time::timeout};

const FRAME_LIMIT: usize = 64 * 1024 * 1024;
const FILE_LIMIT: u64 = 64 * 1024 * 1024;
const EXE: &str = "mind-palace-memory-worker.exe";
const MANIFEST_TEXT: &str = include_str!("../resources/memory-worker/worker-manifest.json");

#[derive(Debug, Serialize)]
pub(crate) struct Error {
    pub code: &'static str,
    pub message: &'static str,
    pub retryable: bool,
}

impl Error {
    fn transport() -> Self {
        Self { code: "WORKER_DISCONNECTED", message: "Memory worker stopped or returned invalid data. Reopen the vault before retrying; a save may already have completed.", retryable: false }
    }
    fn resources() -> Self {
        Self { code: "WORKER_RESOURCES_INVALID", message: "The bundled memory worker is missing or changed. Rebuild the verified development resources.", retryable: false }
    }
    fn shutdown() -> Self {
        Self { code: "WORKER_SHUTDOWN_FAILED", message: "Memory worker shutdown could not be confirmed. Close the app before reopening the vault.", retryable: false }
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Manifest { schema_version: u32, platform: String, executable: String, files: Vec<Resource> }
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Resource { path: String, bytes: u64, sha256: String }

pub(crate) fn no_links(path: &Path) -> Result<(), Error> {
    for parent in path.ancestors() {
        match fs::symlink_metadata(parent) {
            Ok(metadata) => {
                if metadata.file_type().is_symlink() { return Err(Error::resources()); }
                #[cfg(windows)] {
                    use std::os::windows::fs::MetadataExt;
                    if metadata.file_attributes() & 0x400 != 0 { return Err(Error::resources()); }
                }
            }
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => (),
            Err(_) => return Err(Error::resources()),
        }
    }
    Ok(())
}

fn relative_path(value: &str) -> Result<PathBuf, Error> {
    if value.is_empty() || value.contains('\\') || value.contains(':') || value.split('/').count() > 16 {
        return Err(Error::resources());
    }
    for name in value.split('/') {
        if name.is_empty() || name == "." || name == ".." || name.ends_with('.') || name.ends_with(' ')
            || name.chars().any(|c| c.is_control() || "<>\"|?*".contains(c)) {
            return Err(Error::resources());
        }
        let base = name.split('.').next().unwrap_or("").to_ascii_lowercase();
        if ["con", "prn", "aux", "nul"].contains(&base.as_str())
            || (base.len() == 4 && (base.starts_with("com") || base.starts_with("lpt")) && matches!(base.as_bytes()[3], b'1'..=b'9')) {
            return Err(Error::resources());
        }
    }
    let path = PathBuf::from(value);
    if path.components().any(|part| !matches!(part, Component::Normal(_))) { return Err(Error::resources()); }
    Ok(path)
}

fn hash_file(path: &Path, expected_bytes: u64) -> Result<String, Error> {
    // The bounded inventory walk checks each entry with symlink_metadata before
    // calling this function. Rechecking every ancestor for every file makes
    // cold Windows resource verification exceed the capture command deadline.
    let metadata = fs::metadata(path).map_err(|_| Error::resources())?;
    if !metadata.is_file() || metadata.len() != expected_bytes || expected_bytes > FILE_LIMIT { return Err(Error::resources()); }
    let mut file = fs::File::open(path).map_err(|_| Error::resources())?.take(expected_bytes + 1);
    let mut hash = Sha256::new();
    let mut buffer = [0u8; 65536];
    let mut count = 0;
    loop {
        let read = file.read(&mut buffer).map_err(|_| Error::resources())?;
        if read == 0 { break; }
        count += read as u64;
        if count > expected_bytes { return Err(Error::resources()); }
        hash.update(&buffer[..read]);
    }
    if count != expected_bytes { return Err(Error::resources()); }
    Ok(format!("{:x}", hash.finalize()))
}

pub(crate) fn verify_bundle(root: &Path) -> Result<PathBuf, Error> {
    verify_resources(root, MANIFEST_TEXT, EXE)
}

pub(crate) fn verify_resources(root: &Path, manifest_text: &str, executable: &str) -> Result<PathBuf, Error> {
    no_links(root)?;
    let manifest: Manifest = serde_json::from_str(manifest_text).map_err(|_| Error::resources())?;
    if manifest.schema_version != 1 || manifest.platform != "windows-x86_64" || manifest.executable != executable
        || manifest.files.is_empty() || manifest.files.len() > 512 { return Err(Error::resources()); }
    let manifest_path = root.join("worker-manifest.json");
    no_links(&manifest_path)?;
    let mut stored = Vec::new();
    fs::File::open(&manifest_path).map_err(|_| Error::resources())?.take(256 * 1024 + 1)
        .read_to_end(&mut stored).map_err(|_| Error::resources())?;
    if stored != manifest_text.as_bytes() { return Err(Error::resources()); }
    let mut expected = BTreeMap::new();
    let mut total = 0u64;
    for item in manifest.files {
        relative_path(&item.path)?;
        total = total.checked_add(item.bytes).ok_or_else(Error::resources)?;
        if total > 128 * 1024 * 1024 || item.sha256.len() != 64
            || !item.sha256.bytes().all(|b| b.is_ascii_digit() || matches!(b, b'a'..=b'f'))
            || expected.insert(item.path.to_ascii_lowercase(), item).is_some() { return Err(Error::resources()); }
    }
    if !expected.get(executable).is_some_and(|item| item.bytes > 0) { return Err(Error::resources()); }
    let mut pending = vec![root.to_path_buf()];
    let mut entries = 0;
    let mut seen = std::collections::BTreeSet::new();
    while let Some(directory) = pending.pop() {
        for entry in fs::read_dir(directory).map_err(|_| Error::resources())? {
            let path = entry.map_err(|_| Error::resources())?.path();
            entries += 1;
            if entries > 2048 { return Err(Error::resources()); }
            let metadata = fs::symlink_metadata(&path).map_err(|_| Error::resources())?;
            if metadata.file_type().is_symlink() { return Err(Error::resources()); }
            #[cfg(windows)] {
                use std::os::windows::fs::MetadataExt;
                if metadata.file_attributes() & 0x400 != 0 { return Err(Error::resources()); }
            }
            let relative = path.strip_prefix(root).map_err(|_| Error::resources())?.to_str()
                .ok_or_else(Error::resources)?.replace('\\', "/");
            relative_path(&relative)?;
            if metadata.is_dir() { pending.push(path); continue; }
            if !metadata.is_file() { return Err(Error::resources()); }
            if relative == "worker-manifest.json" { continue; }
            let key = relative.to_ascii_lowercase();
            if !seen.insert(key.clone()) { return Err(Error::resources()); }
            let item = expected.get(&key).ok_or_else(Error::resources)?;
            if relative != item.path || hash_file(&path, item.bytes)? != item.sha256 { return Err(Error::resources()); }
        }
    }
    if seen.len() != expected.len() { return Err(Error::resources()); }
    Ok(root.join(executable))
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Response { protocol_version: u32, id: String, result: Option<Value>, error: Option<RemoteError> }
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct RemoteError { code: String, message: String, retryable: bool }

fn decode(frame: &[u8], id: &str) -> Result<Value, Error> {
    if frame.len() > FRAME_LIMIT || !frame.ends_with(b"\n") { return Err(Error::transport()); }
    let shape: Value = serde_json::from_slice(frame).map_err(|_| Error::transport())?;
    let object = shape.as_object().ok_or_else(Error::transport)?;
    if object.contains_key("result") == object.contains_key("error") { return Err(Error::transport()); }
    let value: Response = serde_json::from_slice(frame).map_err(|_| Error::transport())?;
    if value.protocol_version != 1 || value.id != id { return Err(Error::transport()); }
    match (value.result, value.error) {
        (Some(result), None) if result.is_object() => Ok(result),
        (None, Some(error)) if error.message.len() <= 256 => {
            let (code, message) = match error.code.as_str() {
                "NOT_FOUND" => ("NOT_FOUND", "Conversation was not found."),
                "CONFLICT" => ("CONFLICT", "Stored content changed. Existing files were preserved."),
                "BUSY" => ("BUSY", "The vault is busy. Try again later."),
                "VALIDATION_ERROR" => ("VALIDATION_ERROR", "Stored data or request is invalid. Existing files were preserved."),
                "LIMIT_EXCEEDED" => ("LIMIT_EXCEEDED", "The operation exceeds the supported size limit."),
                "INTERNAL_ERROR" => ("INTERNAL_ERROR", "The operation failed. Inspect local storage before retrying."),
                _ => return Err(Error::transport()),
            };
            Err(Error { code, message, retryable: error.retryable && code == "BUSY" })
        }
        _ => Err(Error::transport()),
    }
}

async fn read_frame<R: tokio::io::AsyncRead + Unpin>(output: &mut BufReader<R>) -> Result<Vec<u8>, Error> {
    let mut frame = Vec::new();
    output.take((FRAME_LIMIT + 1) as u64).read_until(b'\n', &mut frame).await.map_err(|_| Error::transport())?;
    if frame.len() > FRAME_LIMIT || !frame.ends_with(b"\n") { return Err(Error::transport()); }
    Ok(frame)
}

pub(crate) struct Worker {
    child: Option<std::sync::Arc<std::sync::Mutex<Child>>>,
    input: Option<ChildStdin>,
    output: Option<BufReader<ChildStdout>>,
    usable: bool,
}

pub(crate) async fn stop_owned(child: &std::sync::Arc<std::sync::Mutex<Child>>) -> Result<(), Error> {
    {
        let mut owned = child.lock().map_err(|_| Error::shutdown())?;
        if owned.try_wait().map_err(|_| Error::shutdown())?.is_some() { return Ok(()); }
        owned.start_kill().map_err(|_| Error::shutdown())?;
    }
    timeout(Duration::from_secs(3), async {
        loop {
            // Never hold a blocking guard over an await.
            if child.lock().map_err(|_| Error::shutdown())?.try_wait()
                .map_err(|_| Error::shutdown())?.is_some() { return Ok::<(), Error>(()); }
            tokio::time::sleep(Duration::from_millis(10)).await;
        }
    }).await.map_err(|_| Error::shutdown())?
}

impl Worker {
    pub(crate) fn is_usable(&self) -> bool { self.usable }
    // The resource root is native-owned; callers may not supply an executable.
    #[cfg(test)]
    pub(crate) async fn start(bundle: &Path, vault: &Path, create: bool) -> Result<Self, Error> {
        Self::start_supervised(bundle, vault, create, |_| Ok(())).await
    }

    pub(crate) async fn start_supervised(
        bundle: &Path, vault: &Path, create: bool,
        register: impl FnOnce(std::sync::Arc<std::sync::Mutex<Child>>) -> Result<(), Error>,
    ) -> Result<Self, Error> {
        let executable = verify_bundle(bundle)?;
        no_links(vault)?;
        if !vault.is_absolute() || vault.parent().is_none() { return Err(Error::resources()); }
        let mut command = Command::new(executable);
        command.args(["--mode", "ui", "--vault"]).arg(vault).current_dir(bundle)
            .stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::null()).env_clear().kill_on_drop(true);
        for name in ["SystemRoot", "WINDIR", "TEMP", "TMP"] {
            if let Some(value) = std::env::var_os(name) { command.env(name, value); }
        }
        #[cfg(windows)] {
            command.creation_flags(0x08000000);
            let system = std::env::var_os("SystemRoot").ok_or_else(Error::resources)?;
            command.env("PATH", PathBuf::from(system).join("System32"));
        }
        if create { command.arg("--create-vault"); }
        let mut child = command.spawn().map_err(|_| Error::transport())?;
        let input = child.stdin.take().ok_or_else(Error::transport)?;
        let output = BufReader::new(child.stdout.take().ok_or_else(Error::transport)?);
        let child = std::sync::Arc::new(std::sync::Mutex::new(child));
        // Register before the first await: exit can stop an opening or busy worker.
        register(child.clone())?;
        let mut worker = Self { child: Some(child), input: Some(input), output: Some(output), usable: true };
        let health = worker.request("health", json!({})).await?;
        if health != json!({"version":"0.1.0","storage":"foundation","ai_enabled":false}) {
            worker.stop().await?;
            return Err(Error::transport());
        }
        Ok(worker)
    }

    pub(crate) async fn request(&mut self, method: &str, params: Value) -> Result<Value, Error> {
        self.request_with_deadline(method, params, Duration::from_secs(30)).await
    }

    pub(crate) async fn request_cancellable(&mut self, method: &str, params: Value,
        control: &mut crate::ai_requests::Request<'_>) -> Result<Value, Error> {
        if !matches!(method, "cloud.preview" | "cloud.prepare" | "cloud.discard") {
            return Err(Error { code: "VALIDATION_ERROR", message: "Only offline AI requests can be cancelled here.", retryable: false });
        }
        match control.run(self.request(method, params), Duration::from_secs(30)).await {
            Ok(result) => result,
            Err(error) => {
                // Dropping a partially written/read JSONL operation is not safe
                // to resume. Confirm shutdown before exposing cancellation.
                self.stop().await?;
                Err(error)
            }
        }
    }

    async fn request_with_deadline(&mut self, method: &str, params: Value, deadline: Duration) -> Result<Value, Error> {
        if !matches!(method, "health" | "sessions.create" | "sessions.read" | "sessions.list" | "sessions.ask"
            | "captures.ingest" | "cloud.preview" | "cloud.prepare" | "cloud.discard") {
            return Err(Error { code: "VALIDATION_ERROR", message: "This worker operation is not available.", retryable: false });
        }
        if !self.usable {
            return Err(if self.child.is_some() { Error::shutdown() } else { Error::transport() });
        }
        let id = uuid::Uuid::new_v4().to_string();
        let mut request = serde_json::to_vec(&json!({"protocol_version":1,"id":id,"method":method,"params":params}))
            .map_err(|_| Error::transport())?;
        request.push(b'\n');
        if request.len() > FRAME_LIMIT { return Err(Error { code: "LIMIT_EXCEEDED", message: "The request is too large.", retryable: false }); }
        // If the owning future is dropped mid-frame, retained state must be
        // unusable rather than feeding its late response to a later request.
        self.usable = false;
        let result = timeout(deadline, async {
            let input = self.input.as_mut().ok_or_else(Error::transport)?;
            input.write_all(&request).await.map_err(|_| Error::transport())?;
            input.flush().await.map_err(|_| Error::transport())?;
            let frame = read_frame(self.output.as_mut().ok_or_else(Error::transport)?).await?;
            decode(&frame, &id)
        }).await.unwrap_or_else(|_| Err(Error::transport()));
        if result.as_ref().is_err_and(|error| error.code == "WORKER_DISCONNECTED") {
            self.stop().await?;
        } else {
            self.usable = true;
        }
        result
    }

    pub(crate) async fn stop(&mut self) -> Result<(), Error> {
        self.usable = false;
        // Release all owned handles even if callers retain the closed Worker.
        // A new vault must not inherit pipes from a previously stopped child.
        drop(self.input.take());
        drop(self.output.take());
        let Some(child) = self.child.take() else { return Ok(()); };
        let result = stop_owned(&child).await;
        // Failed shutdown retains the owned control for another explicit close
        // or app exit, never presenting it as a successfully stopped worker.
        if result.is_err() { self.child = Some(child); }
        result
    }
}

#[cfg(test)]
#[path = "worker_tests.rs"]
mod tests;
