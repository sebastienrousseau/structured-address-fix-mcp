#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""What an agent waits for when it calls these tools.

This server wraps `structured-address-fix`. The library is benchmarked in
its own repository, so re-measuring the policy engine here would just
measure that again. What belongs here is the shape an *agent*
experiences: which of the thirteen tools are cheap enough to call freely,
and which are the ones that cost something.

They fall into two groups, about two orders of magnitude apart.

**Lookups and string helpers** -- `get_cutover_date`, `explain_finding`,
`normalize_country_code`, `split_street_and_building`,
`validate_postal_policy`, `list_policies`. All comfortably inside a few
microseconds. An agent can call these in a loop without thinking about
it, which matters because they are exactly the tools it reaches for while
working out *what to do* rather than doing it.

**The pipeline** -- `classify_address`, `assess_address`,
`remediate_address`. Increasing cost in that order, and the order is the
point: classify is a shape test cheap enough to run over an entire
estate, assess applies a policy to what classification flagged, and
remediate produces a patch for what assessment says is worth fixing.
Screening first, fixing second, which is the shape the November 2026
cutover actually has.

`parse_address_libpostal` is measured separately and **reports which
backend it used**. With the optional `postal` extra installed it calls
libpostal's statistical parser; without it, a deterministic fallback.
Those are different pieces of software with different costs, and a
benchmark that printed one number without saying which had run would be
inviting somebody to quote a figure for code they are not executing.

Run::

    python benches/bench_tool_dispatch.py
    python benches/bench_tool_dispatch.py --json
    python benches/bench_tool_dispatch.py --quick     # what CI runs

Nothing here asserts a threshold: wall-clock is not comparable between
machines, and a flaky performance gate teaches people to ignore red. CI
runs ``--quick`` so a benchmark that has stopped compiling against the
current API fails the build instead of rotting into a file that reads as
verified and is not.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from functools import partial
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import structured_address_fix_mcp.server as server  # noqa: E402

STRUCTURED = {
    "street_name": "Baker Street",
    "building_number": "221B",
    "post_code": "NW1 6XE",
    "town_name": "London",
    "country": "GB",
}

UNSTRUCTURED = {
    "country": "GB",
    "address_lines": ["Flat 2", "221B Baker Street", "London NW1 6XE"],
}

FREE_TEXT = "221B Baker Street, London NW1 6XE"

#: Cheap enough that an agent can call them in a loop.
HELPERS = (
    ("get_cutover_date", server.get_cutover_date),
    ("list_policies", server.list_policies),
    ("explain_finding", partial(server.explain_finding, "SAF001")),
    (
        "normalize_country_code",
        partial(server.normalize_country_code, "Deutschland"),
    ),
    (
        "split_street_and_building",
        partial(server.split_street_and_building, "10 Downing Street"),
    ),
    (
        "validate_postal_policy",
        partial(server.validate_postal_policy, STRUCTURED, "GB"),
    ),
)

#: Screening first, fixing second.
PIPELINE = (
    ("classify_address", partial(server.classify_address, STRUCTURED)),
    ("assess_address", partial(server.assess_address, UNSTRUCTURED)),
    ("remediate_address", partial(server.remediate_address, UNSTRUCTURED)),
)


def _best(call, repeats: int) -> float:
    """Best-of timing after one untimed warm-up.

    The minimum is the least noisy estimator available; the mean follows
    whatever else the machine is doing.
    """
    call()
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        call()
        samples.append(time.perf_counter() - start)
    return min(samples)


def parser_backend() -> str:
    """Which parser `parse_address_libpostal` actually used.

    Reported rather than assumed: the optional `postal` extra needs the
    libpostal C library, so a plain install silently runs a different
    implementation, and its timing says nothing about the other one.
    """
    result = server.parse_address_libpostal(FREE_TEXT, "GB")
    return str(result.get("parser", "unknown"))


def run(quick: bool) -> dict:
    repeats = 200 if quick else 2_000
    return {
        "helpers_us": {
            name: _best(call, repeats) * 1e6 for name, call in HELPERS
        },
        "pipeline_us": {
            name: _best(call, repeats) * 1e6 for name, call in PIPELINE
        },
        "parse_address": {
            "backend": parser_backend(),
            "us": _best(
                partial(server.parse_address_libpostal, FREE_TEXT, "GB"),
                repeats,
            )
            * 1e6,
        },
    }


def render(results: dict) -> None:
    print("  Lookups and string helpers -- callable in a loop:\n")
    for name, micros in results["helpers_us"].items():
        print(f"    {name:<28}{micros:>9.2f} us")

    print("\n  The pipeline -- screening first, fixing second:\n")
    for name, micros in results["pipeline_us"].items():
        print(f"    {name:<28}{micros:>9.2f} us")

    helpers = results["helpers_us"].values()
    pipeline = results["pipeline_us"]
    cheapest = min(helpers)
    dearest = pipeline["remediate_address"]
    if cheapest:
        print(
            f"\n    About {dearest / cheapest:.0f}x between the cheapest "
            f"helper and remediation. classify_address is\n    the stage "
            f"meant to run over an entire estate; assess and remediate run "
            f"on the subset\n    each previous stage hands you."
        )

    parse = results["parse_address"]
    print(
        f"\n  parse_address_libpostal      {parse['us']:>9.2f} us   "
        f"(backend: {parse['backend']})"
    )
    if parse["backend"] != "libpostal":
        print(
            "\n  That is the deterministic fallback, not libpostal. The "
            "optional `postal` extra needs\n  the libpostal C library "
            "installed; without it a different implementation runs, and "
            "this\n  number says nothing about the other one. Install the "
            "extra and re-run to measure that\n  path."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "--quick", action="store_true", help="fewer repeats, as CI runs"
    )
    args = parser.parse_args()

    results = run(quick=args.quick)
    if args.json:
        json.dump(results, sys.stdout, indent=1)
        print()
    else:
        render(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
