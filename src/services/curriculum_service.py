"""
Curriculum Query and Management Service
"""

from typing import List, Dict, Any, Optional
from src.storage.database import CurriculumRepository


class CurriculumService:
    """
    High-level query and retrieval service for curriculum hierarchy.
    """

    def __init__(self, repo: CurriculumRepository):
        self.repo = repo

    def get_full_hierarchy(self) -> Dict[str, Any]:
        """
        Builds complete hierarchical tree:
        Academic Session -> Curriculum -> Units -> Chapters -> Topics -> Subtopics
        """
        units = self.repo.get_units()
        chapters = self.repo.get_chapters()
        topics = self.repo.get_topics()
        subtopics = self.repo.get_subtopics()
        learning_outcomes = self.repo.get_learning_outcomes()

        # Build subtopics map by topic_id
        subtopics_by_topic: Dict[str, List[Dict[str, Any]]] = {}
        for st in subtopics:
            subtopics_by_topic.setdefault(st["topic_id"], []).append(st)

        # Build topics map by chapter_id
        topics_by_ch: Dict[str, List[Dict[str, Any]]] = {}
        for tp in topics:
            tp_copy = dict(tp)
            tp_copy["subtopics"] = subtopics_by_topic.get(tp["topic_id"], [])
            topics_by_ch.setdefault(tp["chapter_id"], []).append(tp_copy)

        # Build outcomes map by chapter_id
        los_by_ch: Dict[str, List[Dict[str, Any]]] = {}
        for lo in learning_outcomes:
            los_by_ch.setdefault(lo["related_chapter_id"], []).append(lo)

        # Build chapters map by unit_id
        chapters_by_unit: Dict[str, List[Dict[str, Any]]] = {}
        for ch in chapters:
            ch_copy = dict(ch)
            ch_copy["topics"] = topics_by_ch.get(ch["chapter_id"], [])
            ch_copy["learning_outcomes"] = los_by_ch.get(ch["chapter_id"], [])
            chapters_by_unit.setdefault(ch["unit_id"], []).append(ch_copy)

        units_tree = []
        for u in units:
            u_copy = dict(u)
            u_copy["chapters"] = chapters_by_unit.get(u["unit_id"], [])
            units_tree.append(u_copy)

        return {
            "session_id": "2026-27",
            "curriculum_id": "CBSE-SCI-10-2026-27",
            "subject": "Science (086)",
            "total_units": len(units),
            "total_chapters": len(chapters),
            "total_topics": len(topics),
            "total_subtopics": len(subtopics),
            "total_learning_outcomes": len(learning_outcomes),
            "units": units_tree
        }
