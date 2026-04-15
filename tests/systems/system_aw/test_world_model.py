"""WP-4 unit tests -- spatial world model."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from axis.systems.construction_kit.memory.types import WorldModelState
from axis.systems.construction_kit.memory.world_model import (
    all_spatial_novelties,
    create_world_model,
    get_neighbor_position,
    get_visit_count,
    spatial_novelty,
    update_world_model,
)


class TestCreation:
    """World model creation tests."""

    def test_create_initial_state(self) -> None:
        wm = create_world_model()
        assert wm.relative_position == (0, 0)
        assert get_visit_count(wm, (0, 0)) == 1

    def test_create_empty_elsewhere(self) -> None:
        wm = create_world_model()
        assert get_visit_count(wm, (1, 0)) == 0
        assert get_visit_count(wm, (0, 1)) == 0
        assert get_visit_count(wm, (-1, -1)) == 0


class TestDeadReckoning:
    """Dead reckoning position update tests."""

    def test_move_right_updates_position(self) -> None:
        wm = create_world_model()
        wm = update_world_model(wm, "right", moved=True)
        assert wm.relative_position == (1, 0)

    def test_move_up_updates_position(self) -> None:
        wm = create_world_model()
        wm = update_world_model(wm, "up", moved=True)
        assert wm.relative_position == (0, 1)

    def test_move_left_updates_position(self) -> None:
        wm = create_world_model()
        wm = update_world_model(wm, "left", moved=True)
        assert wm.relative_position == (-1, 0)

    def test_move_down_updates_position(self) -> None:
        wm = create_world_model()
        wm = update_world_model(wm, "down", moved=True)
        assert wm.relative_position == (0, -1)

    def test_failed_move_position_unchanged(self) -> None:
        wm = create_world_model()
        wm = update_world_model(wm, "right", moved=False)
        assert wm.relative_position == (0, 0)

    def test_failed_move_increments_visit(self) -> None:
        wm = create_world_model()
        wm = update_world_model(wm, "right", moved=False)
        assert get_visit_count(wm, (0, 0)) == 2

    def test_consume_position_unchanged(self) -> None:
        wm = create_world_model()
        wm = update_world_model(wm, "consume", moved=False)
        assert wm.relative_position == (0, 0)
        assert get_visit_count(wm, (0, 0)) == 2

    def test_stay_position_unchanged(self) -> None:
        wm = create_world_model()
        wm = update_world_model(wm, "stay", moved=False)
        assert wm.relative_position == (0, 0)
        assert get_visit_count(wm, (0, 0)) == 2

    def test_unknown_action_raises(self) -> None:
        wm = create_world_model()
        with pytest.raises(ValueError, match="Unknown action"):
            update_world_model(wm, "fly", moved=True)


class TestSpatialNovelty:
    """Spatial novelty computation tests."""

    def test_novelty_unvisited(self) -> None:
        wm = create_world_model()
        assert spatial_novelty(wm, "up") == pytest.approx(1.0)

    def test_novelty_visited_once(self) -> None:
        wm = create_world_model()
        wm = update_world_model(wm, "right", moved=True)
        # Now at (1,0). Origin (0,0) is to the left, visited once.
        assert spatial_novelty(wm, "left") == pytest.approx(0.5)

    def test_novelty_visited_n_times(self) -> None:
        wm = WorldModelState(
            relative_position=(0, 0),
            visit_counts=(((0, 0), 1), ((1, 0), 4)),
        )
        assert spatial_novelty(wm, "right") == pytest.approx(0.2)

    def test_novelty_all_directions(self) -> None:
        wm = create_world_model()
        novelties = all_spatial_novelties(wm)
        assert len(novelties) == 4
        assert all(n == pytest.approx(1.0) for n in novelties)


class TestWorkedExamples:
    """Worked example F1, F2, F3 verification tests."""

    def test_f1_full_trajectory(self) -> None:
        """6-step trajectory from Example F1."""
        wm = create_world_model()

        # Step 0: RIGHT, moved=True -> (1, 0)
        wm = update_world_model(wm, "right", moved=True)
        assert wm.relative_position == (1, 0)
        assert get_visit_count(wm, (1, 0)) == 1

        # Step 1: RIGHT, moved=True -> (2, 0)
        wm = update_world_model(wm, "right", moved=True)
        assert wm.relative_position == (2, 0)
        assert get_visit_count(wm, (2, 0)) == 1

        # Step 2: RIGHT, moved=False (wall) -> stays (2, 0)
        wm = update_world_model(wm, "right", moved=False)
        assert wm.relative_position == (2, 0)
        assert get_visit_count(wm, (2, 0)) == 2

        # Step 3: UP, moved=True -> (2, 1)
        wm = update_world_model(wm, "up", moved=True)
        assert wm.relative_position == (2, 1)
        assert get_visit_count(wm, (2, 1)) == 1

        # Step 4: LEFT, moved=True -> (1, 1)
        wm = update_world_model(wm, "left", moved=True)
        assert wm.relative_position == (1, 1)
        assert get_visit_count(wm, (1, 1)) == 1

        # Step 5: LEFT, moved=True -> (0, 1)
        wm = update_world_model(wm, "left", moved=True)
        assert wm.relative_position == (0, 1)
        assert get_visit_count(wm, (0, 1)) == 1

        # Verify spatial novelties at final position (0, 1)
        assert spatial_novelty(wm, "up") == pytest.approx(
            1.0)      # (0, 2) unvisited
        assert spatial_novelty(wm, "down") == pytest.approx(
            0.5)    # (0, 0) visited 1
        assert spatial_novelty(wm, "left") == pytest.approx(
            1.0)    # (-1, 1) unvisited
        assert spatial_novelty(wm, "right") == pytest.approx(
            0.5)   # (1, 1) visited 1

    def test_f2_novelty_decay_table(self) -> None:
        """Verify spatial novelty for various visit counts."""
        expected = [
            (0, 1.000),
            (1, 0.500),
            (2, 0.333),
            (3, 0.250),
            (5, 0.167),
            (10, 0.091),
            (20, 0.048),
            (100, 0.010),
        ]
        for w, expected_nu in expected:
            visits = (((0, 0), 1),)
            if w > 0:
                visits = (((0, 0), 1), ((1, 0), w))
            else:
                visits = (((0, 0), 1),)
            wm = WorldModelState(relative_position=(0, 0), visit_counts=visits)
            nu = spatial_novelty(wm, "right")
            assert nu == pytest.approx(expected_nu, abs=0.001), (
                f"w={w}: expected {expected_nu}, got {nu}"
            )

    def test_f3_consume_then_stay(self) -> None:
        """3 stationary actions at (3,2), verifying visit count increment."""
        wm = WorldModelState(
            relative_position=(3, 2),
            visit_counts=(((3, 2), 1),),
        )

        # CONSUME -> w=2
        wm = update_world_model(wm, "consume", moved=False)
        assert wm.relative_position == (3, 2)
        assert get_visit_count(wm, (3, 2)) == 2

        # CONSUME -> w=3
        wm = update_world_model(wm, "consume", moved=False)
        assert get_visit_count(wm, (3, 2)) == 3

        # STAY -> w=4
        wm = update_world_model(wm, "stay", moved=False)
        assert get_visit_count(wm, (3, 2)) == 4
        assert wm.relative_position == (3, 2)

        # Novelty at current position's neighbors (all unvisited)
        assert spatial_novelty(wm, "up") == pytest.approx(1.0)


class TestImmutability:
    """State immutability tests."""

    def test_update_returns_new_state(self) -> None:
        wm = create_world_model()
        new_wm = update_world_model(wm, "right", moved=True)
        assert wm is not new_wm
        assert wm.relative_position == (0, 0)
        assert new_wm.relative_position == (1, 0)

    def test_state_is_frozen(self) -> None:
        wm = create_world_model()
        with pytest.raises(ValidationError):
            wm.relative_position = (1, 1)  # type: ignore[misc]
