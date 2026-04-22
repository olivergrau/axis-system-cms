# AXIS Agent Session Starter

Use this file as a quick-start prompt template for a fresh agentic session.

## Recommended Attachments Or References

For most sessions, provide or point the agent to:

1. `docs-internal/bootstrap-context/01-solution-overview.md`
2. `docs-internal/bootstrap-context/02-codebase-map.md`
3. `docs-internal/bootstrap-context/03-execution-and-artifacts.md`
4. `docs-internal/bootstrap-context/04-current-workspace-system-aw.md` if the task is
   about the current `system_aw` workspace
5. the active workspace manifest
6. the active config file

Suggested current files:

- `workspaces/system_aw-baseline/workspace.yaml`
- `workspaces/system_aw-baseline/configs/system_aw-baseline.yaml`

## General Starter Prompt

```text
You are joining an existing AXIS repository session.

Please use these context files first before exploring the wider codebase:
- docs-internal-context/01-solution-overview.md
- docs-internal-context/02-codebase-map.md
- docs-internal-context/03-execution-and-artifacts.md

If the task relates to the current system_aw investigation workspace, also use:
- docs-internal-context/04-current-workspace-system-aw.md
- workspaces/system_aw-baseline/workspace.yaml
- workspaces/system_aw-baseline/configs/system_aw-baseline.yaml

Treat those files as the fast orientation layer.
Use source files only as needed to answer the concrete task.

When you respond:
1. Start with a short restatement of your understanding.
2. State which files you used for initial context.
3. Avoid a full repo rediscovery unless the task requires it.
4. Prefer concrete code references when making claims about behavior.
```

## Debugging Starter Prompt

```text
You are helping debug behavior in the AXIS repository.

First read:
- docs-internal/bootstrap-context/01-solution-overview.md
- docs-internal/bootstrap-context/02-codebase-map.md
- docs-internal/bootstrap-context/03-execution-and-artifacts.md
- docs-internal/bootstrap-context/04-current-workspace-system-aw.md
- workspaces/system_aw-baseline/workspace.yaml
- workspaces/system_aw-baseline/configs/system_aw-baseline.yaml

The immediate goal is to debug or explain behavior in system_aw.

Please:
1. Build initial context from those files first.
2. Then inspect only the most relevant source files for the issue.
3. Explain which layer the issue likely belongs to:
   system logic, world behavior, framework execution, visualization, or workspace flow.
4. If behavior depends on recorded results, say which artifacts should be checked.
```

## Architecture Starter Prompt

```text
You are helping explain or extend the AXIS architecture.

First read:
- docs-internal/bootstrap-context/01-solution-overview.md
- docs-internal/bootstrap-context/02-codebase-map.md
- docs-internal/bootstrap-context/03-execution-and-artifacts.md

Use those as the orientation layer, then inspect deeper implementation files only
where needed.

Please focus on:
- current implementation reality
- architectural boundaries between sdk, framework, systems, world, and visualization
- where older internal design docs may differ from the current code
```

## Workspace Workflow Starter Prompt

```text
You are helping with AXIS workspace behavior and workflow.

Start with:
- docs-internal/bootstrap-context/01-solution-overview.md
- docs-internal/bootstrap-context/03-execution-and-artifacts.md
- docs-internal/bootstrap-context/04-current-workspace-system-aw.md
- workspaces/system_aw-baseline/workspace.yaml

Please reason about the task using the workspace layer first:
- manifest intent
- config resolution
- workspace-local results
- comparison/visualization routing

Only expand into broader source exploration if the task cannot be answered from
that path.
```

## Practical Usage Note

This file is meant to reduce repeated setup cost in new chats.

Good default pattern:

- start with the context pack
- add the exact task
- add the active workspace/config files
- only then ask for deeper code analysis
