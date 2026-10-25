## What

<!-- One paragraph. What changed. -->

## Why

<!-- The problem this solves. Link the issue: Closes #123 -->

## How verified

<!--
Paste the commands you ran and their result. "Tests pass" is not enough —
show which ones.
-->

```
make lint && make test
python tests/e2e/run_e2e.py
```

## Type

- [ ] Bug fix (has a regression test that fails before the fix)
- [ ] Feature (additive)
- [ ] Breaking change (workbook schema or output shape)
- [ ] Documentation only
- [ ] Build / CI / chore

## Checklist

- [ ] Branch name follows `type/scope-short-desc`
- [ ] Commits are conventional and atomic
- [ ] New code has tests
- [ ] `make lint && make test` pass locally
- [ ] `python tests/e2e/run_e2e.py` still passes 28/28
- [ ] No new runtime dependency in `bridgecad-core`
- [ ] Design invariants respected (GUIDE.md §3)
- [ ] Docs updated in this PR — one fact, one place
- [ ] No PII committed (email or phone in tracked source)
- [ ] Benchmarks still inside gates (QA < 200 ms, BOQ < 500 ms, sheet < 3 s)

## Invariant check

- [ ] `BridgeProject` is still the only in-memory truth
- [ ] draw / bill / qa still do not import each other
- [ ] Excel round-trip drift is still ≤5%
- [ ] Missing input still returns explicit `not_calculated`, never a default

## Notes for reviewers

<!-- Anything you are unsure about. Say so — it is faster than a round trip. -->
