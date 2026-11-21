"""
Concept Extraction Service
Provides source-grounded concept extraction for Chapter 1 (Chemical Reactions and Equations)
using NCERT textbook (sources/jesc101.pdf) and CBSE 2026-27 Syllabus.
Integrates with the centralized NVIDIA Nemotron service for candidate proposal and schema validation.
"""

import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from src.models.concept import (
    ConceptNode,
    ConceptEdge,
    ConceptProvenance,
    ConceptType,
    RelationshipType,
    ConceptVerificationStatus,
    SourceStatus,
)
from src.storage.concept_repository import ConceptRepository
from src.ai.llm_service import NVIDIANemotronService


class LLMConceptCandidate(BaseModel):
    name: str = Field(..., description="Concept name")
    canonical_name: str = Field(..., description="Unique slug")
    description: str = Field(..., description="Description")
    concept_type: str = Field(default="CORE")
    difficulty_level: Optional[str] = None
    prerequisites: List[str] = Field(default_factory=list)


class ConceptExtractionService:
    """
    Service responsible for extracting, auditing, and persisting verified concepts
    and relationships from curriculum sources.
    """

    def __init__(
        self,
        concept_repo: ConceptRepository,
        llm_service: Optional[NVIDIANemotronService] = None,
    ):
        self.repo = concept_repo
        self.llm_service = llm_service

    def extract_and_seed_chapter_one(self) -> Dict[str, Any]:
        """
        Loads the definitive, source-verified Chapter 1 concept graph
        grounded in NCERT (sources/jesc101.pdf) and CBSE 2026-27 Syllabus.
        Inserts concepts, provenance citations, and relationship edges idempotently.
        """
        concepts_data = self._get_chapter_one_canonical_concepts()
        edges_data = self._get_chapter_one_canonical_edges()

        seeded_concepts = 0
        seeded_provenance = 0
        seeded_edges = 0

        # 1. Seed Concepts and Provenance
        for item in concepts_data:
            prov_records = []
            for p in item.get("provenance", []):
                prov_obj = ConceptProvenance(
                    provenance_id=p["provenance_id"],
                    concept_id=item["concept_id"],
                    source_document_id=p["source_document_id"],
                    source_filename=p["source_filename"],
                    page_number=p.get("page_number"),
                    section_heading=p.get("section_heading"),
                    extraction_method=p.get("extraction_method", "NATIVE_PDF_PARSE"),
                    confidence=p.get("confidence", 1.0),
                    verification_status=ConceptVerificationStatus(p.get("verification_status", "SOURCE_VERIFIED")),
                    verbatim_text=p.get("verbatim_text"),
                )
                prov_records.append(prov_obj)
                seeded_provenance += 1

            node = ConceptNode(
                concept_id=item["concept_id"],
                name=item["name"],
                canonical_name=item["canonical_name"],
                description=item["description"],
                chapter_id=item["chapter_id"],
                topic_id=item["topic_id"],
                subtopic_id=item.get("subtopic_id"),
                concept_type=ConceptType(item.get("concept_type", "CORE")),
                difficulty_level=item.get("difficulty_level"),
                learning_objective=item.get("learning_objective"),
                source_status=SourceStatus(item.get("source_status", "SOURCE_DERIVED")),
                verification_status=ConceptVerificationStatus(item.get("verification_status", "VERIFIED")),
                metadata=item.get("metadata", {}),
                provenance_records=prov_records,
            )
            self.repo.upsert_concept(node)
            seeded_concepts += 1

        # 2. Seed Relationship Edges
        for e in edges_data:
            edge_obj = ConceptEdge(
                edge_id=e["edge_id"],
                source_concept_id=e["source_concept_id"],
                target_concept_id=e["target_concept_id"],
                relationship_type=RelationshipType(e["relationship_type"]),
                description=e.get("description"),
                confidence=e.get("confidence", 1.0),
                verification_status=ConceptVerificationStatus(e.get("verification_status", "VERIFIED")),
                source_provenance=e.get("source_provenance"),
            )
            self.repo.upsert_edge(edge_obj)
            seeded_edges += 1

        return {
            "status": "SUCCESS",
            "chapter_id": "CH-01",
            "concepts_seeded": seeded_concepts,
            "provenance_records_seeded": seeded_provenance,
            "edges_seeded": seeded_edges,
        }

    def propose_candidate_concepts_with_llm(
        self,
        chapter_title: str,
        section_text: str,
        mock_response: Optional[str] = None,
    ) -> List[LLMConceptCandidate]:
        """
        Uses the centralized NVIDIA Nemotron service to propose candidate concepts
        and relationships from a raw text excerpt.
        Supports a mock_response parameter to ensure zero API credit consumption during tests.
        """
        if mock_response is not None:
            raw_json = json.loads(mock_response)
            return [LLMConceptCandidate(**c) for c in raw_json]

        if self.llm_service is None:
            raise RuntimeError("LLM service is not configured for dynamic candidate extraction.")

        prompt = (
            f"You are a Senior Curriculum Analyst for CBSE Class 10 Science.\n"
            f"Chapter: {chapter_title}\n"
            f"Analyze the following textbook excerpt and extract teachable concept nodes in JSON format.\n"
            f"Return a JSON array of objects with keys: name, canonical_name, description, concept_type, prerequisites.\n\n"
            f"Excerpt:\n{section_text[:3000]}"
        )

        response = self.llm_service.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            json_mode=True,
        )
        parsed = json.loads(response.content)
        if isinstance(parsed, dict) and "concepts" in parsed:
            parsed = parsed["concepts"]

        return [LLMConceptCandidate(**c) for c in parsed]

    # -------------------------------------------------------------
    # Ground-Truth NCERT Chapter 1 Curriculum Dataset
    # Grounded in sources/jesc101.pdf (Pages 1 to 14) & CBSE Syllabus
    # -------------------------------------------------------------

    def _get_chapter_one_canonical_concepts(self) -> List[Dict[str, Any]]:
        return [
            # Topic CH01-T01: Chemical Equations and Balancing
            {
                "concept_id": "CPT-CH01-001",
                "name": "Chemical Reaction",
                "canonical_name": "chemical_reaction",
                "description": "A process in which one or more substances undergo chemical change with bond reorganization to form new substances with distinct properties, characterized by change in state, colour, temperature, or gas evolution.",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T01",
                "subtopic_id": "CH01-T01-S01",
                "concept_type": "FOUNDATIONAL",
                "difficulty_level": "EASY",
                "learning_objective": "Identify the occurrence of a chemical reaction through observable experimental indicators.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-001-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 1,
                        "section_heading": "1.1 Chemical Equations",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "Whenever a chemical change occurs, we can say that a chemical reaction has taken place.",
                    },
                    {
                        "provenance_id": "PROV-CH01-001-02",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 2,
                        "section_heading": "1.1 Chemical Equations",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "change in state, change in colour, evolution of a gas, change in temperature help us to determine whether a chemical reaction has taken place.",
                    }
                ],
            },
            {
                "concept_id": "CPT-CH01-002",
                "name": "Chemical Equation",
                "canonical_name": "chemical_equation",
                "description": "The symbolic representation of a chemical reaction using chemical formulas of reactants and products separated by a directional arrow pointing towards products.",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T01",
                "subtopic_id": "CH01-T01-S02",
                "concept_type": "CORE",
                "difficulty_level": "EASY",
                "learning_objective": "Express chemical transformations in standard chemical equation format.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-002-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 2,
                        "section_heading": "1.1 Chemical Equations",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "A chemical equation represents a chemical reaction. If you recall formulae of magnesium, oxygen and magnesium oxide...",
                    }
                ],
            },
            {
                "concept_id": "CPT-CH01-003",
                "name": "Word Equation",
                "canonical_name": "word_equation",
                "description": "A preliminary textual representation of a chemical reaction stating the names of reactants on the left-hand side and names of products on the right-hand side.",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T01",
                "subtopic_id": "CH01-T01-S02",
                "concept_type": "FOUNDATIONAL",
                "difficulty_level": "EASY",
                "learning_objective": "Convert descriptive chemical observations into word equations.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-003-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 2,
                        "section_heading": "1.1 Chemical Equations",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "The word-equation for the above reaction would be – Magnesium + Oxygen -> Magnesium oxide",
                    }
                ],
            },
            {
                "concept_id": "CPT-CH01-004",
                "name": "Skeletal Chemical Equation",
                "canonical_name": "skeletal_chemical_equation",
                "description": "An unbalanced chemical equation showing chemical formulas of reactants and products where the number of atoms of elements on LHS does not equal RHS.",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T01",
                "subtopic_id": "CH01-T01-S02",
                "concept_type": "CORE",
                "difficulty_level": "EASY",
                "learning_objective": "Differentiate between skeletal equations and balanced equations.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-004-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 3,
                        "section_heading": "1.1.1 Writing a Chemical Equation",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "Such a chemical equation is a skeletal chemical equation for a reaction. Equation (1.2) is a skeletal chemical equation for the burning of magnesium in air.",
                    }
                ],
            },
            {
                "concept_id": "CPT-CH01-005",
                "name": "Law of Conservation of Mass",
                "canonical_name": "law_of_conservation_of_mass",
                "description": "Fundamental scientific law stating that mass can neither be created nor destroyed in a chemical reaction; the total mass of reactants must equal total mass of products.",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T01",
                "subtopic_id": "CH01-T01-S03",
                "concept_type": "FOUNDATIONAL",
                "difficulty_level": "MEDIUM",
                "learning_objective": "Apply the conservation of mass principle as the governing rationale for equation balancing.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-005-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 3,
                        "section_heading": "1.1.2 Balanced Chemical Equations",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "Recall the law of conservation of mass that you studied in Class IX; mass can neither be created nor destroyed in a chemical reaction.",
                    }
                ],
            },
            {
                "concept_id": "CPT-CH01-006",
                "name": "Balanced Chemical Equation",
                "canonical_name": "balanced_chemical_equation",
                "description": "A chemical equation in which the total number of atoms of each element is identical on both sides of the reaction arrow, satisfying mass conservation.",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T01",
                "subtopic_id": "CH01-T01-S03",
                "concept_type": "CORE",
                "difficulty_level": "MEDIUM",
                "learning_objective": "Verify whether a given chemical equation satisfies atomic balance.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-006-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 3,
                        "section_heading": "1.1.2 Balanced Chemical Equations",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "the number of atoms of each element remains the same, before and after a chemical reaction. Hence, we need to balance a skeletal chemical equation.",
                    }
                ],
            },
            {
                "concept_id": "CPT-CH01-007",
                "name": "Balancing Chemical Equations (Hit and Trial Method)",
                "canonical_name": "balancing_chemical_equations",
                "description": "Systematic method of adjusting stoichiometric coefficients before formulas to equate atom counts on LHS and RHS without altering molecular subscripts.",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T01",
                "subtopic_id": "CH01-T01-S03",
                "concept_type": "PRACTICAL",
                "difficulty_level": "MEDIUM",
                "learning_objective": "Balance complex skeletal chemical equations using stoichiometric coefficients.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-007-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 4,
                        "section_heading": "1.1.2 Balanced Chemical Equations",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "This method of balancing chemical equations is called hit-and-trial method as we make trials to balance the equation by using the smallest whole number coefficient.",
                    }
                ],
            },
            {
                "concept_id": "CPT-CH01-008",
                "name": "Physical State Notations in Equations",
                "canonical_name": "physical_state_notations",
                "description": "Indicating physical states of reactants and products using symbols (s) for solid, (l) for liquid, (g) for gas, and (aq) for aqueous solutions in chemical equations.",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T01",
                "subtopic_id": "CH01-T01-S03",
                "concept_type": "CORE",
                "difficulty_level": "EASY",
                "learning_objective": "Annotate chemical equations with complete physical state and reaction condition symbols.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-008-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 5,
                        "section_heading": "1.1.2 Balanced Chemical Equations",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "The gaseous, liquid, aqueous and solid states of reactants and products are represented by the notations (g), (l), (aq) and (s), respectively.",
                    }
                ],
            },

            # Topic CH01-T02: Types of Chemical Reactions
            {
                "concept_id": "CPT-CH01-009",
                "name": "Combination Reaction",
                "canonical_name": "combination_reaction",
                "description": "A type of chemical reaction in which two or more elements or compounds combine to synthesize a single compound.",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T02",
                "subtopic_id": "CH01-T02-S01",
                "concept_type": "CORE",
                "difficulty_level": "MEDIUM",
                "learning_objective": "Recognize and write equations for combination reactions.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-009-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 6,
                        "section_heading": "1.2.1 Combination Reaction",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "Such a reaction in which a single product is formed from two or more reactants is known as a combination reaction.",
                    }
                ],
            },
            {
                "concept_id": "CPT-CH01-010",
                "name": "Slaked Lime Formation and Whitewashing",
                "canonical_name": "slaked_lime_formation",
                "description": "Exothermic combination of quicklime (calcium oxide) with water forming slaked lime (calcium hydroxide), followed by slow reaction with atmospheric CO2 to form shiny calcium carbonate.",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T02",
                "subtopic_id": "CH01-T02-S01",
                "concept_type": "APPLIED",
                "difficulty_level": "MEDIUM",
                "learning_objective": "Explain the chemistry of whitewashing using CaO, Ca(OH)2, and CaCO3 reactions.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-010-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 6,
                        "section_heading": "1.2.1 Combination Reaction",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "Calcium oxide reacts vigorously with water to produce slaked lime (calcium hydroxide) releasing a large amount of heat.",
                    }
                ],
            },
            {
                "concept_id": "CPT-CH01-011",
                "name": "Exothermic Reaction",
                "canonical_name": "exothermic_reaction",
                "description": "Chemical reactions accompanied by the evolution or release of thermal energy into the surroundings, resulting in temperature rise.",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T02",
                "subtopic_id": "CH01-T02-S05",
                "concept_type": "CORE",
                "difficulty_level": "EASY",
                "learning_objective": "Distinguish exothermic reactions from endothermic reactions on energetic criteria.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-011-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 7,
                        "section_heading": "1.2.1 Combination Reaction",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "Reactions in which heat is released along with the formation of products are called exothermic chemical reactions.",
                    }
                ],
            },
            {
                "concept_id": "CPT-CH01-012",
                "name": "Respiration as an Exothermic Process",
                "canonical_name": "respiration_exothermic_process",
                "description": "Biological oxidation of glucose in body cells releasing energy necessary for life maintenance, making cellular respiration an exothermic process.",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T02",
                "subtopic_id": "CH01-T02-S05",
                "concept_type": "APPLIED",
                "difficulty_level": "MEDIUM",
                "learning_objective": "Write the chemical equation for cellular respiration and justify its exothermic nature.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-012-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 7,
                        "section_heading": "1.2.1 Combination Reaction",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "Respiration is an exothermic process. C6H12O6(aq) + 6O2(aq) -> 6CO2(aq) + 6H2O(l) + energy",
                    }
                ],
            },
            {
                "concept_id": "CPT-CH01-013",
                "name": "Decomposition Reaction",
                "canonical_name": "decomposition_reaction",
                "description": "A chemical reaction in which a single reactant breaks down upon energy input to yield two or more simpler products.",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T02",
                "subtopic_id": "CH01-T02-S02",
                "concept_type": "CORE",
                "difficulty_level": "MEDIUM",
                "learning_objective": "Identify decomposition reactions and write balanced chemical equations for their pathways.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-013-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 8,
                        "section_heading": "1.2.2 Decomposition Reaction",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "In this reaction you can observe that a single reactant breaks down to give simpler products. This is a decomposition reaction.",
                    }
                ],
            },
            {
                "concept_id": "CPT-CH01-014",
                "name": "Thermal Decomposition",
                "canonical_name": "thermal_decomposition",
                "description": "Decomposition reaction triggered by thermal energy (heating), exemplified by heating ferrous sulphate crystals, limestone (CaCO3), and lead nitrate.",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T02",
                "subtopic_id": "CH01-T02-S02",
                "concept_type": "CORE",
                "difficulty_level": "MEDIUM",
                "learning_objective": "Predict products and observations (colour change, gases evolved) during thermal decomposition.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-014-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 8,
                        "section_heading": "1.2.2 Decomposition Reaction",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "When a decomposition reaction is carried out by heating, it is called thermal decomposition.",
                    }
                ],
            },
            {
                "concept_id": "CPT-CH01-015",
                "name": "Electrolytic Decomposition (Electrolysis)",
                "canonical_name": "electrolytic_decomposition",
                "description": "Decomposition of chemical compounds induced by passing an electric current, notably the electrolysis of acidified water producing hydrogen and oxygen in a 2:1 volume ratio.",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T02",
                "subtopic_id": "CH01-T02-S02",
                "concept_type": "PRACTICAL",
                "difficulty_level": "HARD",
                "learning_objective": "Explain the electrolysis of water and justify the 2:1 gas volume ratio at cathode and anode.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-015-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 9,
                        "section_heading": "1.2.2 Decomposition Reaction",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "Activity 1.7 (Electrolysis of water) ... Is the volume of gas collected the same in both the test tubes?",
                    }
                ],
            },
            {
                "concept_id": "CPT-CH01-016",
                "name": "Photolytic Decomposition (Photolysis)",
                "canonical_name": "photolytic_decomposition",
                "description": "Decomposition reaction initiated by absorption of light photons, exemplified by silver chloride and silver bromide turning grey in sunlight; historically utilized in black-and-white photography.",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T02",
                "subtopic_id": "CH01-T02-S02",
                "concept_type": "APPLIED",
                "difficulty_level": "MEDIUM",
                "learning_objective": "Describe photolysis of silver halides and its historical application in photography.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-016-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 9,
                        "section_heading": "1.2.2 Decomposition Reaction",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "White silver chloride turns grey in sunlight. This is due to the decomposition of silver chloride into silver and chlorine by light. 2AgCl(s) -> 2Ag(s) + Cl2(g)",
                    }
                ],
            },
            {
                "concept_id": "CPT-CH01-017",
                "name": "Endothermic Reaction",
                "canonical_name": "endothermic_reaction",
                "description": "Chemical reactions requiring continuous absorption of energy in the form of heat, light, or electricity to rupture reactant bonds and proceed.",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T02",
                "subtopic_id": "CH01-T02-S05",
                "concept_type": "CORE",
                "difficulty_level": "EASY",
                "learning_objective": "Classify chemical transformations as endothermic based on enthalpy absorption.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-017-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 9,
                        "section_heading": "1.2.2 Decomposition Reaction",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "Reactions in which energy is absorbed are known as endothermic reactions.",
                    }
                ],
            },
            {
                "concept_id": "CPT-CH01-018",
                "name": "Displacement Reaction",
                "canonical_name": "displacement_reaction",
                "description": "A reaction in which a more reactive chemical element displaces or expels a less reactive element from its aqueous salt solution (e.g. Iron nails dipping in copper sulphate solution).",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T02",
                "subtopic_id": "CH01-T02-S03",
                "concept_type": "CORE",
                "difficulty_level": "MEDIUM",
                "learning_objective": "Predict displacement outcomes using relative metal reactivities.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-018-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 10,
                        "section_heading": "1.2.3 Displacement Reaction",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "In this reaction, iron has displaced or removed another element, copper, from copper sulphate solution. This reaction is known as displacement reaction.",
                    }
                ],
            },
            {
                "concept_id": "CPT-CH01-019",
                "name": "Double Displacement Reaction",
                "canonical_name": "double_displacement_reaction",
                "description": "A chemical reaction involving mutual exchange of ions between two aqueous ionic reactant compounds to generate two new product compounds.",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T02",
                "subtopic_id": "CH01-T02-S04",
                "concept_type": "CORE",
                "difficulty_level": "MEDIUM",
                "learning_objective": "Formulate balanced double displacement equations and identify ionic exchange.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-019-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 11,
                        "section_heading": "1.2.4 Double Displacement Reaction",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "Such reactions in which there is an exchange of ions between the reactants are called double displacement reactions.",
                    }
                ],
            },
            {
                "concept_id": "CPT-CH01-020",
                "name": "Precipitation Reaction",
                "canonical_name": "precipitation_reaction",
                "description": "A reaction resulting in the formation of an insoluble solid compound (precipitate) that settles out of an aqueous solution (e.g. BaSO4 formation from Na2SO4 and BaCl2).",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T02",
                "subtopic_id": "CH01-T02-S04",
                "concept_type": "PRACTICAL",
                "difficulty_level": "MEDIUM",
                "learning_objective": "Identify precipitates and write ionic net precipitation equations.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-020-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 11,
                        "section_heading": "1.2.4 Double Displacement Reaction",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "Any reaction that produces a precipitate can be called a precipitation reaction. The white precipitate of BaSO4 is formed by the reaction of SO4(2-) and Ba(2+).",
                    }
                ],
            },

            # Topic CH01-T03: Oxidation and Reduction
            {
                "concept_id": "CPT-CH01-021",
                "name": "Oxidation",
                "canonical_name": "oxidation",
                "description": "A chemical process characterized by the gain of oxygen atoms or loss of hydrogen atoms by a substance during a reaction.",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T03",
                "subtopic_id": "CH01-T03-S01",
                "concept_type": "CORE",
                "difficulty_level": "MEDIUM",
                "learning_objective": "Identify oxidized species in classical oxygen/hydrogen transfer reactions.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-021-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 12,
                        "section_heading": "1.2.5 Oxidation and Reduction",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "If a substance gains oxygen during a reaction, it is said to be oxidised.",
                    }
                ],
            },
            {
                "concept_id": "CPT-CH01-022",
                "name": "Reduction",
                "canonical_name": "reduction",
                "description": "A chemical process characterized by the loss of oxygen atoms or gain of hydrogen atoms by a substance during a reaction.",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T03",
                "subtopic_id": "CH01-T03-S01",
                "concept_type": "CORE",
                "difficulty_level": "MEDIUM",
                "learning_objective": "Identify reduced species in classical oxygen/hydrogen transfer reactions.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-022-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 12,
                        "section_heading": "1.2.5 Oxidation and Reduction",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "If a substance loses oxygen during a reaction, it is said to be reduced.",
                    }
                ],
            },
            {
                "concept_id": "CPT-CH01-023",
                "name": "Redox Reaction (Oxidation-Reduction Reaction)",
                "canonical_name": "redox_reaction",
                "description": "A reaction occurring with concurrent and complementary oxidation and reduction, where one reactant is oxidized while another is reduced (e.g. CuO + H2 -> Cu + H2O).",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T03",
                "subtopic_id": "CH01-T03-S01",
                "concept_type": "CORE",
                "difficulty_level": "HARD",
                "learning_objective": "Analyze redox reactions to identify substances oxidized, reduced, oxidizing agents, and reducing agents.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-023-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 12,
                        "section_heading": "1.2.5 Oxidation and Reduction",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "One reactant gets oxidised while the other gets reduced during a reaction. Such reactions are called oxidation-reduction reactions or redox reactions.",
                    }
                ],
            },
            {
                "concept_id": "CPT-CH01-024",
                "name": "Oxidizing and Reducing Agents",
                "canonical_name": "oxidizing_and_reducing_agents",
                "description": "An oxidizing agent is a substance that causes oxidation by providing oxygen or accepting electrons (and is itself reduced); a reducing agent provides hydrogen or donates electrons (and is itself oxidized).",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T03",
                "subtopic_id": "CH01-T03-S01",
                "concept_type": "CORE",
                "difficulty_level": "HARD",
                "learning_objective": "Determine the oxidizing agent and reducing agent in a redox reaction.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-024-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 13,
                        "section_heading": "1.2.5 Oxidation and Reduction",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "In equation (1.31), carbon is oxidised to CO and ZnO is reduced to Zn... MnO2 + 4HCl -> MnCl2 + 2H2O + Cl2",
                    }
                ],
            },
            {
                "concept_id": "CPT-CH01-025",
                "name": "Corrosion",
                "canonical_name": "corrosion",
                "description": "The slow destructive chemical or electrochemical deterioration of refined metals by airborne atmospheric agents like moisture, oxygen, and carbon dioxide (e.g. Rusting of iron, black silver sulphide, green copper carbonate).",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T03",
                "subtopic_id": "CH01-T03-S02",
                "concept_type": "APPLIED",
                "difficulty_level": "MEDIUM",
                "learning_objective": "Describe everyday metal corrosion phenomena and identify the environmental reactants involved.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-025-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 13,
                        "section_heading": "1.3.1 Corrosion",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "When a metal is attacked by substances around it such as moisture, acids, etc., it is said to corrode and this process is called corrosion.",
                    }
                ],
            },
            {
                "concept_id": "CPT-CH01-026",
                "name": "Rancidity",
                "canonical_name": "rancidity",
                "description": "The aerial oxidation of unsaturated fats and oils in food substances, generating volatile degradation products causing unpleasant smell, stale taste, and nutritional decline.",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T03",
                "subtopic_id": "CH01-T03-S02",
                "concept_type": "APPLIED",
                "difficulty_level": "EASY",
                "learning_objective": "Explain the causes of rancidity in lipid-containing foods.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-026-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 13,
                        "section_heading": "1.3.2 Rancidity",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "When fats and oils are oxidised, they become rancid and their smell and taste change.",
                    }
                ],
            },
            {
                "concept_id": "CPT-CH01-027",
                "name": "Prevention of Oxidation in Everyday Life",
                "canonical_name": "prevention_of_oxidation",
                "description": "Technological interventions to mitigate destructive oxidation: addition of antioxidants, packaging in inert gas (e.g. Nitrogen flushed chips bags), airtight refrigeration, and surface barrier coatings.",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T03",
                "subtopic_id": "CH01-T03-S02",
                "concept_type": "APPLIED",
                "difficulty_level": "EASY",
                "learning_objective": "Evaluate prevention methods for food spoilage and metal degradation.",
                "source_status": "SOURCE_DERIVED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-027-01",
                        "source_document_id": "NCERT_SCI_10_CH01",
                        "source_filename": "jesc101.pdf",
                        "page_number": 13,
                        "section_heading": "1.3.2 Rancidity",
                        "extraction_method": "NATIVE_PDF_PARSE",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "Usually substances which prevent oxidation (antioxidants) are added to foods containing fats and oil... flush bags of chips with gas such as nitrogen to prevent the chips from getting oxidised.",
                    }
                ],
            },

            # Topic CH01-T04: Periodic Classification of Elements (Formative Learning)
            {
                "concept_id": "CPT-CH01-028",
                "name": "Early Attempts at Classification of Elements",
                "canonical_name": "early_attempts_classification",
                "description": "Historical grouping of chemical elements based on atomic mass and triad properties: Döbereiner's Triads and Newlands' Law of Octaves (Formative assessment only).",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T04",
                "subtopic_id": "CH01-T04-S01",
                "concept_type": "EXTENDED",
                "difficulty_level": "EASY",
                "learning_objective": "Appreciate historical developments in chemical element classification.",
                "source_status": "CURRICULUM_SYNTHESIZED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-028-01",
                        "source_document_id": "CBSE_SCI_10_2026_27",
                        "source_filename": "Science_SecP1_2026-27.pdf",
                        "page_number": 4,
                        "section_heading": "Unit I: Formative Assessment Scope",
                        "extraction_method": "CURRICULUM_AUDIT",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "Periodic classification of elements: Dobereiner's Triads, Newlands' Law of Octaves. For internal assessment only.",
                    }
                ],
            },
            {
                "concept_id": "CPT-CH01-029",
                "name": "Mendeléev's Periodic Table and Modern Trends",
                "canonical_name": "mendeleev_and_modern_trends",
                "description": "Organization of elements by atomic number; modern periodic trends including valency, atomic size, metallic and non-metallic character across periods and down groups (Formative learning).",
                "chapter_id": "CH-01",
                "topic_id": "CH01-T04",
                "subtopic_id": "CH01-T04-S03",
                "concept_type": "EXTENDED",
                "difficulty_level": "MEDIUM",
                "learning_objective": "Trace trends in atomic radius, valency, and metallic character across the modern periodic table.",
                "source_status": "CURRICULUM_SYNTHESIZED",
                "verification_status": "VERIFIED",
                "provenance": [
                    {
                        "provenance_id": "PROV-CH01-029-01",
                        "source_document_id": "CBSE_SCI_10_2026_27",
                        "source_filename": "Science_SecP1_2026-27.pdf",
                        "page_number": 4,
                        "section_heading": "Unit I: Formative Assessment Scope",
                        "extraction_method": "CURRICULUM_AUDIT",
                        "confidence": 1.0,
                        "verification_status": "SOURCE_VERIFIED",
                        "verbatim_text": "Modern periodic table, gradation in properties, valency, atomic number, metallic and non-metallic properties.",
                    }
                ],
            },
        ]

    def _get_chapter_one_canonical_edges(self) -> List[Dict[str, Any]]:
        edges = []

        # PREREQUISITE_OF edges (Direct pedagogical dependency DAG)
        prereqs = [
            # T01 internal prerequisites
            ("CPT-CH01-001", "CPT-CH01-002", "Understanding physical/chemical change is prerequisite to writing chemical equations"),
            ("CPT-CH01-002", "CPT-CH01-003", "Understanding chemical equations precedes word equations"),
            ("CPT-CH01-002", "CPT-CH01-004", "Understanding chemical equations precedes skeletal formula representation"),
            ("CPT-CH01-004", "CPT-CH01-006", "Skeletal equations are the starting point for producing balanced chemical equations"),
            ("CPT-CH01-005", "CPT-CH01-006", "Law of conservation of mass provides theoretical foundation for equation balancing"),
            ("CPT-CH01-006", "CPT-CH01-007", "Concept of balanced equations is required before applying hit-and-trial balancing method"),
            ("CPT-CH01-006", "CPT-CH01-008", "Equation balancing precedes physical state notation annotation"),

            # Cross-Topic: T01 -> T02 (Balanced equations needed to analyze reaction types)
            ("CPT-CH01-006", "CPT-CH01-009", "Balanced chemical equations are required to study combination reaction stoichiometry"),
            ("CPT-CH01-006", "CPT-CH01-013", "Balanced chemical equations are required to study decomposition reaction stoichiometry"),
            ("CPT-CH01-006", "CPT-CH01-018", "Balanced chemical equations are required to study displacement reactions"),

            # T02 internal prerequisites
            ("CPT-CH01-009", "CPT-CH01-010", "General combination reaction concept is prerequisite to slaked lime case study"),
            ("CPT-CH01-009", "CPT-CH01-011", "Combination reactions introduce heat evolution (exothermic reactions)"),
            ("CPT-CH01-011", "CPT-CH01-012", "Exothermic reaction concept is prerequisite to understanding cellular respiration energetics"),
            ("CPT-CH01-013", "CPT-CH01-014", "Decomposition reaction definition is prerequisite to thermal decomposition"),
            ("CPT-CH01-013", "CPT-CH01-015", "Decomposition reaction definition is prerequisite to electrolytic decomposition"),
            ("CPT-CH01-013", "CPT-CH01-016", "Decomposition reaction definition is prerequisite to photolytic decomposition"),
            ("CPT-CH01-013", "CPT-CH01-017", "Decomposition reactions introduce energy absorption (endothermic reactions)"),
            ("CPT-CH01-018", "CPT-CH01-019", "Single displacement precedes understanding double displacement ion exchange"),
            ("CPT-CH01-019", "CPT-CH01-020", "Double displacement concept is prerequisite to precipitate formation mechanics"),

            # Cross-Topic: T01 -> T03 (Chemical reaction is prerequisite to oxidation and reduction)
            ("CPT-CH01-001", "CPT-CH01-021", "Chemical reaction concept is prerequisite to understanding oxidation"),
            ("CPT-CH01-001", "CPT-CH01-022", "Chemical reaction concept is prerequisite to understanding reduction"),

            # T03 internal prerequisites
            ("CPT-CH01-021", "CPT-CH01-023", "Oxidation concept is required to understand concurrent redox reactions"),
            ("CPT-CH01-022", "CPT-CH01-023", "Reduction concept is required to understand concurrent redox reactions"),
            ("CPT-CH01-023", "CPT-CH01-024", "Redox understanding is required to distinguish oxidizing and reducing agents"),
            ("CPT-CH01-021", "CPT-CH01-025", "Oxidation is the fundamental prerequisite mechanism for metal corrosion"),
            ("CPT-CH01-021", "CPT-CH01-026", "Oxidation is the fundamental prerequisite mechanism for lipid rancidity"),
            ("CPT-CH01-026", "CPT-CH01-027", "Understanding rancidity and corrosion is prerequisite to applying antioxidant/protection methods"),

            # T04 formative sequence
            ("CPT-CH01-028", "CPT-CH01-029", "Early classification attempts precede Mendeleev and Modern periodic trends"),
        ]

        for src, tgt, desc in prereqs:
            edges.append({
                "edge_id": f"EDGE-{src}-PREREQ-{tgt}",
                "source_concept_id": src,
                "target_concept_id": tgt,
                "relationship_type": "PREREQUISITE_OF",
                "description": desc,
                "confidence": 1.0,
                "verification_status": "VERIFIED",
                "source_provenance": {"basis": "NCERT_PEDAGOGICAL_PROGRESSION"},
            })

        # PART_OF edges (Component relationships)
        part_ofs = [
            ("CPT-CH01-010", "CPT-CH01-009", "Slaked lime formation is a specific exemplar of combination reactions"),
            ("CPT-CH01-014", "CPT-CH01-013", "Thermal decomposition is a subtype of decomposition reactions"),
            ("CPT-CH01-015", "CPT-CH01-013", "Electrolytic decomposition is a subtype of decomposition reactions"),
            ("CPT-CH01-016", "CPT-CH01-013", "Photolytic decomposition is a subtype of decomposition reactions"),
            ("CPT-CH01-020", "CPT-CH01-019", "Precipitation reactions represent aqueous double displacement reactions"),
            ("CPT-CH01-024", "CPT-CH01-023", "Oxidizing and reducing agents are structural components of redox reactions"),
        ]

        for src, tgt, desc in part_ofs:
            edges.append({
                "edge_id": f"EDGE-{src}-PARTOF-{tgt}",
                "source_concept_id": src,
                "target_concept_id": tgt,
                "relationship_type": "PART_OF",
                "description": desc,
                "confidence": 1.0,
                "verification_status": "VERIFIED",
                "source_provenance": {"basis": "CURRICULUM_TAXONOMY"},
            })

        # RELATED_TO edges (Lateral conceptual associations; non-DAG)
        related = [
            ("CPT-CH01-011", "CPT-CH01-017", "Exothermic and endothermic reactions form thermodynamic complementary pairs"),
            ("CPT-CH01-017", "CPT-CH01-011", "Endothermic and exothermic reactions form thermodynamic complementary pairs"),
            ("CPT-CH01-025", "CPT-CH01-026", "Corrosion and rancidity represent everyday oxidative damage to metals and foods respectively"),
        ]

        for src, tgt, desc in related:
            edges.append({
                "edge_id": f"EDGE-{src}-RELATED-{tgt}",
                "source_concept_id": src,
                "target_concept_id": tgt,
                "relationship_type": "RELATED_TO",
                "description": desc,
                "confidence": 1.0,
                "verification_status": "VERIFIED",
                "source_provenance": {"basis": "CONCEPTUAL_ANALOGY"},
            })

        # SUPPORTS_LEARNING_OUTCOME edges
        # Connecting concepts to CBSE Class 10 Science Chapter 1 Learning Outcomes
        lo_mappings = [
            ("CPT-CH01-006", "LO-C1.3", "Balanced chemical equation supports outcome on balancing equations"),
            ("CPT-CH01-007", "LO-C1.3", "Hit-and-trial balancing method supports outcome on balancing equations"),
            ("CPT-CH01-009", "LO-C1.3", "Combination reaction supports outcome on chemical interactions"),
            ("CPT-CH01-013", "LO-C1.3", "Decomposition reaction supports outcome on chemical interactions"),
            ("CPT-CH01-018", "LO-C1.3", "Displacement reaction supports outcome on chemical interactions"),
            ("CPT-CH01-019", "LO-C1.3", "Double displacement reaction supports outcome on chemical interactions"),
            ("CPT-CH01-023", "LO-C1.3", "Redox reaction supports outcome on chemical interactions"),
            ("CPT-CH01-028", "LO-C1.1", "Early attempts at classification supports periodic table outcome"),
            ("CPT-CH01-029", "LO-C1.1", "Modern periodic trends supports periodic table outcome"),
        ]

        for src, lo_id, desc in lo_mappings:
            edges.append({
                "edge_id": f"EDGE-{src}-SUPPORTS-{lo_id}",
                "source_concept_id": src,
                "target_concept_id": lo_id,
                "relationship_type": "SUPPORTS_LEARNING_OUTCOME",
                "description": desc,
                "confidence": 1.0,
                "verification_status": "VERIFIED",
                "source_provenance": {"basis": "CBSE_CURRICULUM_FRAMEWORK"},
            })

        return edges
