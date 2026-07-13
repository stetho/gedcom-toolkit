"""
Detecting place-name variants that likely refer to the same location, and
suggesting a normalised form -- as a dry-run report only, never an
auto-rewrite.

The reason this never auto-applies anything: some "variants" aren't
messy data at all. Croydon genuinely moved from the county of Surrey into
Greater London in 1965, so "Croydon, Surrey" and "Croydon, Greater London"
can both be correct depending on which era a given fact belongs to.
Blindly merging them would erase real historical information.

Approach: group place strings by their first comma-separated segment (the
actual place name, e.g. "Croydon"), then within each group, score each
distinct variant by how much *usage-weighted* support it gets from other
variants being a structural subsequence of it -- i.e. every segment of the
other variant appears in this one, in order, so nothing is lost by
treating this one as canonical. This is deliberately structural rather
than based on any hardcoded knowledge of geography or administrative
history: a variant that conflicts (like a genuine county change) simply
won't be a subsequence of anything, however often it's used, and gets
reported as a conflict for manual review rather than silently merged or
silently outvoted.

Note: because selection is purely structural, a rare, oddly-ordered
one-off entry can end up as the suggested canonical if it happens to be a
superset of every other variant present -- that's exactly what should
happen structurally, but it's still worth a human glancing at it, so the
canonical's own usage count is always reported alongside the suggestion
rather than hidden.
"""

from __future__ import annotations

from dataclasses import dataclass

from gedcomtoolkit.models import FamilyTree

Segments = tuple[str, ...]


def clean_segments(raw: str) -> Segments:
    """Split on commas, strip whitespace and trailing periods, drop empty
    segments. Handles doubled commas ("Croydon,, England") and a trailing
    full stop on a segment ("Hampshire.") -- both pure formatting noise,
    not genuine differences."""
    segments = []
    for s in raw.split(","):
        cleaned = s.strip().rstrip(".").strip()
        if cleaned:
            segments.append(cleaned)
    return tuple(segments)


def is_subsequence(shorter: Segments, longer: Segments) -> bool:
    """Whether every segment in `shorter` appears in `longer`, in order
    (case-insensitive). An empty `shorter` is trivially a subsequence."""
    it = iter(longer)
    return all(any(seg.lower() == candidate.lower() for candidate in it) for seg in shorter)


@dataclass
class PlaceSuggestion:
    primary_key: str
    suggested_canonical: str
    canonical_count: int
    confidence: float
    compatible_variants: list[tuple[str, int]]  # (display string, usage count)
    conflicting_variants: list[tuple[str, int]]


def collect_place_usage(tree: FamilyTree) -> dict[str, int]:
    """Every non-empty place string used anywhere (birth/death/marriage), with counts."""
    counts: dict[str, int] = {}
    for indi in tree.individuals.values():
        for place in (indi.birth_place, indi.death_place):
            if place:
                counts[place] = counts.get(place, 0) + 1
    for fam in tree.families.values():
        if fam.marriage_place:
            counts[fam.marriage_place] = counts.get(fam.marriage_place, 0) + 1
    return counts


def find_place_suggestions(tree: FamilyTree) -> list[PlaceSuggestion]:
    """
    Cluster place strings by primary place name, and for any cluster with
    more than one distinct cleaned variant, suggest a canonical form.
    Clusters with only a single distinct variant (however many times it's
    used, however messily formatted duplicates like doubled commas) are
    excluded -- there's nothing to normalise.
    """
    raw_counts = collect_place_usage(tree)

    # Merge raw strings that clean to the same segments (e.g. "Croydon,, England"
    # and "Croydon, England"), grouped by primary (first-segment, lowercased) key.
    clusters: dict[str, dict[Segments, int]] = {}
    display_forms: dict[Segments, str] = {}

    for raw, count in raw_counts.items():
        segments = clean_segments(raw)
        if not segments:
            continue
        primary_key = segments[0].lower()
        cluster = clusters.setdefault(primary_key, {})
        cluster[segments] = cluster.get(segments, 0) + count
        # Prefer the first-seen display form for a given cleaned segment tuple
        display_forms.setdefault(segments, ", ".join(segments))

    suggestions = []
    for primary_key, variant_counts in clusters.items():
        if len(variant_counts) < 2:
            continue  # nothing to normalise

        variants = list(variant_counts.items())

        best_segments = None
        best_weight = -1
        for candidate_segments, _ in variants:
            weight = sum(
                other_count
                for other_segments, other_count in variants
                if other_segments != candidate_segments
                and is_subsequence(other_segments, candidate_segments)
            )
            if weight > best_weight or (
                weight == best_weight
                and best_segments is not None
                and len(candidate_segments) > len(best_segments)
            ):
                best_weight = weight
                best_segments = candidate_segments

        compatible = []
        conflicting = []
        for segments, count in variants:
            if segments == best_segments:
                continue
            display = display_forms[segments]
            if is_subsequence(segments, best_segments):
                compatible.append((display, count))
            else:
                conflicting.append((display, count))

        total_other = sum(count for segments, count in variants if segments != best_segments)
        confidence = 100.0 if total_other == 0 else 100.0 * best_weight / total_other

        suggestions.append(
            PlaceSuggestion(
                primary_key=primary_key,
                suggested_canonical=display_forms[best_segments],
                canonical_count=variant_counts[best_segments],
                confidence=confidence,
                compatible_variants=sorted(compatible, key=lambda x: -x[1]),
                conflicting_variants=sorted(conflicting, key=lambda x: -x[1]),
            )
        )

    suggestions.sort(key=lambda s: -sum(c for _d, c in s.compatible_variants))
    return suggestions
