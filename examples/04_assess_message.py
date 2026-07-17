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

"""Example: ``assess_message``.

Assesses every addressed party in a pacs.008 message against a policy,
as of a date past the 14 November 2026 cliff.

Usage::

    python examples/04_assess_message.py
"""

from pathlib import Path

from structured_address_fix_mcp.server import assess_message

XML = (
    (Path(__file__).resolve().parent / "_data")
    .joinpath("pacs008_three_party.xml")
    .read_text(encoding="utf-8")
)


def main() -> None:
    """Assess every party in the sample message and print findings."""
    report = assess_message(XML, "cbpr-2026", as_of="2026-12-01")
    print(f"policy           : {report['policy_id']}")
    print(f"assessed_addresses: {report['assessed_addresses']}")
    print(f"is_compliant     : {report['is_compliant']}")
    for finding in report["findings"]:
        print(
            f"  {finding['code']}  {finding['location']}  "
            f"{finding['message']}"
        )


if __name__ == "__main__":
    main()
