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

"""Example: ``explain_finding``.

Explains what a finding code means, why it matters for the November 2026
cliff, and how to resolve it.

Usage::

    python examples/08_explain_finding.py
"""

from structured_address_fix_mcp.server import explain_finding

CODES = ["SAF001", "SAF002", "SAF003"]


def main() -> None:
    """Explain a handful of finding codes."""
    for code in CODES:
        detail = explain_finding(code)
        print(f"{detail['code']}: {detail['summary']}")
        print(f"  impact: {detail['impact']}")
        print(f"  fix   : {detail['fix']}")


if __name__ == "__main__":
    main()
