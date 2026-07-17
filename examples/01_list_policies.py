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

"""Example: ``list_policies``.

Lists every address policy (rulebook) the server can assess against.
Call this first to discover the ``policy_id`` values the other tools
accept. No input needed.

Usage::

    python examples/01_list_policies.py
"""

from structured_address_fix_mcp.server import list_policies


def main() -> None:
    """Print every available policy with its id, title, and tier."""
    policies = list_policies()
    print(f"Available address policies ({len(policies)}):")
    for policy in policies:
        print(f"  {policy['id']:<20}  [{policy['tier']}]  {policy['title']}")


if __name__ == "__main__":
    main()
