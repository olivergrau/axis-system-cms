# System C+W

System C+W combines the dual-drive architecture of System A+W with the
predictive machinery of System C.

## Documents

| Document | Content |
|---|---|
| [Formal Model](01_System C+W Model.md) | Full model: shared predictive memory, drive-specific traces, dual predictive modulation, and arbitration |
| [Worked Examples](02_System C+W Worked Examples.md) | Numerical walkthroughs of movement curiosity, non-movement suppression, and dual predictive learning |

## Scope

System C+W introduces:

- one shared predictive feature representation over local resource and novelty-derived features,
- one shared predictive memory over compact contexts and actions,
- separate hunger-side and curiosity-side predictive outcome semantics,
- separate hunger and curiosity confidence/frustration traces,
- separate predictive modulation parameters per drive,
- and predictive modulation applied before dynamic drive arbitration.
