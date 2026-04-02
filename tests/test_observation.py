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


def _make_world(grid: list[list[Cell]], agent_pos: Position) -> World:
    """Helper to build a World from a cell grid."""
    return World(grid=grid, agent_position=agent_pos)


def _cell(ct: CellType, rv: float = 0.0) -> Cell:
    """Shorthand cell constructor."""
    return Cell(cell_type=ct, resource_value=rv)


E = CellType.EMPTY
R = CellType.RESOURCE
O = CellType.OBSTACLE


class TestObservationInterior:
    """Agent at interior position — all neighbors within bounds."""

    def test_all_neighbors_observed(self, small_world: World):
        obs = build_observation(small_world, Position(x=1, y=1))
        assert obs.dimension == 10
        assert len(obs.to_vector()) == 10

    def test_center_cell_correct(self, small_world: World):
        # (1,1) = EMPTY
        obs = build_observation(small_world, Position(x=1, y=1))
        assert obs.current.traversability == 1.0
        assert obs.current.resource == 0.0

    def test_up_neighbor(self, small_world: World):
        # up of (1,1) is (1,0) = RESOURCE(0.7)
        obs = build_observation(small_world, Position(x=1, y=1))
        assert obs.up.traversability == 1.0
        assert obs.up.resource == 0.7

    def test_down_neighbor(self, small_world: World):
        # down of (1,1) is (1,2) = EMPTY
        obs = build_observation(small_world, Position(x=1, y=1))
        assert obs.down.traversability == 1.0
        assert obs.down.resource == 0.0

    def test_left_neighbor(self, small_world: World):
        # left of (1,1) is (0,1) = EMPTY
        obs = build_observation(small_world, Position(x=1, y=1))
        assert obs.left.traversability == 1.0
        assert obs.left.resource == 0.0

    def test_right_neighbor(self, small_world: World):
        # right of (1,1) is (2,1) = OBSTACLE
        obs = build_observation(small_world, Position(x=1, y=1))
        assert obs.right.traversability == 0.0
        assert obs.right.resource == 0.0


class TestObservationBoundary:
    """Out-of-bounds neighbors produce (0.0, 0.0)."""

    def test_top_row_up_oob(self):
        """Agent at (0,0), up = (0,-1) is OOB."""
        grid = [[_cell(E)]]
        world = _make_world(grid, Position(x=0, y=0))
        obs = build_observation(world, Position(x=0, y=0))
        assert obs.up.traversability == 0.0
        assert obs.up.resource == 0.0

    def test_bottom_row_down_oob(self):
        """Agent at (0,0) in 1x1, down = (0,1) is OOB."""
        grid = [[_cell(E)]]
        world = _make_world(grid, Position(x=0, y=0))
        obs = build_observation(world, Position(x=0, y=0))
        assert obs.down.traversability == 0.0
        assert obs.down.resource == 0.0

    def test_left_col_left_oob(self):
        """Agent at (0,0), left = (-1,0) is OOB."""
        grid = [[_cell(E)]]
        world = _make_world(grid, Position(x=0, y=0))
        obs = build_observation(world, Position(x=0, y=0))
        assert obs.left.traversability == 0.0
        assert obs.left.resource == 0.0

    def test_right_col_right_oob(self):
        """Agent at (0,0) in 1x1, right = (1,0) is OOB."""
        grid = [[_cell(E)]]
        world = _make_world(grid, Position(x=0, y=0))
        obs = build_observation(world, Position(x=0, y=0))
        assert obs.right.traversability == 0.0
        assert obs.right.resource == 0.0

    def test_1x1_world_all_neighbors_oob(self):
        """In a 1x1 world all four neighbors are OOB."""
        grid = [[_cell(R, 0.5)]]
        world = _make_world(grid, Position(x=0, y=0))
        obs = build_observation(world, Position(x=0, y=0))
        # Center is the resource cell
        assert obs.current.traversability == 1.0
        assert obs.current.resource == 0.5
        # All four neighbors OOB
        for direction in [obs.up, obs.down, obs.left, obs.right]:
            assert direction.traversability == 0.0
            assert direction.resource == 0.0

    def test_corner_position_two_oob(self):
        """Agent at (0,0) in 3x3: up and left are OOB."""
        grid = [
            [_cell(E), _cell(E), _cell(E)],
            [_cell(E), _cell(E), _cell(E)],
            [_cell(E), _cell(E), _cell(E)],
        ]
        world = _make_world(grid, Position(x=0, y=0))
        obs = build_observation(world, Position(x=0, y=0))
        assert obs.up.traversability == 0.0
        assert obs.left.traversability == 0.0
        # down and right are in bounds
        assert obs.down.traversability == 1.0
        assert obs.right.traversability == 1.0


class TestObservationObstacles:
    def test_obstacle_neighbor_traversability(self):
        """Obstacle cell produces traversability=0.0."""
        grid = [
            [_cell(E), _cell(O)],
            [_cell(E), _cell(E)],
        ]
        world = _make_world(grid, Position(x=0, y=0))
        obs = build_observation(world, Position(x=0, y=0))
        # right of (0,0) is (1,0) = OBSTACLE
        assert obs.right.traversability == 0.0
        assert obs.right.resource == 0.0


class TestObservationResourcePropagation:
    def test_resource_value_propagated(self):
        """Resource value from cell appears in observation."""
        grid = [
            [_cell(R, 0.3), _cell(R, 0.8)],
            [_cell(E),       _cell(E)],
        ]
        world = _make_world(grid, Position(x=0, y=0))
        obs = build_observation(world, Position(x=0, y=0))
        assert obs.current.resource == 0.3
        assert obs.right.resource == 0.8

    def test_empty_cell_observation(self):
        """EMPTY cell: traversability=1.0, resource=0.0."""
        grid = [[_cell(E), _cell(E)], [_cell(E), _cell(E)]]
        world = _make_world(grid, Position(x=1, y=1))
        obs = build_observation(world, Position(x=1, y=1))
        assert obs.current.traversability == 1.0
        assert obs.current.resource == 0.0


class TestObservationVectorOrdering:
    def test_to_vector_canonical_order(self):
        """Verify (b_c, r_c, b_up, r_up, b_down, r_down, b_left, r_left, b_right, r_right)."""
        grid = [
            [_cell(R, 0.1), _cell(R, 0.2), _cell(R, 0.3)],
            [_cell(R, 0.4), _cell(R, 0.5), _cell(R, 0.6)],
            [_cell(R, 0.7), _cell(R, 0.8), _cell(R, 0.9)],
        ]
        world = _make_world(grid, Position(x=1, y=1))
        obs = build_observation(world, Position(x=1, y=1))

        # center=(1,1)=0.5, up=(1,0)=0.2, down=(1,2)=0.8, left=(0,1)=0.4, right=(2,1)=0.6
        expected = (
            1.0, 0.5,   # center
            1.0, 0.2,   # up
            1.0, 0.8,   # down
            1.0, 0.4,   # left
            1.0, 0.6,   # right
        )
        assert obs.to_vector() == expected

    def test_dimension_property(self):
        grid = [[_cell(E)]]
        world = _make_world(grid, Position(x=0, y=0))
        obs = build_observation(world, Position(x=0, y=0))
        assert obs.dimension == 10


class TestObservationDirectionalMapping:
    """Verify up=(x,y-1), down=(x,y+1), left=(x-1,y), right=(x+1,y)."""

    def _make_directional_world(self) -> World:
        """5x5 world with unique resource values to identify cells."""
        grid = []
        for y in range(5):
            row = []
            for x in range(5):
                val = round((y * 5 + x + 1) / 25, 2)
                row.append(_cell(R, val))
            grid.append(row)
        return _make_world(grid, Position(x=2, y=2))

    def test_up_is_y_minus_1(self):
        world = self._make_directional_world()
        obs = build_observation(world, Position(x=2, y=2))
        # up = (2, 1), value = (1*5 + 2 + 1)/25 = 8/25 = 0.32
        assert obs.up.resource == 0.32

    def test_down_is_y_plus_1(self):
        world = self._make_directional_world()
        obs = build_observation(world, Position(x=2, y=2))
        # down = (2, 3), value = (3*5 + 2 + 1)/25 = 18/25 = 0.72
        assert obs.down.resource == 0.72

    def test_left_is_x_minus_1(self):
        world = self._make_directional_world()
        obs = build_observation(world, Position(x=2, y=2))
        # left = (1, 2), value = (2*5 + 1 + 1)/25 = 12/25 = 0.48
        assert obs.left.resource == 0.48

    def test_right_is_x_plus_1(self):
        world = self._make_directional_world()
        obs = build_observation(world, Position(x=2, y=2))
        # right = (3, 2), value = (2*5 + 3 + 1)/25 = 14/25 = 0.56
        assert obs.right.resource == 0.56


class TestObservationPurity:
    def test_no_side_effects(self, small_world: World):
        """World state unchanged after building observation."""
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
