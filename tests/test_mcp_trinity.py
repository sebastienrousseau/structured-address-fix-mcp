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

"""Tests for the MCP prompt and resource surface (the "Trinity")."""

import json

import pytest

pytest.importorskip("mcp")

import structured_address_fix_mcp.server as server  # noqa: E402

# ---------------------------------------------------------------------------
# Prompt registration
# ---------------------------------------------------------------------------


def test_prompt_registered():
    """The review prompt is registered on the server's prompt manager."""
    prompts = server.server._prompt_manager.list_prompts()
    by_name = {p.name: p for p in prompts}
    assert "review_address_remediation" in by_name
    assert by_name["review_address_remediation"].title == (
        "Review an address remediation"
    )


# ---------------------------------------------------------------------------
# Prompt body: both branches of the default argument
# ---------------------------------------------------------------------------


def test_prompt_default_policy_branch():
    """Called with no argument, the prompt names the default cbpr-2026."""
    text = server.review_address_remediation()
    assert "cbpr-2026" in text
    assert "default policy" in text
    # The full tool workflow is spelled out, in order.
    for step in (
        "classify_address",
        "assess_address",
        "assess_message",
        "remediate_address",
        "remediate_message",
        "preview_patch",
    ):
        assert step in text
    assert "low-confidence" in text


def test_prompt_custom_policy_branch():
    """Called with an explicit policy, the prompt names that policy."""
    text = server.review_address_remediation("sepa")
    assert "'sepa'" in text
    assert "list_policies" in text
    assert "default policy" not in text


# ---------------------------------------------------------------------------
# Resource registration
# ---------------------------------------------------------------------------


def test_static_resources_registered():
    """Both static resources are registered with their JSON mime type."""
    resources = server.server._resource_manager.list_resources()
    by_uri = {str(r.uri): r for r in resources}
    assert "saf://policies" in by_uri
    assert "saf://cutover-date" in by_uri
    assert by_uri["saf://policies"].mime_type == "application/json"
    assert by_uri["saf://cutover-date"].mime_type == "application/json"


def test_policy_template_registered():
    """The per-policy templated resource is registered."""
    templates = server.server._resource_manager.list_templates()
    uris = {t.uri_template for t in templates}
    assert "saf://policy/{policy_id}" in uris


# ---------------------------------------------------------------------------
# saf://policies
# ---------------------------------------------------------------------------


def test_policies_resource_mirrors_list_policies():
    """The policies resource returns the same catalog as the tool."""
    payload = json.loads(server.policies_resource())
    assert isinstance(payload, list)
    ids = {row["id"] for row in payload}
    assert "cbpr-2026" in ids
    assert all({"id", "title", "tier"} <= set(row) for row in payload)


# ---------------------------------------------------------------------------
# saf://cutover-date
# ---------------------------------------------------------------------------


def test_cutover_date_resource_mirrors_tool():
    """The cutover-date resource returns the same payload as the tool."""
    payload = json.loads(server.cutover_date_resource())
    assert payload == {
        "date": "2026-11-14",
        "scheme": "SWIFT CBPR+ UG2026",
    }


# ---------------------------------------------------------------------------
# saf://policy/{policy_id}: both branches
# ---------------------------------------------------------------------------


def test_policy_resource_known_id():
    """A known policy id resolves to its id, title, and tier."""
    payload = json.loads(server.policy_resource("cbpr-2026"))
    assert payload["id"] == "cbpr-2026"
    assert {"id", "title", "tier"} <= set(payload)


def test_policy_resource_unknown_id_returns_error():
    """An unknown policy id is caught and returned as an error payload."""
    payload = json.loads(server.policy_resource("no-such-policy"))
    assert "error" in payload
