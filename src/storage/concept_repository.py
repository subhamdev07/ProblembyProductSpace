"""
Concept Graph Repository Layer
Provides transactional SQLite storage and retrieval for Concept Nodes,
Relationship Edges, and Source Provenance citations.
"""

import json
from typing import List, Dict, Any, Optional
from src.storage.database import Database
from src.models.concept import (
    ConceptNode,
    ConceptEdge,
    ConceptProvenance,
    ConceptType,
    RelationshipType,
    ConceptVerificationStatus,
    SourceStatus,
)


class ConceptRepository:
    """
    CRUD and query operations for concept graph entities.
    """

    def __init__(self, db: Database):
        self.db = db

    # -------------------------------------------------------------
    # Concept Nodes
    # -------------------------------------------------------------

    def upsert_concept(self, concept: ConceptNode) -> None:
        """
        Inserts or updates a concept node.
        """
        sql = """
        INSERT INTO concepts (
            concept_id, name, canonical_name, description, chapter_id,
            topic_id, subtopic_id, concept_type, difficulty_level,
            learning_objective, source_status, verification_status,
            metadata_json, updated_at
        ) VALUES (
            :concept_id, :name, :canonical_name, :description, :chapter_id,
            :topic_id, :subtopic_id, :concept_type, :difficulty_level,
            :learning_objective, :source_status, :verification_status,
            :metadata_json, CURRENT_TIMESTAMP
        ) ON CONFLICT(concept_id) DO UPDATE SET
            name = excluded.name,
            canonical_name = excluded.canonical_name,
            description = excluded.description,
            chapter_id = excluded.chapter_id,
            topic_id = excluded.topic_id,
            subtopic_id = excluded.subtopic_id,
            concept_type = excluded.concept_type,
            difficulty_level = excluded.difficulty_level,
            learning_objective = excluded.learning_objective,
            source_status = excluded.source_status,
            verification_status = excluded.verification_status,
            metadata_json = excluded.metadata_json,
            updated_at = CURRENT_TIMESTAMP;
        """
        params = {
            "concept_id": concept.concept_id,
            "name": concept.name,
            "canonical_name": concept.canonical_name,
            "description": concept.description,
            "chapter_id": concept.chapter_id,
            "topic_id": concept.topic_id,
            "subtopic_id": concept.subtopic_id,
            "concept_type": concept.concept_type.value if hasattr(concept.concept_type, "value") else concept.concept_type,
            "difficulty_level": concept.difficulty_level,
            "learning_objective": concept.learning_objective,
            "source_status": concept.source_status.value if hasattr(concept.source_status, "value") else concept.source_status,
            "verification_status": concept.verification_status.value if hasattr(concept.verification_status, "value") else concept.verification_status,
            "metadata_json": json.dumps(concept.metadata or {}),
        }

        with self.db.get_connection() as conn:
            conn.execute(sql, params)

        # Upsert any embedded provenance records
        for prov in concept.provenance_records:
            self.upsert_provenance(prov)

    def get_concept(self, concept_id: str) -> Optional[ConceptNode]:
        """
        Retrieves a concept by ID along with its provenance records.
        """
        sql = "SELECT * FROM concepts WHERE concept_id = ?;"
        with self.db.get_connection() as conn:
            row = conn.execute(sql, (concept_id,)).fetchone()
            if not row:
                return None
            return self._row_to_concept(row)

    def get_concept_by_canonical_name(self, canonical_name: str) -> Optional[ConceptNode]:
        """
        Retrieves a concept by canonical name.
        """
        sql = "SELECT * FROM concepts WHERE canonical_name = ?;"
        with self.db.get_connection() as conn:
            row = conn.execute(sql, (canonical_name,)).fetchone()
            if not row:
                return None
            return self._row_to_concept(row)

    def get_concepts_by_chapter(self, chapter_id: str) -> List[ConceptNode]:
        """
        Retrieves all concepts belonging to a chapter.
        """
        sql = "SELECT * FROM concepts WHERE chapter_id = ? ORDER BY concept_id;"
        with self.db.get_connection() as conn:
            rows = conn.execute(sql, (chapter_id,)).fetchall()
            return [self._row_to_concept(r) for r in rows]

    def get_concepts_by_topic(self, topic_id: str) -> List[ConceptNode]:
        """
        Retrieves all concepts belonging to a topic.
        """
        sql = "SELECT * FROM concepts WHERE topic_id = ? ORDER BY concept_id;"
        with self.db.get_connection() as conn:
            rows = conn.execute(sql, (topic_id,)).fetchall()
            return [self._row_to_concept(r) for r in rows]

    def get_all_concepts(self) -> List[ConceptNode]:
        """
        Retrieves all concepts across the entire curriculum.
        """
        sql = "SELECT * FROM concepts ORDER BY chapter_id, concept_id;"
        with self.db.get_connection() as conn:
            rows = conn.execute(sql).fetchall()
            return [self._row_to_concept(r) for r in rows]

    def _row_to_concept(self, row: Any) -> ConceptNode:
        concept_id = row["concept_id"]
        prov_list = self.get_provenance_for_concept(concept_id)
        metadata = {}
        if row["metadata_json"]:
            try:
                metadata = json.loads(row["metadata_json"])
            except Exception:
                metadata = {}

        return ConceptNode(
            concept_id=row["concept_id"],
            name=row["name"],
            canonical_name=row["canonical_name"],
            description=row["description"],
            chapter_id=row["chapter_id"],
            topic_id=row["topic_id"],
            subtopic_id=row["subtopic_id"],
            concept_type=ConceptType(row["concept_type"]),
            difficulty_level=row["difficulty_level"],
            learning_objective=row["learning_objective"],
            source_status=SourceStatus(row["source_status"]),
            verification_status=ConceptVerificationStatus(row["verification_status"]),
            metadata=metadata,
            provenance_records=prov_list,
            created_at=str(row["created_at"]) if row["created_at"] else None,
            updated_at=str(row["updated_at"]) if row["updated_at"] else None,
        )

    # -------------------------------------------------------------
    # Concept Relationships (Edges)
    # -------------------------------------------------------------

    def upsert_edge(self, edge: ConceptEdge) -> None:
        """
        Inserts or updates a concept relationship edge.
        """
        sql = """
        INSERT INTO concept_relationships (
            edge_id, source_concept_id, target_concept_id, relationship_type,
            description, confidence, verification_status, source_provenance_json
        ) VALUES (
            :edge_id, :source_concept_id, :target_concept_id, :relationship_type,
            :description, :confidence, :verification_status, :source_provenance_json
        ) ON CONFLICT(edge_id) DO UPDATE SET
            source_concept_id = excluded.source_concept_id,
            target_concept_id = excluded.target_concept_id,
            relationship_type = excluded.relationship_type,
            description = excluded.description,
            confidence = excluded.confidence,
            verification_status = excluded.verification_status,
            source_provenance_json = excluded.source_provenance_json;
        """
        params = {
            "edge_id": edge.edge_id,
            "source_concept_id": edge.source_concept_id,
            "target_concept_id": edge.target_concept_id,
            "relationship_type": edge.relationship_type.value if hasattr(edge.relationship_type, "value") else edge.relationship_type,
            "description": edge.description,
            "confidence": edge.confidence,
            "verification_status": edge.verification_status.value if hasattr(edge.verification_status, "value") else edge.verification_status,
            "source_provenance_json": json.dumps(edge.source_provenance or {}),
        }

        with self.db.get_connection() as conn:
            conn.execute(sql, params)

    def get_edge(self, edge_id: str) -> Optional[ConceptEdge]:
        """
        Retrieves a relationship edge by ID.
        """
        sql = "SELECT * FROM concept_relationships WHERE edge_id = ?;"
        with self.db.get_connection() as conn:
            row = conn.execute(sql, (edge_id,)).fetchone()
            if not row:
                return None
            return self._row_to_edge(row)

    def get_edges(
        self,
        chapter_id: Optional[str] = None,
        relationship_type: Optional[RelationshipType] = None,
    ) -> List[ConceptEdge]:
        """
        Retrieves relationship edges with optional chapter or type filtering.
        """
        conditions = []
        params = []

        if relationship_type:
            rel_val = relationship_type.value if hasattr(relationship_type, "value") else str(relationship_type)
            conditions.append("r.relationship_type = ?")
            params.append(rel_val)

        if chapter_id:
            conditions.append("c.chapter_id = ?")
            params.append(chapter_id)

        sql = """
        SELECT r.* FROM concept_relationships r
        JOIN concepts c ON r.source_concept_id = c.concept_id
        """
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY r.edge_id;"

        with self.db.get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_edge(r) for r in rows]

    def get_all_edges(self) -> List[ConceptEdge]:
        """
        Retrieves all relationship edges in the database.
        """
        sql = "SELECT * FROM concept_relationships ORDER BY edge_id;"
        with self.db.get_connection() as conn:
            rows = conn.execute(sql).fetchall()
            return [self._row_to_edge(r) for r in rows]

    def get_direct_prerequisites(self, concept_id: str) -> List[str]:
        """
        Returns IDs of concepts that are prerequisites for concept_id.
        (source_concept_id is PREREQUISITE_OF target_concept_id)
        """
        sql = """
        SELECT source_concept_id FROM concept_relationships
        WHERE target_concept_id = ? AND relationship_type = 'PREREQUISITE_OF'
        ORDER BY source_concept_id;
        """
        with self.db.get_connection() as conn:
            rows = conn.execute(sql, (concept_id,)).fetchall()
            return [r[0] for r in rows]

    def get_direct_dependents(self, concept_id: str) -> List[str]:
        """
        Returns IDs of concepts that depend on concept_id.
        (concept_id is PREREQUISITE_OF target_concept_id)
        """
        sql = """
        SELECT target_concept_id FROM concept_relationships
        WHERE source_concept_id = ? AND relationship_type = 'PREREQUISITE_OF'
        ORDER BY target_concept_id;
        """
        with self.db.get_connection() as conn:
            rows = conn.execute(sql, (concept_id,)).fetchall()
            return [r[0] for r in rows]

    def _row_to_edge(self, row: Any) -> ConceptEdge:
        prov = {}
        if row["source_provenance_json"]:
            try:
                prov = json.loads(row["source_provenance_json"])
            except Exception:
                prov = {}

        return ConceptEdge(
            edge_id=row["edge_id"],
            source_concept_id=row["source_concept_id"],
            target_concept_id=row["target_concept_id"],
            relationship_type=RelationshipType(row["relationship_type"]),
            description=row["description"],
            confidence=row["confidence"],
            verification_status=ConceptVerificationStatus(row["verification_status"]),
            source_provenance=prov,
            created_at=str(row["created_at"]) if row["created_at"] else None,
        )

    # -------------------------------------------------------------
    # Concept Provenance
    # -------------------------------------------------------------

    def upsert_provenance(self, prov: ConceptProvenance) -> None:
        """
        Inserts or updates a provenance record.
        """
        sql = """
        INSERT INTO concept_provenance (
            provenance_id, concept_id, source_document_id, source_filename,
            page_number, section_heading, extraction_method, confidence,
            verification_status, verbatim_text
        ) VALUES (
            :provenance_id, :concept_id, :source_document_id, :source_filename,
            :page_number, :section_heading, :extraction_method, :confidence,
            :verification_status, :verbatim_text
        ) ON CONFLICT(provenance_id) DO UPDATE SET
            concept_id = excluded.concept_id,
            source_document_id = excluded.source_document_id,
            source_filename = excluded.source_filename,
            page_number = excluded.page_number,
            section_heading = excluded.section_heading,
            extraction_method = excluded.extraction_method,
            confidence = excluded.confidence,
            verification_status = excluded.verification_status,
            verbatim_text = excluded.verbatim_text;
        """
        params = {
            "provenance_id": prov.provenance_id,
            "concept_id": prov.concept_id,
            "source_document_id": prov.source_document_id,
            "source_filename": prov.source_filename,
            "page_number": prov.page_number,
            "section_heading": prov.section_heading,
            "extraction_method": prov.extraction_method,
            "confidence": prov.confidence,
            "verification_status": prov.verification_status.value if hasattr(prov.verification_status, "value") else prov.verification_status,
            "verbatim_text": prov.verbatim_text,
        }

        with self.db.get_connection() as conn:
            conn.execute(sql, params)

    def get_provenance_for_concept(self, concept_id: str) -> List[ConceptProvenance]:
        """
        Retrieves all provenance records for a given concept.
        """
        sql = "SELECT * FROM concept_provenance WHERE concept_id = ? ORDER BY page_number, provenance_id;"
        with self.db.get_connection() as conn:
            rows = conn.execute(sql, (concept_id,)).fetchall()
            return [
                ConceptProvenance(
                    provenance_id=r["provenance_id"],
                    concept_id=r["concept_id"],
                    source_document_id=r["source_document_id"],
                    source_filename=r["source_filename"],
                    page_number=r["page_number"],
                    section_heading=r["section_heading"],
                    extraction_method=r["extraction_method"],
                    confidence=r["confidence"],
                    verification_status=ConceptVerificationStatus(r["verification_status"]),
                    verbatim_text=r["verbatim_text"],
                    created_at=str(r["created_at"]) if r["created_at"] else None,
                )
                for r in rows
            ]

    # -------------------------------------------------------------
    # Graph Statistics
    # -------------------------------------------------------------

    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        Aggregates concept graph metrics.
        """
        with self.db.get_connection() as conn:
            total_concepts = conn.execute("SELECT COUNT(*) FROM concepts;").fetchone()[0]
            total_edges = conn.execute("SELECT COUNT(*) FROM concept_relationships;").fetchone()[0]
            total_provenance = conn.execute("SELECT COUNT(*) FROM concept_provenance;").fetchone()[0]

            # Breakdown by verification status
            status_counts = {}
            for row in conn.execute("SELECT verification_status, COUNT(*) FROM concepts GROUP BY verification_status;").fetchall():
                status_counts[row[0]] = row[1]

            # Breakdown by concept type
            type_counts = {}
            for row in conn.execute("SELECT concept_type, COUNT(*) FROM concepts GROUP BY concept_type;").fetchall():
                type_counts[row[0]] = row[1]

            # Breakdown by edge relationship type
            rel_counts = {}
            for row in conn.execute("SELECT relationship_type, COUNT(*) FROM concept_relationships GROUP BY relationship_type;").fetchall():
                rel_counts[row[0]] = row[1]

            # Breakdown by chapter
            chapter_counts = {}
            for row in conn.execute("SELECT chapter_id, COUNT(*) FROM concepts GROUP BY chapter_id;").fetchall():
                chapter_counts[row[0]] = row[1]

            return {
                "total_concepts": total_concepts,
                "total_edges": total_edges,
                "total_provenance_records": total_provenance,
                "concepts_by_status": status_counts,
                "concepts_by_type": type_counts,
                "edges_by_relationship": rel_counts,
                "concepts_by_chapter": chapter_counts,
            }
