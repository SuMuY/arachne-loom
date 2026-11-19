# Integrations

Integrations are thin workflow wrappers around the same AI-independent compiler. They do not implement a second document engine. The project target is the shared compiler, not any one AI client.

## Generic shell

```sh
integrations/generic-cli/run.sh model.json profiles/ctd/zh-CN/config.json task.json build/document
```

The wrapper runs `validate` and then `compile`. It requires `PYTHONPATH`-style source execution and can be called by any workbench that can run shell commands.

## Required example integration: Claude Code

The repository-root `SKILL.md` is the canonical, workbench-neutral agent instruction. The `claude-code` directory contains only example CLI usage; it adds no Claude SDK dependency.

Other workbenches can use the same three CLI commands without importing an AI SDK.
