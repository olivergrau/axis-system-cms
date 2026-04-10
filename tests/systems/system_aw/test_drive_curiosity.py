"""WP-6 unit tests -- SystemAWCuriosityDrive."""

from __future__ import annotations

import pytest

from axis.systems.system_a.types import (
    CellObservation,
    BufferEntry,
    ObservationBuffer,
    Observation,
)
from axis.systems.system_aw.drive_curiosity import (
    SystemAWCuriosityDrive,
    compute_composite_novelty,
    compute_curiosity_activation,
    compute_novelty_saturation,
    compute_sensory_novelty,
    compute_spatial_novelty,
)
from axis.systems.system_aw.types import CuriosityDriveOutput, WorldModelState
from axis.systems.system_aw.world_model import create_world_model


def _make_observation(
    current_r: float = 0.0,
    up_r: float = 0.0,
    down_r: float = 0.0,
    left_r: float = 0.0,
    right_r: float = 0.0,
) -> Observation:
    return Observation(
        current=CellObservation(traversability=1.0, resource=current_r),
        up=CellObservation(traversability=1.0, resource=up_r),
        down=CellObservation(traversability=1.0, resource=down_r),
        left=CellObservation(traversability=1.0, resource=left_r),
        right=CellObservation(traversability=1.0, resource=right_r),
    )


def _make_memory(
    observations: list[Observation],
    capacity: int = 5,
) -> ObservationBuffer:
    entries = tuple(
        BufferEntry(timestep=t, observation=obs)
        for t, obs in enumerate(observations)
    )
    return ObservationBuffer(entries=entries, capacity=capacity)


def _empty_buffer(capacity: int = 5) -> ObservationBuffer:
    return ObservationBuffer(entries=(), capacity=capacity)


class TestSpatialNovelty:
    """Spatial novelty computation tests."""

    def test_spatial_novelty_all_unvisited(self) -> None:
        wm = create_world_model()
        result = compute_spatial_novelty(wm)
        assert all(n == pytest.approx(1.0) for n in result)

    def test_spatial_novelty_mixed(self) -> None:
        wm = WorldModelState(
            relative_position=(0, 0),
            visit_counts=(((0, 0), 1), ((1, 0), 3)),
        )
        result = compute_spatial_novelty(wm)
        # UP=(0,1) unvisited, DOWN=(0,-1) unvisited, LEFT=(-1,0) unvisited
        assert result[0] == pytest.approx(1.0)   # UP
        assert result[1] == pytest.approx(1.0)   # DOWN
        assert result[2] == pytest.approx(1.0)   # LEFT
        assert result[3] == pytest.approx(0.25)  # RIGHT: 1/(1+3)


class TestSensoryNovelty:
    """Sensory novelty computation tests."""

    def test_sensory_novelty_empty_buffer(self) -> None:
        obs = _make_observation(up_r=0.3, left_r=0.7)
        result = compute_sensory_novelty(obs, _empty_buffer())
        assert result == pytest.approx((0.3, 0.0, 0.7, 0.0))

    def test_sensory_novelty_matching_buffer(self) -> None:
        obs = _make_observation(up_r=0.3, down_r=0.5)
        mem_obs = _make_observation(up_r=0.3, down_r=0.5)
        memory = _make_memory([mem_obs])
        result = compute_sensory_novelty(obs, memory)
        assert all(n == pytest.approx(0.0) for n in result)

    def test_sensory_novelty_divergent(self) -> None:
        obs = _make_observation(up_r=0.5, down_r=0.2)
        mem_obs = _make_observation(up_r=0.1, down_r=0.6)
        memory = _make_memory([mem_obs])
        result = compute_sensory_novelty(obs, memory)
        assert result[0] == pytest.approx(0.4)   # |0.5 - 0.1|
        assert result[1] == pytest.approx(0.4)   # |0.2 - 0.6|


class TestCompositeNovelty:
    """Composite novelty blending tests."""

    def test_composite_alpha_one(self) -> None:
        spatial = (1.0, 0.5, 0.25, 0.0)
        sensory = (0.0, 0.3, 0.7, 0.9)
        result = compute_composite_novelty(spatial, sensory, alpha=1.0)
        assert result == pytest.approx(spatial)

    def test_composite_alpha_zero(self) -> None:
        spatial = (1.0, 0.5, 0.25, 0.0)
        sensory = (0.0, 0.3, 0.7, 0.9)
        result = compute_composite_novelty(spatial, sensory, alpha=0.0)
        assert result == pytest.approx(sensory)

    def test_composite_alpha_half(self) -> None:
        spatial = (1.0, 0.5, 0.25, 0.0)
        sensory = (0.0, 0.3, 0.7, 0.9)
        result = compute_composite_novelty(spatial, sensory, alpha=0.5)
        expected = (0.5, 0.4, 0.475, 0.45)
        assert result == pytest.approx(expected)


class TestNoveltySaturation:
    """Novelty saturation computation tests."""

    def test_saturation_empty_buffer(self) -> None:
        assert compute_novelty_saturation(_empty_buffer()) == 0.0

    def test_saturation_identical_entries(self) -> None:
        obs = _make_observation(up_r=0.5, down_r=0.5, left_r=0.5, right_r=0.5)
        memory = _make_memory([obs, obs, obs])
        assert compute_novelty_saturation(memory) == pytest.approx(0.0)

    def test_saturation_diverse_entries(self) -> None:
        obs1 = _make_observation(up_r=0.0, down_r=0.0, left_r=0.0, right_r=0.0)
        obs2 = _make_observation(up_r=1.0, down_r=1.0, left_r=1.0, right_r=1.0)
        memory = _make_memory([obs1, obs2])
        result = compute_novelty_saturation(memory)
        assert result > 0.0
        # dir_means = [0.5, 0.5, 0.5, 0.5]
        # obs1 sigma: mean(|0-0.5|*4) = 0.5
        # obs2 sigma: mean(|1-0.5|*4) = 0.5
        # nu_bar = (0.5 + 0.5) / 2 = 0.5
        assert result == pytest.approx(0.5)


class TestDriveActivation:
    """Curiosity drive activation tests."""

    def test_activation_max(self) -> None:
        assert compute_curiosity_activation(1.0, 0.0) == pytest.approx(1.0)

    def test_activation_zero_base(self) -> None:
        assert compute_curiosity_activation(0.0, 0.5) == pytest.approx(0.0)

    def test_activation_partial(self) -> None:
        assert compute_curiosity_activation(1.0, 0.3) == pytest.approx(0.7)


class TestActionContributions:
    """Action contribution tests."""

    def test_movement_contributions_equal_composite(self) -> None:
        drive = SystemAWCuriosityDrive(
            base_curiosity=1.0,
            spatial_sensory_balance=0.5,
            explore_suppression=0.3,
        )
        wm = create_world_model()
        obs = _make_observation(up_r=0.4, left_r=0.6)
        out = drive.compute(obs, _empty_buffer(), wm)
        # Movement contributions = composite novelty
        assert out.action_contributions[0] == pytest.approx(
            out.composite_novelty[0])
        assert out.action_contributions[1] == pytest.approx(
            out.composite_novelty[1])
        assert out.action_contributions[2] == pytest.approx(
            out.composite_novelty[2])
        assert out.action_contributions[3] == pytest.approx(
            out.composite_novelty[3])

    def test_consume_suppressed(self) -> None:
        drive = SystemAWCuriosityDrive(
            base_curiosity=1.0,
            spatial_sensory_balance=0.5,
            explore_suppression=0.3,
        )
        out = drive.compute(_make_observation(),
                            _empty_buffer(), create_world_model())
        assert out.action_contributions[4] == pytest.approx(-0.3)

    def test_stay_suppressed(self) -> None:
        drive = SystemAWCuriosityDrive(
            base_curiosity=1.0,
            spatial_sensory_balance=0.5,
            explore_suppression=0.3,
        )
        out = drive.compute(_make_observation(),
                            _empty_buffer(), create_world_model())
        assert out.action_contributions[5] == pytest.approx(-0.3)


class TestFullPipeline:
    """Full pipeline tests."""

    def test_full_pipeline_output_type(self) -> None:
        drive = SystemAWCuriosityDrive(
            base_curiosity=1.0,
            spatial_sensory_balance=0.5,
            explore_suppression=0.3,
        )
        out = drive.compute(_make_observation(),
                            _empty_buffer(), create_world_model())
        assert isinstance(out, CuriosityDriveOutput)

    def test_full_pipeline_all_fields_present(self) -> None:
        drive = SystemAWCuriosityDrive(
            base_curiosity=1.0,
            spatial_sensory_balance=0.5,
            explore_suppression=0.3,
        )
        out = drive.compute(_make_observation(),
                            _empty_buffer(), create_world_model())
        assert len(out.spatial_novelty) == 4
        assert len(out.sensory_novelty) == 4
        assert len(out.composite_novelty) == 4
        assert len(out.action_contributions) == 6
        assert 0.0 <= out.activation <= 1.0


class TestWorkedExamples:
    """Worked example verification."""

    def test_example_a1_curiosity(self) -> None:
        """A1: e=90, all unvisited, empty observation buffer."""
        drive = SystemAWCuriosityDrive(
            base_curiosity=1.0,
            spatial_sensory_balance=0.5,
            explore_suppression=0.3,
        )
        wm = create_world_model()
        obs = _make_observation(
            current_r=0.8, up_r=0.0, down_r=0.0, left_r=0.3, right_r=0.0,
        )
        out = drive.compute(obs, _empty_buffer(), wm)

        assert out.activation == pytest.approx(1.0, abs=0.01)
        assert out.spatial_novelty == pytest.approx((1.0, 1.0, 1.0, 1.0))
        assert out.sensory_novelty == pytest.approx((0.0, 0.0, 0.3, 0.0))
        assert out.composite_novelty == pytest.approx(
            (0.50, 0.50, 0.65, 0.50), abs=0.01,
        )
        assert out.action_contributions[:4] == pytest.approx(
            (0.50, 0.50, 0.65, 0.50), abs=0.01,
        )
        assert out.action_contributions[4] == pytest.approx(-0.3, abs=0.01)
        assert out.action_contributions[5] == pytest.approx(-0.3, abs=0.01)

    def test_example_b1_curiosity(self) -> None:
        """B1: observation buffer with 3 entries, all neighbors visited once."""
        drive = SystemAWCuriosityDrive(
            base_curiosity=1.0,
            spatial_sensory_balance=0.5,
            explore_suppression=0.3,
        )
        # World model: current visited 3 times, neighbors visited once
        wm = WorldModelState(
            relative_position=(0, 0),
            visit_counts=(
                ((-1, 0), 1),
                ((0, -1), 1),
                ((0, 0), 3),
                ((0, 1), 1),
                ((1, 0), 1),
            ),
        )
        obs = Observation(
            current=CellObservation(traversability=1.0, resource=0.6),
            up=CellObservation(traversability=1.0, resource=0.0),
            down=CellObservation(traversability=1.0, resource=0.4),
            left=CellObservation(traversability=0.0, resource=0.0),
            right=CellObservation(traversability=1.0, resource=0.0),
        )
        # Observation buffer: 3 entries with mean r_dir: up=0.1, down=0.0, left=0.2, right=0.0
        mem_obs1 = _make_observation(
            up_r=0.3, down_r=0.0, left_r=0.6, right_r=0.0)
        mem_obs2 = _make_observation(
            up_r=0.0, down_r=0.0, left_r=0.0, right_r=0.0)
        mem_obs3 = _make_observation(
            up_r=0.0, down_r=0.0, left_r=0.0, right_r=0.0)
        memory = _make_memory([mem_obs1, mem_obs2, mem_obs3])

        out = drive.compute(obs, memory, wm)

        # Spatial: all 0.500 (visited once)
        assert out.spatial_novelty == pytest.approx(
            (0.50, 0.50, 0.50, 0.50), abs=0.01)
        # Sensory: |0.0 - 0.1|=0.1, |0.4 - 0.0|=0.4, |0.0 - 0.2|=0.2, |0.0 - 0.0|=0.0
        assert out.sensory_novelty == pytest.approx(
            (0.1, 0.4, 0.2, 0.0), abs=0.01)
        # Composite (alpha=0.5): (0.30, 0.45, 0.35, 0.25)
        assert out.composite_novelty == pytest.approx(
            (0.30, 0.45, 0.35, 0.25), abs=0.01,
        )

    def test_example_c1_curiosity(self) -> None:
        """C1: contributions are tiny despite high composite."""
        drive = SystemAWCuriosityDrive(
            base_curiosity=1.0,
            spatial_sensory_balance=0.5,
            explore_suppression=0.3,
        )
        wm = create_world_model()
        obs = _make_observation(
            current_r=0.5, up_r=0.0, down_r=0.0, left_r=0.0, right_r=0.2,
        )
        out = drive.compute(obs, _empty_buffer(), wm)
        # phi_C values are the composite novelty values
        # They are NOT yet scaled by w_C * d_C (that's arbitration, WP-7)
        assert out.composite_novelty[0] == pytest.approx(0.50, abs=0.01)  # UP
        assert out.composite_novelty[3] == pytest.approx(
            0.60, abs=0.01)  # RIGHT

    def test_example_e2_alpha_sensitivity(self) -> None:
        """E2: composite novelty for alpha=0.0, 0.5, 1.0."""
        spatial = (0.25, 0.25, 0.25, 0.25)  # visited 3 times -> 1/4
        sensory = (0.7, 0.7, 0.7, 0.7)      # resource difference

        c0 = compute_composite_novelty(spatial, sensory, alpha=0.0)
        assert c0 == pytest.approx((0.7, 0.7, 0.7, 0.7))

        c5 = compute_composite_novelty(spatial, sensory, alpha=0.5)
        assert c5 == pytest.approx((0.475, 0.475, 0.475, 0.475))

        c1 = compute_composite_novelty(spatial, sensory, alpha=1.0)
        assert c1 == pytest.approx((0.25, 0.25, 0.25, 0.25))


class TestReduction:
    """Reduction and boundary condition tests."""

    def test_zero_base_curiosity(self) -> None:
        drive = SystemAWCuriosityDrive(
            base_curiosity=0.0,
            spatial_sensory_balance=0.5,
            explore_suppression=0.3,
        )
        out = drive.compute(_make_observation(),
                            _empty_buffer(), create_world_model())
        assert out.activation == pytest.approx(0.0)

    def test_alpha_one_no_memory_dependency(self) -> None:
        """alpha=1.0: composite independent of observation buffer content."""
        drive = SystemAWCuriosityDrive(
            base_curiosity=1.0,
            spatial_sensory_balance=1.0,
            explore_suppression=0.3,
        )
        wm = create_world_model()
        obs = _make_observation(up_r=0.5)

        out1 = drive.compute(obs, _empty_buffer(), wm)
        mem_obs = _make_observation(
            up_r=0.9, down_r=0.8, left_r=0.7, right_r=0.6)
        out2 = drive.compute(obs, _make_memory([mem_obs]), wm)

        # Composite novelty should be identical (pure spatial)
        assert out1.composite_novelty == pytest.approx(out2.composite_novelty)

    def test_alpha_zero_no_world_model_dependency(self) -> None:
        """alpha=0.0: composite independent of visit counts."""
        drive = SystemAWCuriosityDrive(
            base_curiosity=1.0,
            spatial_sensory_balance=0.0,
            explore_suppression=0.3,
        )
        obs = _make_observation(up_r=0.5)
        memory = _empty_buffer()

        wm1 = create_world_model()
        wm2 = WorldModelState(
            relative_position=(0, 0),
            visit_counts=(((0, 0), 1), ((0, 1), 10), ((1, 0), 5)),
        )

        out1 = drive.compute(obs, memory, wm1)
        out2 = drive.compute(obs, memory, wm2)

        assert out1.composite_novelty == pytest.approx(out2.composite_novelty)
