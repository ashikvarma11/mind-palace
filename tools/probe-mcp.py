"""Synthetic MCP stdio diagnostic. No memory tools, vaults or cloud transport."""
import importlib.metadata
import os
import sys

os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["OTEL_TRACES_EXPORTER"] = "none"
os.environ["OTEL_METRICS_EXPORTER"] = "none"
os.environ["OTEL_LOGS_EXPORTER"] = "none"

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

if importlib.metadata.version("mcp") != "2.2.0":
    raise RuntimeError("Uninspected MCP version")

server = MCPServer("Mind Palace diagnostic only", version="0.0.0", log_level="WARNING")


@server.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False,
                                        idempotentHint=True, openWorldHint=False))
def diagnostic_status() -> dict[str, bool]:
    """Return synthetic diagnostic flags only. Does not read or write memory."""
    return {"synthetic": True, "vault_access": False, "cloud_access": False,
            "frozen": bool(getattr(sys, "frozen", False))}


if __name__ == "__main__":
    server.run(transport="stdio")
