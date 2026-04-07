"""System B tests -- scout agent with scan action."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from axis.sdk.actions import MOVEMENT_DELTAS
from axis.sdk.interfaces import SystemInterface
from axis.sdk.position import Position
from axis.sdk.types import DecideResult, TransitionResult
from axis.sdk.world_types import ActionOutcome, BaseWorldConfig
from axis.systems.system_b.actions import handle_scan
from axis.systems.system_b.config import (
    AgentConfig,
    PolicyConfig,
    SystemBConfig,
    TransitionConfig,
    WorldDynamicsConfig,
)
from axis.systems.system_b.system import SystemB
from axis.systems.system_b.types import AgentState, ScanResult
from axis.world.model import Cell, CellType, World


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _default_config() -> SystemBConfig:
    return SystemBConfig(
        agent=AgentConfig(initial_energy=30.0, max_energy=50.0),
    )


def _make_grid(width: int, height: int) -> list[list[Cell]]:
    return [
        [Cell(cell_type=CellType.EMPTY, resource_value=0.0)
         for _ in range(width)]
        for _ in range(height)
    ]


def _make_resource_grid(
    width: int, height: int, value: float = 0.5,
) -> list[list[Cell]]:
    return [
        [Cell(cell_type=CellType.RESOURCE, resource_value=value)
         for _ in range(width)]
        for _ in range(height)
    ]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def config() -> SystemBConfig:
    return _default_config()


@pytest.fixture()
def system(config: SystemBConfig) -> SystemB:
    return SystemB(config)


@pytest.fixture()
def initial_state(system: SystemB) -> AgentState:
    return system.initialize_state()


@pytest.fixture()
def simple_world() -> World:
    return World(_make_grid(5, 5), Position(x=2, y=2))


@pytest.fixture()
def resource_world() -> World:
    return World(_make_resource_grid(5, 5, 0.5), Position(x=2, y=2))


@pytest.fixture()
def rng() -> np.random.Generator:
    return np.random.default_rng(42)


# ===========================================================================
# 1. Config
# ===========================================================================


class TestSystemBConfig:
    """Config parsing and validation."""

    def test_construct_minimal(self) -> None:
        cfg = SystemBConfig(
            agent=AgentConfig(initial_energy=30, max_energy=50),
        )
        assert cfg.agent.initial_energy == 30.0
        assert cfg.agent.max_energy == 50.0

    def test_defaults_applied(self) -> None:
        cfg = _default_config()
        assert cfg.policy.selection_mode == "sample"
        assert cfg.policy.temperature == 1.0
        assert cfg.policy.scan_bonus == 2.0
        assert cfg.transition.move_cost == 1.0
        assert cfg.transition.scan_cost == 0.5
        assert cfg.transition.stay_cost == 0.5
        assert cfg.world_dynamics.resource_regen_rate == 0.0

    def test_energy_bounds_validation(self) -> None:
        with pytest.raises(ValueError, match="initial_energy"):
            AgentConfig(initial_energy=100.0, max_energy=50.0)

    def test_sub_configs_accessible(self) -> None:
        cfg = _default_config()
        assert isinstance(cfg.agent, AgentConfig)
        assert isinstance(cfg.policy, PolicyConfig)
        assert isinstance(cfg.transition, TransitionConfig)
        assert isinstance(cfg.world_dynamics, WorldDynamicsConfig)

    def test_construct_from_dict(self) -> None:
        raw = {
            "agent": {"initial_energy": 20, "max_energy": 40},
            "policy": {"temperature": 0.5, "scan_bonus": 3.0},
        }
        cfg = SystemBConfig(**raw)
        assert cfg.agent.initial_energy == 20.0
        assert cfg.policy.temperature == 0.5
        assert cfg.policy.scan_bonus == 3.0


# ===========================================================================
# 2. Construction and identity
# ===========================================================================


class TestSystemBConstruction:
    """SystemB construction and identity."""

    def test_constructs_successfully(self, config: SystemBConfig) -> None:
        system = SystemB(config)
        assert system is not None

    def test_system_type(self, system: SystemB) -> None:
        assert system.system_type() == "system_b"

    def test_action_space(self, system: SystemB) -> None:
        actions = system.action_space()
        assert actions == ("up", "down", "left", "right", "scan", "stay")

    def test_action_space_includes_base_actions(self, system: SystemB) -> None:
        actions = system.action_space()
        for base in ("up", "down", "left", "right", "stay"):
            assert base in actions

    def test_action_space_includes_scan(self, system: SystemB) -> None:
        assert "scan" in system.action_space()


# ===========================================================================
# 3. Protocol conformance
# ===========================================================================


class TestProtocolConformance:
    """SystemInterface protocol conformance."""

    def test_system_interface(self, system: SystemB) -> None:
        assert isinstance(system, SystemInterface)


# ===========================================================================
# 4. initialize_state
# ===========================================================================


class TestInitializeState:
    """State initialization."""

    def test_returns_agent_state(self, system: SystemB) -> None:
        state = system.initialize_state()
        assert isinstance(state, AgentState)

    def test_initial_energy(self, system: SystemB) -> None:
        state = system.initialize_state()
        assert state.energy == 30.0

    def test_empty_scan_result(self, system: SystemB) -> None:
        state = system.initialize_state()
        assert state.last_scan.total_resource == 0.0
        assert state.last_scan.cell_count == 0


# ===========================================================================
# 5. vitality
# ===========================================================================


class TestVitality:
    """Normalized vitality metric."""

    def test_full_energy(self, system: SystemB) -> None:
        state = AgentState(energy=50.0)
        assert system.vitality(state) == 1.0

    def test_half_energy(self, system: SystemB) -> None:
        state = AgentState(energy=25.0)
        assert system.vitality(state) == 0.5

    def test_zero_energy(self, system: SystemB) -> None:
        state = AgentState(energy=0.0)
        assert system.vitality(state) == 0.0


# ===========================================================================
# 6. Scan action handler
# ===========================================================================


class TestScanHandler:
    """handle_scan action handler tests."""

    def test_scan_on_empty_grid(self, simple_world: World) -> None:
        outcome = handle_scan(simple_world, context={"scan_radius": 1})
        assert outcome.action == "scan"
        assert outcome.moved is False
        assert outcome.consumed is False
        assert outcome.resource_consumed == 0.0

    def test_scan_on_resource_grid(self, resource_world: World) -> None:
        outcome = handle_scan(resource_world, context={"scan_radius": 1})
        assert outcome.action == "scan"
        assert outcome.moved is False
        # 3x3 neighborhood, all 0.5 → total = 4.5
        assert outcome.resource_consumed == pytest.approx(4.5)

    def test_scan_does_not_mutate_world(self, resource_world: World) -> None:
        cells_before = [
            resource_world.get_cell(Position(x=x, y=y))
            for y in range(5) for x in range(5)
        ]
        handle_scan(resource_world, context={"scan_radius": 1})
        cells_after = [
            resource_world.get_cell(Position(x=x, y=y))
            for y in range(5) for x in range(5)
        ]
        assert cells_before == cells_after

    def test_scan_does_not_move_agent(self, resource_world: World) -> None:
        pos_before = resource_world.agent_position
        outcome = handle_scan(resource_world, context={"scan_radius": 1})
        assert resource_world.agent_position == pos_before
        assert outcome.new_position == pos_before

    def test_scan_at_corner(self) -> None:
        """Scan at (0,0) reads only 4 cells (2x2 in-bounds)."""
        grid = _make_resource_grid(5, 5, 0.5)
        world = World(grid, Position(x=0, y=0))
        outcome = handle_scan(world, context={"scan_radius": 1})
        # Corner: (0,0), (1,0), (0,1), (1,1) → 4 cells * 0.5 = 2.0
        assert outcome.resource_consumed == pytest.approx(2.0)

    def test_scan_at_edge(self) -> None:
        """Scan at (0,2) reads 6 cells."""
        grid = _make_resource_grid(5, 5, 0.5)
        world = World(grid, Position(x=0, y=2))
        outcome = handle_scan(world, context={"scan_radius": 1})
        # Left edge: 2x3 = 6 cells * 0.5 = 3.0
        assert outcome.resource_consumed == pytest.approx(3.0)

    def test_scan_radius_from_context(self) -> None:
        """Larger scan radius reads more cells."""
        grid = _make_resource_grid(5, 5, 0.5)
        world = World(grid, Position(x=2, y=2))
        outcome = handle_scan(world, context={"scan_radius": 2})
        # 5x5 neighborhood, all in bounds → 25 * 0.5 = 12.5
        assert outcome.resource_consumed == pytest.approx(12.5)


# ===========================================================================
# 7. decide
# ===========================================================================


class TestDecide:
    """Decision-making tests."""

    def test_returns_decide_result(
        self, system: SystemB, resource_world: World,
        initial_state: AgentState, rng: np.random.Generator,
    ) -> None:
        result = system.decide(resource_world, initial_state, rng)
        assert isinstance(result, DecideResult)

    def test_action_in_action_space(
        self, system: SystemB, resource_world: World,
        initial_state: AgentState, rng: np.random.Generator,
    ) -> None:
        result = system.decide(resource_world, initial_state, rng)
        assert result.action in system.action_space()

    def test_decision_data_keys(
        self, system: SystemB, resource_world: World,
        initial_state: AgentState, rng: np.random.Generator,
    ) -> None:
        result = system.decide(resource_world, initial_state, rng)
        assert "weights" in result.decision_data
        assert "probabilities" in result.decision_data
        assert "last_scan" in result.decision_data

    def test_inadmissible_actions_get_zero_weight(self) -> None:
        """Agent at corner -- up and left are out of bounds."""
        grid = _make_grid(5, 5)
        world = World(grid, Position(x=0, y=0))
        system = SystemB(_default_config())
        state = system.initialize_state()
        rng = np.random.default_rng(42)
        result = system.decide(world, state, rng)
        weights = result.decision_data["weights"]
        # up (index 0) and left (index 2) should be 0
        assert weights[0] == 0.0  # up
        assert weights[2] == 0.0  # left

    def test_argmax_deterministic(self) -> None:
        cfg = SystemBConfig(
            agent=AgentConfig(initial_energy=30, max_energy=50),
            policy=PolicyConfig(selection_mode="argmax"),
        )
        system = SystemB(cfg)
        state = system.initialize_state()
        world = World(_make_resource_grid(5, 5, 0.5), Position(x=2, y=2))
        actions = set()
        for seed in range(10):
            rng = np.random.default_rng(seed)
            result = system.decide(world, state, rng)
            actions.add(result.action)
        assert len(actions) == 1

    def test_sample_reproducible(self) -> None:
        system = SystemB(_default_config())
        state = system.initialize_state()
        world = World(_make_resource_grid(5, 5, 0.5), Position(x=2, y=2))
        r1 = system.decide(world, state, np.random.default_rng(42))
        r2 = system.decide(world, state, np.random.default_rng(42))
        assert r1.action == r2.action


# ===========================================================================
# 8. transition
# ===========================================================================


class TestTransition:
    """Transition function tests."""

    def test_movement_costs_energy(self, system: SystemB) -> None:
        state = AgentState(energy=30.0)
        outcome = ActionOutcome(
            action="up", moved=True,
            new_position=Position(x=2, y=1),
        )
        result = system.transition(state, outcome, {})
        assert result.new_state.energy == 29.0  # 30 - 1.0 move_cost

    def test_scan_costs_energy(self, system: SystemB) -> None:
        state = AgentState(energy=30.0)
        outcome = ActionOutcome(
            action="scan", moved=False,
            new_position=Position(x=2, y=2),
            resource_consumed=4.5,
        )
        result = system.transition(state, outcome, {})
        assert result.new_state.energy == 29.5  # 30 - 0.5 scan_cost

    def test_stay_costs_energy(self, system: SystemB) -> None:
        state = AgentState(energy=30.0)
        outcome = ActionOutcome(
            action="stay", moved=False,
            new_position=Position(x=2, y=2),
        )
        result = system.transition(state, outcome, {})
        assert result.new_state.energy == 29.5  # 30 - 0.5 stay_cost

    def test_scan_updates_last_scan(self, system: SystemB) -> None:
        state = AgentState(energy=30.0)
        outcome = ActionOutcome(
            action="scan", moved=False,
            new_position=Position(x=2, y=2),
            resource_consumed=4.5,
        )
        result = system.transition(state, outcome, {})
        assert result.new_state.last_scan.total_resource == 4.5
        assert result.new_state.last_scan.cell_count == 9

    def test_non_scan_preserves_last_scan(self, system: SystemB) -> None:
        scan_result = ScanResult(total_resource=3.0, cell_count=9)
        state = AgentState(energy=30.0, last_scan=scan_result)
        outcome = ActionOutcome(
            action="up", moved=True,
            new_position=Position(x=2, y=1),
        )
        result = system.transition(state, outcome, {})
        assert result.new_state.last_scan == scan_result

    def test_termination_on_zero_energy(self, system: SystemB) -> None:
        state = AgentState(energy=1.0)
        outcome = ActionOutcome(
            action="up", moved=True,
            new_position=Position(x=2, y=1),
        )
        result = system.transition(state, outcome, {})
        assert result.new_state.energy == 0.0
        assert result.terminated is True
        assert result.termination_reason == "energy_depleted"

    def test_no_termination_with_energy(self, system: SystemB) -> None:
        state = AgentState(energy=30.0)
        outcome = ActionOutcome(
            action="stay", moved=False,
            new_position=Position(x=2, y=2),
        )
        result = system.transition(state, outcome, {})
        assert result.terminated is False
        assert result.termination_reason is None

    def test_energy_clipped_to_max(self, system: SystemB) -> None:
        state = AgentState(energy=50.0)
        outcome = ActionOutcome(
            action="stay", moved=False,
            new_position=Position(x=2, y=2),
        )
        result = system.transition(state, outcome, {})
        assert result.new_state.energy <= 50.0

    def test_trace_data_keys(self, system: SystemB) -> None:
        state = AgentState(energy=30.0)
        outcome = ActionOutcome(
            action="scan", moved=False,
            new_position=Position(x=2, y=2),
            resource_consumed=4.5,
        )
        result = system.transition(state, outcome, {})
        assert isinstance(result, TransitionResult)
        assert "energy_before" in result.trace_data
        assert "energy_after" in result.trace_data
        assert "energy_delta" in result.trace_data
        assert "action_cost" in result.trace_data
        assert "scan_total" in result.trace_data


# ===========================================================================
# 9. observe
# ===========================================================================


class TestObserve:
    """Observation tests."""

    def test_returns_dict(self, system: SystemB, simple_world: World) -> None:
        obs = system.observe(simple_world, simple_world.agent_position)
        assert isinstance(obs, dict)
        assert obs["x"] == 2
        assert obs["y"] == 2


# ===========================================================================
# 10. Action handlers and context
# ===========================================================================


class TestActionHandlersAndContext:
    """Action handler registration and context."""

    def test_action_handlers_returns_scan(self, system: SystemB) -> None:
        handlers = system.action_handlers()
        assert "scan" in handlers
        assert callable(handlers["scan"])

    def test_action_context_returns_scan_radius(self, system: SystemB) -> None:
        ctx = system.action_context()
        assert "scan_radius" in ctx
        assert ctx["scan_radius"] == 1

    def test_handler_count(self, system: SystemB) -> None:
        """System B has exactly one custom handler (scan)."""
        assert len(system.action_handlers()) == 1


# ===========================================================================
# 11. Registry integration
# ===========================================================================


class TestRegistryIntegration:
    """System B registration and factory."""

    def test_registered_in_registry(self) -> None:
        from axis.framework.registry import registered_system_types
        assert "system_b" in registered_system_types()

    def test_create_via_registry(self) -> None:
        from axis.framework.registry import create_system
        system = create_system("system_b", {
            "agent": {"initial_energy": 30, "max_energy": 50},
        })
        assert isinstance(system, SystemInterface)
        assert system.system_type() == "system_b"

    def test_factory_validates_config(self) -> None:
        from axis.framework.registry import create_system
        with pytest.raises(Exception):
            create_system("system_b", {})  # missing agent


# ===========================================================================
# 12. Framework integration
# ===========================================================================


class TestFrameworkIntegration:
    """Run System B through the framework pipeline."""

    def test_setup_and_run_episode(self) -> None:
        from axis.framework.runner import run_episode, setup_episode

        config = _default_config()
        system = SystemB(config)
        world_config = BaseWorldConfig(grid_width=5, grid_height=5)

        world, registry = setup_episode(
            system, world_config, Position(x=2, y=2), seed=42,
        )

        # Registry should have scan registered
        assert registry.has_handler("scan")

        trace = run_episode(
            system, world, registry,
            max_steps=50, regen_rate=0.0, seed=42,
        )

        assert trace.system_type == "system_b"
        assert trace.total_steps > 0
        assert 0.0 <= trace.final_vitality <= 1.0
        assert trace.termination_reason in (
            "max_steps_reached", "energy_depleted",
        )

    def test_scan_action_appears_in_trace(self) -> None:
        """At least one scan action should appear in a typical run."""
        from axis.framework.runner import run_episode, setup_episode

        config = SystemBConfig(
            agent=AgentConfig(initial_energy=50, max_energy=50),
            policy=PolicyConfig(scan_bonus=10.0),  # strongly prefer scan
        )
        system = SystemB(config)
        world_config = BaseWorldConfig(grid_width=5, grid_height=5)

        world, registry = setup_episode(
            system, world_config, Position(x=2, y=2), seed=42,
        )
        trace = run_episode(
            system, world, registry,
            max_steps=50, regen_rate=0.0, seed=42,
        )

        actions = [step.action for step in trace.steps]
        assert "scan" in actions

    def test_full_experiment_execution(self, tmp_path: Any) -> None:
        from axis.framework.config import ExperimentConfig
        from axis.framework.experiment import execute_experiment
        from axis.framework.persistence import ExperimentRepository

        config = ExperimentConfig(
            system_type="system_b",
            experiment_type="single_run",
            general={"seed": 42},
            execution={"max_steps": 50},
            world={"grid_width": 5, "grid_height": 5},
            system={"agent": {"initial_energy": 30, "max_energy": 50}},
            num_episodes_per_run=3,
        )

        repo = ExperimentRepository(tmp_path)
        result = execute_experiment(config, repo)
        assert len(result.run_results) == 1
        summary = result.run_results[0].summary
        assert summary.num_episodes == 3
        assert 0.0 <= summary.mean_final_vitality <= 1.0

    def test_ofat_experiment(self, tmp_path: Any) -> None:
        from axis.framework.config import ExperimentConfig
        from axis.framework.experiment import execute_experiment
        from axis.framework.persistence import ExperimentRepository

        config = ExperimentConfig(
            system_type="system_b",
            experiment_type="ofat",
            general={"seed": 42},
            execution={"max_steps": 50},
            world={"grid_width": 5, "grid_height": 5},
            system={"agent": {"initial_energy": 30, "max_energy": 50}},
            num_episodes_per_run=2,
            parameter_path="system.policy.scan_bonus",
            parameter_values=[0.5, 2.0, 5.0],
        )

        repo = ExperimentRepository(tmp_path)
        result = execute_experiment(config, repo)
        assert len(result.run_results) == 3

    def test_deterministic_episodes(self) -> None:
        """Two runs with same seed produce identical traces."""
        from axis.framework.runner import run_episode, setup_episode

        config = _default_config()

        traces = []
        for _ in range(2):
            system = SystemB(config)
            world_config = BaseWorldConfig(grid_width=5, grid_height=5)
            world, registry = setup_episode(
                system, world_config, Position(x=2, y=2), seed=42,
            )
            trace = run_episode(
                system, world, registry,
                max_steps=30, regen_rate=0.0, seed=42,
            )
            traces.append(trace)

        assert traces[0].total_steps == traces[1].total_steps
        for s0, s1 in zip(traces[0].steps, traces[1].steps):
            assert s0.action == s1.action
            assert s0.agent_position_after == s1.agent_position_after


# ===========================================================================
# 13. Import verification
# ===========================================================================


class TestImportVerification:
    """Package import tests."""

    def test_top_level_imports(self) -> None:
        from axis.systems.system_b import SystemB, SystemBConfig  # noqa: F401

    def test_module_imports(self) -> None:
        from axis.systems.system_b.types import AgentState, ScanResult  # noqa: F401
        from axis.systems.system_b.actions import handle_scan  # noqa: F401
        from axis.systems.system_b.config import SystemBConfig  # noqa: F401
        from axis.systems.system_b.system import SystemB  # noqa: F401
