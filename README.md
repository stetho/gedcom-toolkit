# gedcom-toolkit

This is another project that's sat on my Gitea server for years. I'm researching
my family tree and found myself parsing lots of data - mainly but not exclusively -
GEDCOM files with one line Python scripts. I then started to turn the most common
actions in to a command-line tool and Python library for exploring, validating, and
querying GEDCOM family tree files and then life got in the way so it didn't get
touched for years. I've decided to ressurect it and put it in my portfolio not
just because it's a useful tool but because it's cyclic graphs, directed graphs,
incomplete data, data that's difficult to clean, analysis, visualisation - all the
things that would look good to a potential employer if they ever see this. 

GEDCOM is the standard file format genealogy software uses to store family
trees. It's a genuinely awkward format: a large amount of loosely structured
text data, riddled with real-world data quality problems (missing dates,
duplicate people, impossible relationships), and hard to query directly. This
project treats a family tree for what it actually is - a directed graph - and
builds tools on top of that idea.

## What it does

```bash
gedcom stats family.ged
```

prints summary statistics about a family tree: how many people, how many
families, how many disconnected branches, how much data is missing.

More commands are planned - see [Roadmap](#roadmap) below. The CLI is
structured so that adding a new one is a small, self-contained change (see
`gedcomtoolkit/commands/`).

## Why a graph?

A family tree is naturally a directed graph: parent → child edges capture
descent, and that structure supports real graph-theory questions -
connectivity, shortest paths between relatives, cycle detection (someone
recorded as their own ancestor is a data error, and also a graph cycle) - for
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
```

## Sample data

`data/sample/sample.ged` is a small, synthetic five-person tree used for
tests and examples. No real family data is stored in this repository -
personal GEDCOM files are excluded via `.gitignore`.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Roadmap

- [ ] `gedcom validate` - detect data problems: cycles, death-before-birth,
      implausible ages, orphaned records
- [ ] `gedcom rn` ("research next") - a weighted list of who to research
      next, based on missing data and how many descendants are affected
- [ ] `gedcom diff` - compare two GEDCOM files (e.g. before/after an import)
- [ ] `gedcom surnames` - surname frequency and spelling-variant clustering
- [ ] `gedcom timeline` - chronological view of events, useful for spotting
      inconsistencies
- [ ] `gedcom fan` - export a fan chart or descendant tree as SVG
- [ ] `gedcom geo` - plot migration paths across generations, where places
      are recorded
- [ ] `gedcom export --format graphml` - hand off to Gephi for visualisation
- [ ] `gedcom merge` - fuzzy-match probable duplicate individuals across
      two files

## Notebooks

`notebooks/` contains exploratory analysis of sample GEDCOM data - the
first pass at ideas before they're solidified into tested package code.

## License

MIT - see [LICENSE](LICENSE).
