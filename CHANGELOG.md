# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-17

Initial release: the Model Context Protocol (MCP) server for
[`structured-address-fix`](https://github.com/sebastienrousseau/structured-address-fix),
exposing ISO 20022 postal-address assessment and remediation as agent
tools ahead of the 14 November 2026 cliff, when fully unstructured
addresses are rejected across CBPR+, HVPS+, T2, CHAPS, and Fedwire.

### Added

- **9 MCP tools over stdio**, each a thin, typed wrapper over the shared
  `structured_address_fix.services` facade (identical behaviour to the
  CLI and any other consumer of the core):
  - `list_policies` — list every available address policy (rulebook)
    with its tier.
  - `classify_address` — classify a postal address as structured,
    hybrid, or unstructured.
  - `assess_address` — score a single address against a policy and
    return its findings.
  - `assess_message` — assess every addressed party in a pacs.008 /
    pain.001 message.
  - `remediate_address` — propose the compliant form of an address,
    with explained before/after and confidence-scored patch operations.
  - `remediate_message` — assess and remediate every addressed party in
    a message, optionally applying the operations and returning the
    patched XML.
  - `preview_patch` — return the patch operations remediation would
    apply (a dry run).
  - `explain_finding` — explain what a finding code means and how to
    resolve it.
  - `get_cutover_date` — return the binding November 2026
    structured-address cutover date and the scheme that sets it.
- **`structured-address-fix-mcp` console entry point** launching the
  FastMCP server over stdio (`--version` supported).
- **Error convention**: tools catch the documented domain, validation,
  and value errors and return an `{"error": ...}` payload rather than
  raising into the MCP client transport.
- **Read-only tool annotations**: every tool is marked
  `readOnlyHint` / non-destructive / idempotent / closed-world, since
  each computes purely over its arguments and bundled data.
- **Supply chain**: 100% line + branch coverage gate, ruff + black +
  mypy `--strict` + bandit + interrogate in CI across Python 3.12/3.13;
  OpenSSF Scorecard; SLSA Build L3 provenance + PEP 740 sigstore
  attestations on release; CycloneDX 1.6 + SPDX 2.3 + pip-licenses
  SBOMs on every GitHub release; NIST SP 800-218 SSDF practice mapping
  in `SECURITY.md`; MCP registry + Glama directory manifests.

[0.1.0]: https://github.com/sebastienrousseau/structured-address-fix-mcp/releases/tag/v0.1.0
