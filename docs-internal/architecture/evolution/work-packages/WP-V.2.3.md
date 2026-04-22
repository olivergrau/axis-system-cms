# WP-V.2.3 Implementation Brief -- Signal Landscape World Adapter

## Context

The signal landscape world has distinct visual semantics from grid_2d: a heatmap color palette (dark blue-gray to hot orange) and hotspot position markers that change each tick. This adapter has the most divergent behavior of the three world adapters.

### Predecessor State

- `DefaultWorldVisualizationAdapter` with rectangular layout available
- Signal landscape world returns per-step hotspot data from `world_metadata()` (WP-V.0.2):
  ```python
  {"hotspots": [{"cx": float, "cy": float, "radius": float, "intensity": float}, ...]}
  ```

### Reference Documents

- `docs/architecture/evolution/visualization-architecture.md` -- Section 11.1 (SignalLandscapeWorldVisualizationAdapter)

---

## Objective

Implement `SignalLandscapeWorldVisualizationAdapter` with heatmap colors, hotspot topology indicators, and world metadata sections.

---

## Scope

### 1. SignalLandscapeWorldVisualizationAdapter

**File**: `src/axis/world/signal_landscape/visualization.py` (new)

```python
"""Signal landscape world visualization adapter.

Heatmap color palette and hotspot position markers.
"""

from __future__ import annotations

from typing import Any

from axis.sdk.snapshot import WorldSnapshot
from axis.visualization.adapters.default_world import DefaultWorldVisualizationAdapter
from axis.visualization.types import (
    AnalysisRow,
    CellColorConfig,
    CellLayout,
    MetadataSection,
    TopologyIndicator,
)


class SignalLandscapeWorldVisualizationAdapter(DefaultWorldVisualizationAdapter):
    """Visualization adapter for the signal_landscape world type.

    Inherits rectangular grid layout and hit-testing from the default.
    Overrides coloring (heatmap), topology indicators (hotspot markers),
    metadata sections (hotspot details), and status line.
    """

    def cell_color_config(self) -> CellColorConfig:
        return CellColorConfig(
            obstacle_color=(0, 0, 0),
            empty_color=(40, 40, 60),
            resource_color_min=(40, 40, 60),
            resource_color_max=(255, 100, 0),
            agent_color=(33, 150, 243),
            agent_selected_color=(33, 150, 243),
            selection_border_color=(255, 160, 0),
            grid_line_color=(80, 80, 100),
        )

    def topology_indicators(
        self,
        world_snapshot: WorldSnapshot,
        world_data: dict[str, Any],
        cell_layout: CellLayout,
    ) -> list[TopologyIndicator]:
        hotspots = world_data.get("hotspots", [])
        indicators: list[TopologyIndicator] = []
        for hs in hotspots:
            # Convert grid-coordinate center to pixel center
            cx, cy = hs["cx"], hs["cy"]
            # Use cell_layout dimensions to compute pixel position
            pixel_x = (cx + 0.5) * cell_layout.canvas_width / cell_layout.grid_width
            pixel_y = (cy + 0.5) * cell_layout.canvas_height / cell_layout.grid_height
            # Radius in pixels (proportional to grid cells)
            cell_w = cell_layout.canvas_width / cell_layout.grid_width
            radius_pixels = hs["radius"] * cell_w
            indicators.append(
                TopologyIndicator(
                    indicator_type="hotspot_center",
                    position=(pixel_x, pixel_y),
                    data={
                        "radius_pixels": radius_pixels,
                        "intensity": hs["intensity"],
                        "label": f"r={hs['radius']:.1f}",
                    },
                )
            )
        return indicators

    def world_metadata_sections(
        self,
        world_data: dict[str, Any],
    ) -> list[MetadataSection]:
        hotspots = world_data.get("hotspots", [])
        if not hotspots:
            return []
        rows = tuple(
            AnalysisRow(
                label=f"Hotspot {i + 1}",
                value=f"({h['cx']:.1f}, {h['cy']:.1f}) r={h['radius']:.1f} I={h['intensity']:.2f}",
            )
            for i, h in enumerate(hotspots)
        )
        return [MetadataSection(title="Hotspots", rows=rows)]

    def format_world_info(
        self,
        world_data: dict[str, Any],
    ) -> str | None:
        hotspots = world_data.get("hotspots", [])
        n = len(hotspots)
        return f"{n} hotspot{'s' if n != 1 else ''} active"
```

**Design notes**:

- Inherits `cell_layout()`, `pixel_to_grid()`, `agent_marker_center()`, `cell_shape()` from `DefaultWorldVisualizationAdapter` (same rectangular geometry)
- Overrides 4 methods: `cell_color_config()`, `topology_indicators()`, `world_metadata_sections()`, `format_world_info()`
- Heatmap palette: dark blue-gray `(40, 40, 60)` as empty/min, hot orange `(255, 100, 0)` as resource max
- Grid line color darkened to `(80, 80, 100)` for visibility against dark background
- Hotspot center conversion: `cx` is a float grid coordinate, converted to pixel by `(cx + 0.5) * canvas_width / grid_width`. The `+0.5` offset centers within a cell when cx is an integer cell index. For fractional positions (hotspots drift), this gives a smooth pixel position.
- `world_metadata_sections()` returns one section "Hotspots" with a row per hotspot showing position, radius, and intensity
- Defensive coding: `world_data.get("hotspots", [])` handles missing key gracefully

### 2. Registration

**Same file**:

```python
from axis.visualization.registry import register_world_visualization

def _signal_landscape_vis_factory(
    world_config: dict[str, Any],
) -> SignalLandscapeWorldVisualizationAdapter:
    return SignalLandscapeWorldVisualizationAdapter()

register_world_visualization("signal_landscape", _signal_landscape_vis_factory)
```

---

## Out of Scope

- Canvas rendering of hotspot indicators (WP-V.4.1)
- Modifications to signal landscape world model or dynamics
- Any PySide6 code

---

## Testing Requirements

**File**: `tests/visualization/test_signal_landscape_world_adapter.py` (new)

### Color tests

1. **`test_signal_landscape_heatmap_colors`**:
   - Assert `config.empty_color == (40, 40, 60)`
   - Assert `config.resource_color_min == (40, 40, 60)`
   - Assert `config.resource_color_max == (255, 100, 0)`
   - Assert `config.obstacle_color == (0, 0, 0)`

2. **`test_signal_landscape_grid_line_color`**:
   - Assert `config.grid_line_color == (80, 80, 100)`

### Topology indicator tests

3. **`test_signal_landscape_topology_with_hotspots`**:
   - Provide `world_data={"hotspots": [{"cx": 5.0, "cy": 3.0, "radius": 2.0, "intensity": 0.8}]}`
   - Assert returns 1 indicator with `indicator_type == "hotspot_center"`

4. **`test_signal_landscape_topology_indicator_position`**:
   - For a 10x10 grid at 200x200, hotspot at cx=5.0:
   - `pixel_x = (5.0 + 0.5) * 200 / 10 = 110.0`
   - Assert position matches computed value

5. **`test_signal_landscape_topology_indicator_data`**:
   - Assert `data["radius_pixels"]` is computed correctly
   - Assert `data["intensity"]` matches input
   - Assert `data["label"]` contains radius

6. **`test_signal_landscape_topology_no_hotspots`**:
   - Provide `world_data={}`, assert returns `[]`

7. **`test_signal_landscape_topology_multiple_hotspots`**:
   - Provide 3 hotspots, assert returns 3 indicators

### Metadata section tests

8. **`test_signal_landscape_metadata_sections`**:
   - Provide 2 hotspots, assert 1 section titled "Hotspots" with 2 rows

9. **`test_signal_landscape_metadata_row_content`**:
   - Assert row label is "Hotspot 1" and value contains position/radius/intensity

10. **`test_signal_landscape_metadata_empty_when_no_hotspots`**:
    - Provide `world_data={}`, assert returns `[]`

### Status line tests

11. **`test_signal_landscape_format_world_info`**:
    - 3 hotspots: assert `"3 hotspots active"`
    - 1 hotspot: assert `"1 hotspot active"` (singular)

12. **`test_signal_landscape_format_world_info_no_hotspots`**:
    - Empty hotspots: assert `"0 hotspots active"`

### Inherited behavior tests

13. **`test_signal_landscape_inherits_rectangular_layout`**:
    - Assert `cell_shape() == CellShape.RECTANGULAR`
    - Assert `cell_layout()` works correctly (inherited)

14. **`test_signal_landscape_registration`**:
    - Import module, resolve `"signal_landscape"`, assert correct type

---

## Expected Deliverable

1. `src/axis/world/signal_landscape/visualization.py`
2. `tests/visualization/test_signal_landscape_world_adapter.py`
3. Confirmation that all existing tests still pass
