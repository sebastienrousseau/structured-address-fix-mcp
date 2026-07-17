# Quickstart

A 10-minute install → MCP client config → first conversation tutorial
for `structured-address-fix-mcp`.

## 1. Install

`structured-address-fix-mcp` runs on macOS, Linux, and Windows and
requires Python 3.12+. It pulls in the core `structured-address-fix`
library and the MCP SDK automatically.

```sh
python -m pip install structured-address-fix-mcp
```

Verify:

```sh
python -c "import structured_address_fix_mcp; print(structured_address_fix_mcp.__version__)"
```

## 2. Launch the server

The package installs a `structured-address-fix-mcp` console entry point
that starts the server over stdio (FastMCP's default transport):

```sh
structured-address-fix-mcp
```

The command speaks MCP on stdin/stdout — it is meant to be launched by
an MCP client, not used interactively. (`structured-address-fix-mcp
--version` prints the version and exits.)

## 3. Register it with your MCP client

### Claude Desktop

Add an entry to `~/Library/Application Support/Claude/claude_desktop_config.json`
(macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "structured-address-fix": { "command": "structured-address-fix-mcp" }
  }
}
```

Restart Claude Desktop. The 9 tools are now available in any chat.

### Other clients (Cursor, Continue, generic stdio MCP clients)

Point the client at the `structured-address-fix-mcp` command. The server
speaks standard MCP — no custom transport, no auth. See the
[deployment cookbook](deployment-cookbook.md) for per-client config
snippets.

## 4. First conversation

Drop a pacs.008 or pain.001 message into a chat and ask the agent to
find the addresses that will fail at the November 2026 cliff and fix
them:

> Here is a pacs.008 message. Assess every party's postal address
> against the CBPR+ policy, tell me which ones will be rejected on
> 14 November 2026, and if I confirm, remediate the message and show me
> the patched XML.

A typical flow: the agent calls `get_cutover_date` to anchor the
deadline, `assess_message` to surface the non-compliant parties,
`preview_patch` to show what would change, and — on your confirmation —
`remediate_message` with `apply=true` to return the patched XML.

## 5. Use in-process (no MCP client needed)

To prototype or write integration tests, call the tools through the
FastMCP instance directly. Every example in `examples/` follows this
pattern. The shortest one:

```python
import asyncio

from structured_address_fix_mcp import server


async def main() -> None:
    result = await server.server.call_tool("get_cutover_date", {})
    content = result[0] if isinstance(result, tuple) else result
    print(content[0].text)  # -> {"date": "2026-11-14", "scheme": "SWIFT CBPR+ UG2026"}


asyncio.run(main())
```

## 6. The 9 tools at a glance

| Tool | What it does |
| --- | --- |
| `list_policies` | List the address policies (rulebooks) and their tiers |
| `classify_address` | Structured / hybrid / unstructured shape check |
| `assess_address` | Score one address against a policy; return findings |
| `assess_message` | Assess every addressed party in a pacs.008 / pain.001 |
| `remediate_address` | Propose the compliant form of one address |
| `remediate_message` | Remediate every party in a message (optionally apply) |
| `preview_patch` | Dry run: the patch operations remediation would apply |
| `explain_finding` | Explain a finding code (e.g. `SAF001`) and how to fix it |
| `get_cutover_date` | The binding November 2026 cutover date + scheme |

Optional parameters on the assessment/remediation tools: `policy_id`
(defaults to `cbpr-2026`), `as_of` (`YYYY-MM-DD`, decides cliff wording;
defaults to today), and `country_hint` (an ISO 3166-1 alpha-2 code to
assume when an address has no country of its own).

## 7. Next steps

- Browse the full [tool catalog](../README.md#tools).
- Read the [deployment cookbook](deployment-cookbook.md) for
  per-client (Claude Desktop, Cursor) and container recipes.
- Read the suite's deeper docs at
  <https://sebastienrousseau.github.io/structured-address-fix/>.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `command not found: structured-address-fix-mcp` | Install went to a venv that isn't on PATH | Re-install in your active env, or invoke `python -m structured_address_fix_mcp.server` |
| MCP client doesn't see the tools | Wrong path in client config | Use an absolute path: `which structured-address-fix-mcp` → paste into the client `command` |
| `unknown finding code: ...` from `explain_finding` | The code isn't in the finding taxonomy | Read a code straight out of an `assess_address` / `assess_message` result and pass that |
