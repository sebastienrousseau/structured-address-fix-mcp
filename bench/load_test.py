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

"""In-process load/latency harness for structured-address-fix-mcp.

v0.1 of the server speaks stdio only: an MCP client launches one process
per operator and there is no network listener to hammer with a real HTTP
load tool. So this harness measures the thing that actually costs time --
the tool dispatch through the FastMCP instance and the underlying
``structured_address_fix.services`` work -- by driving the tools
in-process in a loop and reporting the latency distribution.

It is deliberately dependency-free (standard library only) and lives
outside the pytest / coverage gates (``bench/`` is not in ``testpaths``).
Run it directly::

    python bench/load_test.py                # default: 2000 iterations
    python bench/load_test.py --iterations 10000
    python bench/load_test.py --tool assess_message

The numbers are a local micro-benchmark of dispatch overhead, not a
throughput SLA -- treat them as a regression signal, not a headline.
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
import sys
import time
from pathlib import Path
from typing import Any

# Allow ``python bench/load_test.py`` to run straight from a checkout even
# when the package has not been installed (editable or otherwise): put the
# repo root on the path so ``structured_address_fix_mcp`` imports.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from structured_address_fix_mcp import server  # noqa: E402

# A fully unstructured address (two free-text lines, no structured
# fields) -- the shape rejected at the 14 Nov 2026 cliff, and the most
# expensive to classify + remediate, so it is a fair worst case.
_UNSTRUCTURED: dict[str, Any] = {
    "address_lines": ["10 Downing St", "London SW1A 2AA"],
    "country": "GB",
}

# One representative call per read-only tool that needs no message XML.
# (assess_message / remediate_message / preview_patch take a full XML
# document; point --tool at them with your own payload if you want to
# benchmark the parsing path.)
_WORKLOADS: dict[str, dict[str, Any]] = {
    "get_cutover_date": {},
    "list_policies": {},
    "classify_address": {"address": _UNSTRUCTURED},
    "assess_address": {"address": _UNSTRUCTURED, "policy_id": "cbpr-2026"},
    "remediate_address": {"address": _UNSTRUCTURED, "policy_id": "cbpr-2026"},
    "explain_finding": {"code": "SAF001"},
}


async def _call(name: str, args: dict[str, Any]) -> None:
    """Dispatch one tool call through the FastMCP instance."""
    await server.server.call_tool(name, args)


def _percentile(values: list[float], pct: float) -> float:
    """Return the ``pct`` percentile (0-100) of ``values`` in ms."""
    if not values:
        return 0.0
    ordered = sorted(values)
    k = max(0, min(len(ordered) - 1, round(pct / 100 * (len(ordered) - 1))))
    return ordered[k] * 1000.0


async def _run(tool: str, args: dict[str, Any], iterations: int) -> None:
    """Drive ``tool`` ``iterations`` times and print a latency summary."""
    # Warm up so import / first-call costs don't skew the distribution.
    for _ in range(min(50, iterations)):
        await _call(tool, args)

    samples: list[float] = []
    started = time.perf_counter()
    for _ in range(iterations):
        t0 = time.perf_counter()
        await _call(tool, args)
        samples.append(time.perf_counter() - t0)
    elapsed = time.perf_counter() - started

    rps = iterations / elapsed if elapsed else float("inf")
    print(f"tool={tool}  iterations={iterations}")
    print(f"  wall           {elapsed:8.3f} s")
    print(f"  throughput     {rps:8.1f} calls/s")
    print(f"  mean           {statistics.mean(samples) * 1000:8.3f} ms")
    print(f"  p50            {_percentile(samples, 50):8.3f} ms")
    print(f"  p95            {_percentile(samples, 95):8.3f} ms")
    print(f"  p99            {_percentile(samples, 99):8.3f} ms")
    print(f"  max            {max(samples) * 1000:8.3f} ms")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the harness command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tool",
        default="all",
        choices=["all", *_WORKLOADS],
        help="Which tool to drive (default: all no-XML read-only tools).",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=2000,
        help="Calls per tool (default: 2000).",
    )
    return parser.parse_args(argv)


async def _main(argv: list[str] | None = None) -> None:
    """Run the selected workload(s)."""
    ns = _parse_args(argv)
    tools = list(_WORKLOADS) if ns.tool == "all" else [ns.tool]
    for name in tools:
        await _run(name, _WORKLOADS[name], ns.iterations)
        print()


if __name__ == "__main__":
    asyncio.run(_main())
