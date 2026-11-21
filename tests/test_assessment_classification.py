"""
Tests for Assessment Classifications and Scope Boundary Rules
"""

from src.models.classification import AssessmentClassification


def test_all_topics_have_valid_assessment_classification(seeded_repo):
    topics = seeded_repo.get_topics()
    valid_classes = {e.value for e in AssessmentClassification}
    for t in topics:
        assert t["assessment_status"] in valid_classes


def test_formative_only_topics(seeded_repo):
    topics = seeded_repo.get_topics()
    formative_topics = [t for t in topics if t["assessment_status"] == AssessmentClassification.FORMATIVE.value]
    assert len(formative_topics) >= 3

    formative_names = [t["name"] for t in formative_topics]
    assert any("Periodic Classification" in n for n in formative_names)
    assert any("Evolution" in n for n in formative_names)
    assert any("Motor" in n or "Generator" in n for n in formative_names)


def test_excluded_scope_topics(seeded_repo):
    topics = seeded_repo.get_topics()
    excluded = [t for t in topics if t["assessment_status"] == AssessmentClassification.NOT_IN_CURRENT_SCOPE.value]
    assert len(excluded) >= 1
    assert any("Sunrise" in t["name"] or "Sunset" in t["name"] for t in excluded)


def test_summative_topics_majority(seeded_repo):
    topics = seeded_repo.get_topics()
    summative = [t for t in topics if t["assessment_status"] == AssessmentClassification.SUMMATIVE.value]
    # Board summative syllabus should comprise the majority of core instructional topics
    assert len(summative) >= 35
