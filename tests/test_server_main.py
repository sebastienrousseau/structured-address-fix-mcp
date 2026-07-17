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

"""Tests for the server's command-line entry point (``main``)."""

import pytest

import structured_address_fix_mcp.server as server
from structured_address_fix_mcp import __version__


def test_main_version_exits_zero_and_prints(capsys):
    """``main(["--version"])`` prints the version and exits with code 0."""
    with pytest.raises(SystemExit) as excinfo:
        server.main(["--version"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    assert __version__ in out
    assert "structured-address-fix-mcp" in out


def test_main_runs_server(monkeypatch):
    """``main([])`` starts the FastMCP stdio loop via ``server.run``."""
    calls = []
    monkeypatch.setattr(
        server.server, "run", lambda *a, **k: calls.append((a, k))
    )
    assert server.main([]) is None
    assert len(calls) == 1
