<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# structured-address-fix-mcp Architecture

A map of the codebase for new contributors and maintainers. The goal is
that anyone can navigate, extend, and reason about
structured-address-fix-mcp without prior context.

## The pipeline

```
MCP client (Claude Desktop, IDE, agent)
        |  stdio, streamable HTTP or SSE (JSON-RPC)
        v
structured_address_fix_mcp/server.py   (MCPServer: tools, resources, prompt)
        |  thin typed wrappers
        v
structured_address_fix.services        (the facade the CLI also uses:
        |                               classify, assess, remediate,
        |                               preview, explain, cutover date)
        v
ISO 20022 postal addresses in pacs.008 / pain.001
```

Tools are deliberately thin: every one is a small adapter that delegates
to the
[`structured-address-fix`](https://github.com/sebastienrousseau/structured-address-fix)
library and returns a JSON-serialisable result. The agent surface is the
public service layer of that library, exposed in a way an MCP client can
call.

## Module map

| Area | Module | Responsibility |
| :--- | :--- | :--- |
| **Server** | `structured_address_fix_mcp/server.py` | The MCPServer instance, all tool / resource / prompt registrations |
| **Entry point** | `structured_address_fix_mcp.server:main` (console script: `structured-address-fix-mcp`) | Launches the server over stdio, or over streamable HTTP / SSE with `--transport` (`_cli.py` + `_transports.py`, ADR 0001) |
| **SDK shim** | `structured_address_fix_mcp/_mcp_compat.py` | Builds the server on mcp 2.x (`MCPServer`) or 1.x (`FastMCP`) and reads its version either way |
| **Finding text** | `structured_address_fix_mcp/explanations.py` | Plain-language meaning and fix guidance per finding code, behind `explain_finding` |
| **Version** | `structured_address_fix_mcp/__init__.py` | `__version__`, restated in `pyproject.toml`, `glama.json` and `server.json` |
| **Tests** | `tests/` | In-process tool tests, the SDK compatibility matrix, the transport contract, the README/tool drift check and the suite conformance test |
| **Fixtures** | `tests/fixtures/messages/` | pacs.008 / pain.001 samples for the message tools |
| **Examples** | `examples/` | One runnable script per tool plus `mcp_tools.py`, exercised by `make examples` |
| **Benchmark** | `benches/bench_tool_dispatch.py` | Tool-dispatch timings; CI runs it with `--quick` to prove it still matches the API |
| **Release helpers** | `scripts/verify_versions.py`, `scripts/check_suite_consistency.py` | Every version source agrees; the suite's shared conventions hold |

## Tools, resources, prompts

The current MCP surface:

- **Tools** - `list_policies`, `classify_address`, `assess_address`,
  `assess_message`, `remediate_address`, `remediate_message`,
  `preview_patch`, `explain_finding`, `get_cutover_date`,
  `normalize_country_code`, `split_street_and_building`,
  `validate_postal_policy`, `parse_address_libpostal`.
- **Resources** - `saf://policies`, `saf://cutover-date`,
  `saf://policy/{policy_id}`.
- **Prompts** - `review_address_remediation(policy_id=...)`.

## Key design decisions

- **Delegation, not duplication.** Every tool is a thin wrapper over
  `structured_address_fix.services`. If you want a new tool, port the
  matching service from the core rather than re-implementing it here.
- **Errors as data.** Tools never raise. A domain, validation or value
  error is turned into an `{"error": ...}` payload so the agent can
  reason about failure without parsing tracebacks.
- **One command line, three transports.** stdio is the default and opens
  no socket. `--transport streamable-http` and `--transport sse` bind
  loopback unless told otherwise and carry no authentication; a routable
  deployment sits behind a gateway (ADR 0001).
- **Both SDK majors.** `_mcp_compat` hides the differences between mcp
  1.x and 2.x (`>=1.28.1,<3`); `tests/test_mcp_sdk_compat.py` pins the
  shim's contract on whichever major is installed.
- **Coverage enforced at 100%** line + branch and docstring; the only
  `# pragma: no cover` markers are the SDK branch that cannot be
  installed alongside the other and the `__main__` guard.

## Extension points

- **Add a tool:** add a `@server.tool(...)`-decorated function in
  `structured_address_fix_mcp/server.py`; pair it with tests in
  `tests/test_mcp_server.py`, list it in the README's Tools section (the
  README drift test fails otherwise) and add an example under
  `examples/`.
- **Add a resource:** `@server.resource("saf://...")`.
- **Add a prompt:** `@server.prompt(...)`.
- **Match a new core feature:** when a new service lands in
  `structured-address-fix`, raise the floor in `pyproject.toml` and port
  it as a tool in the same release.

## Where to look first

- Runnable examples: [`examples/`](examples/)
- Decisions: [`docs/adr/`](docs/adr/index.md)
- Roadmap: [`ROADMAP.md`](ROADMAP.md)
- Release process: [`RELEASING.md`](RELEASING.md)
- Parent library: [`structured-address-fix`](https://github.com/sebastienrousseau/structured-address-fix)
