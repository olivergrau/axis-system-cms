"""WP-11 worked example validation tests.

Reproduces every numerical calculation from the worked examples
document (02_System A+W Worked Examples.md) and verifies that the
implementation matches within tolerance.

Tolerances: abs=0.005 for intermediate values, abs=0.01 for probabilities.
"""

from __future__ import annotations

import numpy as np
import pytest

from axis.systems.system_a.types import (
    CellObservation,
    HungerDriveOutput,
    MemoryState,
    Observation,
)
from axis.systems.system_aw.config import ArbitrationConfig, SystemAWConfig
from axis.systems.system_aw.drive_arbitration import (
    compute_action_scores,
    compute_drive_weights,
)
from axis.systems.system_aw.drive_curiosity import (
    SystemAWCuriosityDrive,
    compute_composite_novelty,
    compute_sensory_novelty,
    compute_spatial_novelty,
)
from axis.systems.system_aw.drive_hunger import SystemAWHungerDrive
from axis.systems.system_aw.policy import SystemAWPolicy
from axis.systems.system_aw.system import SystemAW
from axis.systems.system_aw.transition import SystemAWTransition
from axis.systems.system_aw.types import (
    AgentStateAW,
    CuriosityDriveOutput,
    WorldModelState,
)
from axis.systems.system_aw.world_model import (
    create_world_model,
    update_world_model,
)
from axis.sdk.position import Position
from axis.world.grid_2d.model import Cell, CellType, World
from tests.builders.system_aw_config_builder import SystemAWConfigBuilder

# ---------------------------------------------------------------------------
# Common parameters (Section 4 of Worked Examples)
# ---------------------------------------------------------------------------

E_MAX = 100.0
BETA = 2.0  # temperature
W_CONSUME = 2.5
LAMBDA_STAY = 0.1
MU_C = 1.0
ALPHA = 0.5
LAMBDA_EXPLORE = 0.3
W_H_BASE = 0.3
W_C_BASE = 1.0
GAMMA = 2.0
C_MOVE = 1.0
C_CONSUME = 1.0
C_STAY = 0.5
KAPPA = 10.0


def _arb_config(gamma: float = GAMMA) -> ArbitrationConfig:
    return ArbitrationConfig(
        hunger_weight_base=W_H_BASE,
        curiosity_weight_base=W_C_BASE,
        gating_sharpness=gamma,
    )


def _make_obs(
    current_r: float,
    up_r: float, down_r: float, left_r: float, right_r: float,
    left_b: float = 1.0,
) -> Observation:
    """Construct observation. All directions traversable unless overridden."""
    return Observation(
        current=CellObservation(traversability=1.0, resource=current_r),
        up=CellObservation(traversability=1.0, resource=up_r),
        down=CellObservation(traversability=1.0, resource=down_r),
        left=CellObservation(traversability=left_b, resource=left_r),
        right=CellObservation(traversability=1.0, resource=right_r),
    )


def _we_config_builder() -> SystemAWConfigBuilder:
    """Config builder matching Section 4 common parameters."""
    return (
        SystemAWConfigBuilder()
        .with_max_energy(E_MAX)
        .with_memory_capacity(5)
        .with_temperature(BETA)
        .with_consume_weight(W_CONSUME)
        .with_stay_suppression(LAMBDA_STAY)
        .with_base_curiosity(MU_C)
        .with_spatial_sensory_balance(ALPHA)
        .with_explore_suppression(LAMBDA_EXPLORE)
        .with_hunger_weight_base(W_H_BASE)
        .with_curiosity_weight_base(W_C_BASE)
        .with_gating_sharpness(GAMMA)
    )


# ===========================================================================
# Example Group A: Drive Weight Dynamics (Well-Fed Agent, e=90)
# ===========================================================================


class TestExampleA1:
    """A1: Well-fed agent in novel territory (e=90)."""

    # A1 observation: current r=0.8, left r=0.3, others 0
    OBS = _make_obs(0.8, 0.0, 0.0, 0.3, 0.0)

    def test_a1_drive_evaluation(self) -> None:
        """e=90, E_max=100 -> d_H=0.10, d_C=1.0."""
        drive = SystemAWHungerDrive(
            consume_weight=W_CONSUME, stay_suppression=LAMBDA_STAY,
            max_energy=E_MAX,
        )
        state = AgentStateAW(
            energy=90.0,
            memory_state=MemoryState(entries=(), capacity=5),
            world_model=create_world_model(),
        )
        result = drive.compute(state, self.OBS)
        assert result.activation == pytest.approx(0.10, abs=0.005)

        curiosity = SystemAWCuriosityDrive(
            base_curiosity=MU_C, spatial_sensory_balance=ALPHA,
            explore_suppression=LAMBDA_EXPLORE,
        )
        c_result = curiosity.compute(
            self.OBS, state.memory_state, state.world_model)
        assert c_result.activation == pytest.approx(1.0, abs=0.005)

    def test_a1_drive_arbitration(self) -> None:
        """d_H=0.10 -> w_H=0.307, w_C=0.810."""
        weights = compute_drive_weights(0.10, _arb_config())
        assert weights.hunger_weight == pytest.approx(0.307, abs=0.005)
        assert weights.curiosity_weight == pytest.approx(0.810, abs=0.005)

    def test_a1_spatial_novelty(self) -> None:
        """All unvisited -> all nu_spatial = 1.0."""
        wm = create_world_model()
        spatial = compute_spatial_novelty(wm)
        for v in spatial:
            assert v == pytest.approx(1.0, abs=0.005)

    def test_a1_sensory_novelty(self) -> None:
        """Empty memory -> nu_sensory = (0.0, 0.0, 0.3, 0.0)."""
        mem = MemoryState(entries=(), capacity=5)
        sensory = compute_sensory_novelty(self.OBS, mem)
        assert sensory[0] == pytest.approx(0.0, abs=0.005)
        assert sensory[1] == pytest.approx(0.0, abs=0.005)
        assert sensory[2] == pytest.approx(0.3, abs=0.005)
        assert sensory[3] == pytest.approx(0.0, abs=0.005)

    def test_a1_composite_novelty(self) -> None:
        """alpha=0.5 -> nu = (0.50, 0.50, 0.65, 0.50)."""
        spatial = (1.0, 1.0, 1.0, 1.0)
        sensory = (0.0, 0.0, 0.3, 0.0)
        composite = compute_composite_novelty(spatial, sensory, ALPHA)
        assert composite[0] == pytest.approx(0.50, abs=0.005)
        assert composite[1] == pytest.approx(0.50, abs=0.005)
        assert composite[2] == pytest.approx(0.65, abs=0.005)
        assert composite[3] == pytest.approx(0.50, abs=0.005)

    def test_a1_hunger_contributions(self) -> None:
        """Verify all 6 hunger drive action_contributions.

        SystemAHungerDrive returns d_H * phi_H(a) as action_contributions.
        d_H=0.10, so contributions = 0.10 * raw phi_H values.
        """
        drive = SystemAWHungerDrive(
            consume_weight=W_CONSUME, stay_suppression=LAMBDA_STAY,
            max_energy=E_MAX,
        )
        state = AgentStateAW(
            energy=90.0,
            memory_state=MemoryState(entries=(), capacity=5),
            world_model=create_world_model(),
        )
        result = drive.compute(state, self.OBS)
        phi = result.action_contributions
        # Drive returns d_H * phi_H(a): d_H=0.10
        assert phi[0] == pytest.approx(0.0, abs=0.005)    # UP: 0.1*0.0
        assert phi[1] == pytest.approx(0.0, abs=0.005)    # DOWN: 0.1*0.0
        assert phi[2] == pytest.approx(0.03, abs=0.005)   # LEFT: 0.1*0.3
        assert phi[3] == pytest.approx(0.0, abs=0.005)    # RIGHT: 0.1*0.0
        assert phi[4] == pytest.approx(
            0.20, abs=0.005)   # CONSUME: 0.1*2.5*0.8
        assert phi[5] == pytest.approx(-0.01, abs=0.005)  # STAY: -0.1*0.1

    def test_a1_curiosity_contributions(self) -> None:
        """Verify all 6 curiosity phi_C values."""
        curiosity = SystemAWCuriosityDrive(
            base_curiosity=MU_C, spatial_sensory_balance=ALPHA,
            explore_suppression=LAMBDA_EXPLORE,
        )
        state = AgentStateAW(
            energy=90.0,
            memory_state=MemoryState(entries=(), capacity=5),
            world_model=create_world_model(),
        )
        c_result = curiosity.compute(
            self.OBS, state.memory_state, state.world_model)
        phi = c_result.action_contributions
        assert phi[0] == pytest.approx(0.50, abs=0.005)   # UP
        assert phi[1] == pytest.approx(0.50, abs=0.005)   # DOWN
        assert phi[2] == pytest.approx(0.65, abs=0.005)   # LEFT
        assert phi[3] == pytest.approx(0.50, abs=0.005)   # RIGHT
        assert phi[4] == pytest.approx(-0.3, abs=0.005)   # CONSUME
        assert phi[5] == pytest.approx(-0.3, abs=0.005)   # STAY

    def test_a1_combined_scores(self) -> None:
        """Verify all 6 psi(a) combined scores."""
        h_out = HungerDriveOutput(
            activation=0.10,
            action_contributions=(0.0, 0.0, 0.3, 0.0, 2.0, -0.1),
        )
        c_out = CuriosityDriveOutput(
            activation=1.0,
            spatial_novelty=(1.0, 1.0, 1.0, 1.0),
            sensory_novelty=(0.0, 0.0, 0.3, 0.0),
            composite_novelty=(0.50, 0.50, 0.65, 0.50),
            action_contributions=(0.50, 0.50, 0.65, 0.50, -0.3, -0.3),
        )
        weights = compute_drive_weights(0.10, _arb_config())
        scores = compute_action_scores(h_out, c_out, weights)
        # Exact: UP=0.405, DOWN=0.405, LEFT=0.53571, RIGHT=0.405,
        #        CONSUME=-0.1816, STAY=-0.24607
        assert scores[0] == pytest.approx(0.405, abs=0.005)
        assert scores[1] == pytest.approx(0.405, abs=0.005)
        assert scores[2] == pytest.approx(0.536, abs=0.005)
        assert scores[3] == pytest.approx(0.405, abs=0.005)
        assert scores[4] == pytest.approx(-0.182, abs=0.005)
        assert scores[5] == pytest.approx(-0.246, abs=0.005)

    def test_a1_probabilities(self) -> None:
        """Verify all 6 probabilities after softmax (beta=2.0)."""
        scores = (0.405, 0.405, 0.53571, 0.405, -0.1816, -0.24607)
        policy = SystemAWPolicy(temperature=BETA, selection_mode="sample")
        rng = np.random.default_rng(42)
        result = policy.select(scores, self.OBS, rng)
        probs = result.policy_data["probabilities"]
        assert probs[0] == pytest.approx(0.2049, abs=0.01)  # UP
        assert probs[1] == pytest.approx(0.2049, abs=0.01)  # DOWN
        assert probs[2] == pytest.approx(0.2661, abs=0.01)  # LEFT
        assert probs[3] == pytest.approx(0.2049, abs=0.01)  # RIGHT
        assert probs[4] == pytest.approx(0.0634, abs=0.01)  # CONSUME
        assert probs[5] == pytest.approx(0.0557, abs=0.01)  # STAY

    def test_a1_conclusion(self) -> None:
        """Movement collectively > 88%, CONSUME < 7%."""
        scores = (0.405, 0.405, 0.53571, 0.405, -0.1816, -0.24607)
        policy = SystemAWPolicy(temperature=BETA, selection_mode="sample")
        rng = np.random.default_rng(42)
        result = policy.select(scores, self.OBS, rng)
        probs = result.policy_data["probabilities"]
        movement_total = sum(probs[:4])
        assert movement_total > 0.88
        assert probs[4] < 0.07


# ===========================================================================
# Example Group B: Hunger-Curiosity Competition (e=50)
# ===========================================================================


class TestExampleB1:
    """B1: Moderate hunger with resource present (e=50)."""

    OBS = _make_obs(0.6, 0.0, 0.4, 0.0, 0.0, left_b=0.0)  # LEFT blocked

    def test_b1_drive_evaluation(self) -> None:
        """e=50 -> d_H=0.50, d_C=0.85 (assumed nu_bar=0.15)."""
        # d_H is straightforward
        d_h = 1 - 50.0 / E_MAX
        assert d_h == pytest.approx(0.50, abs=0.005)
        # d_C tested via the assumption from the spec
        # d_C = mu_C * (1 - nu_bar) = 1.0 * (1 - 0.15) = 0.85

    def test_b1_drive_arbitration(self) -> None:
        """d_H=0.50 -> w_H=0.475, w_C=0.250."""
        weights = compute_drive_weights(0.50, _arb_config())
        assert weights.hunger_weight == pytest.approx(0.475, abs=0.005)
        assert weights.curiosity_weight == pytest.approx(0.250, abs=0.005)

    def test_b1_novelty(self) -> None:
        """Verify spatial, sensory, composite novelty per direction."""
        # Spatial: all neighbors visited 1x -> 1/(1+1) = 0.5
        # Sensory: |r_obs - r_mean|. up: |0.0-0.1|=0.1, down: |0.4-0|=0.4,
        #          left: |0.0-0.2|=0.2, right: |0.0-0|=0.0
        spatial = (0.500, 0.500, 0.500, 0.500)
        sensory = (0.1, 0.4, 0.2, 0.0)
        composite = compute_composite_novelty(spatial, sensory, ALPHA)
        assert composite[0] == pytest.approx(0.300, abs=0.005)
        assert composite[1] == pytest.approx(0.450, abs=0.005)
        assert composite[2] == pytest.approx(0.350, abs=0.005)
        assert composite[3] == pytest.approx(0.250, abs=0.005)

    def test_b1_combined_scores(self) -> None:
        """Verify all 6 scores (before masking)."""
        h_out = HungerDriveOutput(
            activation=0.50,
            action_contributions=(0.0, 0.4, 0.0, 0.0, 1.5, -0.1),
        )
        c_out = CuriosityDriveOutput(
            activation=0.85,
            spatial_novelty=(0.5, 0.5, 0.5, 0.5),
            sensory_novelty=(0.1, 0.4, 0.2, 0.0),
            composite_novelty=(0.300, 0.450, 0.350, 0.250),
            action_contributions=(0.300, 0.450, 0.350, 0.250, -0.3, -0.3),
        )
        weights = compute_drive_weights(0.50, _arb_config())
        scores = compute_action_scores(h_out, c_out, weights)
        # Exact computed: UP=0.06375, DOWN=0.190625, LEFT=0.074375,
        #                 RIGHT=0.053125, CONSUME=0.2925, STAY=-0.0875
        assert scores[0] == pytest.approx(0.064, abs=0.005)
        assert scores[1] == pytest.approx(0.191, abs=0.005)
        assert scores[2] == pytest.approx(0.074, abs=0.005)
        assert scores[3] == pytest.approx(0.053, abs=0.005)
        assert scores[4] == pytest.approx(0.293, abs=0.005)
        assert scores[5] == pytest.approx(-0.088, abs=0.005)

    def test_b1_masking(self) -> None:
        """LEFT blocked -> psi(LEFT) = -inf after masking."""
        scores = (0.064, 0.191, 0.074, 0.053, 0.293, -0.088)
        policy = SystemAWPolicy(temperature=BETA, selection_mode="sample")
        rng = np.random.default_rng(42)
        result = policy.select(scores, self.OBS, rng)
        probs = result.policy_data["probabilities"]
        assert probs[2] == 0.0  # LEFT is blocked

    def test_b1_probabilities(self) -> None:
        """CONSUME=0.283, DOWN=0.231, LEFT=0.000."""
        scores = (0.06375, 0.190625, 0.074375, 0.053125, 0.2925, -0.0875)
        policy = SystemAWPolicy(temperature=BETA, selection_mode="sample")
        rng = np.random.default_rng(42)
        result = policy.select(scores, self.OBS, rng)
        probs = result.policy_data["probabilities"]
        assert probs[4] == pytest.approx(0.283, abs=0.01)   # CONSUME
        assert probs[1] == pytest.approx(0.231, abs=0.01)   # DOWN
        assert probs[2] == 0.0                                # LEFT


# ===========================================================================
# Example Group C: Hunger Dominance (Starving, e=5)
# ===========================================================================


class TestExampleC1:
    """C1: Starving agent ignores novelty (e=5)."""

    OBS = _make_obs(0.5, 0.0, 0.0, 0.0, 0.2)

    def test_c1_drive_arbitration(self) -> None:
        """d_H=0.95 -> w_H=0.932, w_C=0.003."""
        weights = compute_drive_weights(0.95, _arb_config())
        assert weights.hunger_weight == pytest.approx(0.932, abs=0.005)
        assert weights.curiosity_weight == pytest.approx(0.003, abs=0.005)

    def test_c1_curiosity_contribution_negligible(self) -> None:
        """All curiosity contributions < 0.002."""
        c_out = CuriosityDriveOutput(
            activation=1.0,
            spatial_novelty=(1.0, 1.0, 1.0, 1.0),
            sensory_novelty=(0.0, 0.0, 0.0, 0.2),
            composite_novelty=(0.50, 0.50, 0.50, 0.60),
            action_contributions=(0.50, 0.50, 0.50, 0.60, -0.3, -0.3),
        )
        weights = compute_drive_weights(0.95, _arb_config())
        # w_C * d_C * phi_C(a) for each action
        for i in range(6):
            contrib = weights.curiosity_weight * c_out.activation * \
                c_out.action_contributions[i]
            assert abs(contrib) < 0.002

    def test_c1_combined_scores(self) -> None:
        """CONSUME=1.106 dominates."""
        h_out = HungerDriveOutput(
            activation=0.95,
            action_contributions=(0.0, 0.0, 0.0, 0.2, 1.25, -0.1),
        )
        c_out = CuriosityDriveOutput(
            activation=1.0,
            spatial_novelty=(1.0, 1.0, 1.0, 1.0),
            sensory_novelty=(0.0, 0.0, 0.0, 0.2),
            composite_novelty=(0.50, 0.50, 0.50, 0.60),
            action_contributions=(0.50, 0.50, 0.50, 0.60, -0.3, -0.3),
        )
        weights = compute_drive_weights(0.95, _arb_config())
        scores = compute_action_scores(h_out, c_out, weights)
        # Exact: CONSUME=1.105703
        assert scores[4] == pytest.approx(1.106, abs=0.005)
        # All other scores much smaller
        for i in [0, 1, 2]:
            assert scores[i] < 0.01

    def test_c1_probabilities(self) -> None:
        """CONSUME=0.634, all movements < 0.10."""
        scores = (0.00125, 0.00125, 0.00125, 0.178532, 1.105703, -0.089266)
        policy = SystemAWPolicy(temperature=BETA, selection_mode="sample")
        rng = np.random.default_rng(42)
        result = policy.select(scores, self.OBS, rng)
        probs = result.policy_data["probabilities"]
        assert probs[4] == pytest.approx(0.634, abs=0.01)  # CONSUME
        for i in range(4):
            assert probs[i] < 0.10


# ===========================================================================
# Example Group D: Forage-Explore Cycle (Multi-Step Trajectory)
# ===========================================================================


class TestExampleD1:
    """D1: Forage-explore cycle starting at e=40."""

    def test_d1_step0_consume_dominates(self) -> None:
        """e=40, r_c=0.8 -> CONSUME score=0.614, movement~0.080."""
        d_h = 0.60
        weights = compute_drive_weights(d_h, _arb_config())
        assert weights.hunger_weight == pytest.approx(0.552, abs=0.005)
        assert weights.curiosity_weight == pytest.approx(0.160, abs=0.005)

        h_out = HungerDriveOutput(
            activation=d_h,
            action_contributions=(0.0, 0.0, 0.0, 0.0, 2.0, -0.1),
        )
        c_out = CuriosityDriveOutput(
            activation=1.0,
            spatial_novelty=(1.0, 1.0, 1.0, 1.0),
            sensory_novelty=(0.0, 0.0, 0.0, 0.0),
            composite_novelty=(0.50, 0.50, 0.50, 0.50),
            action_contributions=(0.50, 0.50, 0.50, 0.50, -0.3, -0.3),
        )
        scores = compute_action_scores(h_out, c_out, weights)
        assert scores[4] == pytest.approx(0.614, abs=0.005)  # CONSUME
        assert scores[0] == pytest.approx(0.080, abs=0.005)  # movement

    def test_d1_step0_energy_transition(self) -> None:
        """After CONSUME: e = 40 - 1 + 10 * 0.8 = 47."""
        from axis.sdk.world_types import ActionOutcome

        trans = SystemAWTransition(
            max_energy=E_MAX, move_cost=C_MOVE, consume_cost=C_CONSUME,
            stay_cost=C_STAY, energy_gain_factor=KAPPA,
        )
        state = AgentStateAW(
            energy=40.0,
            memory_state=MemoryState(entries=(), capacity=5),
            world_model=create_world_model(),
        )
        obs = _make_obs(0.8, 0.0, 0.0, 0.0, 0.0)
        outcome = ActionOutcome(
            action="consume", moved=False,
            new_position=Position(x=0, y=0),
            data={"consumed": True, "resource_consumed": 0.8},
        )
        result = trans.transition(state, outcome, obs)
        assert result.new_state.energy == pytest.approx(47.0, abs=0.005)

    def test_d1_step1_movement_dominates(self) -> None:
        """e=47, r_c=0 -> CONSUME negative, movement positive."""
        d_h = 0.53
        weights = compute_drive_weights(d_h, _arb_config())
        assert weights.hunger_weight == pytest.approx(0.497, abs=0.005)
        assert weights.curiosity_weight == pytest.approx(0.221, abs=0.005)

        h_out = HungerDriveOutput(
            activation=d_h,
            action_contributions=(0.0, 0.0, 0.0, 0.0, 0.0, -0.1),
        )
        c_out = CuriosityDriveOutput(
            activation=1.0,
            spatial_novelty=(1.0, 1.0, 1.0, 1.0),
            sensory_novelty=(0.0, 0.0, 0.0, 0.0),
            composite_novelty=(0.50, 0.50, 0.50, 0.50),
            action_contributions=(0.50, 0.50, 0.50, 0.50, -0.3, -0.3),
        )
        scores = compute_action_scores(h_out, c_out, weights)
        assert scores[4] < 0  # CONSUME negative (no resource)
        assert scores[0] > 0  # movement positive

    def test_d1_trajectory_summary(self) -> None:
        """4-step trajectory: verify energy and dominant drive at each step."""
        # Step 0: e=40, d_H=0.60, w_C=0.160, Hunger dominant
        w_d0 = compute_drive_weights(0.60, _arb_config())
        assert w_d0.curiosity_weight == pytest.approx(0.160, abs=0.005)
        # w_H * d_H = 0.552 * 0.60 = 0.3312
        # w_C * d_C = 0.160 * 1.0 = 0.160
        assert w_d0.hunger_weight * 0.60 > w_d0.curiosity_weight * 1.0

        # Step 1: e=47, d_H=0.53, w_C=0.221, Curiosity dominant
        w_d1 = compute_drive_weights(0.53, _arb_config())
        assert w_d1.curiosity_weight == pytest.approx(0.221, abs=0.005)

        # Step 2: e=46, d_H=0.54, w_C=0.212
        w_d2 = compute_drive_weights(0.54, _arb_config())
        assert w_d2.curiosity_weight == pytest.approx(0.212, abs=0.005)

        # Step 3: e=45, d_H=0.55, w_C=0.203
        w_d3 = compute_drive_weights(0.55, _arb_config())
        assert w_d3.curiosity_weight == pytest.approx(0.203, abs=0.005)


# ===========================================================================
# Example Group E: Parameter Sensitivity
# ===========================================================================


class TestExampleE1:
    """E1: Effect of gating sharpness gamma."""

    def test_e1_gamma_table(self) -> None:
        """For gamma in {0.5, 1.0, 2.0, 4.0}: verify w_H, w_C at d_H=0.5."""
        expected = [
            (0.5, 0.795, 0.707),
            (1.0, 0.650, 0.500),
            (2.0, 0.475, 0.250),
            (4.0, 0.344, 0.063),
        ]
        for gamma, exp_wh, exp_wc in expected:
            config = _arb_config(gamma=gamma)
            weights = compute_drive_weights(0.50, config)
            assert weights.hunger_weight == pytest.approx(
                exp_wh, abs=0.005), f"gamma={gamma}: w_H"
            assert weights.curiosity_weight == pytest.approx(
                exp_wc, abs=0.005), f"gamma={gamma}: w_C"


class TestExampleE2:
    """E2: Effect of spatial-sensory balance alpha."""

    def test_e2_alpha_table(self) -> None:
        """For alpha in {0.0, 0.5, 1.0}: verify composite novelty."""
        # Cell visited 3 times, r=0.8, memory mean r_bar=0.1
        nu_spatial = 1 / (1 + 3)  # 0.25
        nu_sensory = abs(0.8 - 0.1)  # 0.7

        expected = [
            (0.0, 0.700),  # pure sensory
            (0.5, 0.475),  # balanced
            (1.0, 0.250),  # pure spatial
        ]
        for alpha, exp_composite in expected:
            composite = compute_composite_novelty(
                (nu_spatial,), (nu_sensory,), alpha)
            assert composite[0] == pytest.approx(
                exp_composite, abs=0.005), f"alpha={alpha}"


# ===========================================================================
# Example Group F: World Model Mechanics
# ===========================================================================


class TestExampleF1:
    """F1: 6-step dead reckoning trajectory."""

    def test_f1_trajectory(self) -> None:
        """R, R, R(fail), U, L, L -> verify final state."""
        wm = create_world_model()  # origin (0,0), visit_count {(0,0):1}

        # Step 0: RIGHT, moved
        wm = update_world_model(wm, "right", True)
        assert wm.relative_position == (1, 0)

        # Step 1: RIGHT, moved
        wm = update_world_model(wm, "right", True)
        assert wm.relative_position == (2, 0)

        # Step 2: RIGHT, failed
        wm = update_world_model(wm, "right", False)
        assert wm.relative_position == (2, 0)

        # Step 3: UP, moved
        wm = update_world_model(wm, "up", True)
        assert wm.relative_position == (2, 1)

        # Step 4: LEFT, moved
        wm = update_world_model(wm, "left", True)
        assert wm.relative_position == (1, 1)

        # Step 5: LEFT, moved
        wm = update_world_model(wm, "left", True)
        assert wm.relative_position == (0, 1)

        # Verify visit counts
        visits = dict(wm.visit_counts)
        assert visits == {
            (0, 0): 1, (1, 0): 1, (2, 0): 2,
            (2, 1): 1, (1, 1): 1, (0, 1): 1,
        }

        # Spatial novelty at (0,1)
        spatial = compute_spatial_novelty(wm)
        # UP -> (0,2): unvisited -> 1.0
        assert spatial[0] == pytest.approx(1.0, abs=0.005)
        # DOWN -> (0,0): visited 1x -> 0.5
        assert spatial[1] == pytest.approx(0.5, abs=0.005)
        # LEFT -> (-1,1): unvisited -> 1.0
        assert spatial[2] == pytest.approx(1.0, abs=0.005)
        # RIGHT -> (1,1): visited 1x -> 0.5
        assert spatial[3] == pytest.approx(0.5, abs=0.005)


class TestExampleF2:
    """F2: Revisitation and novelty decay table."""

    def test_f2_decay_table(self) -> None:
        """For w in {0,1,2,3,5,10,20,100}: verify nu_spatial."""
        expected = [
            (0, 1.000), (1, 0.500), (2, 0.333), (3, 0.250),
            (5, 0.167), (10, 0.091), (20, 0.048), (100, 0.010),
        ]
        for visits, exp_nu in expected:
            nu = 1.0 / (1 + visits)
            assert nu == pytest.approx(exp_nu, abs=0.005), \
                f"visits={visits}"


class TestExampleF3:
    """F3: Stationary actions don't change position, increment visits."""

    def test_f3_stationary_actions(self) -> None:
        """3 actions (CONSUME, CONSUME, STAY) at (3,2) starting w=1."""
        # Build world model at (3,2) with visit count 1
        # Start at origin, move right 3, up 2 to reach (3,2)
        wm = create_world_model()
        for _ in range(3):
            wm = update_world_model(wm, "right", True)
        for _ in range(2):
            wm = update_world_model(wm, "up", True)
        assert wm.relative_position == (3, 2)
        assert dict(wm.visit_counts).get((3, 2)) == 1

        # CONSUME
        wm = update_world_model(wm, "consume", False)
        assert wm.relative_position == (3, 2)
        assert dict(wm.visit_counts).get((3, 2)) == 2

        # CONSUME again
        wm = update_world_model(wm, "consume", False)
        assert wm.relative_position == (3, 2)
        assert dict(wm.visit_counts).get((3, 2)) == 3

        # STAY
        wm = update_world_model(wm, "stay", False)
        assert wm.relative_position == (3, 2)
        assert dict(wm.visit_counts).get((3, 2)) == 4

        # Novelty at current position
        nu_self = 1.0 / (1 + 4)
        assert nu_self == pytest.approx(0.200, abs=0.005)


# ===========================================================================
# Full Pipeline Tests
# ===========================================================================


def _make_resource_grid(
    width: int, height: int, value: float = 0.5,
) -> list[list[Cell]]:
    return [
        [Cell(cell_type=CellType.RESOURCE, resource_value=value)
         for _ in range(width)]
        for _ in range(height)
    ]


def _make_empty_grid(width: int, height: int) -> list[list[Cell]]:
    return [
        [Cell(cell_type=CellType.EMPTY, resource_value=0.0)
         for _ in range(width)]
        for _ in range(height)
    ]


class TestFullPipeline:
    """Full pipeline tests through SystemAW.decide()."""

    def test_a1_full_pipeline(self) -> None:
        """A1 through full system: verify probabilities in decision_data."""
        config_dict = (
            _we_config_builder()
            .with_initial_energy(90.0)
            .build()
        )
        config = SystemAWConfig(**config_dict)
        system = SystemAW(config)
        state = system.initialize_state()

        # Build grid: all cells resource 0.0 except specific ones
        # A1: current(3,3) r=0.8, left(2,3) r=0.3, others 0.0
        grid = _make_empty_grid(10, 10)
        grid[3][3] = Cell(cell_type=CellType.RESOURCE, resource_value=0.8)
        grid[3][2] = Cell(cell_type=CellType.RESOURCE, resource_value=0.3)
        world = World(grid, Position(x=3, y=3))

        rng = np.random.default_rng(42)
        result = system.decide(world, state, rng)

        probs = result.decision_data["policy"]["probabilities"]
        # Movement should dominate
        movement_total = sum(probs[:4])
        assert movement_total > 0.85
        assert probs[4] < 0.10  # CONSUME low

    def test_c1_full_pipeline(self) -> None:
        """C1 through full system: CONSUME dominates."""
        config_dict = (
            _we_config_builder()
            .with_initial_energy(5.0)
            .build()
        )
        config = SystemAWConfig(**config_dict)
        system = SystemAW(config)
        state = system.initialize_state()

        # C1: current r=0.5, right r=0.2, others 0.0
        grid = _make_empty_grid(10, 10)
        grid[3][3] = Cell(cell_type=CellType.RESOURCE, resource_value=0.5)
        grid[3][4] = Cell(cell_type=CellType.RESOURCE, resource_value=0.2)
        world = World(grid, Position(x=3, y=3))

        rng = np.random.default_rng(42)
        result = system.decide(world, state, rng)

        probs = result.decision_data["policy"]["probabilities"]
        assert probs[4] > 0.5  # CONSUME dominates
