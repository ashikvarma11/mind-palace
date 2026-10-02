"""Process-local development environment; no installers or global settings."""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / ".tools/native"
TARGET = "x86_64-pc-windows-msvc"
SDK_VERSION = "10.0.20348.0"
VC_VERSION = "14.44.35207"  # Inspected paths inside hash-verified VSIX archives.


def merge(source: Path, destination: Path) -> None:
    if not source.is_dir() or source.is_symlink() or source.is_junction():
        raise ValueError("Missing or redirected compiler component")
    if destination.exists():
        raise ValueError("Compiler assembly already exists")
    shutil.copytree(source, destination)


def assemble() -> None:
    rust = BASE / "rust"
    vc = BASE / "msvc"
    # Atomic directory rename means an interrupted assembly is not executable.
    if not rust.exists():
        staging = BASE / "rust-staging"
        merge(BASE / f"raw/rustc/rustc-1.99.0-{TARGET}/rustc", staging)
        for name, component in (("cargo", "cargo"), ("rust-std", f"rust-std-{TARGET}")):
            source = BASE / f"raw/{name}/{name}-1.99.0-{TARGET}/{component}"
            shutil.copytree(source, staging, dirs_exist_ok=True)
        staging.rename(rust)
    if not vc.exists():
        staging = BASE / "msvc-staging"
        merge(BASE / f"raw/msvc-tools/Contents/VC/Tools/MSVC/{VC_VERSION}", staging)
        for name in ("msvc-headers", "msvc-crt", "msvc-resources"):
            source = BASE / f"raw/{name}/Contents/VC/Tools/MSVC/{VC_VERSION}"
            shutil.copytree(source, staging, dirs_exist_ok=True)
        staging.rename(vc)
    # Store.base also includes desktop dynamic import libraries: inspected
    # lib/x64/msvcrt.lib, vcruntime.lib and msvcprt.lib (not lib/x64/store).
    extra = BASE / f"raw/msvc-dynamic-crt/Contents/VC/Tools/MSVC/{VC_VERSION}"
    if not extra.is_dir():
        raise ValueError("Missing verified dynamic CRT archive")
    for source in extra.rglob("*"):
        target = vc / source.relative_to(extra)
        if source.is_dir():
            target.mkdir(exist_ok=True, parents=True)
        elif target.exists():
            with source.open("rb") as left, target.open("rb") as right:
                if hashlib.file_digest(left, "sha256").digest() != hashlib.file_digest(right, "sha256").digest():
                    raise ValueError("Conflicting compiler component bytes")
        else:
            shutil.copy2(source, target)


def environment() -> dict[str, str]:
    for path in (ROOT / ".tools", BASE, BASE / "rust", BASE / "msvc"):
        if path.exists() and (path.is_symlink() or path.is_junction()):
            raise ValueError("Redirected toolchain rejected")
    assemble()
    sdk = Path(os.environ["ProgramFiles(x86)"]) / "Windows Kits/10"
    vc = BASE / "msvc"
    binaries = (BASE / "rust/bin", vc / "bin/Hostx64/x64", sdk / f"bin/{SDK_VERSION}/x64")
    libraries = (vc / "lib/x64", sdk / f"Lib/{SDK_VERSION}/ucrt/x64", sdk / f"Lib/{SDK_VERSION}/um/x64")
    headers = (vc / "include", *(sdk / f"Include/{SDK_VERSION}/{part}" for part in ("ucrt", "shared", "um", "winrt")))
    for path in (*binaries, *libraries, *headers):
        if not path.is_dir():
            raise ValueError(f"Missing required native development directory: {path.name}")
    env = os.environ.copy()
    env.update({
        "PATH": os.pathsep.join(str(p) for p in binaries) + os.pathsep + env["PATH"],
        "LIB": os.pathsep.join(str(p) for p in libraries),
        "INCLUDE": os.pathsep.join(str(p) for p in headers),
        "CARGO_HOME": str(BASE / "cargo-cache"),
        "RUSTC": str(BASE / "rust/bin/rustc.exe"),
        "CARGO_TARGET_X86_64_PC_WINDOWS_MSVC_LINKER": str(binaries[1] / "link.exe"),
        "CC": str(binaries[1] / "cl.exe"),
        "CXX": str(binaries[1] / "cl.exe"),
        "CARGO_BUILD_JOBS": "2",
        "RUST_BACKTRACE": "0",
    })
    return env


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("smoke", "cargo", "desktop"))
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.action == "desktop":
        executable = ROOT / "src-tauri/target/debug/mind-palace.exe"
        if not executable.is_file():
            raise ValueError("Build the development desktop first")
        raise SystemExit(subprocess.run([str(executable)], cwd=ROOT).returncode)
    env = environment()
    rustc = BASE / "rust/bin/rustc.exe"
    cargo = BASE / "rust/bin/cargo.exe"
    if args.action == "cargo":
        raise SystemExit(subprocess.run([str(cargo), *args.args], cwd=ROOT, env=env).returncode)
    subprocess.run([str(rustc), "--version"], env=env, check=True)
    subprocess.run([str(cargo), "--version"], env=env, check=True)
    out = BASE / "smoke"
    out.mkdir(exist_ok=True)
    executable = out / "native-smoke.exe"
    subprocess.run([str(rustc), str(ROOT / "tools/fixtures/native-smoke.rs"),
                    "-C", f"linker={env['CARGO_TARGET_X86_64_PC_WINDOWS_MSVC_LINKER']}",
                    "-o", str(executable)], cwd=out, env=env, check=True, timeout=120)
    subprocess.run([str(executable)], env=env, check=True, timeout=10)


if __name__ == "__main__":
    main()
