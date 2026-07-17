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

"""Example: ``remediate_address``.

Proposes the compliant form of an unstructured address and prints the
before/after plus each patch operation, evaluated past the cliff.

Usage::

    python examples/05_remediate_address.py
"""

from structured_address_fix_mcp.server import remediate_address

ADDRESS = {
    "address_lines": ["Flat 2", "221B Baker St", "London NW1 6XE"],
    "country": "GB",
}


def main() -> None:
    """Remediate an unstructured address and print the plan."""
    result = remediate_address(ADDRESS, "cbpr-2026", as_of="2026-12-01")
    suggestion = result["suggestions"][0]
    print(f"compliant before: {result['is_compliant_before']}")
    print(f"compliant after : {result['is_compliant_after']}")
    print(f"class after     : {suggestion['after']['classification']}")
    print("operations      :")
    for op in suggestion["operations"]:
        print(f"  {op['op']:<6} {op['path']:<10} {op.get('value') or ''}")


if __name__ == "__main__":
    main()
