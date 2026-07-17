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

"""Example: ``classify_address``.

Classifies postal addresses as structured, hybrid, or unstructured -- a
quick shape check before deciding whether to remediate.

Usage::

    python examples/02_classify_address.py
"""

from structured_address_fix_mcp.server import classify_address

ADDRESSES = {
    "structured": {
        "street_name": "Downing St",
        "building_number": "10",
        "post_code": "SW1A 2AA",
        "town_name": "London",
        "country": "GB",
    },
    "hybrid": {
        "town_name": "London",
        "country": "GB",
        "address_lines": ["Flat 2", "221B Baker St"],
    },
    "unstructured": {
        "address_lines": ["10 Downing St", "London SW1A 2AA"],
        "country": "GB",
    },
}


def main() -> None:
    """Classify one address of each shape and print the verdict."""
    for expected, address in ADDRESSES.items():
        result = classify_address(address)
        print(f"  expected {expected:<13} -> {result['classification']}")


if __name__ == "__main__":
    main()
