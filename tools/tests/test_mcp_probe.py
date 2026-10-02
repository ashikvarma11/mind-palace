"""Real local stdio protocol checks; no external assistant is connected."""
import asyncio
import os
from pathlib import Path
import sys
import unittest
import tempfile

from mcp import Client, StdioServerParameters

PROBE = Path(__file__).resolve().parents[1] / "probe-mcp.py"


class MCPProbeTests(unittest.IsolatedAsyncioTestCase):
    async def verify(self, frozen, mode):
        command = os.environ["MP_FROZEN_MCP_PROBE"] if frozen else sys.executable
        environment = {"OTEL_SDK_DISABLED": "true"}
        if frozen:
            environment["PATH"] = str(Path(os.environ["SystemRoot"]) / "System32")
        directory = tempfile.TemporaryDirectory(prefix="mind-palace-mcp-test-")
        self.addCleanup(directory.cleanup)
        parameters = StdioServerParameters(command=command, args=[] if frozen else [str(PROBE)],
                                          env=environment, cwd=directory.name)
        async with asyncio.timeout(30):
            async with Client(parameters, mode=mode, read_timeout_seconds=10) as client:
                self.assertEqual(client.protocol_version, "2025-11-25" if mode == "legacy" else "2026-07-28")
                tools = await client.list_tools()
                self.assertEqual([tool.name for tool in tools.tools], ["diagnostic_status"])
                self.assertIs(tools.tools[0].annotations.read_only_hint, True)
                result = await client.call_tool("diagnostic_status", {})
                self.assertFalse(result.is_error)
                self.assertEqual(result.structured_content, {"synthetic": True, "vault_access": False,
                                                            "cloud_access": False, "frozen": frozen})
                try:
                    unknown = await client.call_tool("search_memory", {})
                except Exception as error:
                    self.assertIn("Unknown tool", str(error))
                else:
                    self.assertTrue(unknown.is_error)

    async def test_source_legacy_handshake(self):
        await self.verify(False, "legacy")

    async def test_source_modern_discovery(self):
        await self.verify(False, "auto")

    @unittest.skipUnless(os.environ.get("MP_FROZEN_MCP_PROBE"), "Frozen MCP probe not specified")
    async def test_frozen_stdio(self):
        await self.verify(True, "legacy")


if __name__ == "__main__":
    unittest.main()
