"""Tests for catalog abstractions — WP-04."""

from __future__ import annotations

import pytest

from axis.framework.catalogs import Catalog


class TestCatalog:

    def test_register_and_get(self) -> None:
        cat = Catalog[str]("test")
        cat.register("a", "value_a")
        assert cat.get("a") == "value_a"

    def test_duplicate_raises(self) -> None:
        cat = Catalog[str]("test")
        cat.register("a", "v1")
        with pytest.raises(ValueError, match="Duplicate"):
            cat.register("a", "v2")

    def test_missing_raises_keyerror(self) -> None:
        cat = Catalog[str]("test")
        with pytest.raises(KeyError, match="not found"):
            cat.get("missing")

    def test_get_optional_returns_none(self) -> None:
        cat = Catalog[str]("test")
        assert cat.get_optional("missing") is None

    def test_get_optional_returns_value(self) -> None:
        cat = Catalog[str]("test")
        cat.register("a", "v")
        assert cat.get_optional("a") == "v"

    def test_contains(self) -> None:
        cat = Catalog[str]("test")
        cat.register("a", "v")
        assert "a" in cat
        assert "b" not in cat

    def test_len(self) -> None:
        cat = Catalog[str]("test")
        assert len(cat) == 0
        cat.register("a", "v")
        assert len(cat) == 1

    def test_keys(self) -> None:
        cat = Catalog[str]("test")
        cat.register("b", "v1")
        cat.register("a", "v2")
        assert set(cat.keys()) == {"a", "b"}

    def test_name(self) -> None:
        cat = Catalog[str]("my_catalog")
        assert cat.name == "my_catalog"


class TestBuildCatalogsFromRegistries:
    """Verify bridge from global registries populates catalogs."""

    def test_builds_all_five(self) -> None:
        from axis.plugins import discover_plugins
        discover_plugins()

        from axis.framework.catalogs import build_catalogs_from_registries
        catalogs = build_catalogs_from_registries()

        assert "systems" in catalogs
        assert "worlds" in catalogs
        assert "world_vis" in catalogs
        assert "system_vis" in catalogs
        assert "comparison_extensions" in catalogs

        # At least one system should be registered after plugin discovery.
        assert len(catalogs["systems"]) > 0

    def test_world_vis_preserves_split(self) -> None:
        from axis.plugins import discover_plugins
        discover_plugins()

        from axis.framework.catalogs import build_catalogs_from_registries
        catalogs = build_catalogs_from_registries()

        # world_vis and system_vis are separate catalogs.
        assert catalogs["world_vis"].name != catalogs["system_vis"].name
