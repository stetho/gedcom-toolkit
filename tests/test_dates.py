from gedcomtoolkit.dates import extract_year


def test_simple_date():
    assert extract_year("1 JAN 1900") == 1900


def test_approximate_date():
    assert extract_year("ABT 1850") == 1850


def test_range_date_takes_first_year():
    assert extract_year("BET 1820 AND 1825") == 1820


def test_bare_year():
    assert extract_year("1850") == 1850


def test_none_input():
    assert extract_year(None) is None


def test_empty_string():
    assert extract_year("") is None


def test_no_year_present():
    assert extract_year("ABT") is None
