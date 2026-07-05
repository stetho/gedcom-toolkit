def test_parses_all_individuals(sample_tree):
    assert len(sample_tree.individuals) == 5


def test_parses_all_families(sample_tree):
    assert len(sample_tree.families) == 2


def test_individual_name_split(sample_tree):
    john = sample_tree.get_individual("@I1@")
    assert john.given == "John"
    assert john.surname == "Smith"
    assert john.full_name == "John Smith"


def test_birth_and_death_dates(sample_tree):
    john = sample_tree.get_individual("@I1@")
    assert john.birth_date == "1 JAN 1900"
    assert john.death_date == "1 JAN 1970"


def test_living_flag(sample_tree):
    john = sample_tree.get_individual("@I1@")  # has a death date
    mary = sample_tree.get_individual("@I2@")  # no death date recorded

    assert john.is_living is False
    assert mary.is_living is True


def test_family_links(sample_tree):
    fam1 = sample_tree.get_family("@F1@")
    assert fam1.husband_id == "@I1@"
    assert fam1.wife_id == "@I2@"
    assert fam1.child_ids == ["@I3@"]


def test_individual_family_membership(sample_tree):
    alice = sample_tree.get_individual("@I3@")
    assert alice.family_as_child == "@F1@"
    assert alice.families_as_spouse == ["@F2@"]
