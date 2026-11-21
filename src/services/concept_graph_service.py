"""
Concept Graph Service & Graph Algorithm Engine
Implements deterministic DAG validation, cycle detection with complete cycle path reporting,
topological ordering, ancestor/descendant traversals, and curriculum integrity rules.
"""

from collections import deque, defaultdict
from typing import List, Dict, Any, Optional, Set, Tuple
from pydantic import BaseModel, Field

from src.models.concept import (
    ConceptNode,
    ConceptEdge,
    RelationshipType,
    ConceptVerificationStatus,
)
from src.storage.concept_repository import ConceptRepository
from src.storage.database import CurriculumRepository


class GraphValidationResult(BaseModel):
    """
    Result of a comprehensive concept graph validation pass.
    """
    is_valid: bool = Field(..., description="Whether the entire concept graph passed all validation rules")
    is_dag: bool = Field(..., description="Whether the PREREQUISITE_OF subgraph is strictly acyclic")
    cycle_detected: bool = Field(default=False, description="Whether a cycle was detected in prerequisites")
    cycle_path: Optional[List[str]] = Field(default=None, description="Complete cycle path if detected, e.g. [A, B, C, A]")
    errors: List[str] = Field(default_factory=list, description="Critical validation error messages")
    warnings: List[str] = Field(default_factory=list, description="Pedagogical or audit warnings")
    rules_evaluated: int = Field(default=0, description="Total integrity rules evaluated")
    statistics: Dict[str, Any] = Field(default_factory=dict, description="Graph metrics and counters")


class ConceptGraphService:
    """
    Core service for Concept Graph operations, algorithms, queries, and validation.
    """

    def __init__(self, concept_repo: ConceptRepository, curriculum_repo: Optional[CurriculumRepository] = None):
        self.concept_repo = concept_repo
        self.curriculum_repo = curriculum_repo

    # -------------------------------------------------------------
    # Graph Retrieval & Structure Queries
    # -------------------------------------------------------------

    def get_chapter_graph(self, chapter_id: str) -> Dict[str, Any]:
        """
        Retrieves the complete graph for a given chapter, including concepts, edges,
        and topological learning order.
        """
        concepts = self.concept_repo.get_concepts_by_chapter(chapter_id)
        concept_ids = {c.concept_id for c in concepts}
        all_edges = self.concept_repo.get_edges(chapter_id=chapter_id)

        # Filter edges where both source and target belong to this chapter (or target is LO)
        chapter_edges = [
            e for e in all_edges
            if e.source_concept_id in concept_ids
        ]

        # Calculate topological sort for chapter prerequisites
        prereq_edges = [e for e in chapter_edges if e.relationship_type == RelationshipType.PREREQUISITE_OF]
        topo_order = self.compute_topological_order(list(concept_ids), prereq_edges)

        return {
            "chapter_id": chapter_id,
            "total_concepts": len(concepts),
            "total_edges": len(chapter_edges),
            "concepts": [c.model_dump() for c in concepts],
            "edges": [e.model_dump() for e in chapter_edges],
            "topological_learning_order": topo_order,
        }

    # -------------------------------------------------------------
    # Mathematical Graph Algorithms: DAG, Cycles, Topological Order
    # -------------------------------------------------------------

    def detect_prerequisite_cycle(
        self,
        node_ids: Optional[List[str]] = None,
        edges: Optional[List[ConceptEdge]] = None,
    ) -> Tuple[bool, Optional[List[str]]]:
        """
        Detects if there is any directed cycle in the PREREQUISITE_OF relationships.
        Uses Depth-First Search with recursion stack tracking.
        Returns: (has_cycle: bool, cycle_path: Optional[List[str]])
        If a cycle exists, cycle_path contains the exact sequence of nodes forming the loop:
        e.g., ['A', 'B', 'C', 'A'].
        """
        if edges is None:
            edges = self.concept_repo.get_all_edges()
        if node_ids is None:
            all_concepts = self.concept_repo.get_all_concepts()
            node_ids = [c.concept_id for c in all_concepts]

        # Build adjacency list strictly for PREREQUISITE_OF edges (u -> v: u is prereq of v)
        adj: Dict[str, List[str]] = defaultdict(list)
        for e in edges:
            if e.relationship_type == RelationshipType.PREREQUISITE_OF:
                adj[e.source_concept_id].append(e.target_concept_id)

        # 0 = unvisited, 1 = visiting (in current recursion stack), 2 = visited
        visited: Dict[str, int] = {nid: 0 for nid in node_ids}
        parent: Dict[str, Optional[str]] = {}

        def dfs(u: str, path: List[str]) -> Optional[List[str]]:
            visited[u] = 1
            path.append(u)

            for v in adj.get(u, []):
                if visited.get(v, 0) == 1:
                    # Cycle detected! Reconstruct the exact cycle path
                    cycle_start_idx = path.index(v)
                    cycle_loop = path[cycle_start_idx:] + [v]
                    return cycle_loop
                elif visited.get(v, 0) == 0:
                    parent[v] = u
                    result = dfs(v, path)
                    if result is not None:
                        return result

            visited[u] = 2
            path.pop()
            return None

        for nid in node_ids:
            if visited.get(nid, 0) == 0:
                cycle = dfs(nid, [])
                if cycle is not None:
                    return True, cycle

        return False, None

    def compute_topological_order(
        self,
        node_ids: Optional[List[str]] = None,
        edges: Optional[List[ConceptEdge]] = None,
    ) -> List[str]:
        """
        Computes a valid pedagogical learning sequence using Kahn's algorithm
        on the PREREQUISITE_OF directed acyclic graph.
        In this DAG, an edge u -> v means u is prerequisite of v, so u must come before v.
        """
        if edges is None:
            edges = self.concept_repo.get_all_edges()
        if node_ids is None:
            all_concepts = self.concept_repo.get_all_concepts()
            node_ids = [c.concept_id for c in all_concepts]

        node_set = set(node_ids)
        adj: Dict[str, List[str]] = defaultdict(list)
        in_degree: Dict[str, int] = {nid: 0 for nid in node_set}

        for e in edges:
            if e.relationship_type == RelationshipType.PREREQUISITE_OF:
                u, v = e.source_concept_id, e.target_concept_id
                if u in node_set and v in node_set:
                    adj[u].append(v)
                    in_degree[v] += 1

        # Queue of nodes with zero in-degree (no prerequisites)
        # Sort queue deterministically by concept_id
        zero_in_degree = sorted([nid for nid in node_set if in_degree[nid] == 0])
        queue = deque(zero_in_degree)
        order = []

        while queue:
            u = queue.popleft()
            order.append(u)
            for v in sorted(adj.get(u, [])):
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        if len(order) < len(node_set):
            # Graph has a cycle; full topological order cannot be completed
            return []

        return order

    # -------------------------------------------------------------
    # Transitive Traversals: Ancestors (Prerequisites) and Descendants
    # -------------------------------------------------------------

    def get_transitive_prerequisites(self, concept_id: str) -> List[str]:
        """
        Returns all recursive prerequisites that must be learned prior to concept_id.
        Traverses upstream along reverse PREREQUISITE_OF edges using BFS.
        Result is ordered topologically (foundational concepts first).
        """
        all_edges = self.concept_repo.get_all_edges()
        # Reverse graph: v -> u means u is prerequisite of v
        rev_adj: Dict[str, List[str]] = defaultdict(list)
        for e in all_edges:
            if e.relationship_type == RelationshipType.PREREQUISITE_OF:
                rev_adj[e.target_concept_id].append(e.source_concept_id)

        visited: Set[str] = set()
        queue = deque([concept_id])

        while queue:
            curr = queue.popleft()
            for prereq in rev_adj.get(curr, []):
                if prereq not in visited and prereq != concept_id:
                    visited.add(prereq)
                    queue.append(prereq)

        # Order visited prerequisites topologically
        topo = self.compute_topological_order(list(visited))
        return topo if topo else sorted(list(visited))

    def get_transitive_dependents(self, concept_id: str) -> List[str]:
        """
        Returns all recursive downstream concepts that depend on concept_id.
        Traverses downstream along PREREQUISITE_OF edges (u -> v).
        """
        all_edges = self.concept_repo.get_all_edges()
        adj: Dict[str, List[str]] = defaultdict(list)
        for e in all_edges:
            if e.relationship_type == RelationshipType.PREREQUISITE_OF:
                adj[e.source_concept_id].append(e.target_concept_id)

        visited: Set[str] = set()
        queue = deque([concept_id])

        while queue:
            curr = queue.popleft()
            for dep in adj.get(curr, []):
                if dep not in visited and dep != concept_id:
                    visited.add(dep)
                    queue.append(dep)

        topo = self.compute_topological_order(list(visited))
        return topo if topo else sorted(list(visited))

    def get_cross_topic_relationships(self, chapter_id: str) -> List[Dict[str, Any]]:
        """
        Identifies edges where the source concept and target concept belong
        to different topics within the chapter (or cross-chapter).
        """
        concepts = {c.concept_id: c for c in self.concept_repo.get_all_concepts()}
        edges = self.concept_repo.get_edges(chapter_id=chapter_id)

        cross_topic = []
        for e in edges:
            src = concepts.get(e.source_concept_id)
            tgt = concepts.get(e.target_concept_id)
            if src and tgt and src.topic_id != tgt.topic_id:
                cross_topic.append({
                    "edge_id": e.edge_id,
                    "relationship_type": e.relationship_type.value,
                    "source_concept": src.concept_id,
                    "source_topic": src.topic_id,
                    "target_concept": tgt.concept_id,
                    "target_topic": tgt.topic_id,
                    "description": e.description,
                })
        return cross_topic

    # -------------------------------------------------------------
    # Comprehensive Graph Validation Engine
    # -------------------------------------------------------------

    def validate_graph(self) -> GraphValidationResult:
        """
        Executes a rigorous 8-rule validation check against the entire Concept Graph.
        Ensures DAG compliance, referential integrity, unique constraints,
        and provenance backing.
        """
        errors = []
        warnings = []
        rules_evaluated = 8

        concepts = self.concept_repo.get_all_concepts()
        edges = self.concept_repo.get_all_edges()
        concept_map = {c.concept_id: c for c in concepts}
        canonical_map: Dict[str, str] = {}

        # Rule CG-01: Concept Nodes Uniqueness & Format
        for c in concepts:
            if not c.concept_id.startswith("CPT-"):
                warnings.append(f"Concept '{c.concept_id}' does not follow canonical ID prefix 'CPT-'")
            if c.canonical_name in canonical_map:
                errors.append(f"Rule CG-01 Violation: Duplicate canonical_name '{c.canonical_name}' in '{c.concept_id}' and '{canonical_map[c.canonical_name]}'")
            else:
                canonical_map[c.canonical_name] = c.concept_id

        # Rule CG-02: Valid Curriculum Parent References
        if self.curriculum_repo:
            with self.concept_repo.db.get_connection() as conn:
                valid_chaps = {r[0] for r in conn.execute("SELECT chapter_id FROM chapters;").fetchall()}
                valid_topics = {r[0] for r in conn.execute("SELECT topic_id FROM topics;").fetchall()}
                valid_subtopics = {r[0] for r in conn.execute("SELECT subtopic_id FROM subtopics;").fetchall()}
                valid_los = {r[0] for r in conn.execute("SELECT outcome_id FROM learning_outcomes;").fetchall()}

            for c in concepts:
                if c.chapter_id not in valid_chaps:
                    errors.append(f"Rule CG-02 Violation: Concept '{c.concept_id}' references non-existent chapter_id '{c.chapter_id}'")
                if c.topic_id not in valid_topics:
                    errors.append(f"Rule CG-02 Violation: Concept '{c.concept_id}' references non-existent topic_id '{c.topic_id}'")
                if c.subtopic_id and c.subtopic_id not in valid_subtopics:
                    errors.append(f"Rule CG-02 Violation: Concept '{c.concept_id}' references non-existent subtopic_id '{c.subtopic_id}'")
        else:
            valid_los = set()

        # Rule CG-03: Edge Referential Integrity
        for e in edges:
            if e.source_concept_id not in concept_map:
                errors.append(f"Rule CG-03 Violation: Edge '{e.edge_id}' source '{e.source_concept_id}' does not exist in concepts")

            if e.relationship_type == RelationshipType.SUPPORTS_LEARNING_OUTCOME:
                if valid_los and e.target_concept_id not in valid_los:
                    errors.append(f"Rule CG-03 Violation: Edge '{e.edge_id}' targets unknown learning outcome '{e.target_concept_id}'")
            else:
                if e.target_concept_id not in concept_map:
                    errors.append(f"Rule CG-03 Violation: Edge '{e.edge_id}' target '{e.target_concept_id}' does not exist in concepts")

        # Rule CG-04: Prevent Duplicate Equivalent Edges
        seen_edges: Set[Tuple[str, str, str]] = set()
        for e in edges:
            key = (e.source_concept_id, e.target_concept_id, e.relationship_type.value)
            if key in seen_edges:
                errors.append(f"Rule CG-04 Violation: Duplicate edge detected for ({e.source_concept_id} -> {e.target_concept_id}, type={e.relationship_type.value})")
            seen_edges.add(key)

        # Rule CG-05: PREREQUISITE_OF Subgraph Must Be a Strict DAG (Acyclic)
        node_ids = list(concept_map.keys())
        prereq_edges = [e for e in edges if e.relationship_type == RelationshipType.PREREQUISITE_OF]
        has_cycle, cycle_path = self.detect_prerequisite_cycle(node_ids, prereq_edges)

        is_dag = not has_cycle
        if has_cycle:
            errors.append(f"Rule CG-05 Violation: Cyclic dependency detected in PREREQUISITE_OF relationships! Cycle path: {' -> '.join(cycle_path or [])}")

        # Rule CG-06: RELATED_TO Edges Must Not Trigger DAG Restrictions
        # (Verified by confirming that RELATED_TO edges are excluded from prereq_edges above)

        # Rule CG-07: Provenance Validation
        for c in concepts:
            prov_records = self.concept_repo.get_provenance_for_concept(c.concept_id)
            if not prov_records:
                if c.verification_status in {ConceptVerificationStatus.VERIFIED, ConceptVerificationStatus.SOURCE_VERIFIED}:
                    errors.append(f"Rule CG-07 Violation: Verified concept '{c.concept_id}' has zero provenance records")
                else:
                    warnings.append(f"Concept '{c.concept_id}' has pending or missing provenance citations")

        # Rule CG-08: Cross-Topic Continuity Check
        cross_topic = [
            e for e in prereq_edges
            if e.source_concept_id in concept_map and e.target_concept_id in concept_map
            and concept_map[e.source_concept_id].topic_id != concept_map[e.target_concept_id].topic_id
        ]
        # Informative check: at least some cross-topic continuity is expected in Chapter 1
        # (e.g. Chemical Equations Balancing is a prerequisite for Types of Reactions)

        stats = self.concept_repo.get_graph_statistics()
        stats["is_dag"] = is_dag
        stats["cross_topic_prerequisites"] = len(cross_topic)

        is_valid = (len(errors) == 0)

        return GraphValidationResult(
            is_valid=is_valid,
            is_dag=is_dag,
            cycle_detected=has_cycle,
            cycle_path=cycle_path,
            errors=errors,
            warnings=warnings,
            rules_evaluated=rules_evaluated,
            statistics=stats,
        )
