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

"""Shared fixtures for the structured-address-fix-mcp test suite."""

from pathlib import Path

import pytest

#: A date past the 14 November 2026 cliff, so cliff-gated findings and
#: remediations fire deterministically regardless of when the suite runs.
POST_CLIFF = "2026-12-01"

_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "messages"


@pytest.fixture
def post_cliff() -> str:
    """An ISO 8601 ``as_of`` date past the November 2026 cliff."""
    return POST_CLIFF


@pytest.fixture
def structured_address() -> dict:
    """A fully structured GB address (classifies ``structured``)."""
    return {
        "street_name": "Downing St",
        "building_number": "10",
        "post_code": "SW1A 2AA",
        "town_name": "London",
        "country": "GB",
    }


@pytest.fixture
def hybrid_address() -> dict:
    """A structured address with residual lines (classifies ``hybrid``)."""
    return {
        "town_name": "London",
        "country": "GB",
        "address_lines": ["Flat 2", "221B Baker St"],
    }


@pytest.fixture
def unstructured_address() -> dict:
    """An ``AdrLine``-only GB address (classifies ``unstructured``)."""
    return {
        "address_lines": ["10 Downing St", "London SW1A 2AA"],
        "country": "GB",
    }


@pytest.fixture
def remediable_address() -> dict:
    """An unstructured address remediation lifts to structured form."""
    return {
        "address_lines": ["Flat 2", "221B Baker St", "London NW1 6XE"],
        "country": "GB",
    }


@pytest.fixture
def pacs008_xml() -> str:
    """A three-party pacs.008 message with a mix of address shapes."""
    return (_FIXTURES / "pacs008_three_party.xml").read_text(encoding="utf-8")
