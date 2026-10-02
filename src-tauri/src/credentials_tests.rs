use super::*;

fn fake(value: &[u8]) -> Secret { Secret::new(Zeroizing::new(value.to_vec())).unwrap() }

#[test]
fn secret_validation_and_redaction() {
    for value in [b"".as_slice(), b"short", b"space in fake key value", b"fake-key-with-newline\n", b"fake-key-with-nul\0", &[0xff; 32], &vec![b'x'; MAX_KEY_BYTES + 1]] {
        let error = Secret::new(Zeroizing::new(value.to_vec())).unwrap_err();
        assert_eq!(error.code, "CREDENTIAL_INVALID");
        assert!(!format!("{error:?}").contains("fake-key"));
    }
    let secret = fake(b"fake-test-key-not-a-provider-key");
    assert_eq!(format!("{secret:?}"), "Secret([REDACTED])");
    assert!(secret.with_bytes(|bytes| bytes == b"fake-test-key-not-a-provider-key"));
    assert!(Secret::new(Zeroizing::new(vec![b'x'; 16])).is_ok());
    assert!(Secret::new(Zeroizing::new(vec![b'x'; MAX_KEY_BYTES])).is_ok());
}

#[test]
fn provider_allowlist_and_native_owned_targets() {
    for value in ["off", "other", "../secret", "OPENAI", "https://example.org"] {
        assert!(serde_json::from_value::<Provider>(serde_json::json!(value)).is_err());
    }
    assert!(matches!(serde_json::from_str::<Provider>("\"openai\"").unwrap(), Provider::Openai));
    let store = Store::isolated(uuid::Uuid::new_v4());
    for provider in [Provider::Openai, Provider::Anthropic] {
        let target = store.target(provider);
        assert_eq!(target.last(), Some(&0));
        let text = String::from_utf16(&target[..target.len()-1]).unwrap();
        assert!(text.starts_with("MindPalace/native-test/"));
        assert!(text.ends_with(provider.name()));
        assert!(!text.contains("dev.mindpalace.local"));
    }
}

#[test]
#[cfg(windows)]
fn real_windows_fake_keys_replace_remove_and_reconstruct_store() {
    let id = uuid::Uuid::new_v4();
    let store = Store::isolated(id);
    // No production constructor exists in test builds. No enumeration, API
    // credentials, environment secrets or public targets are accessed.
    for provider in [Provider::Openai, Provider::Anthropic] {
        assert!(!store.status(provider).unwrap(), "Fresh synthetic target unexpectedly exists; preserved");
        struct Cleanup<'a>(&'a Store, Provider);
        impl Drop for Cleanup<'_> {
            fn drop(&mut self) {
                if self.0.remove(self.1).is_err() { eprintln!("Synthetic cleanup failed in {}; no production keys used", self.0.namespace); }
            }
        }
        let cleanup = Cleanup(&store, provider);
        store.save(provider, fake(b"fake-test-key-first-not-a-provider"), false).unwrap();
        assert!(store.status(provider).unwrap());
        let reconstructed = Store::isolated(id);
        assert!(reconstructed.read(provider).unwrap().unwrap().with_bytes(|bytes| bytes == b"fake-test-key-first-not-a-provider"));
        assert_eq!(store.save(provider, fake(b"fake-test-key-second-not-a-provider"), false).unwrap_err().code, "CREDENTIAL_EXISTS");
        assert!(store.read(provider).unwrap().unwrap().with_bytes(|bytes| bytes == b"fake-test-key-first-not-a-provider"));
        store.save(provider, fake(b"fake-test-key-second-not-a-provider"), true).unwrap();
        assert!(reconstructed.read(provider).unwrap().unwrap().with_bytes(|bytes| bytes == b"fake-test-key-second-not-a-provider"));
        store.remove(provider).unwrap();
        assert!(!store.status(provider).unwrap());
        store.remove(provider).unwrap();
        drop(cleanup);
        assert!(!store.status(provider).unwrap());
    }
}

#[test]
#[cfg(windows)]
fn malformed_os_entry_is_preserved_by_save_and_remove() {
    let store = Store::isolated(uuid::Uuid::new_v4());
    let target = store.target(Provider::Openai);
    assert!(!store.status(Provider::Openai).unwrap(), "Fresh synthetic target exists; preserved");
    struct Cleanup(Vec<u16>);
    impl Drop for Cleanup {
        fn drop(&mut self) {
            if os::remove(&self.0).is_err() { eprintln!("Synthetic malformed-entry cleanup failed; no production keys used"); }
        }
    }
    let cleanup = Cleanup(target.clone());
    // Test-only bypass of Secret::new deliberately writes a short malformed
    // synthetic blob to this fresh owned UUID target, never a real entry.
    os::write(&target, &Secret(Zeroizing::new(b"broken".to_vec()))).unwrap();
    assert_eq!(store.status(Provider::Openai).unwrap_err().code, "CREDENTIAL_FORMAT_INVALID");
    assert_eq!(store.save(Provider::Openai, fake(b"fake-replacement-not-a-provider-key"), true).unwrap_err().code, "CREDENTIAL_FORMAT_INVALID");
    assert_eq!(store.remove(Provider::Openai).unwrap_err().code, "CREDENTIAL_FORMAT_INVALID");
    assert_eq!(store.status(Provider::Openai).unwrap_err().code, "CREDENTIAL_FORMAT_INVALID");
    // Only the test's raw cleanup can delete the deliberately invalid entry.
    os::remove(&target).unwrap();
    drop(cleanup);
    assert!(!store.status(Provider::Openai).unwrap());
}
