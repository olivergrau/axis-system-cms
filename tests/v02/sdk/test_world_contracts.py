"""Verification tests for WP-1.2: World Contracts."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from axis.sdk import (
    BASE_ACTIONS,
    DOWN,
    LEFT,
    MOVEMENT_DELTAS,
    RIGHT,
    STAY,
    UP,
    ActionOutcome,
    BaseWorldConfig,
    CellView,
    Position,
    WorldView,
)


# ---------------------------------------------------------------------------
# Position
# ---------------------------------------------------------------------------


class TestPosition:
    """Tests for Position type."""

    def test_construction_origin(self) -> None:
        pos = Position(x=0, y=0)
        assert pos.x == 0
        assert pos.y == 0

    def test_construction_nonzero(self) -> None:
        pos = Position(x=5, y=3)
        assert pos.x == 5
        assert pos.y == 3

    def test_frozen(self) -> None:
        pos = Position(x=1, y=2)
        with pytest.raises(ValidationError):
            pos.x = 10  # type: ignore[misc]

    def test_equality(self) -> None:
        assert Position(x=1, y=2) == Position(x=1, y=2)
        assert Position(x=1, y=2) != Position(x=2, y=1)

    def test_hashable(self) -> None:
        """Position can be used as a dict key."""
        d: dict[Position, str] = {Position(x=0, y=0): "origin"}
        assert d[Position(x=0, y=0)] == "origin"

    def test_negative_coordinates(self) -> None:
        """Position allows negative coordinates (no constraint)."""
        pos = Position(x=-1, y=-5)
        assert pos.x == -1
        assert pos.y == -5


# ---------------------------------------------------------------------------
# CellView
# ---------------------------------------------------------------------------


class TestCellView:
    """Tests for CellView type."""

    def test_construction_empty(self) -> None:
        cell = CellView(cell_type="empty", resource_value=0.0)
        assert cell.cell_type == "empty"
        assert cell.resource_value == 0.0

    def test_construction_resource(self) -> None:
        cell = CellView(cell_type="resource", resource_value=0.75)
        assert cell.cell_type == "resource"
        assert cell.resource_value == 0.75

    def test_construction_obstacle(self) -> None:
        cell = CellView(cell_type="obstacle", resource_value=0.0)
        assert cell.cell_type == "obstacle"

    def test_resource_value_at_boundaries(self) -> None:
        CellView(cell_type="resource", resource_value=0.0)
        CellView(cell_type="resource", resource_value=1.0)

    def test_resource_value_below_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            CellView(cell_type="resource", resource_value=-0.1)

    def test_resource_value_above_one_raises(self) -> None:
        with pytest.raises(ValidationError):
            CellView(cell_type="resource", resource_value=1.1)

    def test_frozen(self) -> None:
        cell = CellView(cell_type="empty", resource_value=0.0)
        with pytest.raises(ValidationError):
            cell.cell_type = "resource"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ActionOutcome
# ---------------------------------------------------------------------------


class TestActionOutcome:
    """Tests for ActionOutcome type."""

    def test_construction_movement(self) -> None:
        outcome = ActionOutcome(
            action="up",
            moved=True,
            new_position=Position(x=1, y=0),
        )
        assert outcome.action == "up"
        assert outcome.moved is True
        assert outcome.new_position == Position(x=1, y=0)

    def test_defaults(self) -> None:
        outcome = ActionOutcome(
            action="up",
            moved=True,
            new_position=Position(x=0, y=0),
        )
        assert outcome.consumed is False
        assert outcome.resource_consumed == 0.0

    def test_construction_consume(self) -> None:
        outcome = ActionOutcome(
            action="consume",
            moved=False,
            new_position=Position(x=2, y=3),
            consumed=True,
            resource_consumed=0.5,
        )
        assert outcome.consumed is True
        assert outcome.resource_consumed == 0.5

    def test_frozen(self) -> None:
        outcome = ActionOutcome(
            action="stay",
            moved=False,
            new_position=Position(x=0, y=0),
        )
        with pytest.raises(ValidationError):
            outcome.moved = True  # type: ignore[misc]

    def test_stay_action(self) -> None:
        outcome = ActionOutcome(
            action="stay",
            moved=False,
            new_position=Position(x=3, y=3),
        )
        assert outcome.action == "stay"
        assert outcome.moved is False


# ---------------------------------------------------------------------------
# BaseWorldConfig
# ---------------------------------------------------------------------------


class TestBaseWorldConfig:
    """Tests for BaseWorldConfig type."""

    def test_construction_minimal(self) -> None:
        config = BaseWorldConfig(grid_width=10, grid_height=10)
        assert config.grid_width == 10
        assert config.grid_height == 10
        assert config.obstacle_density == 0.0

    def test_construction_with_obstacles(self) -> None:
        config = BaseWorldConfig(
            grid_width=20, grid_height=15, obstacle_density=0.3
        )
        assert config.obstacle_density == 0.3

    def test_grid_width_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            BaseWorldConfig(grid_width=0, grid_height=10)

    def test_grid_height_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            BaseWorldConfig(grid_width=10, grid_height=0)

    def test_obstacle_density_one_raises(self) -> None:
        with pytest.raises(ValidationError):
            BaseWorldConfig(grid_width=10, grid_height=10, obstacle_density=1.0)

    def test_obstacle_density_negative_raises(self) -> None:
        with pytest.raises(ValidationError):
            BaseWorldConfig(grid_width=10, grid_height=10, obstacle_density=-0.1)

    def test_obstacle_density_just_below_one(self) -> None:
        config = BaseWorldConfig(
            grid_width=10, grid_height=10, obstacle_density=0.99
        )
        assert config.obstacle_density == 0.99

    def test_frozen(self) -> None:
        config = BaseWorldConfig(grid_width=10, grid_height=10)
        with pytest.raises(ValidationError):
            config.grid_width = 20  # type: ignore[misc]


# ---------------------------------------------------------------------------
# WorldView protocol
# ---------------------------------------------------------------------------


class _MockWorldView:
    """Mock world view satisfying WorldView protocol."""

    def __init__(self) -> None:
        self._width = 5
        self._height = 5
        self._agent_position = Position(x=0, y=0)

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def agent_position(self) -> Position:
        return self._agent_position

    def get_cell(self, position: Position) -> CellView:
        return CellView(cell_type="empty", resource_value=0.0)

    def is_within_bounds(self, position: Position) -> bool:
        return 0 <= position.x < self._width and 0 <= position.y < self._height

    def is_traversable(self, position: Position) -> bool:
        return self.is_within_bounds(position)


class TestWorldViewProtocol:
    """Tests for WorldView protocol conformance."""

    def test_mock_satisfies_protocol(self) -> None:
        assert isinstance(_MockWorldView(), WorldView)

    def test_incomplete_class_fails_protocol(self) -> None:
        class _Incomplete:
            @property
            def width(self) -> int:
                return 5

            @property
            def height(self) -> int:
                return 5

        assert not isinstance(_Incomplete(), WorldView)

    def test_mock_methods_work(self) -> None:
        view = _MockWorldView()
        assert view.width == 5
        assert view.height == 5
        assert view.agent_position == Position(x=0, y=0)

        cell = view.get_cell(Position(x=0, y=0))
        assert isinstance(cell, CellView)

        assert view.is_within_bounds(Position(x=0, y=0)) is True
        assert view.is_within_bounds(Position(x=10, y=10)) is False
        assert view.is_traversable(Position(x=0, y=0)) is True


# ---------------------------------------------------------------------------
# Base action constants
# ---------------------------------------------------------------------------


class TestBaseActions:
    """Tests for base action constants."""

    def test_base_actions_count(self) -> None:
        assert len(BASE_ACTIONS) == 5

    def test_base_actions_content(self) -> None:
        assert BASE_ACTIONS == ("up", "down", "left", "right", "stay")

    def test_individual_constants(self) -> None:
        assert UP == "up"
        assert DOWN == "down"
        assert LEFT == "left"
        assert RIGHT == "right"
        assert STAY == "stay"

    def test_movement_deltas_count(self) -> None:
        assert len(MOVEMENT_DELTAS) == 4

    def test_movement_deltas_no_stay(self) -> None:
        assert "stay" not in MOVEMENT_DELTAS

    def test_movement_deltas_up(self) -> None:
        assert MOVEMENT_DELTAS["up"] == (0, -1)

    def test_movement_deltas_down(self) -> None:
        assert MOVEMENT_DELTAS["down"] == (0, 1)

    def test_movement_deltas_left(self) -> None:
        assert MOVEMENT_DELTAS["left"] == (-1, 0)

    def test_movement_deltas_right(self) -> None:
        assert MOVEMENT_DELTAS["right"] == (1, 0)


# ---------------------------------------------------------------------------
# Import verification
# ---------------------------------------------------------------------------


class TestImports:
    """Verify that all WP-1.2 exports are importable."""

    def test_import_world_types_from_sdk(self) -> None:
        from axis.sdk import (  # noqa: F401
            ActionOutcome,
            BaseWorldConfig,
            CellView,
            Position,
            WorldView,
        )

    def test_import_actions_from_sdk(self) -> None:
        from axis.sdk import (  # noqa: F401
            BASE_ACTIONS,
            DOWN,
            LEFT,
            MOVEMENT_DELTAS,
            RIGHT,
            STAY,
            UP,
        )

    def test_import_from_position_module(self) -> None:
        from axis.sdk.position import Position  # noqa: F401

    def test_import_from_world_types_module(self) -> None:
        from axis.sdk.world_types import (  # noqa: F401
            ActionOutcome,
            BaseWorldConfig,
            CellView,
            WorldView,
        )

    def test_import_from_actions_module(self) -> None:
        from axis.sdk.actions import (  # noqa: F401
            BASE_ACTIONS,
            MOVEMENT_DELTAS,
        )
