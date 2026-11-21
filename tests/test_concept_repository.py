"""
Unit Tests for Concept Graph Repository Persistence & Integrity
"""

import pytest
import sqlite3
from src.models.concept import (
    ConceptNode,
    ConceptEdge,
    ConceptProvenance,
    ConceptType,
    RelationshipType,
    ConceptVerificationStatus,
    SourceStatus,
)


def test_concept_crud_and_retrieval(seeded_repo, concept_repo):
    node = ConceptNode(
        concept_id="CPT-CH01-TEST1",
        name="Test Concept",
        canonical_name="test_concept_unique",
        description="A test concept description.",
        chapter_id="CH-01",
        topic_id="CH01-T01",
        concept_type=ConceptType.CORE,
        difficulty_level="MEDIUM",
        source_status=SourceStatus.SOURCE_DERIVED,
        verification_status=ConceptVerificationStatus.VERIFIED,
    )
    concept_repo.upsert_concept(node)

    retrieved = concept_repo.get_concept("CPT-CH01-TEST1")
    assert retrieved is not None
    assert retrieved.name == "Test Concept"
    assert retrieved.canonical_name == "test_concept_unique"

    by_slug = concept_repo.get_concept_by_canonical_name("test_concept_unique")
    assert by_slug is not None
    assert by_slug.concept_id == "CPT-CH01-TEST1"


def test_invalid_chapter_foreign_key_rejected(seeded_repo, concept_repo):
    node = ConceptNode(
        concept_id="CPT-INVALID-CH",
        name="Invalid Chapter Concept",
        canonical_name="invalid_chapter_cpt",
        description="Description",
        chapter_id="CH-999",  # Does not exist
        topic_id="CH01-T01",
    )
    with pytest.raises(sqlite3.IntegrityError):
        concept_repo.upsert_concept(node)


def test_duplicate_canonical_name_rejected_at_db(seeded_repo, concept_repo):
    node1 = ConceptNode(
        concept_id="CPT-CH01-U1",
        name="Concept 1",
        canonical_name="unique_slug_same",
        description="Description 1",
        chapter_id="CH-01",
        topic_id="CH01-T01",
    )
    concept_repo.upsert_concept(node1)

    node2 = ConceptNode(
        concept_id="CPT-CH01-U2",
        name="Concept 2",
        canonical_name="unique_slug_same",  # Duplicate canonical name
        description="Description 2",
        chapter_id="CH-01",
        topic_id="CH01-T01",
    )
    with pytest.raises(sqlite3.IntegrityError):
        concept_repo.upsert_concept(node2)


def test_edge_persistence_and_queries(seeded_repo, concept_repo):
    node_a = ConceptNode(
        concept_id="CPT-TEST-A",
        name="Node A",
        canonical_name="node_a",
        description="A",
        chapter_id="CH-01",
        topic_id="CH01-T01",
    )
    node_b = ConceptNode(
        concept_id="CPT-TEST-B",
        name="Node B",
        canonical_name="node_b",
        description="B",
        chapter_id="CH-01",
        topic_id="CH01-T01",
    )
    concept_repo.upsert_concept(node_a)
    concept_repo.upsert_concept(node_b)

    edge = ConceptEdge(
        edge_id="EDGE-A-PREREQ-B",
        source_concept_id="CPT-TEST-A",
        target_concept_id="CPT-TEST-B",
        relationship_type=RelationshipType.PREREQUISITE_OF,
        description="A is prerequisite of B",
    )
    concept_repo.upsert_edge(edge)

    prereqs = concept_repo.get_direct_prerequisites("CPT-TEST-B")
    assert prereqs == ["CPT-TEST-A"]

    dependents = concept_repo.get_direct_dependents("CPT-TEST-A")
    assert dependents == ["CPT-TEST-B"]


def test_duplicate_edge_unique_constraint(seeded_repo, concept_repo):
    node_a = ConceptNode(
        concept_id="CPT-DUP-A",
        name="Node A",
        canonical_name="node_dup_a",
        description="A",
        chapter_id="CH-01",
        topic_id="CH01-T01",
    )
    node_b = ConceptNode(
        concept_id="CPT-DUP-B",
        name="Node B",
        canonical_name="node_dup_b",
        description="B",
        chapter_id="CH-01",
        topic_id="CH01-T01",
    )
    concept_repo.upsert_concept(node_a)
    concept_repo.upsert_concept(node_b)

    edge1 = ConceptEdge(
        edge_id="EDGE-DUP-1",
        source_concept_id="CPT-DUP-A",
        target_concept_id="CPT-DUP-B",
        relationship_type=RelationshipType.PREREQUISITE_OF,
    )
    concept_repo.upsert_edge(edge1)

    edge2 = ConceptEdge(
        edge_id="EDGE-DUP-2",
        source_concept_id="CPT-DUP-A",
        target_concept_id="CPT-DUP-B",
        relationship_type=RelationshipType.PREREQUISITE_OF,  # Same (src, tgt, type)
    )
    with pytest.raises(sqlite3.IntegrityError):
        concept_repo.upsert_edge(edge2)


def test_provenance_persistence_and_linkage(seeded_repo, concept_repo):
    node = ConceptNode(
        concept_id="CPT-PROV-TEST",
        name="Prov Concept",
        canonical_name="prov_concept",
        description="Description",
        chapter_id="CH-01",
        topic_id="CH01-T01",
    )
    prov = ConceptProvenance(
        provenance_id="PROV-TEST-01",
        concept_id="CPT-PROV-TEST",
        source_document_id="NCERT_SCI_10_CH01",
        source_filename="jesc101.pdf",
        page_number=3,
        section_heading="1.1.2 Balanced Chemical Equations",
        extraction_method="NATIVE_PDF_PARSE",
        confidence=1.0,
        verification_status=ConceptVerificationStatus.SOURCE_VERIFIED,
        verbatim_text="Chemical equations represent chemical changes.",
    )
    node.provenance_records = [prov]
    concept_repo.upsert_concept(node)

    retrieved_prov = concept_repo.get_provenance_for_concept("CPT-PROV-TEST")
    assert len(retrieved_prov) == 1
    assert retrieved_prov[0].page_number == 3
    assert retrieved_prov[0].source_document_id == "NCERT_SCI_10_CH01"
