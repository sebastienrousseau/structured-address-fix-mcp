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

"""Model Context Protocol (MCP) server for structured-address-fix.

Exposes the ``structured-address-fix`` library's ISO 20022 postal-address
remediation as MCP tools so any MCP-compatible client (Claude Desktop,
IDEs, agents) can classify, assess, and remediate the postal addresses in
pacs.008 / pain.001 messages ahead of the 14 November 2026 cliff, when
fully unstructured addresses are rejected across the major schemes.

Every tool is a thin, typed wrapper over
:mod:`structured_address_fix.services` -- the single shared facade also
used by the CLI -- so the MCP surface behaves identically to every other
consumer of the core. Tools return JSON-serializable data; on a domain or
value error they return an ``{"error": ...}`` payload rather than raising.

Launching the server:
    * As a console script::

        structured-address-fix-mcp

    * In an MCP client config (e.g. Claude Desktop)::

        {
          "mcpServers": {
            "structured-address-fix": {
              "command": "structured-address-fix-mcp"
            }
          }
        }

The server communicates over stdio by default (FastMCP's default
transport).
"""

from __future__ import annotations

import argparse
from datetime import date
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field, ValidationError
from structured_address_fix import services
from structured_address_fix.config import NOV_2026_CLIFF
from structured_address_fix.domain.address import CanonicalAddress
from structured_address_fix.domain.findings import FindingCode
from structured_address_fix.errors import StructuredAddressError

from structured_address_fix_mcp import __version__
from structured_address_fix_mcp.explanations import FINDING_EXPLANATIONS

server = FastMCP("structured-address-fix")
# FastMCP does not expose a version kwarg; without this override the MCP
# SDK's own version leaks into serverInfo.version, breaking manifest /
# runtime coherence checks (e.g. Glama scoring).
server._mcp_server.version = __version__

# Every tool here is a pure, side-effect-free reader: it computes solely
# over its arguments (an address object, an XML string, a policy id) or
# over data bundled with the core, writes nothing, and touches neither the
# filesystem nor the network.
_PURE_READ = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)

# Errors the core documents for these entry points. StructuredAddressError
# covers the taxonomy; ValidationError covers a malformed address object;
# ValueError covers a malformed ``as_of`` date.
_HANDLED = (StructuredAddressError, ValidationError, ValueError)

_AddressInput = Annotated[
    dict[str, Any],
    Field(
        description=(
            "An ISO 20022 postal address as a JSON object using canonical "
            "field names, e.g. {'street_name': 'Downing St', "
            "'building_number': '10', 'post_code': 'SW1A 2AA', "
            "'town_name': 'London', 'country': 'GB'} or "
            "{'address_lines': ['10 Downing St', 'London SW1A 2AA'], "
            "'country': 'GB'}."
        )
    ),
]

_PolicyId = Annotated[
    str | None,
    Field(
        default=None,
        description=(
            "The policy to assess against (see list_policies). Defaults to "
            "'cbpr-2026' when omitted."
        ),
    ),
]

_AsOf = Annotated[
    str | None,
    Field(
        default=None,
        description=(
            "The assessment date as an ISO 8601 string (YYYY-MM-DD). "
            "Decides cliff wording; defaults to today."
        ),
    ),
]


def _parse_as_of(as_of: str | None) -> date | None:
    """Parse an optional ISO 8601 date string into a ``date``."""
    if as_of is None:
        return None
    return date.fromisoformat(as_of)


def _address(payload: dict[str, Any]) -> CanonicalAddress:
    """Validate an incoming address object into a canonical address."""
    return CanonicalAddress.model_validate(payload)


def _dump(model: BaseModel) -> dict[str, Any]:
    """Serialize a domain model to a JSON-safe dict."""
    return model.model_dump(mode="json")


@server.tool(title="List address policies", annotations=_PURE_READ)
def list_policies() -> list[dict[str, Any]] | dict[str, Any]:
    """List every available address policy (rulebook) with its tier.

    Use this first to discover the ``policy_id`` values the other tools
    accept (e.g. ``cbpr-2026``, ``sepa``, ``hvps-plus``,
    ``generic-structured``).

    Returns a list of ``{"id": ..., "title": ..., "tier": ...}`` objects.
    """
    try:
        return [_dump(p) for p in services.list_policies()]
    except _HANDLED as exc:
        return {"error": str(exc)}


@server.tool(title="Classify a postal address", annotations=_PURE_READ)
def classify_address(address: _AddressInput) -> dict[str, Any]:
    """Classify a postal address as structured, hybrid, or unstructured.

    Use this for a quick shape check before deciding whether to remediate.
    For the specific compliance findings under a policy, use
    ``assess_address`` instead.

    Args:
        address: The postal address to classify.
    """
    try:
        result = services.classify_address(_address(address))
        return {"classification": result.value}
    except _HANDLED as exc:
        return {"error": str(exc)}


@server.tool(title="Assess a postal address", annotations=_PURE_READ)
def assess_address(
    address: _AddressInput,
    policy_id: _PolicyId = None,
    as_of: _AsOf = None,
    country_hint: Annotated[
        str | None,
        Field(
            default=None,
            description="ISO 3166-1 alpha-2 hint when the address has no "
            "country of its own.",
        ),
    ] = None,
) -> dict[str, Any]:
    """Score a single address against a policy and return its findings.

    Args:
        address: The postal address to assess.
        policy_id: The policy to assess against (defaults to cbpr-2026).
        as_of: The assessment date (YYYY-MM-DD); defaults to today.
        country_hint: Country to assume when the address has none.
    """
    try:
        report = services.assess_address(
            _address(address),
            policy_id,
            as_of=_parse_as_of(as_of),
            country_hint=country_hint,
        )
        return _dump(report)
    except _HANDLED as exc:
        return {"error": str(exc)}


@server.tool(title="Assess an ISO 20022 message", annotations=_PURE_READ)
def assess_message(
    xml: Annotated[str, Field(description="An ISO 20022 message as XML.")],
    policy_id: _PolicyId = None,
    as_of: _AsOf = None,
) -> dict[str, Any]:
    """Assess every addressed party in a pacs.008 / pain.001 message.

    Args:
        xml: The ISO 20022 message document.
        policy_id: The policy to assess against (defaults to cbpr-2026).
        as_of: The assessment date (YYYY-MM-DD); defaults to today.
    """
    try:
        report = services.assess_message(
            xml, policy_id, as_of=_parse_as_of(as_of)
        )
        return _dump(report)
    except _HANDLED as exc:
        return {"error": str(exc)}


@server.tool(title="Remediate a postal address", annotations=_PURE_READ)
def remediate_address(
    address: _AddressInput,
    policy_id: _PolicyId = None,
    as_of: _AsOf = None,
    country_hint: Annotated[
        str | None,
        Field(default=None, description="ISO 3166-1 alpha-2 hint."),
    ] = None,
) -> dict[str, Any]:
    """Propose the compliant form of an address, with explained changes.

    Returns the findings, the before/after addresses, and the patch
    operations (each carrying the finding it resolves, the source token,
    and a confidence score).

    Args:
        address: The postal address to remediate.
        policy_id: The policy to remediate for (defaults to cbpr-2026).
        as_of: The assessment date (YYYY-MM-DD); defaults to today.
        country_hint: Country to assume when the address has none.
    """
    try:
        result = services.remediate_address(
            _address(address),
            policy_id,
            country_hint=country_hint,
            as_of=_parse_as_of(as_of),
        )
        return _dump(result)
    except _HANDLED as exc:
        return {"error": str(exc)}


@server.tool(title="Remediate an ISO 20022 message", annotations=_PURE_READ)
def remediate_message(
    xml: Annotated[str, Field(description="An ISO 20022 message as XML.")],
    policy_id: _PolicyId = None,
    apply: Annotated[
        bool,
        Field(
            default=False,
            description="When true, apply the operations and return the "
            "patched XML in 'patched_xml'.",
        ),
    ] = False,
    as_of: _AsOf = None,
) -> dict[str, Any]:
    """Assess and remediate every addressed party in a message.

    Args:
        xml: The ISO 20022 message document.
        policy_id: The policy to remediate for (defaults to cbpr-2026).
        apply: Whether to apply the operations and return patched XML.
        as_of: The assessment date (YYYY-MM-DD); defaults to today.
    """
    try:
        result = services.remediate_message(
            xml, policy_id, apply=apply, as_of=_parse_as_of(as_of)
        )
        return _dump(result)
    except _HANDLED as exc:
        return {"error": str(exc)}


@server.tool(title="Preview remediation patch", annotations=_PURE_READ)
def preview_patch(
    xml: Annotated[str, Field(description="An ISO 20022 message as XML.")],
    policy_id: _PolicyId = None,
    as_of: _AsOf = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    """Return the patch operations remediation would apply (a dry run).

    Args:
        xml: The ISO 20022 message document.
        policy_id: The policy to remediate for (defaults to cbpr-2026).
        as_of: The assessment date (YYYY-MM-DD); defaults to today.
    """
    try:
        ops = services.preview_patch(xml, policy_id, as_of=_parse_as_of(as_of))
        return [op.model_dump(mode="json", by_alias=True) for op in ops]
    except _HANDLED as exc:
        return {"error": str(exc)}


@server.tool(title="Explain a finding code", annotations=_PURE_READ)
def explain_finding(
    code: Annotated[
        str,
        Field(
            description="A finding code, e.g. 'SAF001' (see the codes in "
            "any assessment result)."
        ),
    ],
) -> dict[str, Any]:
    """Explain what a finding code means and how to resolve it.

    Args:
        code: The finding code to explain.
    """
    try:
        finding_code = FindingCode(code)
    except ValueError:
        return {"error": f"unknown finding code: {code!r}"}
    detail = FINDING_EXPLANATIONS[finding_code]
    return {"code": finding_code.value, **detail}


@server.tool(title="Get the ISO 20022 cutover date", annotations=_PURE_READ)
def get_cutover_date() -> dict[str, Any]:
    """Return the binding November 2026 structured-address cutover date.

    Returns the date and the scheme that sets it.
    """
    return {
        "date": NOV_2026_CLIFF.isoformat(),
        "scheme": "SWIFT CBPR+ UG2026",
    }


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser for the server."""
    parser = argparse.ArgumentParser(
        prog="structured-address-fix-mcp",
        description=(
            "structured-address-fix MCP server (stdio transport). Exposes "
            "ISO 20022 postal-address assessment and remediation as MCP "
            "tools."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"structured-address-fix-mcp {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Run the MCP server over stdio.

    Parses arguments (currently only ``--version``) and starts the FastMCP
    stdio transport, which an MCP client launches as a subprocess.
    """
    _build_parser().parse_args(argv)
    server.run()


if __name__ == "__main__":  # pragma: no cover
    main()
