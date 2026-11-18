# Contributing

## First: install the leak guard

Git hooks are not cloned. Run this once after cloning:

```sh
sh scripts/install-hooks.sh
```

It installs a `pre-push` hook that scans for sensitive data and refuses the
push if any is found. CI runs the same scanner as a backstop, and `pytest`
includes it as a test.

## Data rule: synthetic only, no real documents

This is a public repository. Real trial identifiers, patient data, drug codes,
internal project numbers, and reviewer names must never enter it — including
inside `.docx` files, whose `word/*.xml` parts are scanned too.

- **Examples and fixtures use synthetic data only**: `STUDY-001`, `DRUG-X`,
  generic populations. Never copy from a real manuscript.
- **Real source documents stay outside this repo.** Author real CTD material
  in a separate, private working area; this package ships only the tool and
  synthetic examples.
- **This repo never stores real identifiers — not even in the pattern list.**
  `scripts/sensitive-patterns.txt` holds only generic *structural* shapes, so
  the tool cannot leak business data by merely existing. If you discover a leak
  whose shape is not yet caught, add a new structural pattern (never a literal
  name, ID, or code). Private literal matching, if ever needed, belongs in a
  business project's own private environment, not in this public tool.

## The five layers of protection

1. **pre-push hook** — blocks the push locally (`scripts/install-hooks.sh`).
2. **CI leak-guard job** — re-runs the scanner on every push/PR (catches anyone
   who skipped the hook).
3. **pytest leak test** — `test_no_sensitive_data_in_repo` fails the suite.
4. **Isolation** — real documents never live here; only synthetic fixtures.
5. **GitHub Secret Scanning + Push Protection** — enabled on the repo for
   generic credential leaks. Optionally run [`gitleaks`](https://github.com/gitleaks/gitleaks)
   locally: `gitleaks detect --source .`

Any one layer is enough to stop a leak; together they mean a real identifier
cannot reach the public repo by being forgotten in a manual check.

## Running the checks manually

```sh
python3 scripts/scan-sensitive.py     # leak guard
cd compiler && pytest                 # full suite (includes leak test)
```

## Release acceptance gate

Do not publish a release until the change's acceptance is complete, including
desktop Word visual/behavior checks for formatting changes. Tool timeouts or
other verification blockers keep the release in draft; passing automated XML
checks does not waive desktop acceptance. Record the blocker and resume
verification before publishing. Preserve existing tags while work continues.
