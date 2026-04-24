"""Tests for behavioral metric extension registration and dispatch."""

from __future__ import annotations

from axis.framework.catalogs import build_catalogs_from_registries
from axis.framework.metrics.extensions import (
    build_system_behavior_metrics,
    register_metric_extension,
    registered_metric_extensions,
)
from axis.framework.metrics.types import StandardBehaviorMetrics, MetricSummaryStats
from axis.sdk.trace import BaseEpisodeTrace


def _standard_metrics() -> StandardBehaviorMetrics:
    stats = MetricSummaryStats(mean=1.0, std=0.0, min=1.0, max=1.0, n=1)
    return StandardBehaviorMetrics(
        mean_steps=1.0,
        death_rate=0.0,
        mean_final_vitality=1.0,
        resource_gain_per_step=stats,
        net_energy_efficiency=stats,
        successful_consume_rate=stats,
        consume_on_empty_rate=stats,
        failed_movement_rate=stats,
        action_entropy=stats,
        policy_sharpness=stats,
        action_inertia=stats,
        unique_cells_visited=stats,
        coverage_efficiency=stats,
        revisit_rate=stats,
    )


class TestMetricExtensions:
    def test_registered_metric_extensions_contains_system_c(self) -> None:
        import axis.systems.system_c.metrics  # noqa: F401

        assert "system_c" in registered_metric_extensions()

    def test_build_system_behavior_metrics_returns_none_when_missing(self) -> None:
        result = build_system_behavior_metrics(
            "no_such_system",
            (),
            _standard_metrics(),
        )
        assert result is None

    def test_metric_extension_dispatch_uses_catalog(self) -> None:
        @register_metric_extension("test_metric_ext")
        def _ext(
            episode_traces: tuple[BaseEpisodeTrace, ...],
            standard_metrics: object,
        ) -> dict[str, object]:
            del episode_traces, standard_metrics
            return {"test_metric_ext": {"ok": True}}

        catalogs = build_catalogs_from_registries()
        result = build_system_behavior_metrics(
            "test_metric_ext",
            (),
            _standard_metrics(),
            extension_catalog=catalogs["metric_extensions"],
        )
        assert result == {"test_metric_ext": {"ok": True}}
