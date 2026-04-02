"""Tests for Action and SelectionMode enums."""

from axis_system_a import Action, SelectionMode


class TestAction:
    def test_has_exactly_six_members(self):
        assert len(Action) == 6

    def test_members_are_correct(self):
        assert set(Action.__members__.keys()) == {
            "UP",
            "DOWN",
            "LEFT",
            "RIGHT",
            "CONSUME",
            "STAY",
        }

    def test_stable_ordering(self):
        assert list(Action) == [
            Action.UP,
            Action.DOWN,
            Action.LEFT,
            Action.RIGHT,
            Action.CONSUME,
            Action.STAY,
        ]

    def test_integer_values(self):
        assert Action.UP == 0
        assert Action.DOWN == 1
        assert Action.LEFT == 2
        assert Action.RIGHT == 3
        assert Action.CONSUME == 4
        assert Action.STAY == 5

    def test_is_int_compatible(self):
        assert isinstance(Action.UP, int)
        assert Action.UP + 1 == 1

    def test_iteration_deterministic(self):
        first = list(Action)
        second = list(Action)
        assert first == second


class TestSelectionMode:
    def test_has_exactly_two_members(self):
        assert len(SelectionMode) == 2

    def test_values(self):
        assert SelectionMode.SAMPLE.value == "sample"
        assert SelectionMode.ARGMAX.value == "argmax"

    def test_from_string(self):
        assert SelectionMode("sample") == SelectionMode.SAMPLE
        assert SelectionMode("argmax") == SelectionMode.ARGMAX
