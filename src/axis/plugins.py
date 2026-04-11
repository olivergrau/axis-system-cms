"""Plugin discovery -- entry points and axis-plugins.yaml.

The framework owns only the generic registry mechanism (register, lookup, list).
This module owns the act of populating registries from discovered plugins.

Discovery sources (checked in order):
1. Setuptools entry points (``axis.plugins`` group) — for installed packages.
2. ``axis-plugins.yaml`` — for local development / unpackaged plugins.

Both feed the same registries.  The idempotency guards in each plugin's
``register()`` function prevent double-registration conflicts.
"""

from __future__ import annotations

import importlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_discovered = False


def discover_plugins(config_path: str | Path | None = None) -> None:
    """Discover and register all axis plugins.

    Scans setuptools entry points first, then the YAML config file.
    Idempotent: subsequent calls are no-ops unless ``_reset_discovery()``
    is called first.

    Parameters
    ----------
    config_path:
        Explicit path to the plugins YAML file.  When *None* (the default),
        searches the current working directory and the source-tree root.
    """
    global _discovered
    if _discovered:
        return
    _discovered = True

    _load_entry_points()
    _load_yaml_plugins(config_path)


def _load_entry_points() -> None:
    """Import plugins registered via setuptools entry points."""
    from importlib.metadata import entry_points

    eps = entry_points(group="axis.plugins")
    for ep in eps:
        try:
            mod = ep.load()
            if hasattr(mod, "register"):
                mod.register()
            else:
                logger.warning(
                    "Entry point %s has no register() function", ep.name,
                )
        except Exception:
            logger.warning(
                "Failed to load entry point %s", ep.name, exc_info=True,
            )


def _load_yaml_plugins(config_path: str | Path | None = None) -> None:
    """Import plugins listed in axis-plugins.yaml."""
    if config_path is None:
        config_path = _find_config()
    if config_path is None:
        logger.debug("No axis-plugins.yaml found; skipping YAML plugin discovery")
        return

    import yaml

    path = Path(config_path)
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        return
    modules = data.get("plugins", [])
    if not isinstance(modules, list):
        return

    for module_path in modules:
        try:
            mod = importlib.import_module(module_path)
            if hasattr(mod, "register"):
                mod.register()
            else:
                logger.warning(
                    "Plugin module %s has no register() function",
                    module_path,
                )
        except Exception:
            logger.warning(
                "Failed to load plugin %s", module_path, exc_info=True,
            )


def _find_config() -> Path | None:
    """Search for axis-plugins.yaml in standard locations."""
    candidates = [
        Path("axis-plugins.yaml"),
        Path(__file__).resolve().parent.parent.parent / "axis-plugins.yaml",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _reset_discovery() -> None:
    """Reset the discovered flag.  Test-only helper.

    After calling this, the next ``discover_plugins()`` will re-read the
    config and re-call all ``register()`` functions.  Callers should
    clear the individual registries first if they need a clean slate.
    """
    global _discovered
    _discovered = False
