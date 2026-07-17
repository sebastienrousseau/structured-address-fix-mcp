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

"""Example: ``assess_address``.

Scores a single address against a policy (defaulting to ``cbpr-2026``)
and reports the compliance findings, evaluated as of a date past the
14 November 2026 cliff.

Usage::

    python examples/03_assess_address.py
"""

from structured_address_fix_mcp.server import assess_address

UNSTRUCTURED = {
    "address_lines": ["10 Downing St", "London SW1A 2AA"],
    "country": "GB",
}


def main() -> None:
    """Assess an unstructured address and print its findings."""
    report = assess_address(UNSTRUCTURED, "cbpr-2026", as_of="2026-12-01")
    print(f"policy      : {report['policy_id']}")
    print(f"is_compliant: {report['is_compliant']}")
    print("findings    :")
    for finding in report["findings"]:
        print(f"  {finding['code']}  {finding['message']}")


if __name__ == "__main__":
    main()
