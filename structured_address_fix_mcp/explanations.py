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

"""Plain-language explanations and fix guidance for each finding code.

Keyed by the core library's stable :class:`~structured_address_fix.domain.
findings.FindingCode` values, this is the data behind the
``explain_finding`` tool: what the finding means, why it matters for the
November 2026 cliff, and how to resolve it.
"""

from __future__ import annotations

from structured_address_fix.domain.findings import FindingCode

#: Finding code -> (summary, why it matters, how to fix).
FINDING_EXPLANATIONS: dict[FindingCode, dict[str, str]] = {
    FindingCode.UNSTRUCTURED_ONLY: {
        "summary": "The address uses only free-form AdrLine text.",
        "impact": (
            "Fully unstructured addresses are rejected by CBPR+, HVPS+, "
            "T2, CHAPS, Fedwire and Lynx from 14 November 2026."
        ),
        "fix": (
            "Provide structured elements (at minimum TwnNm and Ctry). Run "
            "remediate_address to derive them from the existing lines."
        ),
    },
    FindingCode.MISSING_COUNTRY: {
        "summary": "No Ctry (country) element is present.",
        "impact": (
            "Country is mandatory for cross-border payments from the "
            "cliff date; its absence causes rejection."
        ),
        "fix": "Add an ISO 3166-1 alpha-2 Ctry code (e.g. 'GB', 'US').",
    },
    FindingCode.MISSING_TOWN: {
        "summary": "No TwnNm (town name) element is present.",
        "impact": (
            "Town is mandatory for the hybrid minimum bar CBPR+ permits."
        ),
        "fix": "Add a TwnNm element, or remediate to derive it.",
    },
    FindingCode.ADRLINE_OVERFLOW: {
        "summary": "Too many AdrLine lines, or a line over 70 characters.",
        "impact": "The message will fail ISO 20022 length validation.",
        "fix": "Reduce to at most seven lines of at most 70 characters.",
    },
    FindingCode.HYBRID_RESIDUAL_ADRLINE: {
        "summary": "A structured address still carries residual AdrLine.",
        "impact": (
            "Some scheme variants reject residual free-form text; it is "
            "safer to promote it into structured elements."
        ),
        "fix": (
            "Move the residual text into StrtNm/BldgNb, or remediate to "
            "the fully structured form."
        ),
    },
    FindingCode.NON_ISO_COUNTRY_CODE: {
        "summary": "The Ctry value is not a valid ISO 3166-1 alpha-2 code.",
        "impact": "The message will be rejected as malformed.",
        "fix": "Replace it with a valid two-letter country code.",
    },
    FindingCode.NON_LATIN_CHARACTERS: {
        "summary": "The address contains disallowed characters.",
        "impact": "Characters outside the SWIFT set can cause rejection.",
        "fix": "Transliterate to the permitted Latin character set.",
    },
    FindingCode.STRUCTURED_FIELD_OVERFLOW: {
        "summary": "A structured element exceeds its maximum length.",
        "impact": "The message will fail ISO 20022 length validation.",
        "fix": "Shorten the element to its ISO 20022 maximum length.",
    },
}
