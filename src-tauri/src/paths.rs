use std::path::PathBuf;
use tauri::Manager;
use crate::worker::{no_links, Error};

pub(crate) fn resolve(app: &tauri::AppHandle) -> Result<(PathBuf, PathBuf), Error> {
    let invalid = || Error { code: "VAULT_PATH_INVALID", message: "The local storage path is unavailable or redirected.", retryable: false };
    #[cfg(debug_assertions)]
    let bundle = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("resources/memory-worker");
    #[cfg(not(debug_assertions))]
    let bundle = app.path().resource_dir().map_err(|_| invalid())?.join("memory-worker");
    let mut parent = app.path().app_local_data_dir().map_err(|_| invalid())?;
    // The verification harness cannot redirect production storage. Debug-only
    // UUID selects a fixed ignored project directory, not an arbitrary path.
    #[cfg(debug_assertions)]
    if let Some(value) = std::env::var_os("MP_NATIVE_PROBE_ID") {
        let value = value.to_str().ok_or_else(invalid)?;
        if uuid::Uuid::parse_str(value).map_err(|_| invalid())?.to_string() != value { return Err(invalid()); }
        parent = PathBuf::from(env!("CARGO_MANIFEST_DIR")).parent().ok_or_else(invalid)?
            .join(".tools/native/verification").join(format!("vault-{value}"));
    }
    let vault = parent.join("vault");
    if !vault.is_absolute() { return Err(invalid()); }
    no_links(&vault)?;
    Ok((bundle, vault))
}
