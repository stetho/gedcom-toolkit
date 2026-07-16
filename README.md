# gedcom-toolkit

A command-line tool and Python library for exploring, validating, and
querying GEDCOM family tree files.

GEDCOM is the standard file format genealogy software uses to store family
trees. It's a genuinely awkward format: a large amount of loosely structured
text data, riddled with real-world data quality problems (missing dates,
duplicate people, impossible relationships), and hard to query directly. This
project treats a family tree for what it actually is — a directed graph — and
builds tools on top of that idea.

## What it does

```bash
gedcom stats family.ged
```

prints summary statistics about a family tree: how many people, how many
families, how many disconnected branches, how much data is missing.

```bash
gedcom validate family.ged
```

checks for data problems: cycles (someone recorded as their own ancestor),
death recorded before birth, implausible ages, and parents who'd have been
too young -- or already dead -- when a child was born. Exits with status 1
if any errors are found (0 for warnings only), so it's usable as a CI check
against your own working file.

```bash
gedcom findid family.ged "Bob Smith"
```

finds every individual matching a name and prints their unique xref_id.
GEDCOM names aren't unique -- a great-grandfather, his father, and a couple
of distant cousins can easily share one -- so this is how you get an
unambiguous ID to hand to other commands.

```bash
gedcom findrelationship family.ged "Bob Smith" "Jim Jones"
```

finds the relationship path between two individuals, shows it as a chain
(`child of ... spouse of ... parent of ...`), and names the relationship
itself where a term exists ("granddaughter", "first cousin, once removed",
"great-aunt", "sister-in-law"). Naming uses the standard genealogical
approach -- closest common ancestor, plus how many generations each person
is from it -- so it handles cousins-N-times-removed and any number of
"greats" correctly. In-law terms are only attempted for the unambiguous
cases (a spouse's sibling or parent, and the reverse); anything murkier
falls back to showing just the chain rather than guessing at a term. Either
argument can be a name or an xref_id; if a name is ambiguous, every match
is shown so you can re-run with a specific ID from `gedcom findid`.

```bash
gedcom rn family.ged
```

("research next") ranks individuals by how valuable they'd be to research,
based on missing data (no birth date, no death date when they'd clearly be
deceased by now, no parents linked at all) weighted by how many descendants
that gap affects -- filling in a brick wall for someone with fifty
descendants is worth more than for a childless leaf. `--limit` controls how
many rows are shown (default 20).

```bash
gedcom sources family.ged
```

reports how well-evidenced the tree is, not just how complete it is: what
percentage of recorded births, deaths, and marriages have a source citation
attached, plus a ranked list of the individuals and marriages with the most
unsourced facts. An event with no date recorded isn't counted as
"unsourced" -- that's a missing-data gap (`gedcom rn`'s territory), not a
sourcing gap.

```bash
gedcom places family.ged
```

groups place-name variants that likely refer to the same location (e.g.
"Croydon", "Croydon, Surrey", "Croydon, Greater London") and suggests a
canonical form with a confidence score -- a dry-run report only, it never
rewrites the file. Some variants reflect genuine historical differences
(a place moving between counties, say) rather than messy data, so those
are reported separately as conflicts for manual review rather than
silently merged, however common they are in the file.

```bash
gedcom duplicates family.ged
```

flags probable duplicate individuals *within a single file* -- grouped by
exact name match, then scored by birth-year gap and whether they share the
same parents. Deliberately doesn't assert "duplicate": same name and a
close birth year can also mean a genuine namesake (a child named after an
earlier sibling who died young, common in Victorian-era records), so each
pair comes with a note explaining what that pattern usually indicates
rather than a bare confidence number.

```bash
gedcom completeness family.ged
```

reports parent-linkage completeness broken down by generation: what
percentage of individuals have both parents linked, one, or none.
"Generation" means depth from the nearest known root in each individual's
own line, not absolute chronological era, so generation 0 always shows
100% "no parents" by definition -- that's structural, not a finding.
Requires an acyclic tree, so run `gedcom validate` first if that hasn't
been confirmed recently.

More commands are planned — see [Roadmap](#roadmap) below. The CLI is
structured so that adding a new one is a small, self-contained change (see
`gedcomtoolkit/commands/`).

## Why a graph?

A family tree is naturally a directed graph: parent → child edges capture
descent, and that structure supports real graph-theory questions —
connectivity, shortest paths between relatives, cycle detection (someone
recorded as their own ancestor is a data error, and also a graph cycle) — for
free, using [networkx](https://networkx.org/).

## Installation

```bash
git clone https://github.com/stetho/gedcom-toolkit.git
cd gedcom-toolkit
pip install -e ".[dev]"
```

## Usage

```bash
gedcom stats data/sample/sample.ged
gedcom validate data/sample/sample.ged
```

## Sample data

`data/sample/sample.ged` is a small, synthetic five-person tree used for
tests and examples. No real family data is stored in this repository —
personal GEDCOM files are excluded via `.gitignore`.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Roadmap

- [x] `gedcom validate` — detect data problems: cycles, death-before-birth,
      implausible ages, orphaned records. Built first, deliberately: `rn`
      produces a prioritised research list, and that list is only trustworthy
      if the underlying tree isn't already broken.
- [x] `gedcom rn` ("research next") — a weighted list of who to research
      next, based on missing data and how many descendants are affected
- [x] `gedcom findid <name>` — GEDCOM names aren't unique (e.g. a
      great-grandfather, his father, and two distant cousins can all share
      a name); this looks up every individual matching a name and returns
      their unique xref_id plus dates, e.g. `I1234 Bob Smith 28-AUG-1908`.
      A prerequisite for `findrelationship` below.
- [x] `gedcom findrelationship <id-or-name> <id-or-name>` — find the
      relationship path between two individuals and name the relationship
      itself (sibling, cousin-N-times-removed, great-aunt, sister-in-law,
      etc.) via closest common ancestor. Falls back to showing just the
      chain when no unambiguous term applies (e.g. more distant in-laws).
- [x] `gedcom sources` — percentage of individuals and events with no
      source citation attached. A measure of how well-evidenced the tree
      is, not just how complete it is -- important for the tree to be
      credible to other researchers, not just populated.
- [x] `gedcom places` — detect place-name variants that likely refer to
      the same location (e.g. "Croydon", "Croydon, Surrey", "Croydon,
      Greater London") and suggest a normalised form with a confidence
      score. Dry-run report only, never auto-rewrites: some variants
      reflect genuine historical boundary changes (Croydon moved from
      Surrey into Greater London in 1965) rather than messy data, so
      merging them could erase real information.
- [x] `gedcom duplicates` — flag probable duplicate individuals *within
      a single file* (matching name + close dates) -- distinct from
      `merge` below, which compares *two* files. Reports signals (birth-year
      gap, shared parents) with an explanatory note rather than a bare
      verdict, since a namesake sibling can look identical to a duplicate.
- [x] `gedcom completeness` — percentage of individuals with both/one/no
      parents linked, broken down per generation (depth from nearest
      known root, not absolute era). Requires an acyclic tree.
- [ ] `gedcom diff` — compare two GEDCOM files (e.g. before/after an import)
- [ ] `gedcom surnames` — surname frequency and spelling-variant clustering
- [ ] `gedcom timeline` — chronological view of events, useful for spotting
      inconsistencies
- [ ] `gedcom geo` — plot migration paths across generations, where places
      are recorded
- [ ] `gedcom merge` — fuzzy-match probable duplicate individuals across
      two files
- [ ] `gedcom export --format graphml` — hand off to Gephi for visualisation

## Notebooks

`notebooks/` contains exploratory analysis of sample GEDCOM data — the
first pass at ideas before they're solidified into tested package code.

## License

MIT — see [LICENSE](LICENSE).
