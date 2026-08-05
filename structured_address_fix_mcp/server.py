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

The server communicates over stdio by default (MCPServer's default
transport).
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import date
from typing import Annotated, Any

from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field, ValidationError
from structured_address_fix import services
from structured_address_fix.config import NOV_2026_CLIFF
from structured_address_fix.domain.address import CanonicalAddress
from structured_address_fix.domain.findings import FindingCode
from structured_address_fix.errors import StructuredAddressError
from structured_address_fix.services.facade import (
    PolicyInfo,
    default_registry,
)

from structured_address_fix_mcp import __version__
from structured_address_fix_mcp._mcp_compat import build_server
from structured_address_fix_mcp.explanations import FINDING_EXPLANATIONS

server = build_server("structured-address-fix", __version__)

# Every tool here is a pure, side-effect-free reader: it computes solely
# over its arguments (an address object, an XML string, a policy id) or
# over data bundled with the core, writes nothing, and touches neither the
# filesystem nor the network.
# The camelCase spellings are deliberate and must not be "fixed" to
# snake_case. mcp 1.x names these fields `readOnlyHint` etc.; mcp 2.x
# renamed them to `read_only_hint` and kept the camelCase spellings as
# aliases. So camelCase is the only form that works on both majors —
# passing snake_case to 1.x silently lands in an extra attribute and
# leaves the real field None, dropping the annotation without error.
# mypy resolves against 2.x, where the alias is invisible to it.
_PURE_READ = ToolAnnotations(  # type: ignore[call-arg]
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


# ---------------------------------------------------------------------------
# Bundled reference data for the address-splitter tools (Cap 54-56).
#
# These tools compute purely over their arguments and a table shipped inside
# this module -- no new runtime dependency (no pycountry), no network, no
# filesystem. Kept local so the offline, side-effect-free contract of every
# tool here holds.
# ---------------------------------------------------------------------------


def _normalize_key(value: str) -> str:
    """Fold a country string to a lookup key.

    Strips diacritics (so ``España`` matches ``Espana``), lowercases,
    drops periods (so ``U.S.A.`` matches ``USA``), and collapses runs of
    whitespace to single spaces.
    """
    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(
        ch for ch in decomposed if not unicodedata.combining(ch)
    )
    return " ".join(without_accents.lower().replace(".", "").split())


# ISO 3166-1 alpha-2 code -> the names, aliases, and alpha-3 code that
# should resolve to it. Covers the major markets with common
# local-language endonyms (Deutschland, España, Nippon, ...) and everyday
# aliases (UK, USA, Holland, UAE). Not exhaustive of all 249 codes by
# design -- a bundled, dependency-free table for the addresses these tools
# actually see.
_COUNTRY_NAMES: dict[str, tuple[str, ...]] = {
    "US": ("usa", "united states", "united states of america", "america"),
    "CA": ("can", "canada"),
    "MX": ("mex", "mexico"),
    "GB": (
        "gbr",
        "united kingdom",
        "uk",
        "great britain",
        "britain",
        "england",
        "scotland",
        "wales",
        "northern ireland",
    ),
    "IE": ("irl", "ireland", "eire"),
    "FR": ("fra", "france"),
    "DE": ("deu", "germany", "deutschland"),
    "ES": ("esp", "spain", "espana"),
    "PT": ("prt", "portugal"),
    "IT": ("ita", "italy", "italia"),
    "NL": ("nld", "netherlands", "nederland", "holland", "the netherlands"),
    "BE": ("bel", "belgium", "belgique", "belgie"),
    "LU": ("lux", "luxembourg"),
    "CH": ("che", "switzerland", "schweiz", "suisse", "svizzera"),
    "AT": ("aut", "austria", "osterreich"),
    "DK": ("dnk", "denmark", "danmark"),
    "SE": ("swe", "sweden", "sverige"),
    "NO": ("nor", "norway", "norge"),
    "FI": ("fin", "finland", "suomi"),
    "IS": ("isl", "iceland", "island"),
    "PL": ("pol", "poland", "polska"),
    "CZ": ("cze", "czechia", "czech republic", "cesko"),
    "SK": ("svk", "slovakia", "slovensko"),
    "HU": ("hun", "hungary", "magyarorszag"),
    "RO": ("rou", "romania", "romania"),
    "GR": ("grc", "greece", "hellas", "ellada"),
    "HR": ("hrv", "croatia", "hrvatska"),
    "RU": ("rus", "russia", "russian federation"),
    "UA": ("ukr", "ukraine"),
    "TR": ("tur", "turkey", "turkiye"),
    "JP": ("jpn", "japan", "nippon", "nihon"),
    "CN": ("chn", "china", "prc", "peoples republic of china"),
    "HK": ("hkg", "hong kong"),
    "TW": ("twn", "taiwan"),
    "KR": ("kor", "south korea", "korea", "republic of korea"),
    "IN": ("ind", "india", "bharat"),
    "ID": ("idn", "indonesia"),
    "SG": ("sgp", "singapore"),
    "MY": ("mys", "malaysia"),
    "TH": ("tha", "thailand"),
    "VN": ("vnm", "vietnam", "viet nam"),
    "PH": ("phl", "philippines"),
    "AU": ("aus", "australia"),
    "NZ": ("nzl", "new zealand"),
    "BR": ("bra", "brazil", "brasil"),
    "AR": ("arg", "argentina"),
    "CL": ("chl", "chile"),
    "CO": ("col", "colombia"),
    "ZA": ("zaf", "south africa"),
    "NG": ("nga", "nigeria"),
    "EG": ("egy", "egypt"),
    "MA": ("mar", "morocco", "maroc"),
    "IL": ("isr", "israel"),
    "SA": ("sau", "saudi arabia"),
    "AE": ("are", "united arab emirates", "uae", "emirates"),
    "QA": ("qat", "qatar"),
}

# Flattened lookup: every alias (and the alpha-2 code itself) normalised to
# its alpha-2 code. Built once at import.
_COUNTRY_LOOKUP: dict[str, str] = {}
for _code, _aliases in _COUNTRY_NAMES.items():
    _COUNTRY_LOOKUP[_normalize_key(_code)] = _code
    for _alias in _aliases:
        _COUNTRY_LOOKUP[_normalize_key(_alias)] = _code


# A building number: a run of digits, an optional range (10-12, 10/12) and
# an optional trailing letter (221B).
_BUILDING = r"\d+(?:[-/]\d+)?[A-Za-z]?"
# Leading number: "10 Downing Street" (US/UK convention).
_LEADING_NUM = re.compile(rf"^(?P<num>{_BUILDING})\s+(?P<rest>.+?)$")
# Trailing number: "Rue de Rivoli 12" (much of continental Europe).
_TRAILING_NUM = re.compile(rf"^(?P<rest>.+?)\s+(?P<num>{_BUILDING})$")
# Sub-building marker: "Flat 2", "Apt 3B", "Suite 400", "Unit 5", "#7".
_SUB_BUILDING = re.compile(
    r"\b(?:flat|apartment|apt|unit|suite|room|floor|building|bldg)\b\.?"
    r"\s*#?\s*(?:[0-9]+[a-z]?|[a-z])\b",
    re.IGNORECASE,
)

# Country-specific post_code format rules: alpha-2 -> (pattern, human
# description). US ZIP (5 or 5+4), UK alphanumeric, DE/FR 5-digit, JP
# 3-then-4-digit.
_POSTAL_RULES: dict[str, tuple[re.Pattern[str], str]] = {
    "US": (
        re.compile(r"^\d{5}(?:-\d{4})?$"),
        "5 digits or ZIP+4, e.g. 90210 or 90210-1234",
    ),
    "GB": (
        re.compile(r"^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$", re.IGNORECASE),
        "UK postcode, e.g. SW1A 2AA",
    ),
    "DE": (re.compile(r"^\d{5}$"), "5 digits, e.g. 10115"),
    "FR": (re.compile(r"^\d{5}$"), "5 digits, e.g. 75001"),
    "JP": (
        re.compile(r"^\d{3}-?\d{4}$"),
        "3 then 4 digits, e.g. 100-0001",
    ),
}


@server.tool(title="Normalize a country code", annotations=_PURE_READ)
def normalize_country_code(
    country_name_or_code: Annotated[
        str,
        Field(
            description=(
                "A country name, endonym, alias, or 2/3-letter code, e.g. "
                "'Deutschland', 'UK', 'U.S.A.', 'DEU'."
            )
        ),
    ],
) -> dict[str, Any]:
    """Resolve a country name or code to its ISO 3166-1 alpha-2 code.

    Accepts English names, common local-language endonyms (Deutschland,
    España, Nippon), everyday aliases (UK, USA, Holland, UAE), and existing
    2- or 3-letter codes. Matching is case-, accent-, and punctuation-
    insensitive.

    Args:
        country_name_or_code: The country name, alias, or code to resolve.

    Returns a ``{"country_code": "DE"}`` object, or ``{"error": ...}`` when
    the input matches no known country.
    """
    code = _COUNTRY_LOOKUP.get(_normalize_key(country_name_or_code))
    if code is None:
        return {"error": f"unknown country: {country_name_or_code!r}"}
    return {"country_code": code}


@server.tool(title="Split street and building", annotations=_PURE_READ)
def split_street_and_building(
    street_line: Annotated[
        str,
        Field(
            description=(
                "A single free-text street line, e.g. '10 Downing Street', "
                "'Rue de Rivoli 12', or 'Flat 2, 221B Baker Street'."
            )
        ),
    ],
) -> dict[str, Any]:
    """Split a street line into street name, building, and sub-building.

    Handles the leading-number convention (US/UK: ``10 Downing Street``),
    the trailing-number convention (much of continental Europe: ``Rue de
    Rivoli 12``), and an optional sub-building marker (``Flat 2``, ``Apt
    3B``, ``Suite 400``). When no building number is present the whole line
    is returned as ``street_name`` (never an error).

    Args:
        street_line: The free-text street line to split.

    Returns ``{"street_name", "building_number", "sub_building"}`` with
    ``building_number`` / ``sub_building`` set to ``null`` when absent.
    """
    line = street_line.strip()

    sub_building: str | None = None
    sub_match = _SUB_BUILDING.search(line)
    if sub_match is not None:
        sub_building = sub_match.group(0).strip()
        line = (line[: sub_match.start()] + line[sub_match.end() :]).strip()
        line = line.strip(",").strip()

    building_number: str | None = None
    leading = _LEADING_NUM.match(line)
    trailing = _TRAILING_NUM.match(line)
    if leading is not None:
        building_number = leading.group("num")
        street_name = leading.group("rest").strip()
    elif trailing is not None:
        building_number = trailing.group("num")
        street_name = trailing.group("rest").strip()
    else:
        street_name = line

    return {
        "street_name": street_name,
        "building_number": building_number,
        "sub_building": sub_building,
    }


@server.tool(title="Validate a postal-code policy", annotations=_PURE_READ)
def validate_postal_policy(
    address: _AddressInput,
    country_code: Annotated[
        str,
        Field(
            description=(
                "The ISO 3166-1 alpha-2 code whose post_code policy to "
                "apply (US, GB, DE, FR, JP)."
            )
        ),
    ],
) -> dict[str, Any]:
    """Validate an address's post_code against a country's format policy.

    Supported policies: US (5-digit ZIP or ZIP+4), GB (alphanumeric UK
    postcode), DE and FR (5 digits), JP (3-then-4 digits). The address is a
    canonical-field JSON object; only its ``post_code`` is inspected.

    Args:
        address: The structured address whose post_code to validate.
        country_code: The alpha-2 code selecting the policy.

    Returns ``{"is_compliant": bool, "policy_errors": [...]}``. An unknown
    country or a missing post_code is reported as non-compliant with a
    descriptive error rather than raising.
    """
    code = country_code.strip().upper()
    rule = _POSTAL_RULES.get(code)
    if rule is None:
        return {
            "is_compliant": False,
            "policy_errors": [
                f"no postal policy defined for country {code!r}"
            ],
        }

    pattern, description = rule
    post_code = str(address.get("post_code") or "").strip()
    errors: list[str] = []
    if not post_code:
        errors.append("missing post_code")
    elif pattern.match(post_code) is None:
        errors.append(
            f"post_code {post_code!r} does not match the {code} policy "
            f"({description})"
        )
    return {"is_compliant": not errors, "policy_errors": errors}


# ---------------------------------------------------------------------------
# libpostal address parser (Cap 51).
#
# ``parse_address_libpostal`` parses a single free-text address into the ISO
# 20022 postal fields. When the optional ``postal`` binding (pypostal, which
# needs the system libpostal C library) is installed it uses libpostal's
# statistical parser; otherwise it degrades gracefully to the repo's own
# regex heuristics (the country lookup, per-country postal rules, and the
# street/building splitter defined above). The result carries a ``parser``
# field so callers know which path ran.
# ---------------------------------------------------------------------------

#: libpostal component label -> ISO 20022 element local name. libpostal
#: emits ``country`` too; it is handled separately because it must be
#: normalised to an alpha-2 code rather than copied verbatim.
_LIBPOSTAL_TO_ISO: dict[str, str] = {
    "road": "StrtNm",
    "house_number": "BldgNb",
    "postcode": "PstCd",
    "city": "TwnNm",
}

#: The ISO 20022 postal fields these parsers populate, in a stable order.
_ISO_ADDRESS_FIELDS = ("StrtNm", "BldgNb", "PstCd", "TwnNm", "Ctry")


def _empty_iso_fields() -> dict[str, str | None]:
    """Return the ISO 20022 postal fields all set to ``None``."""
    return dict.fromkeys(_ISO_ADDRESS_FIELDS)


def _strip_trailing_country(
    words: list[str],
) -> tuple[str | None, list[str]]:
    """Peel a trailing country name/alias off a word list.

    Tries the last three, two, then one word(s) against the bundled
    country lookup so multi-word names (``United Arab Emirates``) match
    before single-word ones. Returns the resolved alpha-2 code (or
    ``None``) and the remaining words with the country removed.
    """
    for size in (3, 2, 1):
        if len(words) >= size:
            candidate = " ".join(words[-size:])
            code = _COUNTRY_LOOKUP.get(_normalize_key(candidate))
            if code is not None:
                return code, words[:-size]
    return None, words


def _extract_postcode(
    words: list[str], country: str | None
) -> tuple[str | None, list[str]]:
    """Pull a country-shaped post code out of a word list.

    Uses the per-country ``_POSTAL_RULES`` pattern; tries adjacent
    two-word chunks first (so ``SW1A 2AA`` is recovered whole) then single
    words. Countries without a rule yield no post code. Returns the post
    code (or ``None``) and the remaining words with it removed.
    """
    rule = _POSTAL_RULES.get(country or "")
    if rule is None:
        return None, words
    pattern = rule[0]
    for size in (2, 1):
        for i in range(len(words) - size + 1):
            chunk = " ".join(words[i : i + size])
            if pattern.match(chunk):
                return chunk, words[:i] + words[i + size :]
    return None, words


def _fallback_parse(
    unstructured_address: str, country_hint: str | None
) -> dict[str, str | None]:
    """Parse an address into ISO 20022 fields with the regex heuristics.

    The graceful-degradation path used when libpostal is unavailable. It
    resolves the country (from ``country_hint`` or a trailing country
    token), extracts a country-shaped post code, promotes a trailing
    alphabetic word to the town, then reuses ``split_street_and_building``
    for the street name and building number.
    """
    words = unstructured_address.split()
    detected, words = _strip_trailing_country(words)

    country: str | None = None
    if country_hint:
        country = _COUNTRY_LOOKUP.get(_normalize_key(country_hint))
    if country is None:
        country = detected

    post_code, words = _extract_postcode(words, country)

    town: str | None = None
    if len(words) >= 2 and not any(ch.isdigit() for ch in words[-1]):
        town = words[-1]
        words = words[:-1]

    street_line = " ".join(words).strip()
    if street_line:
        split = split_street_and_building(street_line)
    else:
        split = {"street_name": None, "building_number": None}

    return {
        "StrtNm": split["street_name"],
        "BldgNb": split["building_number"],
        "PstCd": post_code,
        "TwnNm": town,
        "Ctry": country,
    }


def _map_libpostal(
    components: list[tuple[str, str]], country_hint: str | None
) -> dict[str, str | None]:
    """Map libpostal ``(value, label)`` components to ISO 20022 fields.

    ``road`` / ``house_number`` / ``postcode`` / ``city`` map directly;
    the ``country`` component is normalised to an ISO 3166-1 alpha-2 code
    (falling back to ``country_hint``). Unrecognised labels are ignored.
    """
    fields = _empty_iso_fields()
    country_raw: str | None = None
    for value, label in components:
        iso = _LIBPOSTAL_TO_ISO.get(label)
        if iso is not None:
            fields[iso] = value
        elif label == "country":
            country_raw = value

    country: str | None = None
    if country_raw is not None:
        country = _COUNTRY_LOOKUP.get(_normalize_key(country_raw))
    if country is None and country_hint:
        country = _COUNTRY_LOOKUP.get(_normalize_key(country_hint))
    fields["Ctry"] = country
    return fields


@server.tool(title="Parse an address with libpostal", annotations=_PURE_READ)
def parse_address_libpostal(
    unstructured_address: Annotated[
        str,
        Field(
            description=(
                "A single free-text postal address, e.g. "
                "'12 Rue de Rivoli, 75001 Paris, France'."
            )
        ),
    ],
    country_hint: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "An ISO 3166-1 alpha-2 hint (or country name) used when the "
                "address text does not name its own country."
            ),
        ),
    ] = None,
) -> dict[str, Any]:
    """Parse a free-text address into ISO 20022 postal fields.

    Uses the optional libpostal statistical parser (the ``postal`` binding,
    which requires the system libpostal C library) when it is installed,
    and otherwise degrades to this repo's own regex heuristics. Either way
    the address is mapped to ``StrtNm``, ``BldgNb``, ``PstCd``, ``TwnNm``
    and ``Ctry``. The result's ``parser`` field is ``"libpostal"`` or
    ``"fallback"`` so callers know which path ran. Runs purely on CPU with
    no network or filesystem access, though the libpostal path depends on
    an external C library.

    Args:
        unstructured_address: The free-text address to parse.
        country_hint: Country to assume when the text names none.

    Returns ``{"parser": ..., "address": {StrtNm, BldgNb, PstCd, TwnNm,
    Ctry}}``.
    """
    try:
        from postal.parser import parse_address as _libpostal_parse
    except ImportError:
        return {
            "parser": "fallback",
            "address": _fallback_parse(unstructured_address, country_hint),
        }

    components = _libpostal_parse(unstructured_address, country=country_hint)
    return {
        "parser": "libpostal",
        "address": _map_libpostal(list(components), country_hint),
    }


# Prompts
# ---------------------------------------------------------------------------

#: The default policy the tools assume when none is supplied. Mirrors the
#: ``_PolicyId`` field description and the core's own default.
_DEFAULT_POLICY = "cbpr-2026"


@server.prompt(title="Review an address remediation")
def review_address_remediation(
    policy_id: Annotated[
        str,
        Field(
            description=(
                "The policy whose rulebook frames the review (see "
                "list_policies). Defaults to 'cbpr-2026'."
            )
        ),
    ] = _DEFAULT_POLICY,
) -> str:
    """Guide an agent through reviewing a postal-address remediation.

    Teaches the end-to-end tool workflow -- classify, assess, remediate,
    then preview the patch -- and stresses hand-checking low-confidence
    fixes before they are accepted.

    Args:
        policy_id: The policy to frame the review against (defaults to
            cbpr-2026).
    """
    if policy_id == _DEFAULT_POLICY:
        policy_note = (
            f"Work against the default policy '{policy_id}' -- the SWIFT "
            "CBPR+ UG2026 rulebook that sets the 14 November 2026 cliff."
        )
    else:
        policy_note = (
            f"Work against policy '{policy_id}'. Confirm it exists with "
            "list_policies before you rely on it."
        )
    return (
        "You are reviewing an ISO 20022 postal-address remediation.\n\n"
        f"{policy_note}\n\n"
        "Follow this workflow:\n"
        "1. classify_address -- check the shape of the address "
        "(structured, hybrid, or unstructured) to decide whether "
        "remediation is even needed.\n"
        "2. assess_address (a single address) or assess_message (every "
        "addressed party in a pacs.008 / pain.001 document) -- score it "
        "against the policy and read the findings.\n"
        "3. remediate_address or remediate_message -- propose the "
        "compliant form, with each patch operation carrying the finding "
        "it resolves, the source token, and a confidence score.\n"
        "4. preview_patch -- dry-run the operations on the message before "
        "anything is applied.\n\n"
        "Scrutinise every low-confidence patch operation: verify each fix "
        "whose confidence is not high by hand against the source address "
        "before accepting it, and use explain_finding for any finding "
        "code you do not recognise."
    )


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


@server.resource(
    "saf://policies",
    title="Address policies",
    mime_type="application/json",
)
def policies_resource() -> str:
    """The catalog of address policies as JSON (mirrors list_policies)."""
    return json.dumps([_dump(p) for p in services.list_policies()])


@server.resource(
    "saf://cutover-date",
    title="ISO 20022 cutover date",
    mime_type="application/json",
)
def cutover_date_resource() -> str:
    """The binding cutover date as JSON (mirrors get_cutover_date)."""
    return json.dumps(get_cutover_date())


@server.resource(
    "saf://policy/{policy_id}",
    title="Address policy",
    mime_type="application/json",
)
def policy_resource(policy_id: str) -> str:
    """A single address policy by id as JSON, or an ``{"error": ...}``.

    Looks the policy up in the core registry; an unknown id is caught and
    returned as an error payload rather than raised.

    Args:
        policy_id: The id of the policy to look up (see saf://policies).
    """
    try:
        policy = default_registry.get(policy_id)
    except _HANDLED as exc:
        return json.dumps({"error": str(exc)})
    info = PolicyInfo(id=policy.id, title=policy.title, tier=policy.tier)
    return json.dumps(_dump(info))


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

    Parses arguments (currently only ``--version``) and starts the MCPServer
    stdio transport, which an MCP client launches as a subprocess.
    """
    _build_parser().parse_args(argv)
    server.run()


if __name__ == "__main__":  # pragma: no cover
    main()
