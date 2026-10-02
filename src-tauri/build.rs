fn main() {
    tauri_build::try_build(
        tauri_build::Attributes::new()
            .app_manifest(tauri_build::AppManifest::new().commands(&["native_health", "vault_status", "vault_open", "vault_close", "sessions_create", "sessions_list", "sessions_read", "ai_preview", "ai_discard", "ai_cancel"])),
    )
    .expect("Native shell build configuration failed");
}
