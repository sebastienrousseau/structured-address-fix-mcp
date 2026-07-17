# structured-address-fix-mcp examples

Runnable, self-contained examples for the structured-address-fix MCP
server. Each script drives the public tool functions from
`structured_address_fix_mcp.server`. Run any of them from the repository
root:

```sh
python examples/<name>.py
```

| Example | Tool | Demonstrates |
|---------|------|--------------|
| [`mcp_tools.py`](mcp_tools.py) | (several) | Driving the tools in-process through the FastMCP dispatch layer, as an agent would |
| [`01_list_policies.py`](01_list_policies.py) | `list_policies` | Discovering the available `policy_id` values and their tiers |
| [`02_classify_address.py`](02_classify_address.py) | `classify_address` | Classifying addresses as structured / hybrid / unstructured |
| [`03_assess_address.py`](03_assess_address.py) | `assess_address` | Scoring one address against a policy and reading its findings |
| [`04_assess_message.py`](04_assess_message.py) | `assess_message` | Assessing every addressed party in a pacs.008 message |
| [`05_remediate_address.py`](05_remediate_address.py) | `remediate_address` | Lifting an unstructured address to a compliant form |
| [`06_remediate_message.py`](06_remediate_message.py) | `remediate_message` | Remediating a whole message and emitting patched XML |
| [`07_preview_patch.py`](07_preview_patch.py) | `preview_patch` | A dry run of the patch operations remediation would apply |
| [`08_explain_finding.py`](08_explain_finding.py) | `explain_finding` | Explaining what a finding code means and how to fix it |
| [`09_get_cutover_date.py`](09_get_cutover_date.py) | `get_cutover_date` | Reading the binding November 2026 cutover date |

The message-level examples read the shared sample in
[`_data/pacs008_three_party.xml`](_data/pacs008_three_party.xml).

The examples import directly from `structured_address_fix_mcp.server`, so
install this package (and the core `structured-address-fix` library it
depends on) first:

```sh
pip install structured-address-fix-mcp   # Python 3.12+
```
