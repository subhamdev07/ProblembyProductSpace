"""
Unit Tests for Concept Graph Service: Algorithms, DAG Validation, and Traversal
"""

import pytest
from src.services.concept_graph_service import ConceptGraphService
from src.models.concept import (
    ConceptNode,
    ConceptEdge,
    RelationshipType,
    ConceptVerificationStatus,
)


def test_seeded_chapter_one_is_valid_dag(seeded_concept_repo, seeded_repo):
    service = ConceptGraphService(seeded_concept_repo, seeded_repo)
    result = service.validate_graph()

    assert result.is_valid is True
    assert result.is_dag is True
    assert result.cycle_detected is False
    assert result.cycle_path is None
    assert len(result.errors) == 0
    assert result.rules_evaluated == 8


def test_topological_learning_order(seeded_concept_repo):
    service = ConceptGraphService(seeded_concept_repo)
    topo = service.compute_topological_order()

    assert len(topo) == 29
    # Foundational concepts should precede dependent concepts
    assert topo.index("CPT-CH01-001") < topo.index("CPT-CH01-002")  # Reaction before Equation
    assert topo.index("CPT-CH01-002") < topo.index("CPT-CH01-006")  # Equation before Balanced Equation
    assert topo.index("CPT-CH01-006") < topo.index("CPT-CH01-007")  # Balanced Eq before Balancing Method
    assert topo.index("CPT-CH01-006") < topo.index("CPT-CH01-009")  # Balanced Eq before Combination Reaction
    assert topo.index("CPT-CH01-021") < topo.index("CPT-CH01-023")  # Oxidation before Redox


def test_transitive_prerequisites_traversal(seeded_concept_repo):
    service = ConceptGraphService(seeded_concept_repo)
    prereqs = service.get_transitive_prerequisites("CPT-CH01-007")  # Balancing equations

    # Prerequisite chain: Reaction -> Equation -> Skeletal Eq + Mass Conservation -> Balanced Eq
    assert "CPT-CH01-001" in prereqs
    assert "CPT-CH01-002" in prereqs
    assert "CPT-CH01-004" in prereqs
    assert "CPT-CH01-005" in prereqs
    assert "CPT-CH01-006" in prereqs


def test_transitive_dependents_traversal(seeded_concept_repo):
    service = ConceptGraphService(seeded_concept_repo)
    dependents = service.get_transitive_dependents("CPT-CH01-001")  # Chemical reaction

    # A large portion of Chapter 1 concepts descend from the foundational chemical reaction concept
    assert len(dependents) >= 20
    assert "CPT-CH01-002" in dependents
    assert "CPT-CH01-006" in dependents
    assert "CPT-CH01-007" in dependents
    assert "CPT-CH01-023" in dependents


def test_cycle_detection_with_complete_path_reporting():
    edges = [
        ConceptEdge(edge_id="E1", source_concept_id="A", target_concept_id="B", relationship_type=RelationshipType.PREREQUISITE_OF),
        ConceptEdge(edge_id="E2", source_concept_id="B", target_concept_id="C", relationship_type=RelationshipType.PREREQUISITE_OF),
        ConceptEdge(edge_id="E3", source_concept_id="C", target_concept_id="A", relationship_type=RelationshipType.PREREQUISITE_OF),
    ]
    service = ConceptGraphService(None)
    has_cycle, cycle_path = service.detect_prerequisite_cycle(node_ids=["A", "B", "C"], edges=edges)

    assert has_cycle is True
    assert cycle_path is not None
    assert cycle_path == ["A", "B", "C", "A"]


def test_related_edges_do_not_trigger_dag_cycle():
    # Mutual bidirectional RELATED_TO edges must be allowed and not counted as a DAG violation
    edges = [
        ConceptEdge(edge_id="R1", source_concept_id="X", target_concept_id="Y", relationship_type=RelationshipType.RELATED_TO),
        ConceptEdge(edge_id="R2", source_concept_id="Y", target_concept_id="X", relationship_type=RelationshipType.RELATED_TO),
    ]
    service = ConceptGraphService(None)
    has_cycle, cycle_path = service.detect_prerequisite_cycle(node_ids=["X", "Y"], edges=edges)

    assert has_cycle is False
    assert cycle_path is None


def test_cross_topic_relationships(seeded_concept_repo):
    service = ConceptGraphService(seeded_concept_repo)
    cross_topic = service.get_cross_topic_relationships("CH-01")

    assert len(cross_topic) >= 5
    # Chemical Equations (T01) is a prerequisite for Combination Reaction (T02)
    t01_to_t02 = [
        ct for ct in cross_topic
        if ct["source_topic"] == "CH01-T01" and ct["target_topic"] == "CH01-T02"
    ]
    assert len(t01_to_t02) >= 3


def test_validation_engine_catches_dangling_target(seeded_concept_repo, seeded_repo):
    # Add an edge targeting a nonexistent concept
    invalid_edge = ConceptEdge(
        edge_id="EDGE-DANGLING",
        source_concept_id="CPT-CH01-001",
        target_concept_id="CPT-NONEXISTENT",
        relationship_type=RelationshipType.PREREQUISITE_OF,
    )
    seeded_concept_repo.upsert_edge(invalid_edge)

    service = ConceptGraphService(seeded_concept_repo, seeded_repo)
    result = service.validate_graph()

    assert result.is_valid is False
    assert any("Rule CG-03 Violation" in err for err in result.errors)
