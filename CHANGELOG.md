# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.4] - 2026-08-29

Documents four tools that were registered and missing from the README,
and adds the benchmark and drift check this repository lacked.

### Fixed

- `normalize_country_code`, `split_street_and_building`,
  `validate_postal_policy` and `parse_address_libpostal` were all
  registered MCP tools and appeared nowhere in the README. They are now
  listed.
- The README said **9 tools**. The server registers **13**.

### Added

- `tests/test_readme_documents_every_tool.py`, which fails when a
  registered tool is missing from the README, when a documented tool no
  longer exists, or when the stated count disagrees with reality. All
  three conditions were live when it was written.
- `benches/bench_tool_dispatch.py` measures what an agent waits for. The
  thirteen tools fall into two groups about two orders of magnitude
  apart: lookups and string helpers an agent can call in a loop, and the
  classify → assess → remediate pipeline, which is priced for screening
  first and fixing second.
- The benchmark reports **which parser backend** `parse_address_libpostal`
  actually used. Without the optional `postal` extra a deterministic
  fallback runs instead of libpostal, and a single number with no label
  would invite quoting a figure for code that never executed.
- `scripts/check_suite_consistency.py` and a scheduled `Suite
  Consistency` workflow comparing this tree, and `structured-address-fix`,
  against PyPI.

### Changed

- Version moved to `0.0.4` in step with `structured-address-fix`.

## [0.0.3] - 2026-08-28

`get_cutover_date` reported a date Swift had withdrawn.

### Fixed

- The tool whose one job is to report the binding structured-address date
  returned `{"date": "2026-11-14", "scheme": "SWIFT CBPR+ UG2026"}`
  unconditionally, as did the `saf://cutover-date` resource. Swift accepted a
  community request on 27 August 2026 and deferred every payments change in
  Standards Release 2026. An agent asking the binding date was handed a
  withdrawn one, with Swift named as the authority.
- `date` is `null` now. The withdrawn date is still returned as
  `announced_date`, labelled, alongside `status`, `deferred_on`,
  `replacement_timing` and the Swift announcement as `source`.
  `requirement_stands` is true: the rule was agreed in 2023 and stands.
- `applies_to` records that the deferral is Swift's and covers CBPR+.
  Domestic market infrastructures set their own timing.

### Changed

- The `saf://cutover-date` resource test asserts against the tool rather than
  a second copy of its payload, so the two cannot drift.
- `structured-address-fix` floor raised to `>=0.0.3`, which introduced the
  constants this server imports. The hash-pinned CI locks pinned `0.0.1` and
  are regenerated.

## [0.0.2] - 2026-07-17

### Fixed

- Release-workflow fixes shipped: the SBOM job no longer breaks on a stale
  dev path dependency, and `server.json` fits the MCP registry description
  limit. The core is installed hash-pinned from PyPI.

## [0.0.1] - 2026-07-17

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

[0.0.1]: https://github.com/sebastienrousseau/structured-address-fix-mcp/releases/tag/v0.0.2
