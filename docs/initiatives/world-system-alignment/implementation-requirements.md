# Implementation Requirements

This document defines implementation constraints for the `World-System Alignment`
initiative.

The purpose is not only technical hygiene. The purpose is to preserve AXIS CMS
as an experimental landscape in which older and newer world/system families can
coexist without forcing each other into a shared dependency chain.

## Core Principle

New exploratory world and system families should be introduced in a way that
preserves the operational independence of existing families.

This means:

- existing worlds and systems must remain runnable
- new worlds and systems must not silently redefine old behavior
- compatibility pressure must not force all variants into a single evolving code path

## Requirements

## 1. Existing Worlds and Systems Must Remain Untouched

The currently implemented worlds and systems must continue to work as they do
today.

That includes in particular:

- existing world classes
- existing system classes
- existing configs
- existing tutorials and manuals as far as they describe already implemented behavior

The `World-System Alignment` initiative may add new experimental branches, but
it must not destabilize the established baseline families.

## 2. New Worlds Should Be Operationally Independent

New worlds may reuse ideas and code from existing worlds, but they should not
be introduced as inheritance-dependent extensions of those worlds.

The preferred rule is:

- code reuse is allowed
- code copying is acceptable
- direct class inheritance from older world families is not the desired default

Reason:

- independent world families remain easier to reason about
- later removal of an old family should not break a new one
- experiment interpretation stays clearer when each world family has its own explicit semantics

This favors explicit duplication over tight coupling.

## 3. New Systems Should Follow the Same Independence Rule

The same constraint applies to systems.

New systems may reuse design ideas and implementation patterns from older
systems, but they should remain independently runnable and independently
maintainable.

The preferred rule is therefore:

- no forced inheritance chain from older systems into newer systems
- explicit code duplication is acceptable where it protects independence
- new system semantics should live in their own implementation path

## 4. Preserve Compatibility by Avoiding Hidden Cross-Dependencies

The initiative should maintain compatibility by resisting hidden entanglement.

Examples of undesired outcomes:

- a new sensor model that changes the behavior of old systems indirectly
- a new world mechanic that requires rewriting old configs
- shared helper changes that silently alter historical behavior

The desired outcome is:

- old families keep their contracts
- new families introduce new contracts
- migration, if any, is explicit rather than implicit

## 5. Construction Kit Should Grow by Addition, Not Mutation

Where the Construction Kit must support new world/system families, it should
prefer adding new components instead of redefining existing ones.

This is especially relevant for areas such as:

- sensor models
- observation interpretation
- transition semantics
- modulation or prediction-related components if variants are needed

So if a new sensing regime is needed, the preferred approach is:

- create a new component or variant
- keep the old component intact

This preserves the ability to compare old and new system families fairly.

## 6. Older Families Must Remain Removable

The architecture should preserve the option to discard older systems or worlds
later without damaging newer ones.

This is an explicit design goal.

It implies:

- avoid deep inheritance from old families
- avoid shared logic that is only accidentally shared because of historical convenience
- keep newer families self-contained enough that old ones can be archived or removed later

## 7. Framework Changes Require Extra Scrutiny

If the AXIS framework itself must be extended, that should be treated as a
separate compatibility-sensitive step.

Framework changes are allowed, but only after careful review.

The key questions should be:

- is the extension truly framework-level, or only needed by one new family?
- does it preserve backward compatibility for existing systems and worlds?
- does it introduce coupling that will make later cleanup harder?
- can the same goal be achieved at the system/world layer instead?

## 8. Preferred Direction: No Framework Changes If Reasonable

The preferred implementation path is to realize the new worlds and systems
without changing the AXIS framework.

This is not a hard rule. It is a preference.

If a framework change is necessary, it is acceptable, but the burden of
justification should be higher than for ordinary world/system additions.

## 9. Practical Interpretation for Upcoming Work

For the upcoming work on prediction-supporting worlds and possible follow-up
systems, the intended interpretation is:

- add new world families rather than mutating old ones
- add new system families rather than rewriting old ones
- add new Construction Kit components where needed
- keep compatibility and removability in view at every layer

This keeps AXIS CMS usable both as:

- a historical record of explored designs
- an experimentation framework for new branches

## Working Conclusion

This initiative should prefer **parallel evolutionary branches** over
in-place transformation.

That means AXIS CMS remains a framework where:

- older worlds/systems continue to run
- newer worlds/systems can diverge when necessary
- shared framework changes happen only when they are clearly justified

This is intentionally more explicit, and sometimes more repetitive, than a
maximally DRY design.

For this initiative, that tradeoff is desired.
