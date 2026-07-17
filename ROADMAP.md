<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# `structured-address-fix-mcp` roadmap

## Mission

The Model Context Protocol (MCP) server for the
[`structured-address-fix`](https://github.com/sebastienrousseau/structured-address-fix)
ISO 20022 postal-address library — an agent-first surface for classifying,
assessing, and remediating postal addresses ahead of the 14 November 2026
cliff, when fully unstructured addresses are rejected across CBPR+, HVPS+,
T2, CHAPS, and Fedwire.

## Where we are (v0.1.0, shipped 2026-07-17)

- **9 tools**, each a thin typed wrapper over the shared
  `structured_address_fix.services` facade:
  - Policy discovery: `list_policies`
  - Classification: `classify_address` (structured / hybrid /
    unstructured shape check)
  - Assessment: `assess_address`, `assess_message` (score a single
    address or every addressed party in a pacs.008 / pain.001 message
    against a policy)
  - Remediation: `remediate_address`, `remediate_message` (explained
    before/after with confidence-scored patch operations; optional
    apply-and-return-patched-XML)
  - Dry run: `preview_patch` (the operations remediation would apply)
  - Explanation: `explain_finding` (what a finding code means and how
    to resolve it)
  - Cliff date: `get_cutover_date` (the binding November 2026 cutover)
- **Stdio transport** (FastMCP default): one process per operator,
  launched by the MCP client, no network surface, no authentication
  needed.
- **Supply chain**: 100% line + branch coverage, OpenSSF Scorecard,
  SLSA Build L3 + PEP 740 sigstore attestations on every release,
  CycloneDX 1.6 + SPDX 2.3 + pip-licenses SBOMs on every GitHub
  release, NIST SP 800-218 SSDF practice mapping in `SECURITY.md`.

## Fast-follow — HTTP transport + observability + entitlement gating

Goal: a shared, multi-tenant deployment shape, mirroring the sibling
`camt053-mcp` server and the core library's plugin design.

- **HTTP/SSE transport variant**:
  `structured-address-fix-mcp --transport=http --bind=…` alongside the
  default stdio, with an optional tenant header forwarded into the
  tool-visible `Context` for multi-tenant scoping.
- **OAuth 2.1 resource-server auth (RFC 9728)** on the HTTP transport:
  bearer JWTs validated against a configured issuer / audience with a
  cached JWKS, `WWW-Authenticate` challenges carrying `resource_metadata`,
  and a static-bearer dev-mode fallback.
- **Observability**: Prometheus metrics on the MCP layer
  (request/tool counters, tool latency histograms, auth-failure
  reasons) and a tamper-evident audit chain reusing the core library's
  HMAC hash-chain.
- **Premium-pack entitlement gating**: gate the higher-tier address
  policies / remediation packs behind an entitlement claim, matching
  the core's plugin-and-pack design, so operators can license the
  scheme packs they need.

## Later

Goal: post-Nov-2026-cliff, field-tested behaviour.

- **More guided workflows** as the core library grows its policy set
  (scheme-specific remediation packs, batch-message flows).
- **MCP API surface freeze** at the first stable minor: any future tool
  name change becomes a minor-bump event per SemVer.
- **OpenSSF Best Practices** badge progression (Passing → Silver → Gold).

## Out of scope (until a contributor steps up)

- **Embedded LLM**: this server delegates all inference to the client's
  model via MCP; no bundled LLM weights, no hosted inference endpoint.
- **OAuth provider integration**: the planned HTTP transport
  authenticates by validating tokens from your existing authorization
  server (Okta, Auth0, Entra ID, ...); running the authorization server
  is the operator's job.

## How to influence the roadmap

- Open an issue with the proposed tool + the use case it unblocks.
- For larger items, sketch a design in the issue body.
- See [`GOVERNANCE.md`](GOVERNANCE.md) for the decision-making
  process.
