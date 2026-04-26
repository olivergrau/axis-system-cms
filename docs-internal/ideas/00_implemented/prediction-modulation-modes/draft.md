# Draft: Prediction Modulation Modes for System C

## Motivation

System C currently uses prediction as a purely multiplicative modifier of
drive-derived action scores:

```text
psi_final(a) = psi_drive(a) * mu(a, context)
```

This preserves the interpretation that prediction does not create
motivation on its own. However, it introduces a hard limitation:

```text
if psi_drive(a) = 0, then psi_final(a) = 0
```

As a result, prediction can never express:

> "This action has historically been reliable in this context"

when the current drive layer assigns that action a zero score.

## Problem

This makes prediction too weak in two practical ways:

1. It can only amplify or suppress an existing preference.
2. It cannot introduce a small action-specific correction when the drive
   layer is indifferent.

That is especially visible in System C visual analysis:
trace accumulation may exist for an action, but no behavioral effect is
visible if the current drive score for that action is zero.

## Goal

Introduce configurable prediction modulation modes that keep the
architectural separation intact:

- drives remain the only source of motivation
- prediction remains an action-level correction mechanism
- prediction may contribute a small bounded correction even when the
  current drive score is zero

## Proposed Modes

### 1. `multiplicative`

Preserve current behavior:

```text
psi_final(a) = psi_drive(a) * mu(a)
```

### 2. `additive`

Use a bounded prediction bias term:

```text
psi_final(a) = psi_drive(a) + lambda_pred * delta_pred(a)
```

where `delta_pred(a)` is derived from confidence/frustration traces and
 clipped to a small symmetric range.

### 3. `hybrid`

Combine both:

```text
psi_final(a) = psi_drive(a) * mu(a) + lambda_pred * delta_pred(a)
```

## Constraints

- prediction must not become an unconstrained extra drive
- the additive correction must remain bounded and configurable
- `lambda_+ = lambda_- = 0` should still collapse prediction influence
- tracing/logging should expose:
  - raw drive scores
  - multiplicative reliability factor
  - additive prediction bias
  - final action scores

## Implementation Direction

1. Extend `PredictionConfig` with:
   - `modulation_mode`
   - `prediction_bias_scale`
   - `prediction_bias_clip`
2. Refactor the modulation helper into a richer computation path that
   returns both multiplicative and additive components.
3. Keep `modulated_scores` as the final score field for compatibility,
   but add explicit logging for intermediate pieces.
4. Update public docs and tests.

## Recommendation

Implement all three modes now, keep `multiplicative` as the default for
backward compatibility, and document `additive` as the recommended mode
when prediction should be able to shape otherwise neutral actions.
