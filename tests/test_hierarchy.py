"""
Tests for Curriculum Hierarchy: Units, Chapters, and Academic Session
"""

from src.services.curriculum_service import CurriculumService


def test_units_count_and_properties(seeded_repo):
    units = seeded_repo.get_units()
    assert len(units) == 5

    unit_marks = {u["unit_id"]: u["marks"] for u in units}
    expected_marks = {
        "UNIT-01": 25,
        "UNIT-02": 25,
        "UNIT-03": 12,
        "UNIT-04": 13,
        "UNIT-05": 5,
    }
    assert unit_marks == expected_marks
    assert sum(unit_marks.values()) == 80  # Theory marks total 80


def test_all_13_chapters_registered(seeded_repo):
    chapters = seeded_repo.get_chapters()
    assert len(chapters) == 13

    # Verify sequential numbers 1 to 13
    ch_nums = [c["chapter_number"] for c in chapters]
    assert ch_nums == list(range(1, 14))

    # Verify official chapter names
    expected_names = [
        "Chemical Reactions and Equations",
        "Acids, Bases and Salts",
        "Metals and Non-Metals",
        "Carbon and Its Compounds",
        "Life Processes",
        "Control and Coordination",
        "How Do Organisms Reproduce?",
        "Heredity",
        "Light – Reflection and Refraction",
        "The Human Eye and the Colourful World",
        "Electricity",
        "Magnetic Effects of Electric Current",
        "Our Environment",
    ]
    for i, name in enumerate(expected_names):
        assert chapters[i]["name"] == name


def test_unit_chapter_mappings(seeded_repo):
    chapters = seeded_repo.get_chapters()
    unit_ch_map = {}
    for c in chapters:
        unit_ch_map.setdefault(c["unit_id"], []).append(c["chapter_number"])

    # Official CBSE Unit distribution:
    # Unit I: Chapters 1, 2, 3, 4
    # Unit II: Chapters 5, 6, 7, 8
    # Unit III: Chapters 9, 10
    # Unit IV: Chapters 11, 12
    # Unit V: Chapter 13
    assert unit_ch_map["UNIT-01"] == [1, 2, 3, 4]
    assert unit_ch_map["UNIT-02"] == [5, 6, 7, 8]
    assert unit_ch_map["UNIT-03"] == [9, 10]
    assert unit_ch_map["UNIT-04"] == [11, 12]
    assert unit_ch_map["UNIT-05"] == [13]


def test_hierarchy_tree_structure(seeded_repo):
    curr_service = CurriculumService(seeded_repo)
    tree = curr_service.get_full_hierarchy()

    assert tree["total_units"] == 5
    assert tree["total_chapters"] == 13
    assert len(tree["units"]) == 5
    for u in tree["units"]:
        assert len(u["chapters"]) > 0
        for ch in u["chapters"]:
            assert len(ch["topics"]) > 0
