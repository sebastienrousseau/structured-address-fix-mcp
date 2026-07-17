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

"""Tests for the structured-address-fix MCP server tools."""

from datetime import date

import pytest

pytest.importorskip("mcp")

from mcp.server.fastmcp import FastMCP  # noqa: E402
from pydantic import ValidationError  # noqa: E402
from structured_address_fix.domain.address import (  # noqa: E402
    CanonicalAddress,
)
from structured_address_fix.errors import (  # noqa: E402
    StructuredAddressError,
)

import structured_address_fix_mcp.server as server  # noqa: E402

EXPECTED_TOOLS = {
    "list_policies",
    "classify_address",
    "assess_address",
    "assess_message",
    "remediate_address",
    "remediate_message",
    "preview_patch",
    "explain_finding",
    "get_cutover_date",
}

# A malformed address: a three-letter country breaks the alpha-2 rule, so
# ``CanonicalAddress.model_validate`` raises and the tool returns an error.
BAD_ADDRESS = {"country": "GBR"}


# ---------------------------------------------------------------------------
# Server / tool registration
# ---------------------------------------------------------------------------


def test_server_and_main_are_well_formed():
    """The module exposes a FastMCP server and a callable ``main``."""
    assert isinstance(server.server, FastMCP)
    assert callable(server.main)


@pytest.mark.asyncio
async def test_all_tools_registered():
    """Every one of the nine tools is registered on the server."""
    tools = await server.server.list_tools()
    assert {tool.name for tool in tools} == EXPECTED_TOOLS


# ---------------------------------------------------------------------------
# Helpers: _parse_as_of and _address
# ---------------------------------------------------------------------------


def test_parse_as_of_none_returns_none():
    """A ``None`` input parses to ``None`` (defaults to today downstream)."""
    assert server._parse_as_of(None) is None


def test_parse_as_of_value_returns_date():
    """A valid ISO 8601 string parses to the matching ``date``."""
    assert server._parse_as_of("2026-12-01") == date(2026, 12, 1)


def test_address_valid_returns_canonical(structured_address):
    """A well-formed payload validates into a ``CanonicalAddress``."""
    result = server._address(structured_address)
    assert isinstance(result, CanonicalAddress)
    assert result.country == "GB"


def test_address_invalid_raises():
    """A malformed payload raises ``ValidationError`` (the caught error)."""
    with pytest.raises(ValidationError):
        server._address(BAD_ADDRESS)


# ---------------------------------------------------------------------------
# list_policies
# ---------------------------------------------------------------------------


def test_list_policies_returns_catalog():
    """The tool lists every policy with id, title, and tier."""
    result = server.list_policies()
    assert isinstance(result, list)
    ids = {row["id"] for row in result}
    assert "cbpr-2026" in ids
    assert all({"id", "title", "tier"} <= set(row) for row in result)


def test_list_policies_error_returns_error_dict(monkeypatch):
    """A failing core call yields an ``{"error": ...}`` dict, not a raise."""

    def boom():
        raise StructuredAddressError("boom")

    monkeypatch.setattr(server.services, "list_policies", boom)
    result = server.list_policies()
    assert result == {"error": "boom"}


# ---------------------------------------------------------------------------
# classify_address
# ---------------------------------------------------------------------------


def test_classify_structured(structured_address):
    """A fully structured address classifies as ``structured``."""
    assert server.classify_address(structured_address) == {
        "classification": "structured"
    }


def test_classify_hybrid(hybrid_address):
    """A structured address with residual lines classifies ``hybrid``."""
    assert server.classify_address(hybrid_address) == {
        "classification": "hybrid"
    }


def test_classify_unstructured(unstructured_address):
    """An ``AdrLine``-only address classifies as ``unstructured``."""
    assert server.classify_address(unstructured_address) == {
        "classification": "unstructured"
    }


def test_classify_bad_address_returns_error():
    """A malformed address yields an ``{"error": ...}`` dict."""
    result = server.classify_address(BAD_ADDRESS)
    assert "error" in result


# ---------------------------------------------------------------------------
# assess_address
# ---------------------------------------------------------------------------


def test_assess_address_returns_report(structured_address, post_cliff):
    """Assessing a compliant address returns a validation report."""
    result = server.assess_address(
        structured_address, "cbpr-2026", as_of=post_cliff
    )
    assert "error" not in result
    assert result["is_compliant"] is True


def test_assess_address_country_hint():
    """The ``country_hint`` supplies a country the address itself lacks."""
    result = server.assess_address(
        {"town_name": "London", "street_name": "Downing St"},
        country_hint="GB",
    )
    assert "error" not in result


def test_assess_address_bad_address_returns_error():
    """A malformed address yields an ``{"error": ...}`` dict."""
    assert "error" in server.assess_address(BAD_ADDRESS)


def test_assess_address_unknown_policy_returns_error(structured_address):
    """An unknown policy id is caught and returned as an error dict."""
    result = server.assess_address(
        structured_address, policy_id="no-such-policy"
    )
    assert "error" in result


def test_assess_address_bad_as_of_returns_error(structured_address):
    """A malformed ``as_of`` date is caught and returned as an error."""
    result = server.assess_address(structured_address, as_of="not-a-date")
    assert "error" in result


# ---------------------------------------------------------------------------
# assess_message
# ---------------------------------------------------------------------------


def test_assess_message_returns_report(pacs008_xml, post_cliff):
    """Assessing a message returns a report over its addressed parties."""
    result = server.assess_message(pacs008_xml, as_of=post_cliff)
    assert "error" not in result
    assert result["assessed_addresses"] >= 1
    assert "is_compliant" in result


def test_assess_message_bad_xml_returns_error():
    """Malformed XML yields an ``{"error": ...}`` dict, not an exception."""
    assert "error" in server.assess_message("<nope/>")


def test_assess_message_bad_as_of_returns_error(pacs008_xml):
    """A malformed ``as_of`` date is caught and returned as an error."""
    assert "error" in server.assess_message(pacs008_xml, as_of="not-a-date")


# ---------------------------------------------------------------------------
# remediate_address
# ---------------------------------------------------------------------------


def test_remediate_address_lifts_to_structured(remediable_address, post_cliff):
    """Remediation lifts an unstructured address to a compliant form."""
    result = server.remediate_address(
        remediable_address, "cbpr-2026", as_of=post_cliff
    )
    assert result["is_compliant_after"] is True
    suggestion = result["suggestions"][0]
    assert suggestion["after"]["classification"] == "structured"
    assert len(suggestion["operations"]) == 6


def test_remediate_address_country_hint():
    """The ``country_hint`` feeds remediation when no country is present."""
    result = server.remediate_address(
        {"address_lines": ["10 Downing St", "London SW1A 2AA"]},
        country_hint="GB",
    )
    assert "error" not in result


def test_remediate_address_bad_address_returns_error():
    """A malformed address yields an ``{"error": ...}`` dict."""
    assert "error" in server.remediate_address(BAD_ADDRESS)


# ---------------------------------------------------------------------------
# remediate_message
# ---------------------------------------------------------------------------


def test_remediate_message_preview(pacs008_xml, post_cliff):
    """Without ``apply``, remediation reports suggestions, no patched XML."""
    result = server.remediate_message(pacs008_xml, as_of=post_cliff)
    assert "error" not in result
    assert "suggestions" in result


def test_remediate_message_apply(pacs008_xml, post_cliff):
    """With ``apply=True``, remediation returns patched XML."""
    result = server.remediate_message(
        pacs008_xml, apply=True, as_of=post_cliff
    )
    assert "error" not in result
    assert result["patched_xml"]


def test_remediate_message_bad_xml_returns_error():
    """Malformed XML yields an ``{"error": ...}`` dict, not an exception."""
    assert "error" in server.remediate_message("<nope/>")


# ---------------------------------------------------------------------------
# preview_patch
# ---------------------------------------------------------------------------


def test_preview_patch_returns_ops(pacs008_xml, post_cliff):
    """A dry run returns the list of patch operations."""
    result = server.preview_patch(pacs008_xml, as_of=post_cliff)
    assert isinstance(result, list)
    assert result
    assert all("op" in op for op in result)


def test_preview_patch_bad_xml_returns_error():
    """Malformed XML yields an ``{"error": ...}`` dict, not an exception."""
    result = server.preview_patch("<nope/>")
    assert isinstance(result, dict)
    assert "error" in result


def test_preview_patch_bad_as_of_returns_error(pacs008_xml):
    """A malformed ``as_of`` date is caught and returned as an error."""
    result = server.preview_patch(pacs008_xml, as_of="not-a-date")
    assert isinstance(result, dict)
    assert "error" in result


# ---------------------------------------------------------------------------
# explain_finding
# ---------------------------------------------------------------------------


def test_explain_finding_known_code():
    """A known code returns its summary, impact, and fix."""
    result = server.explain_finding("SAF001")
    assert result["code"] == "SAF001"
    assert {"summary", "impact", "fix"} <= set(result)


def test_explain_finding_unknown_code_returns_error():
    """An unknown code yields an ``{"error": ...}`` dict."""
    result = server.explain_finding("NOPE")
    assert result == {"error": "unknown finding code: 'NOPE'"}


# ---------------------------------------------------------------------------
# get_cutover_date
# ---------------------------------------------------------------------------


def test_get_cutover_date():
    """The cutover tool returns the binding Nov 2026 date and scheme."""
    result = server.get_cutover_date()
    assert result == {
        "date": "2026-11-14",
        "scheme": "SWIFT CBPR+ UG2026",
    }
