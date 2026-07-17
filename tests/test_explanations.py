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

"""Tests for the finding-code explanation catalog."""

import pytest
from structured_address_fix.domain.findings import FindingCode

from structured_address_fix_mcp.explanations import FINDING_EXPLANATIONS


@pytest.mark.parametrize("code", list(FindingCode), ids=lambda c: c.value)
def test_every_finding_code_has_full_explanation(code):
    """Every finding code has a summary, impact, and fix entry."""
    detail = FINDING_EXPLANATIONS[code]
    assert {"summary", "impact", "fix"} == set(detail)
    assert all(isinstance(text, str) and text for text in detail.values())


def test_explanations_cover_exactly_the_enum():
    """The catalog covers every code and adds none the enum lacks."""
    assert set(FINDING_EXPLANATIONS) == set(FindingCode)
