# Contributing to BridgeCAD

Use a focused branch and pull request. Include the test commands and results, and
link the applicable architectural decision record. Keep source files in
`packages/`, `apps/`, `scripts/` or `tests/`.

For a change to generated drawings or bills, include a synthetic or approved
reference fixture, the applicable code clause, and the before and after output.
Record unresolved assumptions where a reviewer will see them in the output.
Preserve the AutoLISP references and their mapping to the ported implementation.

## Test collection and review

Install the workspace's base packages and pytest to check collection. Add the
development and drawing dependencies before running the complete test suite.

```bash
python -m pytest --collect-only -q
python -m pytest
```

## Protect project data

Use synthetic or approved public fixtures. Remove client identifiers, contact
details, secrets, and private workbook data from patches, logs, and attachments.
Use the [security reporting process](SECURITY.md) for vulnerabilities.
