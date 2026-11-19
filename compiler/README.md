# Compiler

The compiler is the deterministic core of `arachne-loom`. It has no AI dependency and accepts a Canonical Model JSON, a document-format profile, and a generation task. CTD and CSR profiles are supplied.

## Run from source

From the package root:

```sh
cd compiler
PYTHONPATH=. python -m arachne_loom.cli parse ../examples/quickstart/sample.md -o /tmp/model.json
PYTHONPATH=. python -m arachne_loom.cli validate /tmp/model.json ../profiles/ctd/zh-CN/config.json ../examples/quickstart/config.json
PYTHONPATH=. python -m arachne_loom.cli compile /tmp/model.json ../profiles/ctd/zh-CN/config.json ../examples/quickstart/config.json --out-dir /tmp/arachne-loom-build
PYTHONPATH=. python -m arachne_loom.cli inspect /tmp/arachne-loom-build/document.docx -o /tmp/arachne-loom-inspect.json
```

`compile` writes `document.docx`, expected and actual manifests, an acceptance report, and an unresolved-issues list. The compiler rejects invalid IDs, references, resources, and unsupported structures before replacing an existing output directory.

## Input contract

- Canonical Model: `arachne_loom/model.schema.json`
- Generation task: `schemas/generation-task.schema.json`
- CTD profiles: `../profiles/ctd/zh-CN/config.json` or `../profiles/ctd/en-US/config.json`
- CSR profiles: `../profiles/csr/zh-CN/config.json` or `../profiles/csr/en-US/config.json`

Markdown is only an input adapter. For production pipelines, preserve the generated model JSON and manifests as review artifacts.

## Verification

Run `PYTHONPATH=compiler python3 compiler/tests/run_without_pytest.py` when pytest is unavailable. The independent inspector must report an empty `structuralIssues` list before a DOCX is handed to Word.
