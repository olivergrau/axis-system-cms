"""Tests for plugin discovery → catalog bridge — WP-05."""

from __future__ import annotations

from pathlib import Path

from axis.plugins import discover_plugins


class TestPluginCatalogBridge:
    """After discovery, catalogs reflect plugin registrations."""

    def test_catalogs_populated_after_discovery(self, tmp_path: Path) -> None:
        discover_plugins()
        from axis.framework.catalogs import build_catalogs_from_registries

        catalogs = build_catalogs_from_registries()
        # system_a is always registered by the built-in plugin.
        assert "system_a" in catalogs["systems"]

    def test_context_has_catalogs(self, tmp_path: Path) -> None:
        discover_plugins()
        from axis.framework.cli.context import build_context

        ctx = build_context(tmp_path)
        assert "systems" in ctx.catalogs
        assert len(ctx.catalogs["systems"]) > 0

    def test_catalog_matches_global_registry(self) -> None:
        discover_plugins()
        from axis.framework.catalogs import build_catalogs_from_registries
        from axis.framework.registry import _SYSTEM_REGISTRY

        catalogs = build_catalogs_from_registries()
        for key in _SYSTEM_REGISTRY:
            assert key in catalogs["systems"]
