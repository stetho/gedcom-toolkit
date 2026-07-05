from pathlib import Path

import pytest

from gedcomtoolkit.parser import parse_gedcom

SAMPLE_GEDCOM = Path(__file__).parent.parent / "data" / "sample" / "sample.ged"


@pytest.fixture
def sample_tree():
    return parse_gedcom(SAMPLE_GEDCOM)
