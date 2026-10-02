# Project-local native toolchain — 2 October 2026

Verified on this Windows 10 x64 development machine only. No system installation, administrator action, registry edit or global PATH change performed.

## Actual prerequisite result

- Official standalone Rust 1.99.0 rustc/cargo/rust-std and five Microsoft MSVC VSIX packages downloaded into ignored `.tools/native/cache`; all eight SHA-256 values match the locked official manifests.
- Downloaded archives total **217,885,062 bytes**. Sources/hashes are in `config/native-toolchain.json`; raw upstream license/copyright/package metadata remain in ignored extraction directories. This is developer tooling, not an approved redistribution bundle.
- Validated archive member names, case collisions, special files/symlinks and expansion bounds before extraction. Existing redirected tooling roots are rejected. These checks are not protection against a malicious concurrent same-account process changing files after validation.
- Assembled compiler files use the inspected MSVC path version **14.44.35207**. Initial linking failed because `msvcrt.lib` was missing. Inspected CRT.x64.Store.base supplied its desktop `lib/x64` dynamic import libraries; no store-library path substituted.
- Existing Windows SDK **10.0.20348.0** headers/libraries/resource compiler used read-only. No Visual Studio repair/install command executed.
- `cl.exe` and `link.exe` Authenticode status: **Valid**.

## Executed checks

```powershell
python tools/setup-local-native.py --extract
python tools/setup-local-native.py --extract --only msvc-dynamic-crt
python tools/run-native.py smoke
python -m unittest discover -s tools/tests -p test_native_setup.py -v
```

The dynamic CRT was added after the initial seven-artifact extraction. A fresh config now includes all eight; do not repeat extraction over existing raw targets. The default without `--extract` verifies cached hashes and inspects archives without replacing extraction directories.

Smoke output:

```text
rustc 1.99.0 (b940084d7 2026-09-28)
cargo 1.99.0 (5f94df478 2026-08-27)
Mind Palace native compiler probe passed
```

Seven archive/hash/host-safety unit tests pass. Child-process environment supplies explicit linker, compiler, SDK paths and project-local Cargo cache. No rustup/MSI/install.sh or VS installer run. Portable layout is an experimental developer workaround, not a claim of official installed-toolchain support. Mac tools and clean-machine installer prerequisites remain unverified.
