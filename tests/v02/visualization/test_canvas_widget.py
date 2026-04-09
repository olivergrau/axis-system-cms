"""Tests for WP-V.4.1: CanvasWidget (world-adapter-aware canvas)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

from PySide6.QtCore import QPointF, Qt  # noqa: E402
from PySide6.QtGui import QMouseEvent  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from axis.sdk.position import Position  # noqa: E402
from axis.visualization.adapters.default_world import (  # noqa: E402
    DefaultWorldVisualizationAdapter,
)
from axis.visualization.types import (  # noqa: E402
    CellColorConfig,
    CellLayout,
    CellShape,
    TopologyIndicator,
)
from axis.visualization.ui.canvas_widget import CanvasWidget  # noqa: E402
from axis.visualization.view_models import (  # noqa: E402
    AgentViewModel,
    GridCellViewModel,
    GridViewModel,
    SelectionType,
    SelectionViewModel,
)


# ---------------------------------------------------------------------------
# QApplication fixture (session-scoped)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


# ---------------------------------------------------------------------------
# Helper: world adapter fixture
# ---------------------------------------------------------------------------


class _TestWorldAdapter(DefaultWorldVisualizationAdapter):
    """Extends default adapter so pixel_to_grid returns known results."""

    def pixel_to_grid(self, pixel_x, pixel_y, cell_layout):
        # Simple rectangular hit-test
        return super().pixel_to_grid(pixel_x, pixel_y, cell_layout)


def _make_adapter() -> _TestWorldAdapter:
    return _TestWorldAdapter()


# ---------------------------------------------------------------------------
# Helper: grid and frame data
# ---------------------------------------------------------------------------


def _make_grid(
    width: int = 5, height: int = 5,
    obstacle_at: tuple[int, int] | None = None,
    resource_at: tuple[int, int] | None = None,
    resource_value: float = 0.5,
) -> GridViewModel:
    cells = []
    for r in range(height):
        for c in range(width):
            is_obs = obstacle_at == (r, c) if obstacle_at else False
            res = resource_value if (
                resource_at and resource_at == (r, c)) else 0.0
            cells.append(
                GridCellViewModel(
                    row=r, col=c,
                    resource_value=res,
                    is_obstacle=is_obs,
                    is_traversable=not is_obs,
                    is_agent_here=False,
                    is_selected=False,
                ),
            )
    return GridViewModel(width=width, height=height, cells=tuple(cells))


def _make_agent(row: int = 1, col: int = 1) -> AgentViewModel:
    return AgentViewModel(row=row, col=col, vitality=0.8, is_selected=False)


def _make_selection(
    selected_cell: tuple[int, int] | None = None,
) -> SelectionViewModel:
    if selected_cell is not None:
        return SelectionViewModel(
            selection_type=SelectionType.CELL,
            selected_cell=selected_cell,
            agent_selected=False,
        )
    return SelectionViewModel(
        selection_type=SelectionType.NONE,
        selected_cell=None,
        agent_selected=False,
    )


# ---------------------------------------------------------------------------
# Construction tests
# ---------------------------------------------------------------------------


class TestConstruction:

    def test_canvas_construction(self, qapp) -> None:
        adapter = _make_adapter()
        canvas = CanvasWidget(adapter)
        assert canvas.minimumWidth() == 200
        assert canvas.minimumHeight() == 200

    def test_canvas_cell_color_config_from_adapter(self, qapp) -> None:
        adapter = _make_adapter()
        canvas = CanvasWidget(adapter)
        expected = adapter.cell_color_config()
        assert canvas._cell_color_config == expected


# ---------------------------------------------------------------------------
# Color resolution tests
# ---------------------------------------------------------------------------


class TestColorResolution:

    def _canvas(self, qapp) -> CanvasWidget:
        return CanvasWidget(_make_adapter())

    def test_resolve_cell_color_obstacle(self, qapp) -> None:
        canvas = self._canvas(qapp)
        cell = GridCellViewModel(
            row=0, col=0, resource_value=0.0,
            is_obstacle=True, is_traversable=False,
            is_agent_here=False, is_selected=False,
        )
        color = canvas._resolve_cell_color(cell)
        assert color == canvas._cell_color_config.obstacle_color

    def test_resolve_cell_color_empty(self, qapp) -> None:
        canvas = self._canvas(qapp)
        cell = GridCellViewModel(
            row=0, col=0, resource_value=0.0,
            is_obstacle=False, is_traversable=True,
            is_agent_here=False, is_selected=False,
        )
        color = canvas._resolve_cell_color(cell)
        assert color == canvas._cell_color_config.empty_color

    def test_resolve_cell_color_full_resource(self, qapp) -> None:
        canvas = self._canvas(qapp)
        cell = GridCellViewModel(
            row=0, col=0, resource_value=1.0,
            is_obstacle=False, is_traversable=True,
            is_agent_here=False, is_selected=False,
        )
        color = canvas._resolve_cell_color(cell)
        assert color == canvas._cell_color_config.resource_color_max

    def test_resolve_cell_color_half_resource(self, qapp) -> None:
        canvas = self._canvas(qapp)
        cell = GridCellViewModel(
            row=0, col=0, resource_value=0.5,
            is_obstacle=False, is_traversable=True,
            is_agent_here=False, is_selected=False,
        )
        color = canvas._resolve_cell_color(cell)
        cc = canvas._cell_color_config
        # Midpoint between min and max
        expected = tuple(
            int(cc.resource_color_min[i]
                + 0.5 * (cc.resource_color_max[i] - cc.resource_color_min[i]))
            for i in range(3)
        )
        assert color == expected

    def test_resolve_cell_color_clamped(self, qapp) -> None:
        canvas = self._canvas(qapp)
        cell = GridCellViewModel(
            row=0, col=0, resource_value=1.5,
            is_obstacle=False, is_traversable=True,
            is_agent_here=False, is_selected=False,
        )
        color = canvas._resolve_cell_color(cell)
        # Clamped to 1.0 → same as resource_color_max
        assert color == canvas._cell_color_config.resource_color_max


# ---------------------------------------------------------------------------
# Layout tests
# ---------------------------------------------------------------------------


class TestLayout:

    def test_recompute_layout_on_set_frame(self, qapp) -> None:
        canvas = CanvasWidget(_make_adapter())
        canvas.resize(400, 400)
        assert canvas._cell_layout is None
        canvas.set_frame(
            _make_grid(), _make_agent(), _make_selection(),
        )
        assert canvas._cell_layout is not None
        assert canvas._cell_layout.grid_width == 5
        assert canvas._cell_layout.grid_height == 5

    def test_layout_recomputed_on_resize(self, qapp) -> None:
        adapter = _make_adapter()
        canvas = CanvasWidget(adapter)
        canvas.resize(400, 400)
        canvas.set_frame(
            _make_grid(), _make_agent(), _make_selection(),
        )
        layout_before = canvas._cell_layout
        assert layout_before is not None

        # Directly call _recompute_layout after changing size
        # (offscreen widgets don't trigger resizeEvent from resize())
        canvas.resize(600, 600)
        canvas._recompute_layout()
        layout_after = canvas._cell_layout
        assert layout_after is not None
        assert layout_after.canvas_width != layout_before.canvas_width


# ---------------------------------------------------------------------------
# Hit-testing tests
# ---------------------------------------------------------------------------


class TestHitTesting:

    def test_mouse_click_emits_cell_clicked(self, qapp) -> None:
        adapter = _make_adapter()
        canvas = CanvasWidget(adapter)
        canvas.resize(500, 500)
        canvas.set_frame(
            _make_grid(), _make_agent(row=3, col=3), _make_selection(),
        )

        received = []
        canvas.cell_clicked.connect(lambda r, c: received.append((r, c)))

        # Click center of cell (0, 0) → pixel (50, 50) for 500x500 canvas, 5x5 grid
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPointF(50.0, 50.0),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        canvas.mousePressEvent(event)
        assert received == [(0, 0)]

    def test_mouse_click_on_agent_emits_agent_clicked(self, qapp) -> None:
        adapter = _make_adapter()
        canvas = CanvasWidget(adapter)
        canvas.resize(500, 500)
        # Agent at row=1, col=1
        canvas.set_frame(
            _make_grid(), _make_agent(row=1, col=1), _make_selection(),
        )

        agent_signals = []
        canvas.agent_clicked.connect(lambda: agent_signals.append(True))

        # Center of cell (col=1, row=1): pixel (150, 150) for 500/5=100 px cells
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPointF(150.0, 150.0),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        canvas.mousePressEvent(event)
        assert len(agent_signals) == 1

    def test_mouse_click_out_of_bounds(self, qapp) -> None:
        adapter = _make_adapter()
        canvas = CanvasWidget(adapter)
        canvas.resize(500, 500)
        canvas.set_frame(
            _make_grid(), _make_agent(), _make_selection(),
        )

        cell_clicked_emitted = False
        agent_clicked_emitted = False

        def on_cell(r, c):
            nonlocal cell_clicked_emitted
            cell_clicked_emitted = True

        def on_agent():
            nonlocal agent_clicked_emitted
            agent_clicked_emitted = True

        canvas.cell_clicked.connect(on_cell)
        canvas.agent_clicked.connect(on_agent)

        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPointF(-10.0, -10.0),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        canvas.mousePressEvent(event)
        assert not cell_clicked_emitted
        assert not agent_clicked_emitted


# ---------------------------------------------------------------------------
# Frame update tests
# ---------------------------------------------------------------------------


class TestFrameUpdate:

    def test_set_frame_stores_data(self, qapp) -> None:
        canvas = CanvasWidget(_make_adapter())
        canvas.resize(400, 400)
        grid = _make_grid()
        agent = _make_agent()
        selection = _make_selection()

        canvas.set_frame(grid, agent, selection)
        assert canvas._grid is grid
        assert canvas._agent is agent
        assert canvas._selection is selection

    def test_set_frame_triggers_update(self, qapp) -> None:
        canvas = CanvasWidget(_make_adapter())
        canvas.resize(400, 400)

        # Track if update was called by checking that set_frame doesn't crash
        # (In headless mode we can't easily verify paint scheduling,
        #  but we verify the method completes without error)
        grid = _make_grid()
        agent = _make_agent()
        selection = _make_selection()
        canvas.set_frame(grid, agent, selection)
        # If we get here, update() was called without crash
        assert canvas._grid is not None


# ---------------------------------------------------------------------------
# Topology indicator tests
# ---------------------------------------------------------------------------


class TestTopology:

    def test_topology_indicators_stored(self, qapp) -> None:
        canvas = CanvasWidget(_make_adapter())
        canvas.resize(400, 400)

        indicators = (
            TopologyIndicator(
                indicator_type="wrap_edge",
                position=(0.0, 0.0),
                data={"edge": "top"},
            ),
            TopologyIndicator(
                indicator_type="hotspot_center",
                position=(100.0, 100.0),
                data={"radius_pixels": 8, "intensity": 0.5, "label": "H1"},
            ),
        )

        canvas.set_frame(
            _make_grid(), _make_agent(), _make_selection(),
            topology_indicators=indicators,
        )
        assert canvas._topology_indicators == indicators
        assert len(canvas._topology_indicators) == 2


# ---------------------------------------------------------------------------
# Painting tests (smoke tests)
# ---------------------------------------------------------------------------


class TestPainting:

    def test_paint_event_no_crash(self, qapp) -> None:
        canvas = CanvasWidget(_make_adapter())
        canvas.resize(400, 400)
        canvas.set_frame(
            _make_grid(
                obstacle_at=(0, 0),
                resource_at=(2, 2),
                resource_value=0.7,
            ),
            _make_agent(),
            _make_selection(selected_cell=(1, 1)),
            topology_indicators=(
                TopologyIndicator(
                    indicator_type="wrap_edge",
                    position=(10.0, 10.0),
                    data={"edge": "left"},
                ),
                TopologyIndicator(
                    indicator_type="hotspot_center",
                    position=(200.0, 200.0),
                    data={
                        "radius_pixels": 10,
                        "intensity": 0.8,
                        "label": "Center",
                    },
                ),
            ),
        )
        # Force a paint -- should not crash in offscreen mode
        canvas.repaint()

    def test_paint_event_without_frame(self, qapp) -> None:
        canvas = CanvasWidget(_make_adapter())
        canvas.resize(400, 400)
        # No set_frame called -- paintEvent should bail out gracefully
        canvas.repaint()
