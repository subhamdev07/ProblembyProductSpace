"""
Tests for Idempotency and Consistent Re-import
"""

from src.services.source_service import SourceDocumentService
from src.services.extraction_service import CurriculumExtractionService
from src.services.validation_service import CurriculumValidationEngine


def test_idempotent_reimport(repo):
    src_service = SourceDocumentService(repo, sources_dir="sources")
    extractor = CurriculumExtractionService(repo)

    # First run
    src_service.register_available_sources()
    extractor.populate_all()

    units_count_1 = len(repo.get_units())
    chapters_count_1 = len(repo.get_chapters())
    topics_count_1 = len(repo.get_topics())
    subtopics_count_1 = len(repo.get_subtopics())
    los_count_1 = len(repo.get_learning_outcomes())

    # Second run
    src_service.register_available_sources()
    extractor.populate_all()

    units_count_2 = len(repo.get_units())
    chapters_count_2 = len(repo.get_chapters())
    topics_count_2 = len(repo.get_topics())
    subtopics_count_2 = len(repo.get_subtopics())
    los_count_2 = len(repo.get_learning_outcomes())

    assert units_count_1 == units_count_2 == 5
    assert chapters_count_1 == chapters_count_2 == 13
    assert topics_count_1 == topics_count_2
    assert subtopics_count_1 == subtopics_count_2
    assert los_count_1 == los_count_2

    # Validation should still be 100% clean
    engine = CurriculumValidationEngine(repo)
    result = engine.validate()
    assert result.is_valid is True
    assert len(result.errors) == 0
