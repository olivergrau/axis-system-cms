# 8. CLI Architecture

## Entry Point

```
python -m axis_system_a.cli [--root ROOT] [--output {text,json}] <command> ...
```

Program name: `axis`. Entry point: `cli.main(argv)` returns an integer exit code.

## Command Structure

```
axis
├── --root ROOT                 Repository path (default: ./experiments/results)
├── --output {text,json}        Output format (default: text)
│
├── experiments
│   ├── list                    List all experiments
│   ├── run <config_path>       Execute experiment from config file
│   │   └── --redo              Delete existing and re-run
│   ├── resume <experiment_id>  Resume incomplete experiment
│   └── show <experiment_id>    Inspect experiment details
│
├── runs
│   ├── list --experiment <eid> List runs in an experiment
│   └── show <run_id> --experiment <eid>  Inspect a specific run
│
└── visualize                   Launch interactive episode viewer
    ├── --experiment <eid>      (required)
    ├── --run <rid>             (required)
    ├── --episode <N>           (required, 1-based)
    ├── --start-step <N>        (optional, 0-based)
    └── --start-phase <phase>   (optional: BEFORE, AFTER_REGEN, AFTER_ACTION)
```

## Parser Architecture

Two-level subparser nesting (`entity -> action`) with a shared parent parser (`common`) providing `--root` and `--output` at every leaf level. Uses `argparse.SUPPRESS` defaults on the common parser so leaf defaults don't overwrite values from the top-level parser.

`RawDescriptionHelpFormatter` is used to preserve example formatting in epilogs.

## Dispatch Logic

```python
def main(argv):
    args = parser.parse_args(argv)
    if not args.entity: print_help; return 1

    repo = ExperimentRepository(Path(args.root))

    if args.entity == "visualize":
        return _cmd_visualize(repo, args)

    if not args.action: print_help; return 1

    # dispatch to _cmd_{entity}_{action}(repo, ...)
```

All exceptions are caught: `SystemExit` converted to exit code, other exceptions printed to stderr with return code 1.

## Command Handlers

| Command | Handler | Core Operation |
|---------|---------|----------------|
| `experiments list` | `_cmd_experiments_list` | Iterates `repo.list_experiments()`, loads status/metadata/run counts |
| `experiments run` | `_cmd_experiments_run` | Loads config via `_load_config_file()`, calls `ExperimentExecutor.execute()` |
| `experiments resume` | `_cmd_experiments_resume` | Calls `ExperimentExecutor.resume()` |
| `experiments show` | `_cmd_experiments_show` | Loads all experiment artifacts, displays structured output |
| `runs list` | `_cmd_runs_list` | Loads run status, metadata, summary availability |
| `runs show` | `_cmd_runs_show` | Loads all run artifacts, displays structured output |
| `visualize` | `_cmd_visualize` | Lazy-imports visualization, calls `launch_visualization_from_cli()` |

### Config Loading

`_load_config_file(path)` detects YAML (`.yaml`/`.yml`) vs. JSON by file extension, parses, and validates into `ExperimentConfig` via Pydantic's `model_validate()`.

### Output Modes

All list/show handlers support two output formats:
- **text** (default): Human-readable formatted output
- **json**: Machine-readable `json.dumps(data, indent=2)` output

### Visualization Launch

The `visualize` command lazy-imports the visualization package to avoid loading PySide6 for non-visualization commands. It converts `--start-phase` from string to `ReplayPhase` enum and delegates to `launch_visualization_from_cli()`.

## Assumptions and Limitations

- Repository root must exist and be writable
- No authentication or access control
- `--redo` performs `shutil.rmtree` on the experiment directory (destructive, no confirmation)
- Experiment names containing path separators would create nested directories (not validated against)
- The `visualize` command requires a display server (X11/Wayland) for PySide6
