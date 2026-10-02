fn main() {
    tauri_build::try_build(
        tauri_build::Attributes::new()
            .app_manifest(tauri_build::AppManifest::new().commands(&["native_health"])),
    )
    .expect("Native shell build configuration failed");
}
