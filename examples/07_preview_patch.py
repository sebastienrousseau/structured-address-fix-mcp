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

"""Example: ``preview_patch``.

A dry run: returns the patch operations remediation *would* apply to a
message, without producing the patched XML.

Usage::

    python examples/07_preview_patch.py
"""

from pathlib import Path

from structured_address_fix_mcp.server import preview_patch

XML = (
    (Path(__file__).resolve().parent / "_data")
    .joinpath("pacs008_three_party.xml")
    .read_text(encoding="utf-8")
)


def main() -> None:
    """Preview the patch operations for the sample message."""
    ops = preview_patch(XML, "cbpr-2026", as_of="2026-12-01")
    print(f"proposed operations ({len(ops)}):")
    for op in ops:
        print(
            f"  {op['op']:<6} {op['path']:<10} "
            f"[{op.get('reason_code')}]  {op.get('value') or ''}"
        )


if __name__ == "__main__":
    main()
