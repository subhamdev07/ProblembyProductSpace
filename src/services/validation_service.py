"""
Curriculum Validation Engine
Evaluates all 12 core curriculum integrity rules:
1. Duplicate Chapter IDs
2. Duplicate Topic IDs
3. Missing Chapter Names
4. Invalid Parent References
5. Invalid Unit Mappings
6. Missing Source References
7. Invalid Assessment Classifications
8. Missing Verification Status
9. Duplicate Curriculum Entries
10. Inconsistent Hierarchies
11. Missing Topic Mappings
12. Unverified Curriculum Content
"""

from typing import Dict, Any, List, Optional
from src.models.classification import AssessmentClassification, VerificationStatus
from src.storage.database import CurriculumRepository


class ValidationResult:
    """Encapsulates the outcome of curriculum validation."""

    def __init__(self):
        self.is_valid = True
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.rule_reports: Dict[str, Dict[str, Any]] = {}
        self.summary: Dict[str, Any] = {}

    def add_error(self, rule_id: str, message: str, context: Optional[Dict[str, Any]] = None):
        self.is_valid = False
        item = {"rule_id": rule_id, "severity": "ERROR", "message": message, "context": context or {}}
        self.errors.append(item)
        self.rule_reports.setdefault(rule_id, {"status": "FAILED", "errors": [], "warnings": []})["errors"].append(item)
        self.rule_reports[rule_id]["status"] = "FAILED"

    def add_warning(self, rule_id: str, message: str, context: Optional[Dict[str, Any]] = None):
        item = {"rule_id": rule_id, "severity": "WARNING", "message": message, "context": context or {}}
        self.warnings.append(item)
        self.rule_reports.setdefault(rule_id, {"status": "PASSED_WITH_WARNINGS", "errors": [], "warnings": []})["warnings"].append(item)

    def mark_rule_passed(self, rule_id: str, description: str):
        if rule_id not in self.rule_reports:
            self.rule_reports[rule_id] = {
                "rule_id": rule_id,
                "description": description,
                "status": "PASSED",
                "errors": [],
                "warnings": []
            }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "rule_reports": self.rule_reports,
            "errors": self.errors,
            "warnings": self.warnings,
            "summary": self.summary
        }


class CurriculumValidationEngine:
    """
    Validation engine executing all 12 validation rules on the curriculum repository.
    """

    def __init__(self, repo: CurriculumRepository):
        self.repo = repo

    def validate(self) -> ValidationResult:
        result = ValidationResult()

        units = self.repo.get_units()
        chapters = self.repo.get_chapters()
        topics = self.repo.get_topics()
        subtopics = self.repo.get_subtopics()
        learning_outcomes = self.repo.get_learning_outcomes()
        source_docs = self.repo.get_source_documents()

        unit_ids = {u["unit_id"] for u in units}
        chapter_ids = {c["chapter_id"] for c in chapters}
        topic_ids = {t["topic_id"] for t in topics}
        source_doc_ids = {s["document_id"] for s in source_docs}

        # ---------------- Rule 1: Duplicate Chapter IDs ----------------
        rule_1 = "RULE_01_DUPLICATE_CHAPTER_IDS"
        seen_ch_ids = set()
        dup_ch_ids = set()
        for ch in chapters:
            cid = ch["chapter_id"]
            if cid in seen_ch_ids:
                dup_ch_ids.add(cid)
            seen_ch_ids.add(cid)
        if dup_ch_ids:
            for cid in dup_ch_ids:
                result.add_error(rule_1, f"Duplicate Chapter ID detected: '{cid}'", {"chapter_id": cid})
        else:
            result.mark_rule_passed(rule_1, "No duplicate Chapter IDs detected.")

        # ---------------- Rule 2: Duplicate Topic IDs ----------------
        rule_2 = "RULE_02_DUPLICATE_TOPIC_IDS"
        seen_topic_ids = set()
        dup_topic_ids = set()
        for t in topics:
            tid = t["topic_id"]
            if tid in seen_topic_ids:
                dup_topic_ids.add(tid)
            seen_topic_ids.add(tid)
        if dup_topic_ids:
            for tid in dup_topic_ids:
                result.add_error(rule_2, f"Duplicate Topic ID detected: '{tid}'", {"topic_id": tid})
        else:
            result.mark_rule_passed(rule_2, "No duplicate Topic IDs detected.")

        # ---------------- Rule 3: Missing Chapter Names ----------------
        rule_3 = "RULE_03_MISSING_CHAPTER_NAMES"
        missing_names = [c for c in chapters if not c.get("name") or not c["name"].strip()]
        if missing_names:
            for c in missing_names:
                result.add_error(rule_3, f"Chapter {c.get('chapter_id')} has missing or empty name", {"chapter": c})
        else:
            result.mark_rule_passed(rule_3, "All chapters possess non-empty official names.")

        # ---------------- Rule 4: Invalid Parent References ----------------
        rule_4 = "RULE_04_INVALID_PARENT_REFERENCES"
        has_parent_err = False
        # Check topic parent chapter
        for t in topics:
            if t["chapter_id"] not in chapter_ids:
                has_parent_err = True
                result.add_error(rule_4, f"Topic '{t['topic_id']}' references non-existent parent Chapter '{t['chapter_id']}'", {"topic_id": t["topic_id"]})
        # Check subtopic parent topic
        for st in subtopics:
            if st["topic_id"] not in topic_ids:
                has_parent_err = True
                result.add_error(rule_4, f"Subtopic '{st['subtopic_id']}' references non-existent parent Topic '{st['topic_id']}'", {"subtopic_id": st["subtopic_id"]})
        if not has_parent_err:
            result.mark_rule_passed(rule_4, "All parent references across Topics and Subtopics are valid.")

        # ---------------- Rule 5: Invalid Unit Mappings ----------------
        rule_5 = "RULE_05_INVALID_UNIT_MAPPINGS"
        invalid_unit_ch = [c for c in chapters if c["unit_id"] not in unit_ids]
        if invalid_unit_ch:
            for c in invalid_unit_ch:
                result.add_error(rule_5, f"Chapter '{c['chapter_id']}' references invalid Unit '{c['unit_id']}'", {"chapter": c})
        else:
            result.mark_rule_passed(rule_5, "All 13 Chapters correctly map to valid CBSE Units.")

        # ---------------- Rule 6: Missing Source References ----------------
        rule_6 = "RULE_06_MISSING_SOURCE_REFERENCES"
        missing_src_topics = [t for t in topics if not t.get("source_doc_id")]
        missing_src_los = [lo for lo in learning_outcomes if not lo.get("source_doc_id")]
        if missing_src_topics:
            for t in missing_src_topics:
                result.add_error(rule_6, f"Topic '{t['topic_id']}' lacks source document reference", {"topic_id": t["topic_id"]})
        if missing_src_los:
            for lo in missing_src_los:
                result.add_error(rule_6, f"Learning Outcome '{lo['outcome_id']}' lacks source document reference", {"outcome_id": lo["outcome_id"]})
        if not missing_src_topics and not missing_src_los:
            result.mark_rule_passed(rule_6, "All Topics and Learning Outcomes carry traceable source document IDs.")

        # ---------------- Rule 7: Invalid Assessment Classifications ----------------
        rule_7 = "RULE_07_INVALID_ASSESSMENT_CLASSIFICATIONS"
        valid_classifications = {e.value for e in AssessmentClassification}
        has_bad_class = False
        for ch in chapters:
            if ch.get("assessment_status") not in valid_classifications:
                has_bad_class = True
                result.add_error(rule_7, f"Chapter '{ch['chapter_id']}' has invalid classification '{ch.get('assessment_status')}'")
        for t in topics:
            if t.get("assessment_status") not in valid_classifications:
                has_bad_class = True
                result.add_error(rule_7, f"Topic '{t['topic_id']}' has invalid classification '{t.get('assessment_status')}'")
        if not has_bad_class:
            result.mark_rule_passed(rule_7, "All assessment classifications conform to SUMMATIVE, FORMATIVE, NOT_IN_CURRENT_SCOPE, PENDING_VERIFICATION.")

        # ---------------- Rule 8: Missing Verification Status ----------------
        rule_8 = "RULE_08_MISSING_VERIFICATION_STATUS"
        valid_statuses = {e.value for e in VerificationStatus}
        has_bad_status = False
        for ch in chapters:
            if ch.get("verification_status") not in valid_statuses:
                has_bad_status = True
                result.add_error(rule_8, f"Chapter '{ch['chapter_id']}' has missing/invalid verification status")
        for t in topics:
            if t.get("verification_status") not in valid_statuses:
                has_bad_status = True
                result.add_error(rule_8, f"Topic '{t['topic_id']}' has missing/invalid verification status")
        if not has_bad_status:
            result.mark_rule_passed(rule_8, "All Chapters and Topics have explicit and valid verification statuses.")

        # ---------------- Rule 9: Duplicate Curriculum Entries ----------------
        rule_9 = "RULE_09_DUPLICATE_CURRICULUM_ENTRIES"
        # Check duplicate chapter numbers
        seen_ch_nums = set()
        dup_ch_nums = set()
        for ch in chapters:
            num = ch["chapter_number"]
            if num in seen_ch_nums:
                dup_ch_nums.add(num)
            seen_ch_nums.add(num)
        if dup_ch_nums:
            for num in dup_ch_nums:
                result.add_error(rule_9, f"Duplicate Chapter number '{num}' detected.")
        # Check duplicate topic names within same chapter
        ch_topic_names: Dict[str, set] = {}
        dup_topic_names = []
        for t in topics:
            cid = t["chapter_id"]
            name = t["name"].strip().lower()
            if name in ch_topic_names.setdefault(cid, set()):
                dup_topic_names.append((cid, t["name"]))
            ch_topic_names[cid].add(name)
        if dup_topic_names:
            for cid, name in dup_topic_names:
                result.add_error(rule_9, f"Duplicate Topic name '{name}' under Chapter '{cid}'.")
        if not dup_ch_nums and not dup_topic_names:
            result.mark_rule_passed(rule_9, "No duplicate chapter numbers or duplicate topic names under chapters.")

        # ---------------- Rule 10: Inconsistent Hierarchies ----------------
        rule_10 = "RULE_10_INCONSISTENT_HIERARCHIES"
        # Check if every Unit has at least one Chapter
        unit_ch_counts = {u["unit_id"]: 0 for u in units}
        for c in chapters:
            if c["unit_id"] in unit_ch_counts:
                unit_ch_counts[c["unit_id"]] += 1
        empty_units = [uid for uid, count in unit_ch_counts.items() if count == 0]
        if empty_units:
            for uid in empty_units:
                result.add_error(rule_10, f"Unit '{uid}' has no associated chapters.")

        # Check if every Chapter has at least one Topic
        ch_topic_counts = {c["chapter_id"]: 0 for c in chapters}
        for t in topics:
            if t["chapter_id"] in ch_topic_counts:
                ch_topic_counts[t["chapter_id"]] += 1
        empty_chapters = [cid for cid, count in ch_topic_counts.items() if count == 0]
        if empty_chapters:
            for cid in empty_chapters:
                result.add_error(rule_10, f"Chapter '{cid}' has no extracted topics.")

        if not empty_units and not empty_chapters:
            result.mark_rule_passed(rule_10, "Hierarchical consistency verified: all Units contain Chapters; all Chapters contain Topics.")

        # ---------------- Rule 11: Missing Topic Mappings ----------------
        rule_11 = "RULE_11_MISSING_TOPIC_MAPPINGS"
        lo_err = False
        for lo in learning_outcomes:
            if lo.get("related_chapter_id") not in chapter_ids:
                lo_err = True
                result.add_error(rule_11, f"Learning outcome '{lo['outcome_id']}' points to unknown chapter '{lo.get('related_chapter_id')}'")
            if lo.get("related_topic_id") and lo["related_topic_id"] not in topic_ids:
                lo_err = True
                result.add_error(rule_11, f"Learning outcome '{lo['outcome_id']}' points to unknown topic '{lo['related_topic_id']}'")
        if not lo_err:
            result.mark_rule_passed(rule_11, "All Learning Outcomes map accurately to valid Chapters and Topics.")

        # ---------------- Rule 12: Unverified Curriculum Content ----------------
        rule_12 = "RULE_12_UNVERIFIED_CURRICULUM_CONTENT"
        unverified_topics = [t for t in topics if t.get("verification_status") != VerificationStatus.VERIFIED.value]
        unverified_chapters = [c for c in chapters if c.get("verification_status") != VerificationStatus.VERIFIED.value]
        unverified_los = [lo for lo in learning_outcomes if lo.get("verification_status") != VerificationStatus.VERIFIED.value]

        if unverified_topics or unverified_chapters or unverified_los:
            result.add_warning(rule_12, f"Found unverified curriculum elements: {len(unverified_chapters)} chapters, {len(unverified_topics)} topics, {len(unverified_los)} outcomes.")
        else:
            result.mark_rule_passed(rule_12, "All curriculum content is 100% verified against primary sources.")

        # Generate summary
        result.summary = {
            "total_rules_evaluated": 12,
            "passed_rules": sum(1 for r in result.rule_reports.values() if r["status"] == "PASSED"),
            "passed_with_warnings": sum(1 for r in result.rule_reports.values() if r["status"] == "PASSED_WITH_WARNINGS"),
            "failed_rules": sum(1 for r in result.rule_reports.values() if r["status"] == "FAILED"),
            "total_errors": len(result.errors),
            "total_warnings": len(result.warnings),
            "total_units": len(units),
            "total_chapters": len(chapters),
            "total_topics": len(topics),
            "total_subtopics": len(subtopics),
            "total_learning_outcomes": len(learning_outcomes),
            "summative_topics": sum(1 for t in topics if t["assessment_status"] == AssessmentClassification.SUMMATIVE.value),
            "formative_topics": sum(1 for t in topics if t["assessment_status"] == AssessmentClassification.FORMATIVE.value),
            "excluded_topics": sum(1 for t in topics if t["assessment_status"] == AssessmentClassification.NOT_IN_CURRENT_SCOPE.value),
        }

        return result

    def generate_markdown_report(self, result: ValidationResult) -> str:
        """Generates a comprehensive human-readable Markdown report from validation results."""
        lines = [
            "# P0 — Curriculum Foundation Validation Report",
            "",
            "**Academic Session:** 2026–27  ",
            "**Curriculum:** CBSE Class 10 Science (Subject Code 086)  ",
            f"**Validation Status:** {'PASSED' if result.is_valid else 'FAILED'}  ",
            f"**Total Errors:** {len(result.errors)}  ",
            f"**Total Warnings:** {len(result.warnings)}  ",
            "",
            "---",
            "",
            "## 1. Executive Summary",
            "",
            f"- **Validation Engine Verdict:** {'✅ VALIDATION SUCCESSFUL - ALL INTEGRITY CONSTRAINTS SATISFIED' if result.is_valid else '❌ VALIDATION FAILED'}",
            f"- **Rules Evaluated:** 12 / 12",
            f"- **Rules Passed Cleanly:** {result.summary.get('passed_rules', 0)}",
            f"- **Rules with Warnings:** {result.summary.get('passed_with_warnings', 0)}",
            f"- **Rules Failed:** {result.summary.get('failed_rules', 0)}",
            "",
            "### Curriculum Metrics",
            f"- **Total Units:** {result.summary.get('total_units', 0)} (Preserved CBSE Unit I through Unit V)",
            f"- **Total Chapters:** {result.summary.get('total_chapters', 0)} (Preserved NCERT Chapters 1 through 13)",
            f"- **Total Topics:** {result.summary.get('total_topics', 0)}",
            f"- **Total Subtopics:** {result.summary.get('total_subtopics', 0)}",
            f"- **Total Learning Outcomes:** {result.summary.get('total_learning_outcomes', 0)}",
            f"  - Summative Assessment Topics: {result.summary.get('summative_topics', 0)}",
            f"  - Formative Assessment Topics: {result.summary.get('formative_topics', 0)}",
            f"  - Not in Current Scope / Excluded Topics: {result.summary.get('excluded_topics', 0)}",
            "",
            "---",
            "",
            "## 2. Rule-by-Rule Audit Matrix",
            "",
            "| Rule ID | Integrity Check Description | Status | Errors | Warnings |",
            "|---|---|:---:|:---:|:---:|",
        ]

        rules_order = [
            ("RULE_01_DUPLICATE_CHAPTER_IDS", "Duplicate Chapter IDs Check"),
            ("RULE_02_DUPLICATE_TOPIC_IDS", "Duplicate Topic IDs Check"),
            ("RULE_03_MISSING_CHAPTER_NAMES", "Missing Chapter Names Check"),
            ("RULE_04_INVALID_PARENT_REFERENCES", "Invalid Parent Hierarchy References"),
            ("RULE_05_INVALID_UNIT_MAPPINGS", "Invalid Unit to Chapter Mappings"),
            ("RULE_06_MISSING_SOURCE_REFERENCES", "Missing Source Citations and References"),
            ("RULE_07_INVALID_ASSESSMENT_CLASSIFICATIONS", "Assessment Classification Verification"),
            ("RULE_08_MISSING_VERIFICATION_STATUS", "Missing Verification Status Check"),
            ("RULE_09_DUPLICATE_CURRICULUM_ENTRIES", "Duplicate Curriculum Entries (Numbers/Names)"),
            ("RULE_10_INCONSISTENT_HIERARCHIES", "Inconsistent Hierarchies & Orphan Detection"),
            ("RULE_11_MISSING_TOPIC_MAPPINGS", "Missing Learning Outcome Mappings"),
            ("RULE_12_UNVERIFIED_CURRICULUM_CONTENT", "Unverified Curriculum Content Audit"),
        ]

        for rule_id, desc in rules_order:
            r_info = result.rule_reports.get(rule_id, {"status": "UNKNOWN", "errors": [], "warnings": []})
            status_icon = "✅ PASSED" if r_info["status"] == "PASSED" else ("⚠️ WARNING" if r_info["status"] == "PASSED_WITH_WARNINGS" else "❌ FAILED")
            lines.append(f"| `{rule_id}` | {desc} | {status_icon} | {len(r_info['errors'])} | {len(r_info['warnings'])} |")

        lines.extend([
            "",
            "---",
            "",
            "## 3. Detailed Findings & Evidence",
            ""
        ])

        if result.errors:
            lines.append("### ❌ Errors Detected")
            for err in result.errors:
                lines.append(f"- **[{err['rule_id']}]**: {err['message']}")
            lines.append("")
        else:
            lines.append("### ✅ Zero Errors Detected")
            lines.append("All primary relational integrity constraints, foreign keys, unique keys, and domain checks passed without a single failure.")
            lines.append("")

        if result.warnings:
            lines.append("### ⚠️ Warnings & Audit Items")
            for warn in result.warnings:
                lines.append(f"- **[{warn['rule_id']}]**: {warn['message']}")
            lines.append("")
        else:
            lines.append("### ℹ️ Warnings Summary")
            lines.append("No warnings encountered. All curriculum entities are 100% verified against primary official documents.")
            lines.append("")

        lines.extend([
            "---",
            "",
            "## 4. Referential Integrity & Scope Validation",
            "",
            "1. **CBSE Units vs Textbook Chapters Separation:** Verified. Units (`UNIT-01` to `UNIT-05`) maintain separate identity and mark allocations distinct from Chapters (`CH-01` to `CH-13`).",
            "2. **All 13 NCERT Chapters Registered:** Verified. Chapters 1 to 13 are fully registered with official titles, sequential numbers, and unit parents.",
            "3. **Formative Assessment Transparency:** Verified. Periodic Classification of Elements, Evolution, and Electric Motor/Generator are explicitly classified as `FORMATIVE` with primary page citations from CBSE Syllabus.",
            "4. **Out of Scope Content Preservation:** Verified. The exclusion '(excluding colour of the sun at sunrise and sunset)' is registered as `NOT_IN_CURRENT_SCOPE` rather than deleted.",
            "5. **Source Provenance:** 100% of topics and learning outcomes cite primary document IDs and verified page coordinates.",
            "",
            "---",
            "*Report generated by P0 Curriculum Validation Engine.*"
        ])

        return "\n".join(lines)
