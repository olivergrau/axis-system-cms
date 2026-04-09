"""Tests for WP-V.4.3: Generalized UI Panels."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

from PySide6.QtWidgets import QApplication  # noqa: E402

from axis.visualization.snapshot_models import ReplayCoordinate  # noqa: E402
from axis.visualization.types import (  # noqa: E402
    AnalysisRow,
    AnalysisSection,
    MetadataSection,
    OverlayTypeDeclaration,
)
from axis.visualization.view_models import (  # noqa: E402
    AgentViewModel,
    GridCellViewModel,
    GridViewModel,
    SelectionType,
    SelectionViewModel,
    StatusBarViewModel,
    ViewerFrameViewModel,
)
from axis.visualization.viewer_state import PlaybackMode  # noqa: E402

from axis.visualization.ui.status_panel import StatusPanel  # noqa: E402
from axis.visualization.ui.step_analysis_panel import StepAnalysisPanel  # noqa: E402
from axis.visualization.ui.detail_panel import DetailPanel  # noqa: E402
from axis.visualization.ui.replay_controls_panel import (  # noqa: E402
    ReplayControlsPanel,
)
from axis.visualization.ui.overlay_panel import OverlayPanel  # noqa: E402


# ---------------------------------------------------------------------------
# QApplication fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_status(
    step_index: int = 0,
    total_steps: int = 10,
    phase_index: int = 0,
    phase_name: str = "BEFORE",
    vitality_display: str = "50.00 / 100.00",
    vitality_label: str = "Energy",
    world_info: str | None = None,
    at_start: bool = True,
    at_end: bool = False,
    playback_mode: PlaybackMode = PlaybackMode.PAUSED,
) -> StatusBarViewModel:
    return StatusBarViewModel(
        step_index=step_index,
        total_steps=total_steps,
        phase_index=phase_index,
        phase_name=phase_name,
        playback_mode=playback_mode,
        vitality_display=vitality_display,
        vitality_label=vitality_label,
        world_info=world_info,
        at_start=at_start,
        at_end=at_end,
    )


def _make_grid_cell(
    row: int = 0, col: int = 0,
    resource_value: float = 0.0,
    is_obstacle: bool = False,
    is_agent_here: bool = False,
    is_selected: bool = False,
) -> GridCellViewModel:
    return GridCellViewModel(
        row=row, col=col,
        resource_value=resource_value,
        is_obstacle=is_obstacle,
        is_traversable=not is_obstacle,
        is_agent_here=is_agent_here,
        is_selected=is_selected,
    )


def _make_frame(
    selection_type: SelectionType = SelectionType.NONE,
    selected_cell: tuple[int, int] | None = None,
    agent_selected: bool = False,
    world_metadata: tuple[MetadataSection, ...] = (),
    status: StatusBarViewModel | None = None,
) -> ViewerFrameViewModel:
    cells = tuple(
        _make_grid_cell(row=r, col=c, resource_value=0.3 if (
            r == 1 and c == 2) else 0.0)
        for r in range(3)
        for c in range(3)
    )
    grid = GridViewModel(width=3, height=3, cells=cells)
    agent = AgentViewModel(row=1, col=1, vitality=0.8,
                           is_selected=agent_selected)
    selection = SelectionViewModel(
        selection_type=selection_type,
        selected_cell=selected_cell,
        agent_selected=agent_selected,
    )
    return ViewerFrameViewModel(
        coordinate=ReplayCoordinate(step_index=0, phase_index=0),
        grid=grid,
        agent=agent,
        status=status or _make_status(),
        selection=selection,
        topology_indicators=(),
        world_metadata_sections=world_metadata,
        analysis_sections=(),
        overlay_data=(),
    )


# ---------------------------------------------------------------------------
# StatusPanel tests
# ---------------------------------------------------------------------------


class TestStatusPanel:

    def test_status_panel_construction(self, qapp) -> None:
        panel = StatusPanel()
        assert panel.maximumHeight() == 40

    def test_status_panel_step_display(self, qapp) -> None:
        panel = StatusPanel()
        panel.set_frame(_make_status(step_index=0, total_steps=10))
        assert panel._step_label.text() == "Step: 1 / 10"

    def test_status_panel_phase_name(self, qapp) -> None:
        panel = StatusPanel()
        panel.set_frame(_make_status(phase_name="AFTER_REGEN"))
        assert panel._phase_label.text() == "Phase: AFTER_REGEN"

    def test_status_panel_vitality_with_label(self, qapp) -> None:
        panel = StatusPanel()
        panel.set_frame(_make_status(
            vitality_label="Energy",
            vitality_display="50.00 / 100.00",
        ))
        assert panel._vitality_label.text() == "Energy: 50.00 / 100.00"

    def test_status_panel_world_info_shown(self, qapp) -> None:
        panel = StatusPanel()
        panel.set_frame(_make_status(world_info="Toroidal topology"))
        assert not panel._world_info_label.isHidden()
        assert panel._world_info_label.text() == "Toroidal topology"

    def test_status_panel_world_info_hidden(self, qapp) -> None:
        panel = StatusPanel()
        panel.set_frame(_make_status(world_info=None))
        assert panel._world_info_label.isHidden()


# ---------------------------------------------------------------------------
# StepAnalysisPanel tests
# ---------------------------------------------------------------------------


class TestStepAnalysisPanel:

    def test_analysis_panel_hidden_initially(self, qapp) -> None:
        panel = StepAnalysisPanel()
        assert not panel.isVisible()

    def test_analysis_panel_shows_sections(self, qapp) -> None:
        panel = StepAnalysisPanel()
        sections = (
            AnalysisSection(
                title="Section A",
                rows=(AnalysisRow(label="K1", value="V1"),),
            ),
            AnalysisSection(
                title="Section B",
                rows=(AnalysisRow(label="K2", value="V2"),),
            ),
        )
        panel.set_sections(sections)
        assert panel.isVisible()
        text = panel._content_label.text()
        assert "Section A" in text
        assert "Section B" in text

    def test_analysis_panel_hides_when_empty(self, qapp) -> None:
        panel = StepAnalysisPanel()
        # First show it
        panel.set_sections((
            AnalysisSection(title="X", rows=(
                AnalysisRow(label="k", value="v"),)),
        ))
        assert panel.isVisible()
        # Then clear
        panel.set_sections(())
        assert not panel.isVisible()

    def test_analysis_panel_renders_rows(self, qapp) -> None:
        panel = StepAnalysisPanel()
        sections = (
            AnalysisSection(
                title="Overview",
                rows=(
                    AnalysisRow(label="Action", value="right"),
                    AnalysisRow(label="Score", value="0.75"),
                ),
            ),
        )
        panel.set_sections(sections)
        text = panel._content_label.text()
        assert "Action: right" in text
        assert "Score: 0.75" in text

    def test_analysis_panel_renders_sub_rows(self, qapp) -> None:
        panel = StepAnalysisPanel()
        sections = (
            AnalysisSection(
                title="Drives",
                rows=(
                    AnalysisRow(
                        label="Hunger",
                        value="0.60",
                        sub_rows=(
                            AnalysisRow(label="Weight", value="0.3"),
                        ),
                    ),
                ),
            ),
        )
        panel.set_sections(sections)
        text = panel._content_label.text()
        assert "Hunger: 0.60" in text
        assert "Weight: 0.3" in text


# ---------------------------------------------------------------------------
# DetailPanel tests
# ---------------------------------------------------------------------------


class TestDetailPanel:

    def test_detail_panel_no_selection(self, qapp) -> None:
        panel = DetailPanel()
        frame = _make_frame()
        panel.set_frame(frame)
        assert "No entity selected" in panel._content_label.text()

    def test_detail_panel_cell_selection(self, qapp) -> None:
        panel = DetailPanel()
        frame = _make_frame(
            selection_type=SelectionType.CELL,
            selected_cell=(1, 2),
        )
        panel.set_frame(frame)
        text = panel._content_label.text()
        assert "Cell Info" in text
        assert "Position: (1, 2)" in text
        assert "Resource: 0.300" in text

    def test_detail_panel_agent_selection(self, qapp) -> None:
        panel = DetailPanel()
        frame = _make_frame(
            selection_type=SelectionType.AGENT,
            agent_selected=True,
        )
        panel.set_frame(frame)
        text = panel._content_label.text()
        assert "Agent Info" in text
        assert "Position: (1, 1)" in text

    def test_detail_panel_world_metadata(self, qapp) -> None:
        panel = DetailPanel()
        metadata = (
            MetadataSection(
                title="Topology",
                rows=(AnalysisRow(label="Type", value="Toroidal"),),
            ),
        )
        frame = _make_frame(world_metadata=metadata)
        panel.set_frame(frame)
        text = panel._content_label.text()
        assert "Topology" in text
        assert "Type: Toroidal" in text


# ---------------------------------------------------------------------------
# ReplayControlsPanel tests
# ---------------------------------------------------------------------------


class TestReplayControlsPanel:

    def test_controls_3phase_combo(self, qapp) -> None:
        panel = ReplayControlsPanel(["BEFORE", "AFTER_REGEN", "AFTER_ACTION"])
        assert panel._phase_combo.count() == 3

    def test_controls_2phase_combo(self, qapp) -> None:
        panel = ReplayControlsPanel(["BEFORE", "AFTER_ACTION"])
        assert panel._phase_combo.count() == 2

    def test_controls_phase_selected_signal(self, qapp) -> None:
        panel = ReplayControlsPanel(["BEFORE", "AFTER_REGEN", "AFTER_ACTION"])
        received = []
        panel.phase_selected.connect(lambda idx: received.append(idx))
        panel._phase_combo.setCurrentIndex(2)
        assert received == [2]

    def test_controls_button_enabled_state(self, qapp) -> None:
        panel = ReplayControlsPanel(["BEFORE", "AFTER_ACTION"])
        # At start → back disabled
        panel.set_frame(_make_status(at_start=True, at_end=False))
        assert not panel._btn_back.isEnabled()
        assert panel._btn_fwd.isEnabled()

        # At end → forward disabled
        panel.set_frame(_make_status(at_start=False, at_end=True))
        assert panel._btn_back.isEnabled()
        assert not panel._btn_fwd.isEnabled()

    def test_controls_no_re_entrant_signal(self, qapp) -> None:
        panel = ReplayControlsPanel(["BEFORE", "AFTER_REGEN", "AFTER_ACTION"])
        received = []
        panel.phase_selected.connect(lambda idx: received.append(idx))
        # set_frame should NOT emit phase_selected
        panel.set_frame(_make_status(phase_index=1))
        assert len(received) == 0


# ---------------------------------------------------------------------------
# OverlayPanel tests
# ---------------------------------------------------------------------------


_DECLARATIONS_3 = [
    OverlayTypeDeclaration(
        key="action_pref", label="Action Pref", description="Arrow overlay",
        legend_html="<span style='color:cyan'>\u2192</span>=selected",
    ),
    OverlayTypeDeclaration(
        key="drive_contrib", label="Drive Contrib", description="Bar chart",
        legend_html="<span style='color:blue'>\u25a0</span>=contribution",
    ),
    OverlayTypeDeclaration(
        key="consumption", label="Consumption", description="Diamond + dots",
        legend_html="<span style='color:gold'>\u25c6</span>=resource",
    ),
]

_DECLARATIONS_2 = [
    OverlayTypeDeclaration(
        key="action_weights", label="Weights", description="Action weight arrows",
        legend_html="<span style='color:yellow'>\u2192</span>=selected",
    ),
    OverlayTypeDeclaration(
        key="scan_result", label="Scan", description="Scan radius circle",
    ),
]


class TestOverlayPanel:

    def test_overlay_panel_dynamic_checkboxes(self, qapp) -> None:
        panel = OverlayPanel(_DECLARATIONS_3)
        assert len(panel._checkboxes) == 3
        assert "action_pref" in panel._checkboxes
        assert "drive_contrib" in panel._checkboxes
        assert "consumption" in panel._checkboxes

    def test_overlay_panel_2_declarations(self, qapp) -> None:
        panel = OverlayPanel(_DECLARATIONS_2)
        assert len(panel._checkboxes) == 2

    def test_overlay_panel_master_enables_children(self, qapp) -> None:
        panel = OverlayPanel(_DECLARATIONS_3)
        # Initially disabled
        for cb in panel._checkboxes.values():
            assert not cb.isEnabled()
        # Toggle master on
        panel._master_cb.setChecked(True)
        for cb in panel._checkboxes.values():
            assert cb.isEnabled()

    def test_overlay_panel_master_disables_children(self, qapp) -> None:
        panel = OverlayPanel(_DECLARATIONS_3)
        panel._master_cb.setChecked(True)
        panel._master_cb.setChecked(False)
        for cb in panel._checkboxes.values():
            assert not cb.isEnabled()

    def test_overlay_panel_overlay_toggled_signal(self, qapp) -> None:
        panel = OverlayPanel(_DECLARATIONS_3)
        panel._master_cb.setChecked(True)

        received = []
        panel.overlay_toggled.connect(
            lambda key, checked: received.append((key, checked)))

        panel._checkboxes["action_pref"].setChecked(True)
        assert ("action_pref", True) in received

    def test_overlay_panel_tooltips(self, qapp) -> None:
        panel = OverlayPanel(_DECLARATIONS_3)
        assert panel._checkboxes["action_pref"].toolTip() == "Arrow overlay"
        assert panel._checkboxes["drive_contrib"].toolTip() == "Bar chart"
        assert panel._checkboxes["consumption"].toolTip() == "Diamond + dots"


# ---------------------------------------------------------------------------
# OverlayPanel legend tests
# ---------------------------------------------------------------------------


class TestOverlayPanelLegend:

    def test_legend_labels_created_for_declarations_with_html(
        self, qapp,
    ) -> None:
        panel = OverlayPanel(_DECLARATIONS_3)
        assert len(panel._legend_labels) == 3
        assert "action_pref" in panel._legend_labels
        assert "drive_contrib" in panel._legend_labels
        assert "consumption" in panel._legend_labels

    def test_legend_labels_not_created_when_html_empty(self, qapp) -> None:
        # _DECLARATIONS_2: scan_result has no legend_html
        panel = OverlayPanel(_DECLARATIONS_2)
        assert "action_weights" in panel._legend_labels
        assert "scan_result" not in panel._legend_labels

    def test_legend_labels_hidden_initially(self, qapp) -> None:
        panel = OverlayPanel(_DECLARATIONS_3)
        for lbl in panel._legend_labels.values():
            assert lbl.isHidden()

    def test_legend_shows_when_overlay_toggled_on(self, qapp) -> None:
        panel = OverlayPanel(_DECLARATIONS_3)
        panel._master_cb.setChecked(True)
        panel._checkboxes["action_pref"].setChecked(True)
        assert not panel._legend_labels["action_pref"].isHidden()
        assert panel._legend_labels["drive_contrib"].isHidden()

    def test_legend_hides_when_overlay_toggled_off(self, qapp) -> None:
        panel = OverlayPanel(_DECLARATIONS_3)
        panel._master_cb.setChecked(True)
        panel._checkboxes["action_pref"].setChecked(True)
        panel._checkboxes["action_pref"].setChecked(False)
        assert panel._legend_labels["action_pref"].isHidden()

    def test_legend_hidden_when_master_off(self, qapp) -> None:
        panel = OverlayPanel(_DECLARATIONS_3)
        panel._master_cb.setChecked(True)
        panel._checkboxes["action_pref"].setChecked(True)
        assert not panel._legend_labels["action_pref"].isHidden()
        # Turn master off
        panel._master_cb.setChecked(False)
        assert panel._legend_labels["action_pref"].isHidden()

    def test_legend_restored_when_master_back_on(self, qapp) -> None:
        panel = OverlayPanel(_DECLARATIONS_3)
        panel._master_cb.setChecked(True)
        panel._checkboxes["action_pref"].setChecked(True)
        panel._master_cb.setChecked(False)
        panel._master_cb.setChecked(True)
        assert not panel._legend_labels["action_pref"].isHidden()

    def test_legend_contains_expected_html(self, qapp) -> None:
        panel = OverlayPanel(_DECLARATIONS_3)
        lbl = panel._legend_labels["action_pref"]
        assert "selected" in lbl.text()
