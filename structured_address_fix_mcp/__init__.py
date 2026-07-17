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

"""structured-address-fix-mcp: an MCP server for ISO 20022 address fixing.

A thin Model Context Protocol transport over the ``structured-address-fix``
library. Every tool is a typed wrapper over the shared
``structured_address_fix.services`` facade, so the MCP surface behaves
identically to the CLI and any other consumer of the core.
"""

__version__ = "0.1.0"
