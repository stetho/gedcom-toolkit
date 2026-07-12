"""
Thin wrapper around ged4py.

This is the only module that should import from ged4py. Everything else
in the package works with gedcomtoolkit.models.FamilyTree.
"""

from __future__ import annotations

from pathlib import Path

from ged4py.parser import GedcomReader

from gedcomtoolkit.models import Family, FamilyTree, Individual


def parse_gedcom(path: str | Path) -> FamilyTree:
    tree = FamilyTree()

    with GedcomReader(str(path)) as reader:
        for indi in reader.records0("INDI"):
            given, surname = _split_name(indi)
            birt = indi.sub_tag("BIRT")
            deat = indi.sub_tag("DEAT")
            famc = indi.sub_tags("FAMC")
            fams = indi.sub_tags("FAMS")

            tree.individuals[indi.xref_id] = Individual(
                xref_id=indi.xref_id,
                given=given,
                surname=surname,
                sex=indi.sex,
                birth_date=_date_str(birt),
                death_date=_date_str(deat),
                birth_sourced=_has_source(birt),
                death_sourced=_has_source(deat),
                birth_place=_place_str(birt),
                death_place=_place_str(deat),
                family_as_child=famc[0].xref_id if famc else None,
                families_as_spouse=[f.xref_id for f in fams],
            )

        for fam in reader.records0("FAM"):
            husb = fam.sub_tag("HUSB")
            wife = fam.sub_tag("WIFE")
            children = fam.sub_tags("CHIL")
            marr = fam.sub_tag("MARR")

            tree.families[fam.xref_id] = Family(
                xref_id=fam.xref_id,
                husband_id=husb.xref_id if husb else None,
                wife_id=wife.xref_id if wife else None,
                marriage_date=_date_str(marr),
                marriage_sourced=_has_source(marr),
                marriage_place=_place_str(marr),
                child_ids=[c.xref_id for c in children],
            )

    return tree


def _date_str(event_record) -> str | None:
    """
    ged4py returns DATE values as DateValueSimple/DateValueRange objects
    (not plain strings), so events without a resolvable date, or without
    the sub-tag at all, need guarding.
    """
    if event_record is None:
        return None
    value = event_record.sub_tag_value("DATE")
    return str(value) if value is not None else None


def _has_source(event_record) -> bool:
    """Whether a BIRT/DEAT/MARR sub-record has a SOUR citation attached."""
    if event_record is None:
        return False
    return event_record.sub_tag("SOUR") is not None


def _place_str(event_record) -> str | None:
    """Raw PLAC value on a BIRT/DEAT/MARR sub-record, if present."""
    if event_record is None:
        return None
    value = event_record.sub_tag_value("PLAC")
    return str(value) if value else None


def _split_name(indi) -> tuple[str | None, str | None]:
    """ged4py's Name object already splits given/surname; guard for blanks."""
    name = indi.name
    if name is None:
        return None, None
    given = name.given or None
    surname = name.surname or None
    return given, surname
