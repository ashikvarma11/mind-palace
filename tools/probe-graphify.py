"""Step 02: pinned local Graphify extraction of a synthetic fixture only."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import tempfile
import re


def deny_network(event, arguments):
    if event in ("socket.connect", "socket.connect_ex", "socket.getaddrinfo", "subprocess.Popen", "os.system"):
        raise PermissionError("Network and child processes are disabled in this diagnostic")


def prepare_environment():
    for name in list(os.environ):
        upper = name.upper()
        if any(part in upper for part in ("API_KEY", "TOKEN", "SECRET", "CREDENTIAL", "PROXY")):
            os.environ.pop(name)
        elif upper.startswith(("GRAPHIFY_", "OPENAI_", "ANTHROPIC_", "AWS_", "AZURE_", "GOOGLE_", "GEMINI_", "OLLAMA_")):
            os.environ.pop(name)
    os.environ["GRAPHIFY_QUERY_LOG_DISABLE"] = "1"
    sys.dont_write_bytecode = True
    sys.addaudithook(deny_network)


def validate_graph(graph, root):
    allowed_sources = {"src/auth.ts", "src/store.ts"}
    ids = {node["id"] for node in graph["nodes"]}
    if len(ids) != len(graph["nodes"]):
        raise ValueError("Duplicate graph nodes")
    for item in graph["nodes"] + graph["edges"]:
        source = item["source_file"]
        location = item["source_location"]
        if source not in allowed_sources or not re.fullmatch(r"L[1-9][0-9]*", location):
            raise ValueError("Invalid source evidence")
        if int(location[1:]) > len((root / source).read_text(encoding="utf-8").splitlines()):
            raise ValueError("Source line outside fixture")
        if item["_origin"] != "ast":
            raise ValueError("Unexpected provenance")
    for edge in graph["edges"]:
        if edge["source"] not in ids or edge["target"] not in ids:
            raise ValueError("Dangling graph edge")
        if edge["confidence"] not in ("EXTRACTED", "INFERRED"):
            raise ValueError("Unknown edge confidence")
    expected_call = any(edge["source"] == "src_auth_authservice_remember" and
                        edge["target"] == "src_store_memorystore_save" and
                        edge["relation"] == "calls" and edge["confidence"] == "INFERRED" and
                        edge["source_file"] == "src/auth.ts" and edge["source_location"] == "L7"
                        for edge in graph["edges"])
    if not expected_call:
        raise ValueError("Known cross-file call was not resolved with its inferred status")


def probe():
    if importlib.metadata.version("graphifyy") != "0.9.73":
        raise RuntimeError("Uninspected Graphify version")
    from graphify.extract import extract
    root = Path(__file__).resolve().parent / "fixtures" / "probe-repo"
    files = [root / "src" / "auth.ts", root / "src" / "store.ts"]
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in root.rglob("*") if path.is_file()}
    with tempfile.TemporaryDirectory(prefix="mind-palace-graph-probe-") as directory:
        graph = extract(files, root=root, cache_root=Path(directory), parallel=False)
    after = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in root.rglob("*") if path.is_file()}
    if before != after:
        raise RuntimeError("Extractor changed fixture files")
    if graph["input_tokens"] != 0 or graph["output_tokens"] != 0 or graph["failed_sources"]:
        raise RuntimeError("Unexpected extraction failure or model use")
    validate_graph(graph, root)
    return graph


if __name__ == "__main__":
    prepare_environment()
    print(json.dumps(probe(), ensure_ascii=False, indent=2))
