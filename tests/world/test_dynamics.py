"""WP-2.2 verification tests -- World dynamics (regeneration)."""

from __future__ import annotations

from axis.sdk.position import Position
from axis.world.grid_2d.dynamics import apply_regeneration
from axis.world.grid_2d.model import Cell, CellType, World


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_world_with_cells(
    cells: dict[tuple[int, int], Cell],
    width: int = 5,
    height: int = 5,
    agent_pos: Position | None = None,
) -> World:
    """Create a world with specific cells placed on an otherwise empty grid."""
    empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
    grid = [[empty for _ in range(width)] for _ in range(height)]
    for (x, y), cell in cells.items():
        grid[y][x] = cell
    return World(
        grid=grid,
        agent_position=agent_pos or Position(x=0, y=0),
    )


# ---------------------------------------------------------------------------
# No-op when rate is zero
# ---------------------------------------------------------------------------


class TestRegenZeroRate:
    """No changes when regen_rate is 0.0."""

    def test_returns_zero(self) -> None:
        world = _make_world_with_cells({})
        count = apply_regeneration(world, regen_rate=0.0)
        assert count == 0

    def test_world_unchanged(self) -> None:
        cells = {
            (1, 1): Cell(cell_type=CellType.RESOURCE, resource_value=0.5),
        }
        world = _make_world_with_cells(cells)
        apply_regeneration(world, regen_rate=0.0)
        cell = world.get_internal_cell(Position(x=1, y=1))
        assert cell.resource_value == 0.5


# ---------------------------------------------------------------------------
# Basic regeneration
# ---------------------------------------------------------------------------


class TestBasicRegeneration:
    """Empty cells gain resource and become RESOURCE."""

    def test_empty_cell_gains_resource(self) -> None:
        world = _make_world_with_cells({})
        count = apply_regeneration(world, regen_rate=0.1)
        # All 25 empty cells should gain resource
        assert count == 25
        cell = world.get_internal_cell(Position(x=2, y=2))
        assert cell.cell_type == CellType.RESOURCE
        assert cell.resource_value == pytest.approx(0.1)

    def test_returns_updated_count(self) -> None:
        # Place one non-eligible cell to verify count
        cells = {
            (1, 1): Cell(
                cell_type=CellType.EMPTY, resource_value=0.0, regen_eligible=False,
            ),
        }
        world = _make_world_with_cells(cells)
        count = apply_regeneration(world, regen_rate=0.1)
        # 25 cells total, 1 non-eligible -> 24 updated
        assert count == 24

    def test_zero_cooldown_preserves_immediate_regeneration(self) -> None:
        cells = {
            (1, 1): Cell(cell_type=CellType.EMPTY, resource_value=0.0),
        }
        world = _make_world_with_cells(cells, width=3, height=3)
        count = apply_regeneration(world, regen_rate=0.1)
        assert count == 9
        cell = world.get_internal_cell(Position(x=1, y=1))
        assert cell.cell_type == CellType.RESOURCE
        assert cell.resource_value == 0.1


# ---------------------------------------------------------------------------
# Resource accumulation
# ---------------------------------------------------------------------------

import pytest  # noqa: E402


class TestResourceAccumulation:
    """Resource values accumulate and clamp at 1.0."""

    def test_accumulates(self) -> None:
        cells = {
            (2, 2): Cell(cell_type=CellType.RESOURCE, resource_value=0.5),
        }
        world = _make_world_with_cells(cells)
        apply_regeneration(world, regen_rate=0.3)
        cell = world.get_internal_cell(Position(x=2, y=2))
        assert cell.resource_value == pytest.approx(0.8)

    def test_clamps_to_one(self) -> None:
        cells = {
            (2, 2): Cell(cell_type=CellType.RESOURCE, resource_value=0.9),
        }
        world = _make_world_with_cells(cells)
        apply_regeneration(world, regen_rate=0.2)
        cell = world.get_internal_cell(Position(x=2, y=2))
        assert cell.resource_value == pytest.approx(1.0)

    def test_already_full_not_counted(self) -> None:
        cells = {
            (2, 2): Cell(cell_type=CellType.RESOURCE, resource_value=1.0),
        }
        world = _make_world_with_cells(cells)
        count = apply_regeneration(world, regen_rate=0.1)
        # Cell at (2,2) unchanged; other 24 cells updated
        assert count == 24


# ---------------------------------------------------------------------------
# Obstacle cells skipped
# ---------------------------------------------------------------------------


class TestObstacleSkipped:
    """Obstacle cells are never regenerated."""

    def test_obstacle_unchanged(self) -> None:
        cells = {
            (2, 2): Cell(cell_type=CellType.OBSTACLE, resource_value=0.0),
        }
        world = _make_world_with_cells(cells)
        apply_regeneration(world, regen_rate=0.1)
        cell = world.get_internal_cell(Position(x=2, y=2))
        assert cell.cell_type == CellType.OBSTACLE
        assert cell.resource_value == 0.0

    def test_obstacle_not_counted(self) -> None:
        # 3x3 grid: 1 obstacle at center, agent at (0,0)
        cells = {
            (1, 1): Cell(cell_type=CellType.OBSTACLE, resource_value=0.0),
        }
        world = _make_world_with_cells(cells, width=3, height=3)
        count = apply_regeneration(world, regen_rate=0.1)
        assert count == 8  # 9 - 1 obstacle


# ---------------------------------------------------------------------------
# Non-eligible cells skipped
# ---------------------------------------------------------------------------


class TestNonEligibleSkipped:
    """Non-regen-eligible cells are skipped even if traversable."""

    def test_ineligible_empty_unchanged(self) -> None:
        cells = {
            (2, 2): Cell(
                cell_type=CellType.EMPTY, resource_value=0.0, regen_eligible=False,
            ),
        }
        world = _make_world_with_cells(cells)
        apply_regeneration(world, regen_rate=0.1)
        cell = world.get_internal_cell(Position(x=2, y=2))
        assert cell.cell_type == CellType.EMPTY
        assert cell.resource_value == 0.0

    def test_ineligible_resource_unchanged(self) -> None:
        cells = {
            (2, 2): Cell(
                cell_type=CellType.RESOURCE, resource_value=0.5, regen_eligible=False,
            ),
        }
        world = _make_world_with_cells(cells)
        apply_regeneration(world, regen_rate=0.1)
        cell = world.get_internal_cell(Position(x=2, y=2))
        assert cell.resource_value == 0.5  # unchanged


class TestCooldownBehavior:
    """Cooldown cells do not regenerate until cooldown expires."""

    def test_cooldown_decrements_without_regrowth(self) -> None:
        cells = {
            (1, 1): Cell(
                cell_type=CellType.EMPTY,
                resource_value=0.0,
                cooldown_remaining=2,
            ),
        }
        world = _make_world_with_cells(cells, width=3, height=3)
        count = apply_regeneration(world, regen_rate=0.1)
        assert count == 9
        cell = world.get_internal_cell(Position(x=1, y=1))
        assert cell.cell_type == CellType.EMPTY
        assert cell.resource_value == 0.0
        assert cell.cooldown_remaining == 1

    def test_cooldown_zero_after_tick_still_does_not_regrow_same_tick(self) -> None:
        cells = {
            (1, 1): Cell(
                cell_type=CellType.EMPTY,
                resource_value=0.0,
                cooldown_remaining=1,
            ),
        }
        world = _make_world_with_cells(cells, width=3, height=3)
        apply_regeneration(world, regen_rate=0.1)
        cell = world.get_internal_cell(Position(x=1, y=1))
        assert cell.cell_type == CellType.EMPTY
        assert cell.resource_value == 0.0
        assert cell.cooldown_remaining == 0

    def test_regrowth_resumes_after_cooldown_expires(self) -> None:
        cells = {
            (1, 1): Cell(
                cell_type=CellType.EMPTY,
                resource_value=0.0,
                cooldown_remaining=1,
            ),
        }
        world = _make_world_with_cells(cells, width=3, height=3)
        apply_regeneration(world, regen_rate=0.1)
        apply_regeneration(world, regen_rate=0.1)
        cell = world.get_internal_cell(Position(x=1, y=1))
        assert cell.cell_type == CellType.RESOURCE
        assert cell.resource_value == 0.1


# ---------------------------------------------------------------------------
# Full grid regeneration
# ---------------------------------------------------------------------------


class TestFullGridRegeneration:
    """Multiple cells updated in one call."""

    def test_multiple_cells_updated(self) -> None:
        # 3x3 grid, all empty -> all should gain resource
        world = _make_world_with_cells({}, width=3, height=3)
        count = apply_regeneration(world, regen_rate=0.2)
        assert count == 9
        for y in range(3):
            for x in range(3):
                cell = world.get_internal_cell(Position(x=x, y=y))
                assert cell.cell_type == CellType.RESOURCE
                assert cell.resource_value == pytest.approx(0.2)

    def test_mixed_grid(self) -> None:
        """Mixed grid: obstacle, ineligible, resource, empty."""
        cells = {
            (0, 0): Cell(cell_type=CellType.OBSTACLE, resource_value=0.0),
            (1, 0): Cell(
                cell_type=CellType.EMPTY, resource_value=0.0, regen_eligible=False,
            ),
            (2, 0): Cell(cell_type=CellType.RESOURCE, resource_value=0.5),
        }
        # Agent at (1,1) to avoid obstacle at (0,0)
        world = _make_world_with_cells(
            cells, width=3, height=3, agent_pos=Position(x=1, y=1))
        count = apply_regeneration(world, regen_rate=0.1)

        # (0,0) obstacle: skipped
        # (1,0) ineligible: skipped
        # (2,0) resource 0.5 -> 0.6: counted
        # remaining 6 empty cells: all gain 0.1, counted
        assert count == 7

        # Verify specific cells
        assert world.get_internal_cell(
            Position(x=0, y=0)).cell_type == CellType.OBSTACLE
        assert world.get_internal_cell(
            Position(x=1, y=0)).resource_value == 0.0
        assert world.get_internal_cell(
            Position(x=2, y=0)).resource_value == pytest.approx(0.6)


# ---------------------------------------------------------------------------
# Import verification
# ---------------------------------------------------------------------------


class TestImports:
    """Import paths work correctly."""

    def test_import_from_dynamics_module(self) -> None:
        from axis.world.grid_2d.dynamics import apply_regeneration  # noqa: F401
