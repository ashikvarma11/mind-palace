import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from memory_worker.atomic_io import digest, file_hash, write
from memory_worker.cloud_contracts import decode
from memory_worker.cloud_preview import Previews
from memory_worker.errors import WorkerError
from memory_worker.protocol import serve
from memory_worker.service import dispatch
from memory_worker.vault import Vault
from test_foundation import call, op


class CloudTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="mp-cloud-offline-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "vault"
        self.vault = Vault(self.root, True)
        self.original = "User: Keep SQLite.\r\nAssistant: Noted."
        self.receipt = call(self.vault, "sessions.create", op_id=op(), title="Synthetic", body="DO NOT SHARE THIS SUMMARY", source_text=self.original)
        self.params = {"provider": "openai", "model": "synthetic-test-model", "question": "What was selected?", "max_output_tokens": 512,
                       "selections": [{"kind": "session", "id": self.receipt["id"], "start": 0, "end": 18}]}
        self.excerpts = [{"source_id": "S1", "text": "User: Keep SQLite."}]
        self.answer = {"status": "answered", "answer": "SQLite was selected.", "sources": [{"source_id": "S1", "quote": "Keep SQLite"}]}

    def preview(self, **changes):
        return call(self.vault, "cloud.preview", **{**self.params, **changes})

    def consent(self, preview):
        return {"preview_id": preview["preview_id"], "payload_sha256": preview["payload_sha256"], "accept_sharing_and_api_charges": True}

    def raw(self, provider, answer=None):
        text = json.dumps(self.answer if answer is None else answer)
        if provider == "openai":
            return {"status": "completed", "output": [{"type": "reasoning"}, {"type": "message", "role": "assistant", "status": "completed",
                     "content": [{"type": "output_text", "text": text}]}], "usage": {"input_tokens": 120, "output_tokens": 40, "total_tokens": 160}}
        return {"type": "message", "role": "assistant", "stop_reason": "end_turn", "content": [{"type": "text", "text": text}],
                "usage": {"input_tokens": 120, "output_tokens": 40, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 3}}

    def decode(self, provider, response):
        return decode(provider, json.dumps(response).encode(), self.excerpts)

    def test_openai_exact_preview_does_not_send_or_write(self):
        before = {str(path.relative_to(self.root)): digest(path.read_bytes()) for path in self.root.rglob("*") if path.is_file()}
        with patch("socket.socket", side_effect=AssertionError("Network prohibited")), patch("subprocess.Popen", side_effect=AssertionError("Process prohibited")):
            preview = self.preview()
            prepared = call(self.vault, "cloud.prepare", **self.consent(preview))
        self.assertFalse(prepared["can_send"])
        self.assertEqual(prepared["request"], preview["request"])
        self.assertEqual(digest((json.dumps(preview["request"], ensure_ascii=False, sort_keys=True) + "\n").encode()), preview["payload_sha256"])
        self.assertEqual(preview["request"]["endpoint"], "https://api.openai.com/v1/responses")
        self.assertFalse(preview["request"]["body"]["store"])
        self.assertNotIn("Authorization", prepared["request"]["headers"])
        self.assertNotIn("DO NOT SHARE", json.dumps(prepared))
        self.assertNotIn(str(self.root), json.dumps(prepared))
        prompt = json.loads(prepared["request"]["body"]["input"][0]["content"])
        self.assertEqual(prompt["sources"], [{"source_id": "S1", "text": self.original[:18]}])
        self.assertNotIn(self.receipt["id"], json.dumps(prepared["request"]))
        after = {str(path.relative_to(self.root)): digest(path.read_bytes()) for path in self.root.rglob("*") if path.is_file()}
        self.assertEqual(before, after)

    def test_anthropic_request_contract(self):
        preview = self.preview(provider="anthropic")
        request = preview["request"]
        self.assertEqual(request["endpoint"], "https://api.anthropic.com/v1/messages")
        self.assertEqual(request["headers"]["anthropic-version"], "2023-06-01")
        self.assertEqual(request["body"]["max_tokens"], 512)
        self.assertFalse(request["body"]["stream"])
        self.assertNotIn("x-api-key", request["headers"])
        self.assertNotIn("tools", request["body"])

    def test_consent_required_and_payload_hash_bound(self):
        preview = self.preview()
        for changes in [{"accept_sharing_and_api_charges": False}, {"payload_sha256": "0" * 64}, {"api_key": "FAKE-DO-NOT-USE"}]:
            with self.assertRaises(WorkerError):
                call(self.vault, "cloud.prepare", **{**self.consent(preview), **changes})
        call(self.vault, "cloud.prepare", **self.consent(preview))

    def test_preparation_is_single_use(self):
        preview = self.preview()
        call(self.vault, "cloud.prepare", **self.consent(preview))
        with self.assertRaises(WorkerError):
            call(self.vault, "cloud.prepare", **self.consent(preview))

    def test_preview_return_cannot_mutate_saved_request(self):
        preview = self.preview()
        expected = copy.deepcopy(preview["request"])
        preview["request"]["body"]["model"] = "changed"
        self.assertEqual(call(self.vault, "cloud.prepare", **self.consent(preview))["request"], expected)

    def test_expiry_discard_and_capacity(self):
        clock = [10.0]
        self.vault.previews = Previews(lambda: clock[0])
        preview = self.preview()
        clock[0] += 301
        with self.assertRaises(WorkerError):
            call(self.vault, "cloud.prepare", **self.consent(preview))
        previews = [self.preview() for _ in range(8)]
        with self.assertRaises(WorkerError) as error:
            self.preview()
        self.assertEqual(error.exception.code, "BUSY")
        call(self.vault, "cloud.discard", preview_id=previews[0]["preview_id"])
        with self.assertRaises(WorkerError):
            call(self.vault, "cloud.prepare", **self.consent(previews[0]))
        self.preview()

    def test_unknown_provider_endpoint_key_and_bad_ranges_rejected(self):
        for changes in [{"provider": "other"}, {"endpoint": "https://example.invalid"}, {"api_key": "FAKE"}, {"model": "https://example.invalid"},
                        {"max_output_tokens": 1025}, {"selections": []}, {"question": "x" * 2001},
                        {"selections": [{**self.params["selections"][0], "end": 99999}]},
                        {"selections": [{**self.params["selections"][0], "start": 18, "end": 2}]}]:
            with self.assertRaises(WorkerError):
                self.preview(**changes)

    def test_original_change_invalidates_preview(self):
        preview = self.preview()
        loaded = call(self.vault, "sessions.read", id=self.receipt["id"])
        path = self.root / "sources" / loaded["metadata"]["source_id"] / "original.txt"
        write(path, b"Changed source", file_hash(path))
        with self.assertRaises(WorkerError):
            call(self.vault, "cloud.prepare", **self.consent(preview))

    def test_decision_revision_change_requires_new_preview(self):
        receipt = call(self.vault, "decisions.create", op_id=op(), title="Example", body="Choice")
        preview = self.preview(selections=[{"kind": "decision", "id": receipt["id"], "start": 0, "end": 18}])
        source = json.loads(preview["request"]["body"]["input"][0]["content"])["sources"][0]
        self.assertEqual(source["decision_state"], "proposed")
        call(self.vault, "decisions.confirm", op_id=op(), id=receipt["id"], expected_revision=1, confirm=True)
        with self.assertRaises(WorkerError) as error:
            call(self.vault, "cloud.prepare", **self.consent(preview))
        self.assertEqual(error.exception.code, "CONFLICT")

    def test_multibyte_total_size_and_exact_original_newlines(self):
        preview = self.preview(selections=[{**self.params["selections"][0], "end": len(self.original)}])
        source = json.loads(preview["request"]["body"]["input"][0]["content"])["sources"][0]
        self.assertEqual(source["text"], self.original)
        receipt = call(self.vault, "sessions.create", op_id=op(), title="Unicode example", body="", source_text="😀" * 16000)
        with self.assertRaises(WorkerError) as error:
            self.preview(selections=[{"kind": "session", "id": receipt["id"], "start": 0, "end": 8000},
                                     {"kind": "session", "id": receipt["id"], "start": 8000, "end": 16000}])
        self.assertEqual(error.exception.code, "LIMIT_EXCEEDED")

    def test_responses_normalized_without_claiming_correctness(self):
        for provider in ("openai", "anthropic"):
            result = self.decode(provider, self.raw(provider))
            self.assertEqual(result["answer"], "SQLite was selected.")
            self.assertEqual(result["reported_usage"]["output_tokens"], 40)
            self.assertEqual(result["verification"], "exact_quotes_only")
            self.assertTrue(result["requires_review"])

    def test_unknown_citation_and_fabricated_quote_rejected(self):
        for source in [{"source_id": "S2", "quote": "Keep SQLite"}, {"source_id": "S1", "quote": "Use Angular"}]:
            for provider in ("openai", "anthropic"):
                with self.assertRaises(WorkerError) as error:
                    self.decode(provider, self.raw(provider, {**self.answer, "sources": [source]}))
                self.assertEqual(error.exception.code, "UNSUPPORTED_EVIDENCE")

    def test_abstention_and_uncited_answer_contract(self):
        for provider in ("openai", "anthropic"):
            result = self.decode(provider, self.raw(provider, {"status": "insufficient_evidence", "answer": "No evidence supports that.", "sources": []}))
            self.assertEqual(result["status"], "insufficient_evidence")
            with self.assertRaises(WorkerError):
                self.decode(provider, self.raw(provider, {**self.answer, "sources": []}))

    def test_malformed_refusal_toolcall_truncation_and_usage_errors(self):
        bad = [b'{"status":NaN}', b'{"a":1,"a":2}', b'\xff', b'x' * (1024 * 1024 + 1)]
        for raw in bad:
            with self.assertRaises(WorkerError):
                decode("openai", raw, self.excerpts)
        for provider in ("openai", "anthropic"):
            base = self.raw(provider)
            invalid = [dict(base, usage={"input_tokens": True, "output_tokens": 1}), dict(base, usage=None)]
            if provider == "openai":
                invalid.extend([dict(base, status="incomplete"), dict(base, output=[{"type": "function_call"}]), dict(base, output=[])])
            else:
                invalid.extend([dict(base, stop_reason="max_tokens"), dict(base, content=[{"type": "tool_use"}]), dict(base, content=[])])
            for response in invalid:
                with self.assertRaises(WorkerError):
                    self.decode(provider, response)

    def test_jsonl_preview_and_prepare_preserve_ai_disabled(self):
        preview = self.preview()
        requests = [{"protocol_version": 1, "id": "prepare", "method": "cloud.prepare", "params": self.consent(preview)},
                    {"protocol_version": 1, "id": "health", "method": "health", "params": {}}]
        incoming = io.BytesIO(("\n".join(json.dumps(request) for request in requests) + "\n").encode())
        outgoing = io.BytesIO()
        self.assertEqual(serve(self.vault, incoming, outgoing), 0)
        responses = [json.loads(line) for line in outgoing.getvalue().splitlines()]
        self.assertFalse(responses[0]["result"]["can_send"])
        self.assertFalse(responses[1]["result"]["ai_enabled"])


if __name__ == "__main__":
    unittest.main()
