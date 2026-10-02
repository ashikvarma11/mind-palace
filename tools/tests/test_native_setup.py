import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location(
    "native_setup", Path(__file__).resolve().parents[1] / "setup-local-native.py"
)
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class NativeArchiveTests(unittest.TestCase):
    def test_hash_matches_known_bytes(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "data"
            path.write_bytes(b"abc")
            self.assertEqual(setup.digest(path), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_unknown_download_host_never_requested(self):
        with self.assertRaises(ValueError):
            setup.download({"url": "https://example.invalid/tool.exe", "sha256": "0" * 64})

    def test_rejects_escaping_and_windows_names(self):
        for name in ("../x", "/x", "a/../x", "C:/x", "a\\x", "a/./x", "x\x00", "x\x01", "a/NUL.txt", "a/x.", "a/x?"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                setup.safe_name(name)

    def test_rejects_case_duplicate_before_writing(self):
        with tempfile.TemporaryDirectory() as root:
            archive = Path(root) / "test.zip"
            dest = Path(root) / "out"
            with zipfile.ZipFile(archive, "w") as pack:
                pack.writestr("A.txt", "a")
                pack.writestr("a.txt", "b")
            with self.assertRaises(ValueError):
                setup.unpack(archive, "zip", dest, False)
            self.assertFalse(dest.exists())

    def test_valid_archive_preserves_bytes(self):
        with tempfile.TemporaryDirectory() as root:
            archive = Path(root) / "test.zip"
            dest = Path(root) / "out"
            with zipfile.ZipFile(archive, "w") as pack:
                pack.writestr("a/data", b"synthetic\x00bytes")
            setup.unpack(archive, "zip", dest, False)
            self.assertEqual((dest / "a/data").read_bytes(), b"synthetic\x00bytes")

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            archive = Path(root) / "test.zip"
            with zipfile.ZipFile(archive, "w") as pack:
                entry = zipfile.ZipInfo("link")
                entry.external_attr = 0o120777 << 16
                pack.writestr(entry, "target")
            with self.assertRaises(ValueError):
                setup.unpack(archive, "zip", Path(root) / "out", False)

    def test_size_limit_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            archive = Path(root) / "test.zip"
            with zipfile.ZipFile(archive, "w") as pack:
                pack.writestr("data", "abc")
            previous = setup.MAX_EXPANDED
            try:
                setup.MAX_EXPANDED = 2
                with self.assertRaises(ValueError):
                    setup.unpack(archive, "zip", Path(root) / "out", False)
            finally:
                setup.MAX_EXPANDED = previous


if __name__ == "__main__":
    unittest.main()
