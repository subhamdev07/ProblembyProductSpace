"""
Unit Tests for Concept Graph Domain Models & Validation Rules
"""

import pytest
from pydantic import ValidationError
from src.models.concept import (
    ConceptNode,
    ConceptEdge,
    ConceptProvenance,
    ConceptType,
    RelationshipType,
    ConceptVerificationStatus,
    SourceStatus,
)


def test_valid_concept_node_creation():
    node = ConceptNode(
        concept_id="CPT-CH01-001",
        name="Chemical Reaction",
        canonical_name="chemical_reaction",
        description="A chemical transformation.",
        chapter_id="CH-01",
        topic_id="CH01-T01",
        subtopic_id="CH01-T01-S01",
        concept_type=ConceptType.FOUNDATIONAL,
        difficulty_level="EASY",
        source_status=SourceStatus.SOURCE_DERIVED,
        verification_status=ConceptVerificationStatus.VERIFIED,
    )
    assert node.concept_id == "CPT-CH01-001"
    assert node.canonical_name == "chemical_reaction"
    assert node.difficulty_level == "EASY"


def test_invalid_difficulty_level_rejected():
    with pytest.raises(ValidationError):
        ConceptNode(
            concept_id="CPT-CH01-001",
            name="Chemical Reaction",
            canonical_name="chemical_reaction",
            description="A chemical transformation.",
            chapter_id="CH-01",
            topic_id="CH01-T01",
            difficulty_level="SUPER_DIFFICULT",  # Invalid enum value
        )


def test_valid_concept_edge_creation():
    edge = ConceptEdge(
        edge_id="EDGE-001-PREREQ-002",
        source_concept_id="CPT-CH01-001",
        target_concept_id="CPT-CH01-002",
        relationship_type=RelationshipType.PREREQUISITE_OF,
        description="Concept 1 is prerequisite to Concept 2",
        confidence=0.95,
        verification_status=ConceptVerificationStatus.VERIFIED,
    )
    assert edge.source_concept_id == "CPT-CH01-001"
    assert edge.target_concept_id == "CPT-CH01-002"
    assert edge.relationship_type == RelationshipType.PREREQUISITE_OF


def test_self_loop_edge_forbidden():
    with pytest.raises(ValueError, match="Self-loops are forbidden"):
        ConceptEdge(
            edge_id="EDGE-LOOP",
            source_concept_id="CPT-CH01-001",
            target_concept_id="CPT-CH01-001",  # Self-loop
            relationship_type=RelationshipType.PREREQUISITE_OF,
        )


def test_provenance_model_validation():
    prov = ConceptProvenance(
        provenance_id="PROV-001",
        concept_id="CPT-CH01-001",
        source_document_id="NCERT_SCI_10_CH01",
        source_filename="jesc101.pdf",
        page_number=2,
        section_heading="1.1 Chemical Equations",
        extraction_method="NATIVE_PDF_PARSE",
        confidence=1.0,
        verification_status=ConceptVerificationStatus.SOURCE_VERIFIED,
        verbatim_text="Sample text quote from NCERT",
    )
    assert prov.page_number == 2
    assert prov.confidence == 1.0


def test_provenance_confidence_out_of_bounds():
    with pytest.raises(ValidationError):
        ConceptProvenance(
            provenance_id="PROV-ERR",
            concept_id="CPT-CH01-001",
            source_document_id="NCERT_SCI_10_CH01",
            source_filename="jesc101.pdf",
            extraction_method="TEST",
            confidence=1.5,  # > 1.0 forbidden
        )
