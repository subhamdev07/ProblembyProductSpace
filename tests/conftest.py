"""
Pytest Fixtures for P0 Syllabus Foundation
"""

import pytest
import os
import gc
import tempfile
from src.storage.database import Database, CurriculumRepository
from src.storage.concept_repository import ConceptRepository
from src.services.source_service import SourceDocumentService
from src.services.extraction_service import CurriculumExtractionService
from src.services.concept_extraction_service import ConceptExtractionService
from src.storage.question_repository import QuestionRepository
from src.services.question_bank_service import QuestionBankService


@pytest.fixture
def temp_db():
    """Provides a temporary, isolated SQLite database."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = Database(path)
    yield db
    # Teardown: ensure garbage collection releases connection handles before removal
    gc.collect()
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


@pytest.fixture
def repo(temp_db):
    """Provides a CurriculumRepository connected to temp_db."""
    return CurriculumRepository(temp_db)


@pytest.fixture
def concept_repo(temp_db):
    """Provides a ConceptRepository connected to temp_db."""
    return ConceptRepository(temp_db)


@pytest.fixture
def seeded_repo(repo):
    """Provides a repository pre-populated with source docs and complete curriculum data."""
    src_service = SourceDocumentService(repo, sources_dir="sources")
    src_service.register_available_sources()
    extractor = CurriculumExtractionService(repo)
    extractor.populate_all()
    return repo


@pytest.fixture
def seeded_concept_repo(seeded_repo, concept_repo):
    """Provides a repository pre-populated with complete curriculum and Chapter 1 concept graph."""
    extractor = ConceptExtractionService(concept_repo)
    extractor.extract_and_seed_chapter_one()
    return concept_repo


@pytest.fixture
def question_repo(temp_db):
    """Provides a QuestionRepository connected to temp_db."""
    return QuestionRepository(temp_db)


@pytest.fixture
def seeded_question_bank(seeded_concept_repo, question_repo):
    """Provides a repository pre-populated with curriculum, concept graph, and Chapter 1 Question Bank."""
    service = QuestionBankService(question_repo)
    service.seed_chapter_one_question_bank()
    return question_repo

