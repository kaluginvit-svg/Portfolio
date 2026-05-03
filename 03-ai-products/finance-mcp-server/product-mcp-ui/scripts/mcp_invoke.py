"""One-shot MCP tool invocation for product-mcp-ui (stdout JSON)."""

from __future__ import annotations

import json
import os
import sys


def main() -> None:
    if len(sys.argv) < 3:
        print(json.dumps({"success": False, "error": "usage: mcp_invoke.py <tool> <json_payload>", "data": {}}))
        sys.exit(1)

    root = os.environ.get("PRODUCT_MCP_PATH", "").strip()
    if not root:
        print(json.dumps({"success": False, "error": "PRODUCT_MCP_PATH is not set", "data": {}}))
        sys.exit(0)

    root = os.path.abspath(root)
    os.chdir(root)
    if root not in sys.path:
        sys.path.insert(0, root)

    tool = sys.argv[1]
    try:
        payload = json.loads(sys.argv[2])
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": f"Invalid JSON payload: {e}", "data": {}}))
        sys.exit(0)

    try:
        from config import ensure_data_directories, setup_logging
        from db import init_database
        from seed import seed_if_empty
        from config import DB_PATH

        setup_logging()
        ensure_data_directories()
        init_database(DB_PATH)
        seed_if_empty()

        from mcp.server.fastmcp import FastMCP
        from tools import register_all

        mcp = FastMCP("product-mcp-ui-bridge")
        register_all(mcp)

        import registry

        out = registry.dispatch(tool, payload if isinstance(payload, dict) else {})
        print(json.dumps(out, default=str))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e), "data": {}}))


if __name__ == "__main__":
    main()
