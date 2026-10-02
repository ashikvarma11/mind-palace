#[allow(dead_code)] // Internal transport is tested before exposing vault commands.
mod worker;

#[tauri::command]
fn native_health() -> &'static str {
    "desktop_shell_only: storage_disconnected, ai_disabled"
}

pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![native_health])
        .run(tauri::generate_context!())
        .expect("Mind Palace desktop shell failed to start");
}

#[cfg(test)]
mod tests {
    #[test]
    fn health_does_not_claim_storage_or_ai() {
        assert_eq!(super::native_health(), "desktop_shell_only: storage_disconnected, ai_disabled");
    }
}
