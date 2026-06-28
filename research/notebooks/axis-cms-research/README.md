# AXIS CMS Research Notebook Track

This folder is the home for the primary AXIS CMS research notebook sequence.

Recommended common notebook prologue:

```python
from _bootstrap import setup_notebook

ROOT = setup_notebook()
```

From there, notebooks can import shared helpers such as:

```python
from research.lib import load_series_metrics_csv, load_series_summary
from research.lib.plotting import bar_plot, line_plot
```
