"""
Minimal date handling for validation purposes.

gedcomtoolkit stores dates as the raw display string ged4py produces
(e.g. "1 JAN 1900", "ABT 1850", "BET 1820 AND 1825" for approximate or
range dates -- GEDCOM allows all of these). Validation only needs a year
to do arithmetic on, so this pulls the first 4-digit year out of the
string rather than attempting a full GEDCOM date parse. Good enough for
plausibility checks; not intended for exact-date logic.
"""

from __future__ import annotations

import re

_YEAR_RE = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")


def extract_year(date_str: str | None) -> int | None:
    """Return the first 4-digit year found in a raw GEDCOM date string, or None."""
    if not date_str:
        return None
    match = _YEAR_RE.search(date_str)
    return int(match.group(1)) if match else None
