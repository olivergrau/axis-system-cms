"""Tests for the transition engine."""

import inspect

import pytest
from pydantic import ValidationError

from axis_system_a import (
    Action,
    AgentState,
    Cell,
    CellType,
    MemoryState,
    Position,
    StepResult,
    TransitionTrace,
    World,
    step,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cell(kind: str = "empty", resource: float = 0.0) -> Cell:
    """Shorthand cell factory."""
    if kind == "resource":
        return Cell(cell_type=CellType.RESOURCE, resource_value=resource)
    if kind == "obstacle":
        return Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)
    return Cell(cell_type=CellType.EMPTY, resource_value=0.0)


def _make_world(
    grid: list[list[Cell]],
    agent_pos: tuple[int, int] = (1, 1),
) -> World:
    return World(grid=grid, agent_position=Position(x=agent_pos[0], y=agent_pos[1]))


def _agent(energy: float = 50.0, capacity: int = 5) -> AgentState:
    return AgentState(energy=energy, memory_state=MemoryState(capacity=capacity))


def _3x3_world() -> World:
    """Standard 3x3 world for transition tests.

    Row 0: [EMPTY,         RESOURCE(0.7), EMPTY       ]
    Row 1: [EMPTY,         EMPTY,         OBSTACLE    ]
    Row 2: [RESOURCE(0.3), EMPTY,         EMPTY       ]

    Agent at (1, 1).
    """
    grid = [
        [_cell(), _cell("resource", 0.7), _cell()],
        [_cell(), _cell(), _cell("obstacle")],
        [_cell("resource", 0.3), _cell(), _cell()],
    ]
    return _make_world(grid)


_DEFAULT_KWARGS = dict(
    move_cost=1.0,
    consume_cost=1.0,
    stay_cost=0.5,
    max_consume=1.0,
    energy_gain_factor=10.0,
    max_energy=100.0,
)


# ---------------------------------------------------------------------------
# Movement tests
# ---------------------------------------------------------------------------


class TestMovement:
    def test_move_up(self):
        world = _3x3_world()  # agent at (1,1)
        result = step(world, _agent(), Action.UP, 0, **_DEFAULT_KWARGS)
        assert world.agent_position == Position(x=1, y=0)
        assert result.trace.moved is True
        assert result.trace.position_after == Position(x=1, y=0)

    def test_move_down(self):
        world = _3x3_world()
        result = step(world, _agent(), Action.DOWN, 0, **_DEFAULT_KWARGS)
        assert world.agent_position == Position(x=1, y=2)
        assert result.trace.moved is True

    def test_move_left(self):
        world = _3x3_world()
        result = step(world, _agent(), Action.LEFT, 0, **_DEFAULT_KWARGS)
        assert world.agent_position == Position(x=0, y=1)
        assert result.trace.moved is True

    def test_move_right_blocked_by_obstacle(self):
        world = _3x3_world()  # (2,1) is OBSTACLE
        result = step(world, _agent(), Action.RIGHT, 0, **_DEFAULT_KWARGS)
        assert world.agent_position == Position(x=1, y=1)
        assert result.trace.moved is False

    def test_move_up_blocked_by_boundary(self):
        world = _3x3_world()
        # First move up to (1,0)
        step(world, _agent(), Action.UP, 0, **_DEFAULT_KWARGS)
        # Now try to move up again (out of bounds)
        result = step(world, _agent(), Action.UP, 1, **_DEFAULT_KWARGS)
        assert world.agent_position == Position(x=1, y=0)
        assert result.trace.moved is False

    def test_blocked_move_still_costs_energy(self):
        world = _3x3_world()  # RIGHT is obstacle
        agent = _agent(energy=50.0)
        result = step(world, agent, Action.RIGHT, 0, **_DEFAULT_KWARGS)
        assert result.agent_state.energy == pytest.approx(49.0)
        assert result.trace.moved is False

    def test_successful_move_costs_energy(self):
        world = _3x3_world()
        agent = _agent(energy=50.0)
        result = step(world, agent, Action.UP, 0, **_DEFAULT_KWARGS)
        assert result.agent_state.energy == pytest.approx(49.0)

    def test_movement_does_not_change_cells(self):
        world = _3x3_world()
        cell_before = world.get_cell(Position(x=1, y=0))
        step(world, _agent(), Action.UP, 0, **_DEFAULT_KWARGS)
        cell_after = world.get_cell(Position(x=1, y=0))
        assert cell_before.cell_type == cell_after.cell_type
        assert cell_before.resource_value == cell_after.resource_value


# ---------------------------------------------------------------------------
# Consume tests
# ---------------------------------------------------------------------------


class TestConsume:
    def test_consume_on_resource_cell(self):
        """Move to resource cell, then consume."""
        grid = [
            [_cell("resource", 0.5), _cell()],
            [_cell(), _cell()],
        ]
        world = _make_world(grid, agent_pos=(0, 0))
        result = step(world, _agent(), Action.CONSUME, 0, **_DEFAULT_KWARGS)
        assert result.trace.consumed is True
        assert result.trace.resource_consumed == pytest.approx(0.5)

    def test_consume_fully_depletes_cell(self):
        """Cell resource <= max_consume → cell becomes EMPTY."""
        grid = [[_cell("resource", 0.5)]]
        world = _make_world(grid, agent_pos=(0, 0))
        step(world, _agent(), Action.CONSUME, 0, **_DEFAULT_KWARGS)
        cell = world.get_cell(Position(x=0, y=0))
        assert cell.cell_type is CellType.EMPTY
        assert cell.resource_value == 0.0

    def test_consume_partial_depletion(self):
        """max_consume < cell resource → cell stays RESOURCE with reduced value."""
        grid = [[_cell("resource", 0.8)]]
        world = _make_world(grid, agent_pos=(0, 0))
        kwargs = {**_DEFAULT_KWARGS, "max_consume": 0.3}
        result = step(world, _agent(), Action.CONSUME, 0, **kwargs)
        cell = world.get_cell(Position(x=0, y=0))
        assert cell.cell_type is CellType.RESOURCE
        assert cell.resource_value == pytest.approx(0.5)
        assert result.trace.resource_consumed == pytest.approx(0.3)

    def test_consume_on_empty_cell(self):
        grid = [[_cell()]]
        world = _make_world(grid, agent_pos=(0, 0))
        result = step(world, _agent(), Action.CONSUME, 0, **_DEFAULT_KWARGS)
        assert result.trace.consumed is False
        assert result.trace.resource_consumed == 0.0

    def test_consume_on_empty_cell_still_costs_energy(self):
        grid = [[_cell()]]
        world = _make_world(grid, agent_pos=(0, 0))
        agent = _agent(energy=50.0)
        result = step(world, agent, Action.CONSUME, 0, **_DEFAULT_KWARGS)
        # consume_cost=1.0, no gain
        assert result.agent_state.energy == pytest.approx(49.0)

    def test_consume_only_affects_current_cell(self):
        grid = [
            [_cell("resource", 0.5), _cell("resource", 0.9)],
        ]
        world = _make_world(grid, agent_pos=(0, 0))
        step(world, _agent(), Action.CONSUME, 0, **_DEFAULT_KWARGS)
        neighbor = world.get_cell(Position(x=1, y=0))
        assert neighbor.resource_value == pytest.approx(0.9)

    def test_consume_energy_gain(self):
        """Energy gain = energy_gain_factor * resource_consumed."""
        grid = [[_cell("resource", 0.5)]]
        world = _make_world(grid, agent_pos=(0, 0))
        agent = _agent(energy=50.0)
        # gain = 10.0 * 0.5 = 5.0, cost = 1.0, net = +4.0
        result = step(world, agent, Action.CONSUME, 0, **_DEFAULT_KWARGS)
        assert result.agent_state.energy == pytest.approx(54.0)

    def test_trace_resource_consumed_value(self):
        grid = [[_cell("resource", 0.4)]]
        world = _make_world(grid, agent_pos=(0, 0))
        result = step(world, _agent(), Action.CONSUME, 0, **_DEFAULT_KWARGS)
        assert result.trace.resource_consumed == pytest.approx(0.4)


# ---------------------------------------------------------------------------
# Stay tests
# ---------------------------------------------------------------------------


class TestStay:
    def test_stay_position_unchanged(self):
        world = _3x3_world()
        result = step(world, _agent(), Action.STAY, 0, **_DEFAULT_KWARGS)
        assert world.agent_position == Position(x=1, y=1)
        assert result.trace.moved is False
        assert result.trace.consumed is False

    def test_stay_costs_stay_cost(self):
        world = _3x3_world()
        agent = _agent(energy=50.0)
        result = step(world, agent, Action.STAY, 0, **_DEFAULT_KWARGS)
        assert result.agent_state.energy == pytest.approx(49.5)  # 50 - 0.5

    def test_stay_does_not_change_cells(self):
        world = _3x3_world()
        cells_before = [
            (Position(x=x, y=y), world.get_cell(Position(x=x, y=y)))
            for y in range(3) for x in range(3)
            if world.get_cell(Position(x=x, y=y)).cell_type is not CellType.OBSTACLE
        ]
        step(world, _agent(), Action.STAY, 0, **_DEFAULT_KWARGS)
        for pos, cell in cells_before:
            after = world.get_cell(pos)
            assert after.resource_value == cell.resource_value


# ---------------------------------------------------------------------------
# Energy update tests
# ---------------------------------------------------------------------------


class TestEnergyUpdate:
    def test_move_costs_move_cost(self):
        world = _3x3_world()
        result = step(
            world, _agent(energy=50.0), Action.UP, 0,
            **{**_DEFAULT_KWARGS, "move_cost": 2.0},
        )
        assert result.agent_state.energy == pytest.approx(48.0)

    def test_consume_costs_consume_cost(self):
        grid = [[_cell()]]  # empty cell, no gain
        world = _make_world(grid, agent_pos=(0, 0))
        result = step(
            world, _agent(energy=50.0), Action.CONSUME, 0,
            **{**_DEFAULT_KWARGS, "consume_cost": 3.0},
        )
        assert result.agent_state.energy == pytest.approx(47.0)

    def test_stay_costs_stay_cost(self):
        world = _3x3_world()
        result = step(
            world, _agent(energy=50.0), Action.STAY, 0,
            **{**_DEFAULT_KWARGS, "stay_cost": 2.5},
        )
        assert result.agent_state.energy == pytest.approx(47.5)

    def test_energy_gain_from_consume(self):
        """gain = energy_gain_factor * delta_R."""
        grid = [[_cell("resource", 0.6)]]
        world = _make_world(grid, agent_pos=(0, 0))
        result = step(
            world, _agent(energy=50.0), Action.CONSUME, 0,
            **{**_DEFAULT_KWARGS, "energy_gain_factor": 5.0},
        )
        # cost=1.0, gain=5.0*0.6=3.0, net=50-1+3=52
        assert result.agent_state.energy == pytest.approx(52.0)

    def test_no_gain_from_movement(self):
        world = _3x3_world()
        # Move UP to (1,0) which is RESOURCE(0.7), but movement doesn't consume
        result = step(world, _agent(energy=50.0),
                      Action.UP, 0, **_DEFAULT_KWARGS)
        assert result.agent_state.energy == pytest.approx(49.0)  # just cost

    def test_energy_clipped_to_max(self):
        grid = [[_cell("resource", 1.0)]]
        world = _make_world(grid, agent_pos=(0, 0))
        # start at 95, gain=10*1.0=10, cost=1, raw=104 → clipped to 100
        result = step(
            world, _agent(energy=95.0), Action.CONSUME, 0, **_DEFAULT_KWARGS,
        )
        assert result.agent_state.energy == pytest.approx(100.0)

    def test_energy_clipped_to_zero(self):
        world = _3x3_world()
        result = step(
            world, _agent(energy=0.5), Action.UP, 0, **_DEFAULT_KWARGS,
        )
        # 0.5 - 1.0 = -0.5 → clipped to 0
        assert result.agent_state.energy == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Memory update tests
# ---------------------------------------------------------------------------


class TestMemoryUpdate:
    def test_memory_updated_with_new_observation(self):
        """Memory records the post-transition observation, not the pre-transition one."""
        grid = [[_cell("resource", 0.5)]]
        world = _make_world(grid, agent_pos=(0, 0))
        agent = _agent(energy=50.0)
        result = step(world, agent, Action.CONSUME, 0, **_DEFAULT_KWARGS)
        # After consume, cell is depleted → observation.current.resource == 0.0
        mem_obs = result.agent_state.memory_state.entries[-1].observation
        assert mem_obs.current.resource == pytest.approx(0.0)

    def test_memory_entry_has_correct_timestep(self):
        world = _3x3_world()
        result = step(world, _agent(), Action.STAY, 42, **_DEFAULT_KWARGS)
        assert result.agent_state.memory_state.entries[-1].timestep == 42

    def test_memory_capacity_respected(self):
        world = _3x3_world()
        agent = _agent(energy=100.0, capacity=2)
        # Fill memory with 2 steps, then a 3rd should drop oldest
        r1 = step(world, agent, Action.STAY, 0, **_DEFAULT_KWARGS)
        r2 = step(world, r1.agent_state, Action.STAY, 1, **_DEFAULT_KWARGS)
        r3 = step(world, r2.agent_state, Action.STAY, 2, **_DEFAULT_KWARGS)
        mem = r3.agent_state.memory_state
        assert len(mem.entries) == 2
        assert mem.entries[0].timestep == 1
        assert mem.entries[1].timestep == 2

    def test_trace_memory_counts(self):
        world = _3x3_world()
        agent = _agent()
        result = step(world, agent, Action.STAY, 0, **_DEFAULT_KWARGS)
        assert result.trace.memory_entries_before == 0
        assert result.trace.memory_entries_after == 1


# ---------------------------------------------------------------------------
# Termination tests
# ---------------------------------------------------------------------------


class TestTermination:
    def test_energy_above_zero_not_terminated(self):
        world = _3x3_world()
        result = step(world, _agent(energy=50.0),
                      Action.STAY, 0, **_DEFAULT_KWARGS)
        assert result.terminated is False

    def test_energy_depleted_to_zero(self):
        world = _3x3_world()
        # stay_cost=0.5, start at 0.5 → 0.0
        result = step(world, _agent(energy=0.5),
                      Action.STAY, 0, **_DEFAULT_KWARGS)
        assert result.terminated is True
        assert result.agent_state.energy == pytest.approx(0.0)

    def test_cost_exceeds_energy(self):
        world = _3x3_world()
        # move_cost=1.0, start at 0.3 → clipped to 0
        result = step(world, _agent(energy=0.3),
                      Action.UP, 0, **_DEFAULT_KWARGS)
        assert result.terminated is True
        assert result.agent_state.energy == pytest.approx(0.0)

    def test_step_result_terminated_matches_trace(self):
        world = _3x3_world()
        result = step(world, _agent(energy=0.5),
                      Action.STAY, 0, **_DEFAULT_KWARGS)
        assert result.terminated == result.trace.terminated


# ---------------------------------------------------------------------------
# Transition trace tests
# ---------------------------------------------------------------------------


class TestTransitionTrace:
    def test_has_required_fields(self):
        assert set(TransitionTrace.model_fields.keys()) == {
            "action",
            "position_before",
            "position_after",
            "moved",
            "consumed",
            "resource_consumed",
            "energy_before",
            "energy_after",
            "energy_delta",
            "memory_entries_before",
            "memory_entries_after",
            "terminated",
        }

    def test_trace_is_frozen(self):
        world = _3x3_world()
        result = step(world, _agent(), Action.STAY, 0, **_DEFAULT_KWARGS)
        with pytest.raises(ValidationError):
            result.trace.moved = True

    def test_action_matches_input(self):
        world = _3x3_world()
        result = step(world, _agent(), Action.LEFT, 0, **_DEFAULT_KWARGS)
        assert result.trace.action is Action.LEFT

    def test_energy_delta_consistent(self):
        world = _3x3_world()
        result = step(world, _agent(energy=50.0),
                      Action.UP, 0, **_DEFAULT_KWARGS)
        assert result.trace.energy_delta == pytest.approx(
            result.trace.energy_after - result.trace.energy_before,
        )

    def test_position_before_matches_input(self):
        world = _3x3_world()  # agent at (1,1)
        result = step(world, _agent(), Action.UP, 0, **_DEFAULT_KWARGS)
        assert result.trace.position_before == Position(x=1, y=1)
        assert result.trace.position_after == Position(x=1, y=0)


# ---------------------------------------------------------------------------
# StepResult structure tests
# ---------------------------------------------------------------------------


class TestStepResult:
    def test_has_required_fields(self):
        assert set(StepResult.model_fields.keys()) == {
            "agent_state",
            "observation",
            "terminated",
            "trace",
        }

    def test_step_result_is_frozen(self):
        world = _3x3_world()
        result = step(world, _agent(), Action.STAY, 0, **_DEFAULT_KWARGS)
        with pytest.raises(ValidationError):
            result.terminated = True

    def test_agent_state_is_new_instance(self):
        world = _3x3_world()
        agent = _agent()
        result = step(world, agent, Action.STAY, 0, **_DEFAULT_KWARGS)
        assert result.agent_state is not agent


# ---------------------------------------------------------------------------
# Determinism tests
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_same_inputs_same_outputs(self):
        world1 = _3x3_world()
        world2 = _3x3_world()
        agent = _agent(energy=50.0)
        r1 = step(world1, agent, Action.UP, 0, **_DEFAULT_KWARGS)
        r2 = step(world2, agent, Action.UP, 0, **_DEFAULT_KWARGS)
        assert r1.agent_state.energy == r2.agent_state.energy
        assert r1.trace.moved == r2.trace.moved
        assert r1.terminated == r2.terminated
        assert world1.agent_position == world2.agent_position

    def test_repeated_setup_identical_results(self):
        """Two independent runs with fresh identical state produce same output."""
        for _ in range(3):
            world = _3x3_world()
            agent = _agent(energy=30.0)
            result = step(world, agent, Action.DOWN, 5, **_DEFAULT_KWARGS)
            assert result.agent_state.energy == pytest.approx(29.0)
            assert world.agent_position == Position(x=1, y=2)


# ---------------------------------------------------------------------------
# Phase ordering tests
# ---------------------------------------------------------------------------


class TestPhaseOrdering:
    def test_observation_reflects_post_action_world(self):
        """After consuming, observation shows depleted cell."""
        grid = [[_cell("resource", 0.5)]]
        world = _make_world(grid, agent_pos=(0, 0))
        result = step(world, _agent(), Action.CONSUME, 0, **_DEFAULT_KWARGS)
        # Observation built AFTER consume → current cell has resource=0.0
        assert result.observation.current.resource == pytest.approx(0.0)

    def test_memory_contains_post_action_observation(self):
        """Memory records the post-action observation, not pre-action."""
        grid = [[_cell("resource", 0.5)]]
        world = _make_world(grid, agent_pos=(0, 0))
        result = step(world, _agent(), Action.CONSUME, 0, **_DEFAULT_KWARGS)
        mem_entry = result.agent_state.memory_state.entries[-1]
        assert mem_entry.observation == result.observation

    def test_observation_reflects_post_movement(self):
        """After moving, observation is from the new position."""
        world = _3x3_world()  # (1,0) is RESOURCE(0.7)
        result = step(world, _agent(), Action.UP, 0, **_DEFAULT_KWARGS)
        # Now at (1,0), current cell is RESOURCE(0.7)
        assert result.observation.current.resource == pytest.approx(0.7)

    def test_world_unchanged_before_action(self):
        """Phase 1 (world regen) is a no-op."""
        world = _3x3_world()
        resource_cell = world.get_cell(Position(x=1, y=0))
        assert resource_cell.resource_value == pytest.approx(0.7)
        step(world, _agent(), Action.STAY, 0, **_DEFAULT_KWARGS)
        resource_cell_after = world.get_cell(Position(x=1, y=0))
        assert resource_cell_after.resource_value == pytest.approx(0.7)


# ---------------------------------------------------------------------------
# Separation / architecture tests
# ---------------------------------------------------------------------------


class TestSeparation:
    def test_transition_does_not_import_drives(self):
        import axis_system_a.transition as t_mod

        source = inspect.getsource(t_mod)
        assert "from axis_system_a.drives" not in source
        assert "import drives" not in source

    def test_transition_does_not_import_policy(self):
        import axis_system_a.transition as t_mod

        source = inspect.getsource(t_mod)
        assert "from axis_system_a.policy" not in source
        assert "import policy" not in source

    def test_step_signature_has_no_policy_params(self):
        sig = inspect.signature(step)
        for name in ["selection_mode", "temperature", "rng", "contributions"]:
            assert name not in sig.parameters


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_1x1_world_all_movement_blocked(self):
        grid = [[_cell()]]
        world = _make_world(grid, agent_pos=(0, 0))
        for action in [Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT]:
            w = _make_world([[_cell()]], agent_pos=(0, 0))
            result = step(w, _agent(), action, 0, **_DEFAULT_KWARGS)
            assert result.trace.moved is False
            assert w.agent_position == Position(x=0, y=0)

    def test_max_consume_zero(self):
        grid = [[_cell("resource", 0.5)]]
        world = _make_world(grid, agent_pos=(0, 0))
        kwargs = {**_DEFAULT_KWARGS, "max_consume": 0.0}
        result = step(world, _agent(), Action.CONSUME, 0, **kwargs)
        assert result.trace.consumed is False
        assert result.trace.resource_consumed == 0.0
        # Cell unchanged
        assert world.get_cell(
            Position(x=0, y=0)).resource_value == pytest.approx(0.5)

    def test_energy_exactly_equals_cost(self):
        world = _3x3_world()
        # move_cost=1.0, energy=1.0 → 0.0 → terminated
        result = step(world, _agent(energy=1.0),
                      Action.UP, 0, **_DEFAULT_KWARGS)
        assert result.agent_state.energy == pytest.approx(0.0)
        assert result.terminated is True

    def test_energy_gain_factor_zero(self):
        grid = [[_cell("resource", 0.8)]]
        world = _make_world(grid, agent_pos=(0, 0))
        kwargs = {**_DEFAULT_KWARGS, "energy_gain_factor": 0.0}
        result = step(world, _agent(energy=50.0), Action.CONSUME, 0, **kwargs)
        # No gain, just cost: 50 - 1 = 49
        assert result.agent_state.energy == pytest.approx(49.0)
