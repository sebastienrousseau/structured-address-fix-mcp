<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# `structured-address-fix-mcp` style guide

`structured-address-fix-mcp` follows the cross-suite
[`STYLEGUIDE.md`](https://github.com/sebastienrousseau/structured-address-fix/blob/main/STYLEGUIDE.md)
maintained in the core repository. That document is the single source of
truth for:

- Voice + spelling conventions (British prose, American code, no em-dashes,
  no emojis outside the standard checkmark/cross in supported-versions
  tables).
- README structure (section template + badge order).
- CHANGELOG structure (Keep-a-Changelog + suite Quality gates + Suite
  alignment tables).
- SECURITY.md structure (including the NIST SSDF practice mapping).
- SUPPORT.md / CONTRIBUTING.md structure.
- CI floor (test + lint + security + docstring-coverage gates + release-only
  gates).
- PR style (conventional commits + signed commits + branch policy).
- Branch naming, issue filing, naming conventions.

## Local additions

`structured-address-fix-mcp` adds one suite convention: **MCP tool names use
the `verbNoun` snake_case pattern** (matching the Stripe MCP precedent):

```
list_policies          # not get_policies or policies()
classify_address       # not is_structured or address_classify
assess_message         # not message_assessment or check_message
get_cutover_date       # not cutover_date or the_cliff
```

This makes tool names read naturally as English imperatives in agent
prompts.

## Updating

If you find divergence between this repo's practice and the core
STYLEGUIDE, the core wins; open a PR to align this repo (and/or fix
the deviation).
