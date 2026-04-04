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
    TransitionStepResult,
    TransitionTrace,
    World,
    step,
)
from tests.builders.agent_state_builder import AgentStateBuilder
from tests.builders.world_builder import WorldBuilder
from tests.fixtures.scenario_fixtures import _DEFAULT_STEP_KWARGS
from tests.fixtures.world_fixtures import empty_cell, obstacle_cell, resource_cell


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
    return AgentStateBuilder().with_energy(energy).with_memory_capacity(capacity).build()


def _3x3_world() -> World:
    """Standard 3x3 world for transition tests.

    Row 0: [EMPTY,         RESOURCE(0.7), EMPTY       ]
    Row 1: [EMPTY,         EMPTY,         OBSTACLE    ]
    Row 2: [RESOURCE(0.3), EMPTY,         EMPTY       ]

    Agent at (1, 1).
    """
    return (
        WorldBuilder()
        .with_food(1, 0, 0.7)
        .with_obstacle(2, 1)
        .with_food(0, 2, 0.3)
        .build()
    )


# ---------------------------------------------------------------------------
# Movement tests
# ---------------------------------------------------------------------------


class TestMovement:
    def test_move_up(self):
        world = _3x3_world()
        result = step(world, _agent(), Action.UP, 0, **_DEFAULT_STEP_KWARGS)
        assert world.agent_position == Position(x=1, y=0)
        assert result.trace.moved is True
        assert result.trace.position_after == Position(x=1, y=0)

    def test_move_down(self):
        world = _3x3_world()
        result = step(world, _agent(), Action.DOWN, 0, **_DEFAULT_STEP_KWARGS)
        assert world.agent_position == Position(x=1, y=2)
        assert result.trace.moved is True

    def test_move_left(self):
        world = _3x3_world()
        result = step(world, _agent(), Action.LEFT, 0, **_DEFAULT_STEP_KWARGS)
        assert world.agent_position == Position(x=0, y=1)
        assert result.trace.moved is True

    def test_move_right_blocked_by_obstacle(self):
        world = _3x3_world()
        result = step(world, _agent(), Action.RIGHT, 0, **_DEFAULT_STEP_KWARGS)
        assert world.agent_position == Position(x=1, y=1)
        assert result.trace.moved is False

    def test_move_up_blocked_by_boundary(self):
        world = _3x3_world()
        step(world, _agent(), Action.UP, 0, **_DEFAULT_STEP_KWARGS)
        result = step(world, _agent(), Action.UP, 1, **_DEFAULT_STEP_KWARGS)
        assert world.agent_position == Position(x=1, y=0)
        assert result.trace.moved is False

    def test_blocked_move_still_costs_energy(self):
        world = _3x3_world()
        agent = _agent(energy=50.0)
        result = step(world, agent, Action.RIGHT, 0, **_DEFAULT_STEP_KWARGS)
        assert result.agent_state.energy == pytest.approx(49.0)
        assert result.trace.moved is False

    def test_successful_move_costs_energy(self):
        world = _3x3_world()
        agent = _agent(energy=50.0)
        result = step(world, agent, Action.UP, 0, **_DEFAULT_STEP_KWARGS)
        assert result.agent_state.energy == pytest.approx(49.0)

    def test_movement_does_not_change_cells(self):
        world = _3x3_world()
        cell_before = world.get_cell(Position(x=1, y=0))
        step(world, _agent(), Action.UP, 0, **_DEFAULT_STEP_KWARGS)
        cell_after = world.get_cell(Position(x=1, y=0))
        assert cell_before.cell_type == cell_after.cell_type
        assert cell_before.resource_value == cell_after.resource_value


# ---------------------------------------------------------------------------
# Consume tests
# ---------------------------------------------------------------------------


class TestConsume:
    def test_consume_on_resource_cell(self):
        grid = [
            [_cell("resource", 0.5), _cell()],
            [_cell(), _cell()],
        ]
        world = _make_world(grid, agent_pos=(0, 0))
        result = step(world, _agent(), Action.CONSUME,
                      0, **_DEFAULT_STEP_KWARGS)
        assert result.trace.consumed is True
        assert result.trace.resource_consumed == pytest.approx(0.5)

    def test_consume_fully_depletes_cell(self):
        grid = [[_cell("resource", 0.5)]]
        world = _make_world(grid, agent_pos=(0, 0))
        step(world, _agent(), Action.CONSUME, 0, **_DEFAULT_STEP_KWARGS)
        cell = world.get_cell(Position(x=0, y=0))
        assert cell.cell_type is CellType.EMPTY
        assert cell.resource_value == 0.0

    def test_consume_partial_depletion(self):
        grid = [[_cell("resource", 0.8)]]
        world = _make_world(grid, agent_pos=(0, 0))
        kwargs = {**_DEFAULT_STEP_KWARGS, "max_consume": 0.3}
        result = step(world, _agent(), Action.CONSUME, 0, **kwargs)
        cell = world.get_cell(Position(x=0, y=0))
        assert cell.cell_type is CellType.RESOURCE
        assert cell.resource_value == pytest.approx(0.5)
        assert result.trace.resource_consumed == pytest.approx(0.3)

    def test_consume_on_empty_cell(self):
        grid = [[_cell()]]
        world = _make_world(grid, agent_pos=(0, 0))
        result = step(world, _agent(), Action.CONSUME,
                      0, **_DEFAULT_STEP_KWARGS)
        assert result.trace.consumed is False
        assert result.trace.resource_consumed == 0.0

    def test_consume_on_empty_cell_still_costs_energy(self):
        grid = [[_cell()]]
        world = _make_world(grid, agent_pos=(0, 0))
        agent = _agent(energy=50.0)
        result = step(world, agent, Action.CONSUME, 0, **_DEFAULT_STEP_KWARGS)
        assert result.agent_state.energy == pytest.approx(49.0)

    def test_consume_only_affects_current_cell(self):
        grid = [
            [_cell("resource", 0.5), _cell("resource", 0.9)],
        ]
        world = _make_world(grid, agent_pos=(0, 0))
        step(world, _agent(), Action.CONSUME, 0, **_DEFAULT_STEP_KWARGS)
        neighbor = world.get_cell(Position(x=1, y=0))
        assert neighbor.resource_value == pytest.approx(0.9)

    def test_consume_energy_gain(self):
        grid = [[_cell("resource", 0.5)]]
        world = _make_world(grid, agent_pos=(0, 0))
        agent = _agent(energy=50.0)
        result = step(world, agent, Action.CONSUME, 0, **_DEFAULT_STEP_KWARGS)
        assert result.agent_state.energy == pytest.approx(54.0)

    def test_trace_resource_consumed_value(self):
        grid = [[_cell("resource", 0.4)]]
        world = _make_world(grid, agent_pos=(0, 0))
        result = step(world, _agent(), Action.CONSUME,
                      0, **_DEFAULT_STEP_KWARGS)
        assert result.trace.resource_consumed == pytest.approx(0.4)


# ---------------------------------------------------------------------------
# Stay tests
# ---------------------------------------------------------------------------


class TestStay:
    def test_stay_position_unchanged(self):
        world = _3x3_world()
        result = step(world, _agent(), Action.STAY, 0, **_DEFAULT_STEP_KWARGS)
        assert world.agent_position == Position(x=1, y=1)
        assert result.trace.moved is False
        assert result.trace.consumed is False

    def test_stay_costs_stay_cost(self):
        world = _3x3_world()
        agent = _agent(energy=50.0)
        result = step(world, agent, Action.STAY, 0, **_DEFAULT_STEP_KWARGS)
        assert result.agent_state.energy == pytest.approx(49.5)

    def test_stay_does_not_change_cells(self):
        world = _3x3_world()
        cells_before = [
            (Position(x=x, y=y), world.get_cell(Position(x=x, y=y)))
            for y in range(3) for x in range(3)
            if world.get_cell(Position(x=x, y=y)).cell_type is not CellType.OBSTACLE
        ]
        step(world, _agent(), Action.STAY, 0, **_DEFAULT_STEP_KWARGS)
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
            **{**_DEFAULT_STEP_KWARGS, "move_cost": 2.0},
        )
        assert result.agent_state.energy == pytest.approx(48.0)

    def test_consume_costs_consume_cost(self):
        grid = [[_cell()]]
        world = _make_world(grid, agent_pos=(0, 0))
        result = step(
            world, _agent(energy=50.0), Action.CONSUME, 0,
            **{**_DEFAULT_STEP_KWARGS, "consume_cost": 3.0},
        )
        assert result.agent_state.energy == pytest.approx(47.0)

    def test_stay_costs_stay_cost(self):
        world = _3x3_world()
        result = step(
            world, _agent(energy=50.0), Action.STAY, 0,
            **{**_DEFAULT_STEP_KWARGS, "stay_cost": 2.5},
        )
        assert result.agent_state.energy == pytest.approx(47.5)

    def test_energy_gain_from_consume(self):
        grid = [[_cell("resource", 0.6)]]
        world = _make_world(grid, agent_pos=(0, 0))
        result = step(
            world, _agent(energy=50.0), Action.CONSUME, 0,
            **{**_DEFAULT_STEP_KWARGS, "energy_gain_factor": 5.0},
        )
        assert result.agent_state.energy == pytest.approx(52.0)

    def test_no_gain_from_movement(self):
        world = _3x3_world()
        result = step(world, _agent(energy=50.0),
                      Action.UP, 0, **_DEFAULT_STEP_KWARGS)
        assert result.agent_state.energy == pytest.approx(49.0)

    def test_energy_clipped_to_max(self):
        grid = [[_cell("resource", 1.0)]]
        world = _make_world(grid, agent_pos=(0, 0))
        result = step(
            world, _agent(energy=95.0), Action.CONSUME, 0, **_DEFAULT_STEP_KWARGS,
        )
        assert result.agent_state.energy == pytest.approx(100.0)

    def test_energy_clipped_to_zero(self):
        world = _3x3_world()
        result = step(
            world, _agent(energy=0.5), Action.UP, 0, **_DEFAULT_STEP_KWARGS,
        )
        assert result.agent_state.energy == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Memory update tests
# ---------------------------------------------------------------------------


class TestMemoryUpdate:
    def test_memory_updated_with_new_observation(self):
        grid = [[_cell("resource", 0.5)]]
        world = _make_world(grid, agent_pos=(0, 0))
        agent = _agent(energy=50.0)
        result = step(world, agent, Action.CONSUME, 0, **_DEFAULT_STEP_KWARGS)
        mem_obs = result.agent_state.memory_state.entries[-1].observation
        assert mem_obs.current.resource == pytest.approx(0.0)

    def test_memory_entry_has_correct_timestep(self):
        world = _3x3_world()
        result = step(world, _agent(), Action.STAY, 42, **_DEFAULT_STEP_KWARGS)
        assert result.agent_state.memory_state.entries[-1].timestep == 42

    def test_memory_capacity_respected(self):
        world = _3x3_world()
        agent = _agent(energy=100.0, capacity=2)
        r1 = step(world, agent, Action.STAY, 0, **_DEFAULT_STEP_KWARGS)
        r2 = step(world, r1.agent_state, Action.STAY,
                  1, **_DEFAULT_STEP_KWARGS)
        r3 = step(world, r2.agent_state, Action.STAY,
                  2, **_DEFAULT_STEP_KWARGS)
        mem = r3.agent_state.memory_state
        assert len(mem.entries) == 2
        assert mem.entries[0].timestep == 1
        assert mem.entries[1].timestep == 2

    def test_trace_memory_counts(self):
        world = _3x3_world()
        agent = _agent()
        result = step(world, agent, Action.STAY, 0, **_DEFAULT_STEP_KWARGS)
        assert result.trace.memory_entries_before == 0
        assert result.trace.memory_entries_after == 1


# ---------------------------------------------------------------------------
# Termination tests
# ---------------------------------------------------------------------------


class TestTermination:
    def test_energy_above_zero_not_terminated(self):
        world = _3x3_world()
        result = step(world, _agent(energy=50.0),
                      Action.STAY, 0, **_DEFAULT_STEP_KWARGS)
        assert result.terminated is False

    def test_energy_depleted_to_zero(self):
        world = _3x3_world()
        result = step(world, _agent(energy=0.5),
                      Action.STAY, 0, **_DEFAULT_STEP_KWARGS)
        assert result.terminated is True
        assert result.agent_state.energy == pytest.approx(0.0)

    def test_cost_exceeds_energy(self):
        world = _3x3_world()
        result = step(world, _agent(energy=0.3),
                      Action.UP, 0, **_DEFAULT_STEP_KWARGS)
        assert result.terminated is True
        assert result.agent_state.energy == pytest.approx(0.0)

    def test_step_result_terminated_matches_trace(self):
        world = _3x3_world()
        result = step(world, _agent(energy=0.5),
                      Action.STAY, 0, **_DEFAULT_STEP_KWARGS)
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
            "world_before",
            "world_after_regen",
            "world_after_action",
            "agent_snapshot_before",
            "agent_snapshot_after",
            "memory_state_before",
            "memory_state_after",
            "observation_before",
            "observation_after",
            "regen_summary",
            "termination_reason",
        }

    def test_trace_is_frozen(self):
        world = _3x3_world()
        result = step(world, _agent(), Action.STAY, 0, **_DEFAULT_STEP_KWARGS)
        with pytest.raises(ValidationError):
            result.trace.moved = True

    def test_action_matches_input(self):
        world = _3x3_world()
        result = step(world, _agent(), Action.LEFT, 0, **_DEFAULT_STEP_KWARGS)
        assert result.trace.action is Action.LEFT

    def test_energy_delta_consistent(self):
        world = _3x3_world()
        result = step(world, _agent(energy=50.0),
                      Action.UP, 0, **_DEFAULT_STEP_KWARGS)
        assert result.trace.energy_delta == pytest.approx(
            result.trace.energy_after - result.trace.energy_before,
        )

    def test_position_before_matches_input(self):
        world = _3x3_world()
        result = step(world, _agent(), Action.UP, 0, **_DEFAULT_STEP_KWARGS)
        assert result.trace.position_before == Position(x=1, y=1)
        assert result.trace.position_after == Position(x=1, y=0)


# ---------------------------------------------------------------------------
# StepResult structure tests
# ---------------------------------------------------------------------------


class TestTransitionStepResult:
    def test_has_required_fields(self):
        assert set(TransitionStepResult.model_fields.keys()) == {
            "agent_state",
            "observation",
            "terminated",
            "trace",
        }

    def test_step_result_is_frozen(self):
        world = _3x3_world()
        result = step(world, _agent(), Action.STAY, 0, **_DEFAULT_STEP_KWARGS)
        with pytest.raises(ValidationError):
            result.terminated = True

    def test_agent_state_is_new_instance(self):
        world = _3x3_world()
        agent = _agent()
        result = step(world, agent, Action.STAY, 0, **_DEFAULT_STEP_KWARGS)
        assert result.agent_state is not agent


# ---------------------------------------------------------------------------
# Determinism tests
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_same_inputs_same_outputs(self):
        world1 = _3x3_world()
        world2 = _3x3_world()
        agent = _agent(energy=50.0)
        r1 = step(world1, agent, Action.UP, 0, **_DEFAULT_STEP_KWARGS)
        r2 = step(world2, agent, Action.UP, 0, **_DEFAULT_STEP_KWARGS)
        assert r1.agent_state.energy == r2.agent_state.energy
        assert r1.trace.moved == r2.trace.moved
        assert r1.terminated == r2.terminated
        assert world1.agent_position == world2.agent_position

    def test_repeated_setup_identical_results(self):
        for _ in range(3):
            world = _3x3_world()
            agent = _agent(energy=30.0)
            result = step(world, agent, Action.DOWN, 5, **_DEFAULT_STEP_KWARGS)
            assert result.agent_state.energy == pytest.approx(29.0)
            assert world.agent_position == Position(x=1, y=2)


# ---------------------------------------------------------------------------
# Phase ordering tests
# ---------------------------------------------------------------------------


class TestPhaseOrdering:
    def test_observation_reflects_post_action_world(self):
        grid = [[_cell("resource", 0.5)]]
        world = _make_world(grid, agent_pos=(0, 0))
        result = step(world, _agent(), Action.CONSUME,
                      0, **_DEFAULT_STEP_KWARGS)
        assert result.observation.current.resource == pytest.approx(0.0)

    def test_memory_contains_post_action_observation(self):
        grid = [[_cell("resource", 0.5)]]
        world = _make_world(grid, agent_pos=(0, 0))
        result = step(world, _agent(), Action.CONSUME,
                      0, **_DEFAULT_STEP_KWARGS)
        mem_entry = result.agent_state.memory_state.entries[-1]
        assert mem_entry.observation == result.observation

    def test_observation_reflects_post_movement(self):
        world = _3x3_world()
        result = step(world, _agent(), Action.UP, 0, **_DEFAULT_STEP_KWARGS)
        assert result.observation.current.resource == pytest.approx(0.7)

    def test_world_unchanged_when_regen_rate_zero(self):
        world = _3x3_world()
        resource_c = world.get_cell(Position(x=1, y=0))
        assert resource_c.resource_value == pytest.approx(0.7)
        step(world, _agent(), Action.STAY, 0, **_DEFAULT_STEP_KWARGS)
        resource_c_after = world.get_cell(Position(x=1, y=0))
        assert resource_c_after.resource_value == pytest.approx(0.7)


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
        for action in [Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT]:
            w = _make_world([[_cell()]], agent_pos=(0, 0))
            result = step(w, _agent(), action, 0, **_DEFAULT_STEP_KWARGS)
            assert result.trace.moved is False
            assert w.agent_position == Position(x=0, y=0)

    def test_max_consume_zero(self):
        grid = [[_cell("resource", 0.5)]]
        world = _make_world(grid, agent_pos=(0, 0))
        kwargs = {**_DEFAULT_STEP_KWARGS, "max_consume": 0.0}
        result = step(world, _agent(), Action.CONSUME, 0, **kwargs)
        assert result.trace.consumed is False
        assert result.trace.resource_consumed == 0.0
        assert world.get_cell(
            Position(x=0, y=0)).resource_value == pytest.approx(0.5)

    def test_energy_exactly_equals_cost(self):
        world = _3x3_world()
        result = step(world, _agent(energy=1.0),
                      Action.UP, 0, **_DEFAULT_STEP_KWARGS)
        assert result.agent_state.energy == pytest.approx(0.0)
        assert result.terminated is True

    def test_energy_gain_factor_zero(self):
        grid = [[_cell("resource", 0.8)]]
        world = _make_world(grid, agent_pos=(0, 0))
        kwargs = {**_DEFAULT_STEP_KWARGS, "energy_gain_factor": 0.0}
        result = step(world, _agent(energy=50.0), Action.CONSUME, 0, **kwargs)
        assert result.agent_state.energy == pytest.approx(49.0)


# ---------------------------------------------------------------------------
# Regeneration tests
# ---------------------------------------------------------------------------


class TestRegeneration:
    def test_regen_increases_resource(self):
        grid = [[_cell()]]
        world = _make_world(grid, agent_pos=(0, 0))
        kwargs = {**_DEFAULT_STEP_KWARGS, "resource_regen_rate": 0.1}
        step(world, _agent(), Action.STAY, 0, **kwargs)
        cell = world.get_cell(Position(x=0, y=0))
        assert cell.resource_value == pytest.approx(0.1)

    def test_regen_clipped_at_one(self):
        grid = [[_cell("resource", 0.9)]]
        world = _make_world(grid, agent_pos=(0, 0))
        kwargs = {**_DEFAULT_STEP_KWARGS, "resource_regen_rate": 0.2}
        step(world, _agent(), Action.STAY, 0, **kwargs)
        cell = world.get_cell(Position(x=0, y=0))
        assert cell.resource_value == pytest.approx(1.0)

    def test_obstacle_does_not_regenerate(self):
        grid = [
            [_cell(), _cell("obstacle")],
        ]
        world = _make_world(grid, agent_pos=(0, 0))
        kwargs = {**_DEFAULT_STEP_KWARGS, "resource_regen_rate": 0.5}
        step(world, _agent(), Action.STAY, 0, **kwargs)
        obstacle = world.get_cell(Position(x=1, y=0))
        assert obstacle.cell_type is CellType.OBSTACLE
        assert obstacle.resource_value == 0.0

    def test_regen_zero_rate_is_noop(self):
        grid = [[_cell("resource", 0.3)]]
        world = _make_world(grid, agent_pos=(0, 0))
        kwargs = {**_DEFAULT_STEP_KWARGS, "resource_regen_rate": 0.0}
        step(world, _agent(), Action.STAY, 0, **kwargs)
        cell = world.get_cell(Position(x=0, y=0))
        assert cell.resource_value == pytest.approx(0.3)

    def test_regen_all_cells_updated(self):
        grid = [
            [_cell(), _cell("resource", 0.5)],
            [_cell("obstacle"), _cell()],
        ]
        world = _make_world(grid, agent_pos=(0, 0))
        kwargs = {**_DEFAULT_STEP_KWARGS, "resource_regen_rate": 0.1}
        step(world, _agent(), Action.STAY, 0, **kwargs)
        assert world.get_cell(
            Position(x=0, y=0)).resource_value == pytest.approx(0.1)
        assert world.get_cell(
            Position(x=1, y=0)).resource_value == pytest.approx(0.6)
        assert world.get_cell(Position(x=0, y=1)).resource_value == 0.0
        assert world.get_cell(
            Position(x=1, y=1)).resource_value == pytest.approx(0.1)

    def test_regen_cell_type_empty_to_resource(self):
        grid = [[_cell()]]
        world = _make_world(grid, agent_pos=(0, 0))
        kwargs = {**_DEFAULT_STEP_KWARGS, "resource_regen_rate": 0.2}
        step(world, _agent(), Action.STAY, 0, **kwargs)
        cell = world.get_cell(Position(x=0, y=0))
        assert cell.cell_type is CellType.RESOURCE
        assert cell.resource_value == pytest.approx(0.2)

    def test_regen_already_at_max(self):
        grid = [[_cell("resource", 1.0)]]
        world = _make_world(grid, agent_pos=(0, 0))
        kwargs = {**_DEFAULT_STEP_KWARGS, "resource_regen_rate": 0.1}
        step(world, _agent(), Action.STAY, 0, **kwargs)
        cell = world.get_cell(Position(x=0, y=0))
        assert cell.resource_value == pytest.approx(1.0)

    def test_regen_before_action(self):
        grid = [[_cell("resource", 0.3)]]
        world = _make_world(grid, agent_pos=(0, 0))
        kwargs = {**_DEFAULT_STEP_KWARGS, "resource_regen_rate": 0.2}
        result = step(world, _agent(), Action.CONSUME, 0, **kwargs)
        assert result.trace.resource_consumed == pytest.approx(0.5)

    def test_regen_before_observation(self):
        grid = [
            [_cell(), _cell("resource", 0.4)],
        ]
        world = _make_world(grid, agent_pos=(0, 0))
        kwargs = {**_DEFAULT_STEP_KWARGS, "resource_regen_rate": 0.1}
        result = step(world, _agent(), Action.STAY, 0, **kwargs)
        assert result.observation.current.resource == pytest.approx(0.1)
        assert result.observation.right.resource == pytest.approx(0.5)

    def test_regen_does_not_affect_position(self):
        world = _3x3_world()
        kwargs = {**_DEFAULT_STEP_KWARGS, "resource_regen_rate": 0.1}
        step(world, _agent(), Action.STAY, 0, **kwargs)
        assert world.agent_position == Position(x=1, y=1)

    def test_regen_does_not_affect_agent_state(self):
        world = _3x3_world()
        agent = _agent(energy=50.0)
        kwargs_regen = {**_DEFAULT_STEP_KWARGS, "resource_regen_rate": 0.1}
        r_regen = step(world, agent, Action.STAY, 0, **kwargs_regen)
        world2 = _3x3_world()
        r_no_regen = step(world2, agent, Action.STAY,
                          0, **_DEFAULT_STEP_KWARGS)
        assert r_regen.agent_state.energy == r_no_regen.agent_state.energy
        assert len(r_regen.agent_state.memory_state.entries) == len(
            r_no_regen.agent_state.memory_state.entries)

    def test_regen_deterministic(self):
        for _ in range(3):
            grid = [[_cell("resource", 0.5)]]
            world = _make_world(grid, agent_pos=(0, 0))
            kwargs = {**_DEFAULT_STEP_KWARGS, "resource_regen_rate": 0.15}
            step(world, _agent(), Action.STAY, 0, **kwargs)
            assert world.get_cell(
                Position(x=0, y=0)).resource_value == pytest.approx(0.65)


# --- WP17: Regeneration Eligibility Tests ---


class TestRegenerationEligibility:
    """Verify that regeneration respects the regen_eligible flag."""

    def test_eligible_cell_regenerates(self):
        cell = Cell(cell_type=CellType.EMPTY,
                    resource_value=0.0, regen_eligible=True)
        grid = [[cell]]
        world = _make_world(grid, agent_pos=(0, 0))
        kwargs = {**_DEFAULT_STEP_KWARGS, "resource_regen_rate": 0.1}
        step(world, _agent(), Action.STAY, 0, **kwargs)
        assert world.get_cell(
            Position(x=0, y=0)).resource_value == pytest.approx(0.1)

    def test_ineligible_cell_does_not_regenerate(self):
        cell = Cell(cell_type=CellType.EMPTY,
                    resource_value=0.0, regen_eligible=False)
        grid = [[cell]]
        world = _make_world(grid, agent_pos=(0, 0))
        kwargs = {**_DEFAULT_STEP_KWARGS, "resource_regen_rate": 0.1}
        step(world, _agent(), Action.STAY, 0, **kwargs)
        assert world.get_cell(Position(x=0, y=0)).resource_value == 0.0

    def test_mixed_eligibility(self):
        """Only eligible cells regenerate in a 1x3 grid."""
        eligible = Cell(cell_type=CellType.EMPTY,
                        resource_value=0.0, regen_eligible=True)
        ineligible = Cell(cell_type=CellType.EMPTY,
                          resource_value=0.0, regen_eligible=False)
        grid = [[eligible, ineligible, eligible]]
        world = _make_world(grid, agent_pos=(0, 0))
        kwargs = {**_DEFAULT_STEP_KWARGS, "resource_regen_rate": 0.2}
        step(world, _agent(), Action.STAY, 0, **kwargs)
        assert world.get_cell(
            Position(x=0, y=0)).resource_value == pytest.approx(0.2)
        assert world.get_cell(Position(x=1, y=0)).resource_value == 0.0
        assert world.get_cell(
            Position(x=2, y=0)).resource_value == pytest.approx(0.2)

    def test_clipping_still_holds_for_eligible(self):
        cell = Cell(cell_type=CellType.RESOURCE,
                    resource_value=0.95, regen_eligible=True)
        grid = [[cell]]
        world = _make_world(grid, agent_pos=(0, 0))
        kwargs = {**_DEFAULT_STEP_KWARGS, "resource_regen_rate": 0.2}
        step(world, _agent(), Action.STAY, 0, **kwargs)
        assert world.get_cell(
            Position(x=0, y=0)).resource_value == pytest.approx(1.0)

    def test_eligibility_preserved_after_regen(self):
        cell = Cell(cell_type=CellType.EMPTY,
                    resource_value=0.0, regen_eligible=True)
        grid = [[cell]]
        world = _make_world(grid, agent_pos=(0, 0))
        kwargs = {**_DEFAULT_STEP_KWARGS, "resource_regen_rate": 0.3}
        step(world, _agent(), Action.STAY, 0, **kwargs)
        updated = world.get_cell(Position(x=0, y=0))
        assert updated.regen_eligible is True

    def test_eligibility_preserved_after_consume(self):
        cell = Cell(cell_type=CellType.RESOURCE,
                    resource_value=0.5, regen_eligible=True)
        grid = [[cell]]
        world = _make_world(grid, agent_pos=(0, 0))
        step(world, _agent(), Action.CONSUME, 0, **_DEFAULT_STEP_KWARGS)
        updated = world.get_cell(Position(x=0, y=0))
        assert updated.regen_eligible is True

    def test_ineligible_preserved_after_consume(self):
        cell = Cell(cell_type=CellType.RESOURCE,
                    resource_value=0.5, regen_eligible=False)
        grid = [[cell]]
        world = _make_world(grid, agent_pos=(0, 0))
        step(world, _agent(), Action.CONSUME, 0, **_DEFAULT_STEP_KWARGS)
        updated = world.get_cell(Position(x=0, y=0))
        assert updated.regen_eligible is False

    def test_all_traversable_regression(self):
        """Default cells (regen_eligible=True) behave like pre-WP17 baseline."""
        grid = [[_cell("resource", 0.5)]]
        world = _make_world(grid, agent_pos=(0, 0))
        kwargs = {**_DEFAULT_STEP_KWARGS, "resource_regen_rate": 0.1}
        step(world, _agent(), Action.STAY, 0, **kwargs)
        assert world.get_cell(
            Position(x=0, y=0)).resource_value == pytest.approx(0.6)
