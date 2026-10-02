mod worker;
mod paths;
mod commands;
mod ai_requests;
#[allow(dead_code)] // Internal foundation only; no credential command/UI until cancellation is verified.
mod credentials;
use tauri::Manager;

#[tauri::command]
fn native_health() -> &'static str {
    "desktop_local_storage_available: ai_disabled"
}

pub fn run() {
    tauri::Builder::default()
        .manage(commands::VaultState::default())
        .invoke_handler(tauri::generate_handler![native_health, commands::vault_status,
            commands::vault_open, commands::vault_close, commands::sessions_create,
            commands::sessions_list, commands::sessions_read, commands::ai_preview,
            commands::ai_discard, commands::ai_cancel])
        .build(tauri::generate_context!())
        .expect("Mind Palace desktop shell failed to start")
        .run(|app, event| {
            if matches!(event, tauri::RunEvent::ExitRequested { .. } | tauri::RunEvent::Exit) {
                app.state::<commands::VaultState>().shutdown();
            }
        });
}

#[cfg(test)]
mod tests {
    #[test]
    fn health_declares_storage_capability_not_an_open_vault_or_ai() {
        assert_eq!(super::native_health(), "desktop_local_storage_available: ai_disabled");
    }
}
