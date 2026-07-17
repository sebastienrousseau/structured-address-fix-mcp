# Deployment cookbook

End-to-end recipes for wiring `structured-address-fix-mcp` into MCP
clients. v0.1 speaks **stdio only** — one process per operator, launched
by the client, no network surface and no authentication. (A shared
HTTP/OAuth transport for multi-tenant deployments is on the
[roadmap](../ROADMAP.md), not in this release.)

The recipes are **opinionated minimums**: enough to be useful, small
enough to read in one sitting.

## Contents

- [1. Claude Desktop](#1-claude-desktop)
- [2. Cursor](#2-cursor)
- [3. Generic stdio MCP clients](#3-generic-stdio-mcp-clients)
- [4. Isolated / pinned install](#4-isolated--pinned-install)
- [5. Container image](#5-container-image)
- [Recipes you'll likely want next](#recipes-youll-likely-want-next)

## Common assumptions

Every recipe assumes:

- Python 3.12+ with `structured-address-fix-mcp` installed and its
  `structured-address-fix-mcp` console entry point on `PATH`
  (`which structured-address-fix-mcp` to confirm).
- The client launches the server as a subprocess and speaks MCP over
  the process's stdin/stdout. No port, no token.
- If the entry point is not on the client's `PATH` (GUI apps often have
  a minimal `PATH`), use the **absolute path** from `which` in the
  `command` field.

---

## 1. Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`
(macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "structured-address-fix": {
      "command": "structured-address-fix-mcp"
    }
  }
}
```

If the command isn't found after a restart, use the absolute path:

```json
{
  "mcpServers": {
    "structured-address-fix": {
      "command": "/opt/venvs/saf/bin/structured-address-fix-mcp"
    }
  }
}
```

Restart Claude Desktop; the 9 tools appear in any chat.

---

## 2. Cursor

Add the server to `~/.cursor/mcp.json` (global) or `.cursor/mcp.json`
in a project:

```json
{
  "mcpServers": {
    "structured-address-fix": {
      "command": "structured-address-fix-mcp",
      "args": []
    }
  }
}
```

Reload the window (Command Palette → "Reload Window") so Cursor picks up
the new server, then enable it in Settings → MCP.

---

## 3. Generic stdio MCP clients

Any client that launches a stdio MCP server takes the same three
pieces — command, optional args, optional environment:

```json
{
  "mcpServers": {
    "structured-address-fix": {
      "command": "structured-address-fix-mcp",
      "args": [],
      "env": {}
    }
  }
}
```

To run without installing the entry point on `PATH`, invoke the module:

```json
{
  "mcpServers": {
    "structured-address-fix": {
      "command": "python",
      "args": ["-m", "structured_address_fix_mcp.server"]
    }
  }
}
```

---

## 4. Isolated / pinned install

Keep the server (and its core dependency) in a dedicated virtualenv so a
client always launches a known version:

```sh
python -m venv /opt/venvs/saf
/opt/venvs/saf/bin/pip install -U structured-address-fix-mcp
/opt/venvs/saf/bin/structured-address-fix-mcp --version
```

Then point the client's `command` at
`/opt/venvs/saf/bin/structured-address-fix-mcp`. Upgrades are a single
`pip install -U` against that venv; no client config change needed.

---

## 5. Container image

The repo's `Dockerfile` builds a minimal stdio image. Build it, then let
your MCP client launch the container per session:

```sh
docker build -t structured-address-fix-mcp .
```

```json
{
  "mcpServers": {
    "structured-address-fix": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "structured-address-fix-mcp"]
    }
  }
}
```

`-i` keeps stdin open so the client can speak MCP to the container;
`--rm` cleans it up when the session ends. The image runs as a non-root
`mcp` user and carries a `HEALTHCHECK` that imports the server module, so
a dependency mismatch fails fast before the first tool call.

Until the core `structured-address-fix` library is on PyPI, override the
build spec to install it from source:

```sh
docker build \
  --build-arg CORE_PIP_SPEC="git+https://github.com/sebastienrousseau/structured-address-fix.git" \
  -t structured-address-fix-mcp .
```

---

## Recipes you'll likely want next

- **HTTP / multi-tenant.** Not in v0.1. The [roadmap](../ROADMAP.md)
  tracks an HTTP/SSE transport with OAuth 2.1 resource-server auth,
  Prometheus metrics, and entitlement gating — mirroring the sibling
  `camt053-mcp` server.
- **Pin the core.** Once `structured-address-fix` is published, pin both
  it and this server to exact versions in your deployment venv so agent
  behaviour is reproducible.
- **Audit logging.** Route the Python logging output of the launched
  process to your log pipeline if you need a record of tool calls.
