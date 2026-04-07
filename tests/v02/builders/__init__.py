"""Test builders for the axis package.

Builders follow the fluent pattern:
    result = SomeBuilder().with_x(value).with_y(value).build()

Each builder:
- Has sensible defaults (builds a valid object with no arguments)
- Returns self from all with_* methods
- Produces the target object from build()
"""
