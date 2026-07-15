# First GitHub Release Checklist

## Before publishing

- [ ] Create a Git repository at this package root (`arachne-loom/`), not at the parent CTD work directory.
- [ ] Review the files to be published; do not add `.DS_Store`, `__pycache__`, local virtual environments, or private source documents.
- [ ] Run `python -m pip install -e 'compiler[dev]'` and `pytest` (or the fallback smoke runner when pytest is unavailable). This requires access to PyPI for build dependencies in a clean environment.
- [ ] Run the README quickstart from a clean shell and inspect the generated DOCX.
- [ ] Confirm the Word acceptance log identifies the tested Word version and the remaining unsupported capabilities.
- [ ] Tag the first release as `v0.0.2` only after the above checks pass.

## What users need

Users need a checkout of this repository, Python 3.10+, `python-docx`, `lxml`, a CTD profile, a task JSON, and desktop Word for field-update/behavior acceptance. The compiler itself has no AI dependency. The `generic-cli` integration is the workbench-neutral entry point. The first release is checkout-based; publishing a standalone PyPI wheel requires a separate packaging pass for profiles, templates, and example resources.

## Scope of the first release

The first release supports headings, rectangular tables, figures, native captions, body cross-references, TOC/table/figure lists, validation, and independent DOCX inspection. Merged cells, literature-management fields, comments/revisions, section-specific headers, and automated desktop Word testing remain out of scope.
