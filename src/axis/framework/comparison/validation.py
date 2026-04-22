"""Strict pair validation for episode traces (WP-02)."""

from __future__ import annotations

from axis.framework.comparison.types import PairValidationResult, PairingMode
from axis.framework.persistence import RunMetadata
from axis.framework.run import RunConfig
from axis.sdk.trace import BaseEpisodeTrace


def _derive_episode_seed(
    base_seed: int | None, episode_index: int | None,
) -> int | None:
    if base_seed is None or episode_index is None:
        return None
    return base_seed + episode_index


def validate_trace_pair(
    reference: BaseEpisodeTrace,
    candidate: BaseEpisodeTrace,
    *,
    allow_world_changes: bool = False,
    reference_run_config: RunConfig | None = None,
    candidate_run_config: RunConfig | None = None,
    reference_run_metadata: RunMetadata | None = None,
    candidate_run_metadata: RunMetadata | None = None,
    reference_episode_index: int | None = None,
    candidate_episode_index: int | None = None,
) -> tuple[PairValidationResult, PairingMode | None, int | None]:
    """Validate that two episode traces form a valid comparison pair.

    Returns (validation_result, pairing_mode, episode_seed).
    """
    errors: list[str] = []

    # World type
    world_type_match = reference.world_type == candidate.world_type
    if not world_type_match:
        errors.append("world_type_mismatch")

    # World config
    world_config_match = reference.world_config == candidate.world_config
    if not world_config_match and not allow_world_changes:
        errors.append("world_config_mismatch")

    # Start position
    ref_start = reference.steps[0].agent_position_before if reference.steps else None
    cand_start = candidate.steps[0].agent_position_before if candidate.steps else None
    start_position_match = ref_start == cand_start
    if not start_position_match:
        errors.append("start_position_mismatch")

    # Episode seed — try explicit first, then derived
    pairing_mode: PairingMode | None = None
    episode_seed: int | None = None
    episode_seed_match: bool | None = None

    ref_base = reference_run_config.base_seed if reference_run_config else None
    cand_base = candidate_run_config.base_seed if candidate_run_config else None

    ref_seed = _derive_episode_seed(ref_base, reference_episode_index)
    cand_seed = _derive_episode_seed(cand_base, candidate_episode_index)

    if ref_seed is not None and cand_seed is not None:
        episode_seed_match = ref_seed == cand_seed
        if episode_seed_match:
            pairing_mode = PairingMode.DERIVED_SEED
            episode_seed = ref_seed
        else:
            errors.append("episode_seed_mismatch")

    # Shared action labels
    ref_actions = {s.action for s in reference.steps}
    cand_actions = {s.action for s in candidate.steps}
    shared = sorted(ref_actions & cand_actions)
    if not shared and (ref_actions or cand_actions):
        errors.append("action_space_no_shared_labels")

    is_valid = len(errors) == 0

    validation = PairValidationResult(
        is_valid_pair=is_valid,
        errors=tuple(errors),
        world_type_match=world_type_match,
        world_config_match=world_config_match,
        start_position_match=start_position_match,
        episode_seed_match=episode_seed_match,
        shared_action_labels=tuple(shared),
    )
    return validation, pairing_mode, episode_seed
