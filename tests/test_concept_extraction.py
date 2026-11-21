"""
Unit Tests for Concept Extraction Service & LLM Assistance
"""

import json
import pytest
from src.services.concept_extraction_service import (
    ConceptExtractionService,
    LLMConceptCandidate,
)
from src.models.concept import ConceptVerificationStatus


def test_chapter_one_extraction_seeding(seeded_repo, concept_repo):
    extractor = ConceptExtractionService(concept_repo)
    result = extractor.extract_and_seed_chapter_one()

    assert result["status"] == "SUCCESS"
    assert result["concepts_seeded"] == 29
    assert result["provenance_records_seeded"] == 30
    assert result["edges_seeded"] == 46

    # Verify concepts retrieved from database
    concepts = concept_repo.get_concepts_by_chapter("CH-01")
    assert len(concepts) == 29

    # Verify all concepts are VERIFIED
    for c in concepts:
        assert c.verification_status == ConceptVerificationStatus.VERIFIED
        assert len(c.provenance_records) > 0


def test_extraction_idempotency(seeded_repo, concept_repo):
    extractor = ConceptExtractionService(concept_repo)
    # Run once
    extractor.extract_and_seed_chapter_one()
    # Run second time
    res2 = extractor.extract_and_seed_chapter_one()

    assert res2["status"] == "SUCCESS"
    # Counts should remain exactly 29, 46, 30 without duplication
    stats = concept_repo.get_graph_statistics()
    assert stats["total_concepts"] == 29
    assert stats["total_edges"] == 46
    assert stats["total_provenance_records"] == 30


def test_llm_candidate_proposal_mocked(concept_repo):
    mock_json = json.dumps([
        {
            "name": "Candidate Concept",
            "canonical_name": "candidate_concept",
            "description": "Candidate description extracted by LLM.",
            "concept_type": "CORE",
            "difficulty_level": "MEDIUM",
            "prerequisites": ["CPT-CH01-001"],
        }
    ])

    extractor = ConceptExtractionService(concept_repo)
    candidates = extractor.propose_candidate_concepts_with_llm(
        chapter_title="Chemical Reactions",
        section_text="Sample text for extraction",
        mock_response=mock_json,
    )

    assert len(candidates) == 1
    assert candidates[0].name == "Candidate Concept"
    assert candidates[0].canonical_name == "candidate_concept"
    assert candidates[0].prerequisites == ["CPT-CH01-001"]


def test_llm_candidate_proposal_malformed_json_raises_error(concept_repo):
    mock_invalid_json = "{ malformed json "

    extractor = ConceptExtractionService(concept_repo)
    with pytest.raises(Exception):
        extractor.propose_candidate_concepts_with_llm(
            chapter_title="Chemical Reactions",
            section_text="Sample text for extraction",
            mock_response=mock_invalid_json,
        )


def test_extraction_provenance_integrity(seeded_repo, concept_repo):
    extractor = ConceptExtractionService(concept_repo)
    extractor.extract_and_seed_chapter_one()

    c1 = concept_repo.get_concept("CPT-CH01-001")
    assert c1 is not None
    assert len(c1.provenance_records) == 2
    prov = c1.provenance_records[0]
    assert prov.source_document_id == "NCERT_SCI_10_CH01"
    assert prov.source_filename == "jesc101.pdf"
    assert prov.page_number == 1
    assert "chemical reaction has taken place" in prov.verbatim_text
