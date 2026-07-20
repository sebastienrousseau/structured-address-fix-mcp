# syntax=docker/dockerfile:1.6
# Multi-stage build for a minimal structured-address-fix-mcp image.
#
# The container runs the FastMCP server over stdio so an MCP client can
# launch it directly with ``docker run -i --rm structured-address-fix-mcp``.

FROM python:3.14-slim@sha256:cea0e6040540fb2b965b6e7fb5ffa00871e632eef63719f0ea54bca189ce14a6 AS builder

WORKDIR /build

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# The core library this server is a thin transport over. The spec can be
# overridden at build-time so the GHCR pipeline can install the core from a
# matching feat/* branch (a git+ URL) before it hits PyPI; the default pulls
# the published ``structured-address-fix`` from PyPI. The git client is
# needed only when the override spec is a git+ URL; it stays in this build
# stage and never ships in the final image.
ARG CORE_PIP_SPEC="structured-address-fix"
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# pyproject.toml carries ``readme = "README.md"``, so README.md must be
# present at build-time for ``pip install .`` to resolve the package
# metadata.
COPY pyproject.toml README.md ./
COPY structured_address_fix_mcp ./structured_address_fix_mcp

# Install the core (from PyPI or the override spec), then layer this package
# on top inside a self-contained virtualenv.
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install "$CORE_PIP_SPEC" \
    && /opt/venv/bin/pip install .


FROM python:3.14-slim@sha256:cea0e6040540fb2b965b6e7fb5ffa00871e632eef63719f0ea54bca189ce14a6

LABEL org.opencontainers.image.title="structured-address-fix-mcp" \
      org.opencontainers.image.description="Model Context Protocol server for the structured-address-fix ISO 20022 postal-address library." \
      org.opencontainers.image.source="https://github.com/sebastienrousseau/structured-address-fix-mcp" \
      org.opencontainers.image.licenses="Apache-2.0"

# Non-root user (MCP clients launch the container with stdio; no extra
# privileges needed).
RUN groupadd --system mcp && useradd --system --gid mcp --home /home/mcp mcp \
    && mkdir -p /home/mcp \
    && chown -R mcp:mcp /home/mcp

COPY --from=builder /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER mcp
WORKDIR /home/mcp

# A non-zero exit here means an import / dependency mismatch; the MCP
# client will see it before the first tool call.
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import structured_address_fix_mcp.server" || exit 1

ENTRYPOINT ["structured-address-fix-mcp"]
