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

"""Example: ``remediate_message``.

Assesses and remediates every addressed party in a pacs.008 message.
With ``apply=True`` it returns the patched XML.

Usage::

    python examples/06_remediate_message.py
"""

from pathlib import Path

from structured_address_fix_mcp.server import remediate_message

XML = (
    (Path(__file__).resolve().parent / "_data")
    .joinpath("pacs008_three_party.xml")
    .read_text(encoding="utf-8")
)


def main() -> None:
    """Remediate the sample message and report the patched result."""
    result = remediate_message(
        XML, "cbpr-2026", apply=True, as_of="2026-12-01"
    )
    print(f"compliant before: {result['is_compliant_before']}")
    print(f"compliant after : {result['is_compliant_after']}")
    print(f"suggestions     : {len(result['suggestions'])}")
    print(f"patched_xml bytes: {len(result['patched_xml'])}")


if __name__ == "__main__":
    main()
