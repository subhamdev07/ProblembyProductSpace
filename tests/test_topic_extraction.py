"""
Tests for Topic and Subtopic Extraction
"""


def test_every_chapter_has_topics(seeded_repo):
    chapters = seeded_repo.get_chapters()
    for ch in chapters:
        topics = seeded_repo.get_topics(ch["chapter_id"])
        assert len(topics) >= 1, f"Chapter {ch['chapter_id']} has no extracted topics"


def test_unique_topic_ids(seeded_repo):
    topics = seeded_repo.get_topics()
    ids = [t["topic_id"] for t in topics]
    assert len(ids) == len(set(ids)), "Duplicate topic IDs detected"


def test_subtopics_exist_and_mapped(seeded_repo):
    subtopics = seeded_repo.get_subtopics()
    assert len(subtopics) > 40
    topic_ids = {t["topic_id"] for t in seeded_repo.get_topics()}
    for st in subtopics:
        assert st["topic_id"] in topic_ids
        assert st["name"] is not None
        assert st["sequence_order"] >= 1


def test_chapter_one_detailed_topics(seeded_repo):
    ch1_topics = seeded_repo.get_topics("CH-01")
    names = [t["name"] for t in ch1_topics]
    assert any("Chemical Equations" in n for n in names)
    assert any("Types of Chemical Reactions" in n for n in names)
    assert any("Oxidation and Reduction" in n for n in names)
    assert any("Periodic Classification" in n for n in names)
