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

"""Example: ``get_cutover_date``.

Returns the binding November 2026 structured-address cutover date and the
scheme that sets it. No input needed.

Usage::

    python examples/09_get_cutover_date.py
"""

from structured_address_fix_mcp.server import get_cutover_date


def main() -> None:
    """Print the cutover date and its governing scheme."""
    result = get_cutover_date()
    print(f"cutover date: {result['date']}")
    print(f"scheme      : {result['scheme']}")


if __name__ == "__main__":
    main()
