fn main() {
    tauri_build::try_build(
        tauri_build::Attributes::new()
            .app_manifest(tauri_build::AppManifest::new().commands(&["native_health", "vault_status", "vault_open", "vault_close", "sessions_create", "sessions_list", "sessions_read", "sessions_ask", "ai_preview", "ai_discard", "ai_cancel", "capture_status", "capture_configure", "capture_index", "capture_import", "capture_codex_hook", "capture_recover", "capture_cleanup", "capture_history_preview", "capture_history_import"])),
    )
    .expect("Native shell build configuration failed");
}
