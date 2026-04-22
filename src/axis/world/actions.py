"""Action engine: registry, built-in handlers, and dispatch."""

from __future__ import annotations

from typing import Any, Protocol

from axis.sdk.actions import BASE_ACTIONS, MOVEMENT_DELTAS
from axis.sdk.position import Position
from axis.sdk.world_types import ActionOutcome, MutableWorldProtocol


def _canonicalize_position(world: MutableWorldProtocol, position: Position) -> Position:
    """Return a world-canonical position when the world exposes one."""
    canonicalize = getattr(world, "canonicalize_position", None)
    if callable(canonicalize):
        return canonicalize(position)
    return position


class ActionHandler(Protocol):
    """Protocol for action handlers.

    Action handlers receive the world and a context dict,
    mutate the world, and return an ActionOutcome.
    """

    def __call__(
        self,
        world: MutableWorldProtocol,
        *,
        context: dict[str, Any],
    ) -> ActionOutcome: ...


def _handle_movement(
    world: MutableWorldProtocol,
    action: str,
    *,
    context: dict[str, Any],
) -> ActionOutcome:
    """Handle a movement action (up/down/left/right).

    Attempts to move the agent in the specified direction.
    Movement succeeds if the target cell is within bounds and traversable.
    """
    delta = MOVEMENT_DELTAS[action]
    pos = world.agent_position
    target = _canonicalize_position(
        world,
        Position(x=pos.x + delta[0], y=pos.y + delta[1]),
    )

    if world.is_within_bounds(target) and world.is_traversable(target):
        world.agent_position = target
        return ActionOutcome(action=action, moved=True, new_position=target)

    return ActionOutcome(action=action, moved=False, new_position=pos)


def _handle_stay(
    world: MutableWorldProtocol,
    *,
    context: dict[str, Any],
) -> ActionOutcome:
    """Handle the stay action. No world mutation."""
    return ActionOutcome(
        action="stay",
        moved=False,
        new_position=world.agent_position,
    )


def _make_movement_handler(action_name: str) -> ActionHandler:
    """Create a movement handler bound to a specific direction."""

    def handler(world: MutableWorldProtocol, *, context: dict[str, Any]) -> ActionOutcome:
        return _handle_movement(world, action_name, context=context)

    return handler  # type: ignore[return-value]


class ActionRegistry:
    """Registry for action handlers.

    Base actions (movement + stay) are registered automatically.
    Systems register additional handlers for custom actions.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, ActionHandler] = {}
        # Register built-in handlers
        for action_name in MOVEMENT_DELTAS:
            self._handlers[action_name] = _make_movement_handler(action_name)
        self._handlers["stay"] = _handle_stay  # type: ignore[assignment]

    def register(self, action_name: str, handler: ActionHandler) -> None:
        """Register a handler for a custom action.

        Raises ValueError if action_name is a base action (cannot override).
        Raises ValueError if a handler is already registered for this action.
        """
        if action_name in BASE_ACTIONS:
            raise ValueError(
                f"Cannot override base action handler: {action_name}"
            )
        if action_name in self._handlers:
            raise ValueError(
                f"Handler already registered for action: {action_name}"
            )
        self._handlers[action_name] = handler

    def has_handler(self, action_name: str) -> bool:
        """Check if a handler is registered for the given action."""
        return action_name in self._handlers

    @property
    def registered_actions(self) -> tuple[str, ...]:
        """Return all registered action names."""
        return tuple(self._handlers.keys())

    def apply(
        self,
        world: MutableWorldProtocol,
        action: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> ActionOutcome:
        """Apply an action to the world.

        Dispatches to the registered handler for the given action name.
        Raises KeyError if no handler is registered.
        """
        if action not in self._handlers:
            raise KeyError(f"No handler registered for action: {action}")
        handler = self._handlers[action]
        return handler(world, context=context or {})


def create_action_registry() -> ActionRegistry:
    """Create a new ActionRegistry with base actions pre-registered."""
    return ActionRegistry()
