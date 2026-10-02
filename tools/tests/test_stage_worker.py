import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("stage_worker", Path(__file__).resolve().parents[1] / "stage-worker.py")
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


class StageWorkerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="mp-stage-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / ".tools/probe-dist/mind-palace-memory-worker"
        self.target = self.root / "src-tauri/resources/memory-worker"
        self.source.mkdir(parents=True)
        (self.source / worker.EXE).write_bytes(b"synthetic-not-executable")
        (self.source / "_internal").mkdir()
        (self.source / "_internal/python.dll").write_bytes(b"synthetic-library")

    def test_stage_check_and_repeat_are_identical(self):
        first = worker.stage(self.root)
        self.assertEqual(first, worker.stage(self.root, check=True))
        self.assertEqual(first, worker.stage(self.root))
        self.assertEqual(len(first["files"]), 2)
        self.assertEqual((self.target / worker.EXE).read_bytes(), b"synthetic-not-executable")
        self.assertFalse((self.root / ".tools/worker-stage-backups").exists())

    def test_source_change_requires_refresh_and_retains_previous(self):
        first = worker.stage(self.root)
        (self.source / worker.EXE).write_bytes(b"synthetic-new-worker")
        with self.assertRaises(ValueError):
            worker.stage(self.root, check=True)
        with self.assertRaises(ValueError):
            worker.stage(self.root)
        second = worker.stage(self.root, refresh=True)
        self.assertNotEqual(first, second)
        backups = list((self.root / ".tools/worker-stage-backups").iterdir())
        self.assertEqual(len(backups), 1)
        self.assertEqual(worker.verify(backups[0]), first)

    def test_target_tampering_is_never_overwritten_or_moved(self):
        worker.stage(self.root)
        (self.target / worker.EXE).write_bytes(b"changed-staged-file")
        for flags in ({}, {"check": True}, {"refresh": True}):
            with self.assertRaises(ValueError):
                worker.stage(self.root, **flags)
        self.assertEqual((self.target / worker.EXE).read_bytes(), b"changed-staged-file")
        self.assertFalse((self.root / ".tools/worker-stage-backups").exists())

    def test_extra_file_and_duplicate_manifest_fail(self):
        worker.stage(self.root)
        (self.target / "extra.dll").write_bytes(b"unexpected")
        with self.assertRaises(ValueError):
            worker.verify(self.target)
        # Remove only this test's synthetic extra, never a staged application file.
        (self.target / "extra.dll").unlink()
        manifest = self.target / worker.MANIFEST
        text = manifest.read_text()
        manifest.write_text('{"schema_version":1,' + text[1:])
        with self.assertRaises(ValueError):
            worker.verify(self.target)

    def test_missing_executable_and_size_bounds(self):
        (self.source / worker.EXE).unlink()
        with self.assertRaises(ValueError):
            worker.stage(self.root)
        (self.source / worker.EXE).write_bytes(b"synthetic")
        with patch.object(worker, "MAX_FILE_BYTES", 1):
            with self.assertRaises(ValueError):
                worker.stage(self.root)
        with patch.object(worker, "MAX_FILES", 1):
            with self.assertRaises(ValueError):
                worker.stage(self.root)
        self.assertFalse(self.target.exists())

    def test_escaping_windows_names_and_owned_root_rejected(self):
        for name in ("../x", "/x", "a/../x", "C:/x", "a\\x", "a/./x", "a//x", "x\x00", "a/NUL.txt", "a/x."):
            with self.subTest(name=name), self.assertRaises(ValueError):
                worker.safe_relative(name)
        for path in (self.root, self.root / ".." / "outside"):
            with self.assertRaises(ValueError):
                worker.owned(path, self.root)

    def test_redirected_path_fails_before_copy(self):
        # Windows symlink creation may require OS privileges. Inject the queried
        # junction flag to test the guard without changing OS privileges.
        with patch.object(Path, "is_junction", return_value=True):
            with self.assertRaises(ValueError):
                worker.stage(self.root)
        self.assertFalse(self.target.exists())

    def test_bounded_hash_rejects_concurrent_size_change(self):
        path = self.source / worker.EXE
        path.write_bytes(b"abc")
        self.assertEqual(worker.file_digest(path, 3), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
        for expected in (2, 4):
            with self.assertRaises(ValueError):
                worker.file_digest(path, expected)

    def test_hardlinked_input_is_rejected(self):
        import os
        os.link(self.source / worker.EXE, self.source / "hardlink.exe")
        with self.assertRaises(ValueError):
            worker.stage(self.root)
        self.assertFalse(self.target.exists())


if __name__ == "__main__":
    unittest.main()
