"""Tests for observation builder (sensor projection)."""

from axis_system_a import (
    AgentState,
    Cell,
    CellType,
    Observation,
    Position,
    World,
    build_observation,
)
from tests.builders.world_builder import WorldBuilder
from tests.fixtures.world_fixtures import empty_cell, obstacle_cell, resource_cell


E = CellType.EMPTY
R = CellType.RESOURCE
O = CellType.OBSTACLE


def _cell(ct: CellType, rv: float = 0.0) -> Cell:
    """Shorthand cell constructor."""
    return Cell(cell_type=ct, resource_value=rv)


class TestObservationInterior:
    """Agent at interior position — all neighbors within bounds."""

    def test_all_neighbors_observed(self, small_world: World):
        obs = build_observation(small_world, Position(x=1, y=1))
        assert obs.dimension == 10
        assert len(obs.to_vector()) == 10

    def test_center_cell_correct(self, small_world: World):
        obs = build_observation(small_world, Position(x=1, y=1))
        assert obs.current.traversability == 1.0
        assert obs.current.resource == 0.0

    def test_up_neighbor(self, small_world: World):
        obs = build_observation(small_world, Position(x=1, y=1))
        assert obs.up.traversability == 1.0
        assert obs.up.resource == 0.7

    def test_down_neighbor(self, small_world: World):
        obs = build_observation(small_world, Position(x=1, y=1))
        assert obs.down.traversability == 1.0
        assert obs.down.resource == 0.0

    def test_left_neighbor(self, small_world: World):
        obs = build_observation(small_world, Position(x=1, y=1))
        assert obs.left.traversability == 1.0
        assert obs.left.resource == 0.0

    def test_right_neighbor(self, small_world: World):
        obs = build_observation(small_world, Position(x=1, y=1))
        assert obs.right.traversability == 0.0
        assert obs.right.resource == 0.0


class TestObservationBoundary:
    """Out-of-bounds neighbors produce (0.0, 0.0)."""

    def test_top_row_up_oob(self):
        world = WorldBuilder().with_size(1, 1).with_agent_at(0, 0).build()
        obs = build_observation(world, Position(x=0, y=0))
        assert obs.up.traversability == 0.0
        assert obs.up.resource == 0.0

    def test_bottom_row_down_oob(self):
        world = WorldBuilder().with_size(1, 1).with_agent_at(0, 0).build()
        obs = build_observation(world, Position(x=0, y=0))
        assert obs.down.traversability == 0.0
        assert obs.down.resource == 0.0

    def test_left_col_left_oob(self):
        world = WorldBuilder().with_size(1, 1).with_agent_at(0, 0).build()
        obs = build_observation(world, Position(x=0, y=0))
        assert obs.left.traversability == 0.0
        assert obs.left.resource == 0.0

    def test_right_col_right_oob(self):
        world = WorldBuilder().with_size(1, 1).with_agent_at(0, 0).build()
        obs = build_observation(world, Position(x=0, y=0))
        assert obs.right.traversability == 0.0
        assert obs.right.resource == 0.0

    def test_1x1_world_all_neighbors_oob(self):
        grid = [[_cell(R, 0.5)]]
        world = World(grid=grid, agent_position=Position(x=0, y=0))
        obs = build_observation(world, Position(x=0, y=0))
        assert obs.current.traversability == 1.0
        assert obs.current.resource == 0.5
        for direction in [obs.up, obs.down, obs.left, obs.right]:
            assert direction.traversability == 0.0
            assert direction.resource == 0.0

    def test_corner_position_two_oob(self):
        world = WorldBuilder().with_agent_at(0, 0).build()
        obs = build_observation(world, Position(x=0, y=0))
        assert obs.up.traversability == 0.0
        assert obs.left.traversability == 0.0
        assert obs.down.traversability == 1.0
        assert obs.right.traversability == 1.0


class TestObservationObstacles:
    def test_obstacle_neighbor_traversability(self):
        grid = [
            [_cell(E), _cell(O)],
            [_cell(E), _cell(E)],
        ]
        world = World(grid=grid, agent_position=Position(x=0, y=0))
        obs = build_observation(world, Position(x=0, y=0))
        assert obs.right.traversability == 0.0
        assert obs.right.resource == 0.0


class TestObservationResourcePropagation:
    def test_resource_value_propagated(self):
        grid = [
            [_cell(R, 0.3), _cell(R, 0.8)],
            [_cell(E),       _cell(E)],
        ]
        world = World(grid=grid, agent_position=Position(x=0, y=0))
        obs = build_observation(world, Position(x=0, y=0))
        assert obs.current.resource == 0.3
        assert obs.right.resource == 0.8

    def test_empty_cell_observation(self):
        grid = [[_cell(E), _cell(E)], [_cell(E), _cell(E)]]
        world = World(grid=grid, agent_position=Position(x=1, y=1))
        obs = build_observation(world, Position(x=1, y=1))
        assert obs.current.traversability == 1.0
        assert obs.current.resource == 0.0


class TestObservationVectorOrdering:
    def test_to_vector_canonical_order(self):
        grid = [
            [_cell(R, 0.1), _cell(R, 0.2), _cell(R, 0.3)],
            [_cell(R, 0.4), _cell(R, 0.5), _cell(R, 0.6)],
            [_cell(R, 0.7), _cell(R, 0.8), _cell(R, 0.9)],
        ]
        world = World(grid=grid, agent_position=Position(x=1, y=1))
        obs = build_observation(world, Position(x=1, y=1))
        expected = (
            1.0, 0.5,   # center
            1.0, 0.2,   # up
            1.0, 0.8,   # down
            1.0, 0.4,   # left
            1.0, 0.6,   # right
        )
        assert obs.to_vector() == expected

    def test_dimension_property(self):
        world = WorldBuilder().with_size(1, 1).with_agent_at(0, 0).build()
        obs = build_observation(world, Position(x=0, y=0))
        assert obs.dimension == 10


class TestObservationDirectionalMapping:
    """Verify up=(x,y-1), down=(x,y+1), left=(x-1,y), right=(x+1,y)."""

    def _make_directional_world(self) -> World:
        grid = []
        for y in range(5):
            row = []
            for x in range(5):
                val = round((y * 5 + x + 1) / 25, 2)
                row.append(_cell(R, val))
            grid.append(row)
        return World(grid=grid, agent_position=Position(x=2, y=2))

    def test_up_is_y_minus_1(self):
        world = self._make_directional_world()
        obs = build_observation(world, Position(x=2, y=2))
        assert obs.up.resource == 0.32

    def test_down_is_y_plus_1(self):
        world = self._make_directional_world()
        obs = build_observation(world, Position(x=2, y=2))
        assert obs.down.resource == 0.72

    def test_left_is_x_minus_1(self):
        world = self._make_directional_world()
        obs = build_observation(world, Position(x=2, y=2))
        assert obs.left.resource == 0.48

    def test_right_is_x_plus_1(self):
        world = self._make_directional_world()
        obs = build_observation(world, Position(x=2, y=2))
        assert obs.right.resource == 0.56


class TestObservationPurity:
    def test_no_side_effects(self, small_world: World):
        pos = small_world.agent_position
        cell_before = small_world.get_cell(Position(x=1, y=0))
        build_observation(small_world, pos)
        cell_after = small_world.get_cell(Position(x=1, y=0))
        assert cell_before == cell_after
        assert small_world.agent_position == pos


class TestObservationSeparation:
    def test_no_position_in_agent_state(self):
        assert "position" not in AgentState.model_fields

    def test_observation_has_no_coordinate_fields(self):
        field_names = set(Observation.model_fields.keys())
        assert "x" not in field_names
        assert "y" not in field_names
        assert "position" not in field_names


# --- WP17: Observation purity — regen_eligible is not projected ---


class TestObservationRegenEligibilityPurity:
    """regen_eligible must not leak into the observation vector."""

    def test_identical_observation_regardless_of_eligibility(self):
        """Two cells differing only in regen_eligible produce the same obs."""
        eligible_cell = Cell(cell_type=CellType.RESOURCE,
                             resource_value=0.7, regen_eligible=True)
        ineligible_cell = Cell(cell_type=CellType.RESOURCE,
                               resource_value=0.7, regen_eligible=False)

        grid_a = [[eligible_cell]]
        grid_b = [[ineligible_cell]]

        world_a = World(grid=grid_a,
                        agent_position=Position(x=0, y=0))
        world_b = World(grid=grid_b,
                        agent_position=Position(x=0, y=0))

        obs_a = build_observation(world_a, Position(x=0, y=0))
        obs_b = build_observation(world_b, Position(x=0, y=0))

        assert obs_a == obs_b
        assert obs_a.to_vector() == obs_b.to_vector()
