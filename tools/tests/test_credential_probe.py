import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import unittest

PROBE = Path(__file__).resolve().parents[1] / "probe-credentials.py"
spec = importlib.util.spec_from_file_location("credential_probe", PROBE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CredentialTests(unittest.TestCase):
    def test_only_uuid_diagnostic_targets_allowed(self):
        for target in ["MindPalace/openai", "MindPalace/diagnostic/*", "other", None, "MindPalace/diagnostic/../openai"]:
            with self.assertRaises(module.CredentialError):
                module.valid_target(target)

    @unittest.skipUnless(os.name == "nt", "Windows-specific diagnostic")
    def test_real_fake_credential_roundtrip_and_cleanup(self):
        result = module.probe()
        self.assertTrue(result["fake_credential_roundtrip"])
        self.assertTrue(result["cleanup_verified"])
        self.assertFalse(result["production_key_used"])
        self.assertFalse(result["existing_credentials_enumerated"])
        self.assertEqual(result["provider_calls"], 0)

    def test_unknown_option_fails_without_credential_access(self):
        child = subprocess.run([sys.executable, str(PROBE), "--target", "MindPalace/openai"], capture_output=True, timeout=15)
        self.assertEqual(child.returncode, 2)
        self.assertEqual(child.stdout, b"")


if __name__ == "__main__":
    unittest.main()
