# Contributing to structured-address-fix-mcp

Thank you for your interest in contributing to structured-address-fix-mcp. This
guide covers the development workflow and standards.

`structured-address-fix-mcp` is the Model Context Protocol (MCP) server of the
**structured-address-fix suite** — alongside the core
[`structured-address-fix`](https://github.com/sebastienrousseau/structured-address-fix)
library. It depends on `structured-address-fix` and exposes its services as
agent tools, so most behaviour lives in the core library.

## Development Setup

### Prerequisites

- Python 3.12+
- [Poetry](https://python-poetry.org/docs/#installation)
- Git with SSH commit signing configured

### Setup

```bash
# Clone and install
git clone git@github.com:sebastienrousseau/structured-address-fix-mcp.git
cd structured-address-fix-mcp
poetry install

# Verify
poetry run pytest tests/ -q
```

> **Note:** `structured-address-fix-mcp` depends on the core
> `structured-address-fix` library. Until it is published to PyPI, install it
> from source first (the dev dependency group already points at the sibling
> checkout `../structured-address-fix`):
>
> ```bash
> pip install "git+https://github.com/sebastienrousseau/structured-address-fix.git"
> ```

### On macOS

```bash
brew install python@3.12 poetry
```

### On Linux (Debian/Ubuntu)

```bash
sudo apt install python3 python3-pip
pip install poetry
```

### On WSL

```bash
sudo apt install python3 python3-pip
pip install poetry
# Ensure ~/.local/bin is in PATH
```

## Workflow

1. **Fork** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feat/my-feature
   ```
3. **Make changes** — follow the coding standards below
4. **Run tests**:
   ```bash
   poetry run pytest tests/ -v
   ```
5. **Run linters**:
   ```bash
   poetry run ruff check structured_address_fix_mcp/
   poetry run mypy structured_address_fix_mcp/
   poetry run black --check structured_address_fix_mcp/ tests/
   ```
6. **Sign and commit**:
   ```bash
   git commit -S -m "feat: add my feature"
   ```
7. **Push** and open a pull request

## Commit Signing (Required)

All commits **must** be signed with SSH or GPG.

### SSH Signing

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519
git config --global commit.gpgsign true
```

### Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add a new MCP tool wrapping a services helper
fix: return an error payload instead of raising on bad input
docs: update README with the MCP client config
test: cover the remediate_address tool
refactor: simplify the tool registration
```

## Coding Standards

- **Line length:** 79 characters (enforced by Black + Ruff)
- **Type hints:** Required on all public functions (mypy strict)
- **Docstrings:** Required on all public classes and functions
- **Tests:** Every new tool or change must include tests

## Testing

```bash
# Full suite
poetry run pytest tests/ -v

# Single file
poetry run pytest tests/test_mcp_server.py -v
```

## Pull Request Checklist

- [ ] All tests pass (`poetry run pytest`)
- [ ] Linters pass (`ruff check`, `mypy`, `black --check`)
- [ ] Commits are signed
- [ ] PR title follows conventional commit format
- [ ] New features include tests and documentation

## License

By contributing, you agree that your contributions will be licensed under
the [Apache License 2.0](LICENSE).
