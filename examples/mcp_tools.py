#!/usr/bin/env python3
# Copyright (C) 2023-2026 Sebastien Rousseau.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Example: drive the structured-address-fix MCP tools in-process.

The server (launched as ``structured-address-fix-mcp`` over stdio)
exposes the ``structured-address-fix`` library to AI agents. This example
invokes the same tools directly through the FastMCP instance, without a
transport, to show what an agent would receive.

Usage::

    pip install structured-address-fix-mcp   # requires Python 3.12+
    python examples/mcp_tools.py
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from structured_address_fix_mcp.server import server

XML = (
    (Path(__file__).resolve().parent / "_data")
    .joinpath("pacs008_three_party.xml")
    .read_text(encoding="utf-8")
)


async def _call(name: str, args: dict[str, Any]) -> str:
    """Invoke a tool through FastMCP and return its first text block.

    FastMCP returns either a ``(content, structured)`` tuple or a plain
    sequence of content blocks depending on the tool's return type; the
    leading text block carries the JSON payload in every case.
    """
    result = await server.call_tool(name, args)
    content = result[0] if isinstance(result, tuple) else result
    return content[0].text if content else ""


async def main() -> None:
    """Call a representative slice of the server's nine tools."""
    names = [tool.name for tool in await server.list_tools()]
    print("Registered MCP tools:", names)

    print(
        "list_policies    ->", (await _call("list_policies", {}))[:60], "..."
    )
    print(
        "classify_address ->",
        await _call(
            "classify_address",
            {
                "address": {
                    "address_lines": ["10 Downing St", "London"],
                    "country": "GB",
                }
            },
        ),
    )
    print(
        "preview_patch    ->",
        (await _call("preview_patch", {"xml": XML, "as_of": "2026-12-01"}))[
            :60
        ],
        "...",
    )
    print("get_cutover_date ->", await _call("get_cutover_date", {}))


if __name__ == "__main__":
    asyncio.run(main())
