"""Visualization viewer entry point.

Resolves adapters from episode data, builds session, launches UI.
"""

from __future__ import annotations

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

    Returns:
        Qt application exit code.
    """
    # 1. Import adapter modules to trigger registration
    _import_adapter_modules()

    # 2. Load and validate episode
    access = ReplayAccessService(repository)
    episode_handle = access.load_replay_episode(
        experiment_id, run_id, episode_index,
    )

    # 3. Read type identifiers from episode trace
    episode = episode_handle.episode_trace
    system_type = episode.system_type
    world_type = getattr(episode, "world_type", "grid_2d")
    world_config = getattr(episode, "world_config", {})

    # 4. Resolve adapters
    world_adapter = resolve_world_adapter(world_type, world_config)
    system_adapter = resolve_system_adapter(system_type)

    # 5. Build session controller
    controller = VisualizationSessionController(
        episode_handle, world_adapter, system_adapter,
    )

    # 6. Optional seek
    if start_step is not None:
        phase = start_phase if start_phase is not None else 0
        total = episode_handle.validation.total_steps
        if start_step < 0 or start_step >= total:
            raise StepOutOfBoundsError(start_step, total)
        controller.seek_to_coordinate(
            ReplayCoordinate(step_index=start_step, phase_index=phase),
        )

    # 7. Ensure QApplication exists before creating any widgets
    import os
    import sys
    from PySide6.QtWidgets import QApplication

    if scale != 1.0:
        os.environ["QT_SCALE_FACTOR"] = str(scale)

    app = QApplication.instance() or QApplication(sys.argv)

    # 8. Build window
    phase_names = system_adapter.phase_names()
    overlay_declarations = system_adapter.available_overlay_types()

    window = VisualizationMainWindow(
        world_adapter, phase_names, overlay_declarations,
    )

    # 9. Launch
    return launch_interactive_session(window, controller)


def _import_adapter_modules() -> None:
    """Import adapter visualization modules to trigger registration.

    Each module calls register_world_visualization() or
    register_system_visualization() at import time.
    """
    try:
        import axis.world.grid_2d.visualization  # noqa: F401
    except ImportError:
        pass
    try:
        import axis.world.toroidal.visualization  # noqa: F401
    except ImportError:
        pass
    try:
        import axis.world.signal_landscape.visualization  # noqa: F401
    except ImportError:
        pass
    try:
        import axis.systems.system_a.visualization  # noqa: F401
    except ImportError:
        pass
    try:
        import axis.systems.system_aw.visualization  # noqa: F401
    except ImportError:
        pass
    try:
        import axis.systems.system_b.visualization  # noqa: F401
    except ImportError:
        pass
