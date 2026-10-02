//! Native-only secrets. No WebView read command, enumeration, files or network.
use serde::{Deserialize, Serialize};
use zeroize::Zeroizing;

const MAX_KEY_BYTES: usize = 2048;
const OWNER: &str = "Mind Palace development API credential v1";
static ACCESS: std::sync::Mutex<()> = std::sync::Mutex::new(());

#[derive(Clone, Copy, Debug, Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]
pub(crate) enum Provider { Openai, Anthropic }
impl Provider {
    fn name(self) -> &'static str { match self { Self::Openai => "openai", Self::Anthropic => "anthropic" } }
}

#[derive(Debug, Serialize)]
pub(crate) struct Error { pub code: &'static str, pub message: &'static str }
impl Error {
    fn unavailable() -> Self { Self { code: "SECURE_STORAGE_UNAVAILABLE", message: "OS credential storage failed. No plaintext fallback was used." } }
    fn invalid() -> Self { Self { code: "CREDENTIAL_INVALID", message: "Key must contain 16–2048 printable ASCII bytes without spaces." } }
    fn format() -> Self { Self { code: "CREDENTIAL_FORMAT_INVALID", message: "The existing credential has an unexpected format and was preserved." } }
    fn conflict() -> Self { Self { code: "CREDENTIAL_EXISTS", message: "A credential already exists. Explicit replacement is required." } }
}

// Not Clone/Serialize/Deref. Debug is always redacted; the native sender can
// borrow bytes only for a bounded operation. This is not protection against
// same-user processes, OS/admin access, memory dumps or prior caller copies.
pub(crate) struct Secret(Zeroizing<Vec<u8>>);
impl std::fmt::Debug for Secret {
    fn fmt(&self, out: &mut std::fmt::Formatter<'_>) -> std::fmt::Result { out.write_str("Secret([REDACTED])") }
}
impl Secret {
    pub(crate) fn new(bytes: Zeroizing<Vec<u8>>) -> Result<Self, Error> {
        if !(16..=MAX_KEY_BYTES).contains(&bytes.len()) || !bytes.iter().all(|b| (0x21..=0x7e).contains(b)) {
            return Err(Error::invalid());
        }
        Ok(Self(bytes))
    }
    pub(crate) fn with_bytes<T>(&self, operation: impl FnOnce(&[u8]) -> T) -> T { operation(&self.0) }
}

pub(crate) struct Store { namespace: String }
impl Store {
    #[cfg(not(test))]
    pub(crate) fn development() -> Self { Self { namespace: "MindPalace/dev.mindpalace.local/api/v1".into() } }
    #[cfg(test)]
    fn isolated(id: uuid::Uuid) -> Self { Self { namespace: format!("MindPalace/native-test/{id}") } }
    fn target(&self, provider: Provider) -> Vec<u16> {
        format!("{}/{}", self.namespace, provider.name()).encode_utf16().chain(Some(0)).collect()
    }
    pub(crate) fn status(&self, provider: Provider) -> Result<bool, Error> { Ok(self.read(provider)?.is_some()) }
    pub(crate) fn read(&self, provider: Provider) -> Result<Option<Secret>, Error> {
        let _guard = ACCESS.lock().map_err(|_| Error::unavailable())?;
        os::read(&self.target(provider))
    }
    pub(crate) fn save(&self, provider: Provider, secret: Secret, replace: bool) -> Result<(), Error> {
        let _guard = ACCESS.lock().map_err(|_| Error::unavailable())?;
        let target = self.target(provider);
        if os::read(&target)?.is_some() && !replace { return Err(Error::conflict()); }
        os::write(&target, &secret)
    }
    pub(crate) fn remove(&self, provider: Provider) -> Result<(), Error> {
        let _guard = ACCESS.lock().map_err(|_| Error::unavailable())?;
        let target = self.target(provider);
        // Unexpected existing formats belong to neither this version nor this
        // operation. Never overwrite/remove them silently.
        if os::read(&target)?.is_some() { os::remove(&target)?; }
        Ok(())
    }
}

#[cfg(windows)]
mod os {
    use super::*;
    use zeroize::Zeroize;
    use windows_sys::Win32::{Foundation::{GetLastError, ERROR_NOT_FOUND}, Security::Credentials::*};

    // Win32 promises NUL-terminated strings within its returned allocation.
    // Stop at the first NUL; never scan an unbounded foreign string.
    unsafe fn wide_matches(pointer: *const u16, expected: &[u16]) -> bool {
        if pointer.is_null() { return false; }
        for (index, wanted) in expected.iter().enumerate() {
            let actual = unsafe { *pointer.add(index) };
            if actual != *wanted { return false; }
            if actual == 0 { return index + 1 == expected.len(); }
        }
        false
    }
    fn owner() -> Vec<u16> { OWNER.encode_utf16().chain(Some(0)).collect() }
    struct Allocation(*mut CREDENTIALW);
    impl Drop for Allocation {
        fn drop(&mut self) {
            // SAFETY: only constructed from a successful non-null CredReadW.
            // Blob is writable OS-owned memory freed once by CredFree.
            unsafe {
                let value = &*self.0;
                if !value.CredentialBlob.is_null() && value.CredentialBlobSize <= CRED_MAX_CREDENTIAL_BLOB_SIZE {
                    std::slice::from_raw_parts_mut(value.CredentialBlob, value.CredentialBlobSize as usize).zeroize();
                }
                CredFree(self.0.cast());
            }
        }
    }
    pub(super) fn read(target: &[u16]) -> Result<Option<Secret>, Error> {
        let mut pointer = std::ptr::null_mut();
        // SAFETY: target is native-generated, live, and NUL-terminated; output
        // points to a local initialized pointer. No generic caller target.
        if unsafe { CredReadW(target.as_ptr(), CRED_TYPE_GENERIC, 0, &mut pointer) } == 0 {
            return if unsafe { GetLastError() } == ERROR_NOT_FOUND { Ok(None) } else { Err(Error::unavailable()) };
        }
        if pointer.is_null() { return Err(Error::format()); }
        let owned = Allocation(pointer);
        // SAFETY: Win32 owns a valid CREDENTIALW until this allocation drops.
        let credential = unsafe { &*owned.0 };
        if credential.Type != CRED_TYPE_GENERIC || credential.Persist != CRED_PERSIST_LOCAL_MACHINE
            || credential.Flags != 0 || credential.AttributeCount != 0
            || !(16..=MAX_KEY_BYTES).contains(&(credential.CredentialBlobSize as usize))
            || credential.CredentialBlob.is_null()
            || !unsafe { wide_matches(credential.TargetName, target) }
            || !unsafe { wide_matches(credential.Comment, &owner()) } { return Err(Error::format()); }
        // SAFETY: validated bounded blob size and non-null pointer from Win32.
        let bytes = unsafe { std::slice::from_raw_parts(credential.CredentialBlob, credential.CredentialBlobSize as usize) };
        Secret::new(Zeroizing::new(bytes.to_vec())).map(Some).map_err(|_| Error::format())
    }
    pub(super) fn write(target: &[u16], secret: &Secret) -> Result<(), Error> {
        let mut comment = owner();
        secret.with_bytes(|bytes| {
            let value = CREDENTIALW { Type: CRED_TYPE_GENERIC, TargetName: target.as_ptr().cast_mut(),
                Comment: comment.as_mut_ptr(), CredentialBlobSize: bytes.len() as u32,
                CredentialBlob: bytes.as_ptr().cast_mut(), Persist: CRED_PERSIST_LOCAL_MACHINE,
                ..Default::default() };
            // SAFETY: all pointers remain live for the synchronous input-only
            // CredWriteW call; flags/attributes initialized to zero.
            if unsafe { CredWriteW(&value, 0) } == 0 { Err(Error::unavailable()) } else { Ok(()) }
        })
    }
    pub(super) fn remove(target: &[u16]) -> Result<(), Error> {
        // SAFETY: native-generated live NUL-terminated target, fixed type/flags.
        if unsafe { CredDeleteW(target.as_ptr(), CRED_TYPE_GENERIC, 0) } == 0
            && unsafe { GetLastError() } != ERROR_NOT_FOUND { return Err(Error::unavailable()); }
        Ok(())
    }
}

#[cfg(not(windows))]
mod os {
    use super::*;
    pub(super) fn read(_: &[u16]) -> Result<Option<Secret>, Error> { Err(Error::unavailable()) }
    pub(super) fn write(_: &[u16], _: &Secret) -> Result<(), Error> { Err(Error::unavailable()) }
    pub(super) fn remove(_: &[u16]) -> Result<(), Error> { Err(Error::unavailable()) }
}

#[cfg(test)]
#[path = "credentials_tests.rs"]
mod tests;
