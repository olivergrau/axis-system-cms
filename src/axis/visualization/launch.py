"""Visualization viewer entry point.

Resolves adapters from episode data, builds session, launches UI.
"""

from __future__ import annotations

from pathlib import Path

from axis.framework.persistence import ExperimentRepository
from axis.visualization.errors import StepOutOfBoundsError
from axis.visualization.registry import (
    resolve_system_adapter,
    resolve_world_adapter,
)
from axis.visualization.replay_access import ReplayAccessService
from axis.visualization.snapshot_models import ReplayCoordinate
from axis.visualization.ui.app import launch_interactive_session
from axis.visualization.ui.main_window import VisualizationMainWindow
from axis.visualization.ui.session_controller import (
    VisualizationSessionController,
)


def launch_visualization(
    repository: ExperimentRepository,
    experiment_id: str,
    run_id: str,
    episode_index: int,
    *,
    start_step: int | None = None,
    start_phase: int | None = None,
    scale: float = 1.0,
    width_percent: float | None = None,
    world_vis_catalog: object | None = None,
    system_vis_catalog: object | None = None,
) -> int:
    """Load episode, resolve adapters, and launch the visualization viewer.

    Args:
        repository: Experiment repository root.
        experiment_id: Experiment to visualize.
        run_id: Run within the experiment.
        episode_index: Episode index within the run.
        start_step: Optional initial step (0-based).
        start_phase: Optional initial phase index.
        scale: UI scale factor (default 1.0).
        width_percent: Optional width as a percentage of the primary screen.

    Returns:
        Qt application exit code.
    """
    # 1. Import adapter modules to trigger registration
    _import_adapter_modules()

    # 2. Reject non-replay execution modes early.
    _ensure_visualization_supported(repository, experiment_id, run_id)

    # 3. Load and validate episode
    access = ReplayAccessService(repository)
    episode_handle = access.load_replay_episode(
        experiment_id, run_id, episode_index,
    )

    # 4. Read type identifiers from episode trace
    episode = episode_handle.episode_trace
    system_type = episode.system_type
    world_type = getattr(episode, "world_type", "grid_2d")
    world_config = getattr(episode, "world_config", {})

    # 5. Resolve adapters
    world_adapter = resolve_world_adapter(
        world_type, world_config,
        world_vis_catalog=world_vis_catalog,
    )
    system_adapter = resolve_system_adapter(
        system_type,
        system_vis_catalog=system_vis_catalog,
    )

    # 6. Build session controller
    controller = VisualizationSessionController(
        episode_handle, world_adapter, system_adapter,
    )

    # 7. Optional seek
    if start_step is not None:
        phase = start_phase if start_phase is not None else 0
        total = episode_handle.validation.total_steps
        if start_step < 0 or start_step >= total:
            raise StepOutOfBoundsError(start_step, total)
        controller.seek_to_coordinate(
            ReplayCoordinate(step_index=start_step, phase_index=phase),
        )

    # 8. Ensure QApplication exists before creating any widgets
    import os
    import sys
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon, QPixmap
    from PySide6.QtWidgets import QApplication

    if scale != 1.0:
        os.environ["QT_SCALE_FACTOR"] = str(scale)

    app = QApplication.instance() or QApplication(sys.argv)
    app.setDesktopFileName("axis-replay-viewer")

    experiment_config_text = _load_config_text(
        access.load_experiment_config,
        experiment_id,
    )
    run_config_text = _load_config_text(
        access.load_run_config,
        experiment_id,
        run_id,
    )

    icon_path = (
        Path(__file__).resolve().parents[3]
        / "docs" / "assets" / "images" / "logo_futuristic_elegant.png"
    )
    if icon_path.exists():
        icon = QIcon()
        pixmap = QPixmap(str(icon_path))
        for size in (16, 24, 32, 48, 64, 128, 256):
            icon.addPixmap(
                pixmap.scaled(size, size, mode=Qt.TransformationMode.SmoothTransformation),
            )
        app.setWindowIcon(icon)

    # 9. Build window
    phase_names = system_adapter.phase_names()
    overlay_declarations = system_adapter.available_overlay_types()
    initial_width, initial_height = _resolve_initial_window_size(
        app, width_percent=width_percent,
    )

    window = VisualizationMainWindow(
        world_adapter,
        phase_names,
        overlay_declarations,
        experiment_config_text=experiment_config_text,
        run_config_text=run_config_text,
        initial_width=initial_width,
        initial_height=initial_height,
    )

    # 10. Launch
    return launch_interactive_session(window, controller)


def _import_adapter_modules() -> None:
    """Legacy adapter import -- delegates to discover_plugins()."""
    from axis.plugins import discover_plugins

    discover_plugins()


def _load_config_text(loader, *args: object) -> str:
    """Return a JSON-formatted config text, falling back gracefully."""
    try:
        config = loader(*args)
    except Exception as exc:
        return f"Unavailable.\n\n{exc}"
    return config.model_dump_json(indent=2)


def _ensure_visualization_supported(
    repository: ExperimentRepository,
    experiment_id: str,
    run_id: str,
) -> None:
    """Reject visualization for non-replay execution outputs."""
    from axis.framework.experiment_output import load_experiment_output

    # Older or minimal repositories may not carry normalized experiment
    # output metadata yet. In that case we fall back to the replay loader
    # path and only enforce this guard when the persisted trace mode is
    # explicitly known to be non-replay-compatible.
    try:
        output = load_experiment_output(repository, experiment_id)
    except (FileNotFoundError, ValueError):
        output = None

    if getattr(output, "trace_mode", None) == "light":
        raise ValueError(
            f"Experiment '{experiment_id}' was executed in light trace mode and "
            "does not provide replay-compatible artifacts for visualization."
        )

    # Run-level metadata is checked as a second guardrail to catch mixed or
    # partially migrated metadata states.
    try:
        run_meta = repository.load_run_metadata(experiment_id, run_id)
    except Exception:
        return
    if getattr(run_meta, "trace_mode", None) == "light":
        raise ValueError(
            f"Run '{run_id}' in experiment '{experiment_id}' was executed in light "
            "trace mode and cannot be visualized."
        )


def _resolve_initial_window_size(
    app,
    *,
    width_percent: float | None,
) -> tuple[int, int]:
    """Resolve initial viewer size from screen geometry and optional width."""
    default_width = 1440
    default_height = 800
    screen = app.primaryScreen()
    if screen is None:
        return default_width, default_height

    available = screen.availableGeometry()
    max_width = max(960, int(available.width() * 0.95))
    max_height = max(700, int(available.height() * 0.9))
    if width_percent is None:
        width = min(default_width, max_width)
    else:
        width = int(available.width() * (width_percent / 100.0))
        width = min(width, max_width)
    height = min(default_height, max_height)
    return width, height
