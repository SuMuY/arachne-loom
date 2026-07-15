# CTD Profiles

`zh-CN/` and `en-US/` are separate runtime contracts. Each fixes the document language, localized labels, style-role names, and base-template path. The compiler, Canonical Model, validator, manifests, and field mechanics remain shared.

The legacy `profiles/ctd/config.json` is kept as the default Chinese alias for tools that expect the original v0 path. New tasks should select an explicit locale directory.

Do not compile a Chinese model with the English profile or mix locale-specific bases. The validator rejects a profile/model language mismatch.
