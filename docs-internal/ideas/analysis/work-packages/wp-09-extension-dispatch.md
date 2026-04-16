# WP-09: Minimal Extension Dispatch

**Phase**: 4 -- System-Specific Extensions  
**Dependencies**: WP-07  
**Scope**: Small  
**Spec reference**: Section 19

---

## Objective

Create the minimal dispatch layer for optional system-specific comparison extensions.

This WP should not implement any concrete system extension yet. It only defines the extension attachment mechanism.

---

## Deliverables

Create:

- `src/axis/framework/comparison/extensions.py`
- `tests/framework/comparison/test_extensions.py`

Potentially update:

- `src/axis/framework/comparison/compare.py`

---

## Required Behavior

The extension layer must:

- inspect system type(s) from the comparison inputs
- decide whether a system-specific block can be attached
- return a dict under `system_specific_analysis`
- remain optional and noninvasive

---

## Implementation Steps

1. Create an internal extension dispatch function such as:
   ```python
   def build_system_specific_analysis(...):
       ...
   ```
2. Keep dispatch simple and local; do not introduce plugin registration yet.
3. Return an empty dict or `None` when no extension applies.
4. Wire the dispatch into `compare.py`.

---

## Tests

Cover at least:

- no extension available
- extension surface returns empty or omitted block
- compare result can carry extension payloads structurally

---

## Verification

1. Generic core still works without any extension.
2. Extension logic is isolated in one module.

---

## Files Created

- `src/axis/framework/comparison/extensions.py`
- `tests/framework/comparison/test_extensions.py`

## Files Modified

- `src/axis/framework/comparison/compare.py`

## Files Deleted

None.
