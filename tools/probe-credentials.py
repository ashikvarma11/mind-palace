"""Windows-only fake credential diagnostic; not the app credential backend."""
import argparse
import ctypes
from ctypes import wintypes
import json
import os
import re
import secrets
import uuid

PREFIX = "MindPalace/diagnostic/"
GENERIC, SESSION, NOT_FOUND = 1, 1, 1168


class CredentialError(Exception):
    pass


class Credential(ctypes.Structure):
    _fields_ = [("Flags", wintypes.DWORD), ("Type", wintypes.DWORD), ("TargetName", wintypes.LPWSTR),
                ("Comment", wintypes.LPWSTR), ("LastWritten", wintypes.FILETIME),
                ("CredentialBlobSize", wintypes.DWORD), ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
                ("Persist", wintypes.DWORD), ("AttributeCount", wintypes.DWORD), ("Attributes", ctypes.c_void_p),
                ("TargetAlias", wintypes.LPWSTR), ("UserName", wintypes.LPWSTR)]


def valid_target(target):
    if not isinstance(target, str) or not re.fullmatch(re.escape(PREFIX) + r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", target):
        raise CredentialError("Only an isolated diagnostic credential target is allowed.")


class DiagnosticStore:
    def __init__(self):
        if os.name != "nt":
            raise CredentialError("Windows Credential Manager is unavailable on this platform.")
        self.api = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
        self.api.CredWriteW.argtypes = [ctypes.POINTER(Credential), wintypes.DWORD]
        self.api.CredWriteW.restype = wintypes.BOOL
        self.api.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(Credential))]
        self.api.CredReadW.restype = wintypes.BOOL
        self.api.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
        self.api.CredDeleteW.restype = wintypes.BOOL
        self.api.CredFree.argtypes = [ctypes.c_void_p]
        self.api.CredFree.restype = None

    def read(self, target):
        valid_target(target)
        pointer = ctypes.POINTER(Credential)()
        if not self.api.CredReadW(target, GENERIC, 0, ctypes.byref(pointer)):
            if ctypes.get_last_error() == NOT_FOUND:
                return None
            raise CredentialError("OS credential read failed; no plaintext fallback.")
        try:
            credential = pointer.contents
            if credential.Type != GENERIC or credential.TargetName != target or credential.CredentialBlobSize > 512:
                raise CredentialError("Unexpected diagnostic credential format.")
            return ctypes.string_at(credential.CredentialBlob, credential.CredentialBlobSize)
        finally:
            self.api.CredFree(pointer)

    def write_fake(self, target, value):
        valid_target(target)
        if not isinstance(value, bytes) or len(value) != 32:
            raise CredentialError("Only 32-byte diagnostic values are accepted.")
        blob = (ctypes.c_ubyte * len(value)).from_buffer_copy(value)
        credential = Credential()
        credential.Type, credential.TargetName = GENERIC, target
        credential.Comment = "Mind Palace temporary fake credential diagnostic"
        credential.CredentialBlobSize, credential.CredentialBlob = len(value), blob
        credential.Persist = SESSION
        try:
            if not self.api.CredWriteW(ctypes.byref(credential), 0):
                raise CredentialError("OS credential write failed; no plaintext fallback.")
        finally:
            ctypes.memset(blob, 0, len(value))

    def remove(self, target):
        valid_target(target)
        if not self.api.CredDeleteW(target, GENERIC, 0) and ctypes.get_last_error() != NOT_FOUND:
            raise CredentialError("OS diagnostic credential cleanup failed.")


def probe():
    store = DiagnosticStore()
    target = PREFIX + str(uuid.uuid4())
    if store.read(target) is not None:
        raise CredentialError("Diagnostic target already exists; nothing was changed.")
    # Never read a provider key, environment secret or a user's existing target.
    value = secrets.token_bytes(32)
    try:
        store.write_fake(target, value)
        matched = store.read(target) == value
        if not matched:
            raise CredentialError("Diagnostic credential round-trip mismatch.")
    finally:
        store.remove(target)
    removed = store.read(target) is None
    if not removed:
        raise CredentialError("Diagnostic credential cleanup was not verified.")
    return {"platform": "windows", "fake_credential_roundtrip": matched, "cleanup_verified": removed,
            "persistence": "logon_session_only", "existing_credentials_enumerated": False,
            "production_key_used": False, "provider_calls": 0,
            "pending": ["native Rust credential backend", "macOS Keychain", "app UI integration", "persistent-key lifecycle tests"]}


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    try:
        print(json.dumps(probe(), sort_keys=True))
    except CredentialError as error:
        print(json.dumps({"error": str(error)}))
        raise SystemExit(1)
