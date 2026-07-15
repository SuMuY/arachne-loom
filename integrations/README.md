# Integrations

Integrations are thin workflow wrappers around the same AI-independent compiler. They do not implement a second document engine. The project target is the shared compiler, not any one AI client.

## Generic shell

```sh
integrations/generic-cli/run.sh model.json profiles/ctd/zh-CN/config.json task.json build/document
```

The wrapper runs `validate` and then `compile`. It requires `PYTHONPATH`-style source execution and can be called by any workbench that can run shell commands.

## Required example integration: Claude Code

The assembly instructions require one `claude-code` example. Read `claude-code/workflow.md` to see how a workbench can produce CTD-Markdown or Canonical Model JSON, invoke the shared generic CLI, and give a separate review role only the requirement, manifests, and DOCX. This is an example adapter, not a dependency or a change in project target.

Other workbenches can use the same three CLI commands without importing an AI SDK.
