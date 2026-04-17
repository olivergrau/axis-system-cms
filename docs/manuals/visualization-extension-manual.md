# AXIS Visualization Extension Developer Manual (v0.2.3)

> **Related manuals:**
> [System Development](system-dev-manual.md) |
> [Visualization](visualization-manual.md) |
> [CLI User Guide](cli-manual.md)
>
> **Tutorials:**
> [Building a System](../tutorials/building-a-system.md)

---

## Overview

When the interactive episode viewer opens a trace, it delegates all
system-specific rendering to a **visualization adapter**. Each system
can register its own adapter to control the analysis panel, debug
overlays, vitality formatting, and phase navigation.

This manual explains the adapter interface, the data types it uses,
and the step-by-step process for building and registering a new adapter.

---

## 1. Architecture

```
axis visualize --experiment <eid> --run <rid> --episode 1
      │
      ▼
  resolve_system_adapter(system_type)
      │
      ├── registered? ──► calls factory() ──► YourAdapter instance
      │
      └── not found?  ──► NullSystemVisualizationAdapter (fallback)
```

The framework never imports any specific system's visualization code.
Instead, each system registers a zero-argument factory function into a
string-keyed registry. The viewer resolves the adapter at runtime by
looking up `system_type` from the loaded trace.

If no adapter is registered for a system type, the viewer falls back
to `NullSystemVisualizationAdapter`, which provides empty analysis and
overlay data with sensible vitality defaults.

---

## 2. The Adapter Interface

Every visualization adapter must implement six methods. There is no
formal Protocol class -- the interface is defined structurally by
what the viewer calls.

| Method | Return type | Purpose |
|---|---|---|
| `phase_names()` | `list[str]` | Step phases for the phase navigation bar |
| `vitality_label()` | `str` | Display label for vitality (e.g. `"Energy"`) |
| `format_vitality(value, system_data)` | `str` | Format a 0-1 vitality float for display |
| `build_step_analysis(step_trace)` | `list[AnalysisSection]` | Build the analysis panel for one step |
| `build_overlays(step_trace)` | `list[OverlayData]` | Build debug overlay layers for one step |
| `available_overlay_types()` | `list[OverlayTypeDeclaration]` | Declare all overlay types the adapter can produce |

### 2.1 `phase_names()`

Returns the list of phase names that appear in the viewer's phase
navigation bar. Each phase corresponds to a snapshot key in the step
trace's `intermediate_snapshots` dict (plus `"BEFORE"` and the final
`"AFTER_ACTION"` state).

```python
def phase_names(self) -> list[str]:
    return ["BEFORE", "AFTER_REGEN", "AFTER_ACTION"]
```

### 2.2 `vitality_label()` and `format_vitality()`

`vitality_label()` returns the display name (e.g. `"Energy"` instead
of the generic `"Vitality"`). `format_vitality()` converts the
normalized 0-1 float into a human-readable string.

```python
def vitality_label(self) -> str:
    return "Energy"

def format_vitality(self, value: float, system_data: dict[str, object]) -> str:
    energy = value * self._max_energy
    return f"{energy:.1f} / {self._max_energy:.0f}"
```

### 2.3 `build_step_analysis()`

Returns a list of `AnalysisSection` objects that populate the analysis
panel. Each section has a title and a list of key-value rows.

```python
from axis.visualization.types import AnalysisRow, AnalysisSection

def build_step_analysis(self, step_trace: BaseStepTrace) -> list[AnalysisSection]:
    return [
        AnalysisSection(
            title="Step Overview",
            rows=(
                AnalysisRow(label="Timestep", value=str(step_trace.timestep)),
                AnalysisRow(label="Action", value=step_trace.action),
            ),
        ),
    ]
```

Rows can be nested using the `sub_rows` field for hierarchical display:

```python
AnalysisRow(
    label="Drive Output",
    value="",
    sub_rows=(
        AnalysisRow(label="hunger", value="0.82"),
        AnalysisRow(label="curiosity", value="0.35"),
    ),
)
```

### 2.4 `build_overlays()` and `available_overlay_types()`

`available_overlay_types()` declares metadata about each overlay the
adapter can produce. The viewer uses this to build the overlay toggle
menu.

```python
from axis.visualization.types import OverlayTypeDeclaration

def available_overlay_types(self) -> list[OverlayTypeDeclaration]:
    return [
        OverlayTypeDeclaration(
            key="action_preference",
            label="Action Preference",
            description="Arrows showing preferred movement direction",
            legend_html="<b>Arrow</b>: preferred direction",
        ),
    ]
```

`build_overlays()` returns the actual overlay data for the current
step. Each `OverlayData` references an overlay type by key and
contains a list of `OverlayItem` objects positioned on the grid.

```python
from axis.visualization.types import OverlayData, OverlayItem

def build_overlays(self, step_trace: BaseStepTrace) -> list[OverlayData]:
    return [
        OverlayData(
            overlay_type="action_preference",
            items=(
                OverlayItem(
                    item_type="direction_arrow",
                    grid_position=(5, 3),
                    data={"direction": "north", "strength": 0.8},
                ),
            ),
        ),
    ]
```

Built-in `item_type` values recognized by the renderer include:

| `item_type` | Data keys | Description |
|---|---|---|
| `direction_arrow` | `direction`, `strength` | Directional arrow |
| `bar_chart` | `values`, `labels`, `colors` | Per-cell bar chart |
| `diamond_marker` | `color`, `size` | Diamond marker |
| `x_marker` | `color`, `size` | X marker |
| `center_dot` | `color`, `radius` | Centered dot |
| `saturation_ring` | `saturation`, `color` | Ring with variable saturation |
| `modulation_cell` | `value`, `color_pos`, `color_neg` | Cell-fill by signed value |

---

## 3. Data Types Reference

All types are imported from `axis.visualization.types`:

```python
from axis.visualization.types import (
    AnalysisRow,
    AnalysisSection,
    OverlayData,
    OverlayItem,
    OverlayTypeDeclaration,
)
```

All are frozen Pydantic models. Their fields:

**`AnalysisRow`** -- a single key-value row in the analysis panel.

| Field | Type | Default |
|---|---|---|
| `label` | `str` | required |
| `value` | `str` | required |
| `sub_rows` | `tuple[AnalysisRow, ...] \| None` | `None` |

**`AnalysisSection`** -- a titled group of rows.

| Field | Type |
|---|---|
| `title` | `str` |
| `rows` | `tuple[AnalysisRow, ...]` |

**`OverlayTypeDeclaration`** -- metadata for one overlay type.

| Field | Type | Default |
|---|---|---|
| `key` | `str` | required |
| `label` | `str` | required |
| `description` | `str` | required |
| `legend_html` | `str` | `""` |

**`OverlayItem`** -- a single positioned item on the grid.

| Field | Type |
|---|---|
| `item_type` | `str` |
| `grid_position` | `tuple[int, int]` |
| `data` | `dict[str, Any]` |

**`OverlayData`** -- a collection of items for one overlay type.

| Field | Type |
|---|---|
| `overlay_type` | `str` |
| `items` | `tuple[OverlayItem, ...]` |

---

## 4. Registration

### 4.1 The registry

The visualization registry lives in `axis.visualization.registry`. Two
functions are relevant for adapter authors:

```python
from axis.visualization.registry import (
    register_system_visualization,
    registered_system_visualizations,
)
```

- `register_system_visualization(system_type, factory)` -- registers a
  zero-argument factory callable that returns an adapter instance.
  Raises `ValueError` on duplicate registration.
- `registered_system_visualizations()` -- returns a tuple of registered
  system type strings (used for idempotency guards).

### 4.2 Module-level registration

At the bottom of your adapter module, define a factory and register it:

```python
def _my_system_vis_factory() -> MySystemVisualizationAdapter:
    return MySystemVisualizationAdapter(max_energy=100.0)

register_system_visualization("my_system", _my_system_vis_factory)
```

The factory is called with **no arguments**. Bake any parameters
(like `max_energy`) into the closure.

### 4.3 Plugin integration

In your system's `__init__.py`, import the adapter module inside
`register()` using the standard guarded pattern:

```python
def register() -> None:
    # ... system factory registration ...

    from axis.visualization.registry import registered_system_visualizations

    if "my_system" not in registered_system_visualizations():
        try:
            import axis.systems.my_system.visualization  # noqa: F401
        except ImportError:
            pass
```

The `try/except ImportError` makes visualization optional -- if
PySide6 is not installed, the adapter is simply not registered and the
viewer falls back to the null adapter.

---

## 5. Complete Example

This example builds a minimal adapter for a hypothetical `system_x`.

### `src/axis/systems/system_x/visualization.py`

```python
from __future__ import annotations

from typing import Any

from axis.sdk.trace import BaseStepTrace
from axis.visualization.registry import register_system_visualization
from axis.visualization.types import (
    AnalysisRow,
    AnalysisSection,
    OverlayData,
    OverlayItem,
    OverlayTypeDeclaration,
)


class SystemXVisualizationAdapter:
    def __init__(self, max_energy: float) -> None:
        self._max_energy = max_energy

    def phase_names(self) -> list[str]:
        return ["BEFORE", "AFTER_ACTION"]

    def vitality_label(self) -> str:
        return "Energy"

    def format_vitality(self, value: float, system_data: dict[str, Any]) -> str:
        return f"{value * self._max_energy:.1f} / {self._max_energy:.0f}"

    def build_step_analysis(self, step_trace: BaseStepTrace) -> list[AnalysisSection]:
        sd = step_trace.system_data or {}
        return [
            AnalysisSection(
                title="System X Status",
                rows=(
                    AnalysisRow(label="Timestep", value=str(step_trace.timestep)),
                    AnalysisRow(label="Action", value=step_trace.action),
                    AnalysisRow(label="Score", value=f"{sd.get('score', 0):.3f}"),
                ),
            ),
        ]

    def build_overlays(self, step_trace: BaseStepTrace) -> list[OverlayData]:
        pos = step_trace.agent_position_before
        return [
            OverlayData(
                overlay_type="agent_marker",
                items=(
                    OverlayItem(
                        item_type="center_dot",
                        grid_position=(pos.x, pos.y),
                        data={"color": "#FF5500", "radius": 6},
                    ),
                ),
            ),
        ]

    def available_overlay_types(self) -> list[OverlayTypeDeclaration]:
        return [
            OverlayTypeDeclaration(
                key="agent_marker",
                label="Agent Marker",
                description="Dot at agent position",
            ),
        ]


def _factory() -> SystemXVisualizationAdapter:
    return SystemXVisualizationAdapter(max_energy=100.0)

register_system_visualization("system_x", _factory)
```

### `src/axis/systems/system_x/__init__.py`

```python
def register() -> None:
    from axis.framework.registry import register_system, registered_system_types

    if "system_x" not in registered_system_types():
        register_system("system_x", lambda cfg: ...)

    from axis.visualization.registry import registered_system_visualizations

    if "system_x" not in registered_system_visualizations():
        try:
            import axis.systems.system_x.visualization  # noqa: F401
        except ImportError:
            pass
```

---

## 6. Existing Implementations

Use these as reference when building your own adapter:

| System | File | Overlays | Analysis sections |
|---|---|---|---|
| System A | `src/axis/systems/system_a/visualization.py` | 4 (action preference, drive contribution, consumption opportunity, buffer saturation) | 6 |
| System A+W | `src/axis/systems/system_aw/visualization.py` | Extended set from System A | Extended from System A |
| System C | `src/axis/systems/system_c/visualization.py` | 6 (adds modulated contribution, modulation factor, neighbor modulation) | 7-8 (adds prediction and modulation sections) |
| System B | `src/axis/systems/system_b/visualization.py` | System B specific overlays | System B specific |

---

## 7. Tips

- **Keep adapters stateless.** The factory creates a fresh instance
  each time the viewer opens a trace. Do not store step-level state
  between calls.
- **Read from `step_trace.system_data`.** This dict is the opaque bag
  each system populates during execution. Your adapter knows the
  internal structure -- the framework does not.
- **Use `intermediate_snapshots`** to access world state at each phase.
  The keys match the strings returned by `phase_names()`.
- **Test your adapter** by constructing synthetic `BaseStepTrace`
  objects and calling each method. No Qt or viewer needed.
- **Visualization is optional.** The `try/except ImportError` guard in
  `register()` means the system works without PySide6 installed.
