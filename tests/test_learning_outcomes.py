"""
Tests for Learning Outcome Registry and Competencies
"""

from src.models.classification import ProvenanceType, VerificationStatus


def test_learning_outcomes_exist(seeded_repo):
    los = seeded_repo.get_learning_outcomes()
    assert len(los) >= 10


def test_learning_outcomes_provenance(seeded_repo):
    los = seeded_repo.get_learning_outcomes()
    for lo in los:
        assert lo["provenance_type"] in [ProvenanceType.OFFICIAL.value, ProvenanceType.INFERRED.value, ProvenanceType.PENDING.value]
        assert lo["verification_status"] == VerificationStatus.VERIFIED.value
        assert lo["source_doc_id"] == "CBSE_SCI_10_2026_27"
        assert lo["source_page"] in [2, 3, 4]


def test_learning_outcome_chapter_associations(seeded_repo):
    chapters = {c["chapter_id"] for c in seeded_repo.get_chapters()}
    los = seeded_repo.get_learning_outcomes()
    for lo in los:
        assert lo["related_chapter_id"] in chapters
