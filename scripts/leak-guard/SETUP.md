# Leak Guard — reusable sensitive-data protection

A five-layer guard that stops real identifiers (trial IDs, names, project
codes, secrets) from reaching a public repo — including data hidden inside
`.docx`/`.xlsx`/`.pptx` files. Drop this folder into any git repo and wire it up.

## Why five layers

Any single check gets forgotten. These overlap so that **any one layer stops a
leak**, and the CI layer cannot be bypassed:

| Layer | What | Runs when | Bypassable? |
|---|---|---|---|
| 1. pre-push hook | `scan.py` before push | every `git push` | yes — hook isn't cloned |
| 2. CI job | `scan.py` on the runner | every push / PR | **no** — the backstop |
| 3. test | `scan.py` from the test suite | every test run | no |
| 4. isolation | real docs never enter the repo | policy | — |
| 5. platform | GitHub Secret Scanning + Push Protection | server-side | no |

## Install (3 steps)

**1. Copy this folder** into your repo, e.g. `scripts/leak-guard/`, then edit
`patterns.txt`: keep the structural shapes that fit your domain. Add literal
business strings only if your repo is **private** — never put real names, IDs,
or codes in a public repo, not even in the pattern list.

**2. Install the local hook** (once per checkout / machine — hooks aren't cloned):

```sh
sh scripts/leak-guard/install-hooks.sh
```

**3. Add the CI backstop.** In your workflow (e.g. `.github/workflows/test.yml`),
run the scan before anything else and make other jobs depend on it:

```yaml
jobs:
  leak-guard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python3 scripts/leak-guard/scan.py
  # make your other jobs `needs: leak-guard`
```

## Recommended extras

**Test-suite gate (layer 3).** Add one test so the suite also fails on a leak:

```python
def test_no_sensitive_data_in_repo():
    import subprocess, pathlib
    root = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True, check=True).stdout.strip()
    r = subprocess.run(["python3", f"{root}/scripts/leak-guard/scan.py"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
```

**Isolation (layer 4).** State in CONTRIBUTING that examples/fixtures use only
synthetic data and real source documents never enter the repo.

**Platform (layer 5).** For a GitHub repo:

```sh
gh api -X PATCH repos/OWNER/REPO \
  -f 'security_and_analysis[secret_scanning][status]=enabled' \
  -f 'security_and_analysis[secret_scanning_push_protection][status]=enabled'
```

Optionally run [`gitleaks`](https://github.com/gitleaks/gitleaks): `gitleaks detect --source .`

## Run manually

```sh
python3 scripts/leak-guard/scan.py   # exit 0 = clean, 1 = found, 2 = config error
```

## Gotchas (learned the hard way)

- **Scan inside Office files.** Real data hides in `word/*.xml`; `scan.py`
  unzips `.docx`/`.xlsx`/`.pptx` and scans the XML, not just visible text.
- **Structural regexes over-match OOXML hex.** IDs like `000001FF` look like
  "6 digits + 2 letters". The trial-ID pattern requires a non-hex letter
  (`G-Z`) in the suffix so pure-hex IDs are ignored. Test new patterns against
  real files before trusting them.
- **The hook is convenience, CI is insurance.** `.git/hooks/` is never cloned,
  so a fresh checkout has no hook until `install-hooks.sh` runs. The CI job is
  the layer that always runs.
- **Prefer shapes over literals.** When a new leak shape surfaces, add a
  structural pattern. Literal names/IDs/codes belong only in a private repo —
  a public tool that lists them leaks them by existing.
