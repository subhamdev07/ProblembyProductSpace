"""
Curriculum Extraction Service
Encapsulates official CBSE Class 10 Science (086) 2026-27 syllabus data
and verified NCERT textbook chapter contents. Provides idempotent database seeding.
"""

from typing import Dict, Any, List
from src.models.classification import AssessmentClassification, VerificationStatus, ProvenanceType
from src.storage.database import CurriculumRepository


class CurriculumExtractionService:
    """
    Extracts and populates curriculum hierarchy, topics, subtopics,
    assessment classifications, and learning outcomes from primary sources.
    """

    def __init__(self, repo: CurriculumRepository):
        self.repo = repo

    def populate_all(self):
        """Idempotently populates the entire verified curriculum hierarchy."""
        self._populate_session_and_curriculum()
        self._populate_units()
        self._populate_chapters()
        self._populate_topics_and_subtopics()
        self._populate_learning_outcomes()
        self._populate_curriculum_mappings()

    def _populate_session_and_curriculum(self):
        # 1. Academic Session
        self.repo.upsert_academic_session({
            "session_id": "2026-27",
            "name": "Academic Session 2026–27",
            "start_year": 2026,
            "end_year": 2027,
            "is_active": 1
        })

        # 2. Subject
        self.repo.upsert_subject({
            "subject_id": "SCI-10",
            "code": "086",
            "name": "Science",
            "class_level": 10,
            "description": "CBSE Secondary School Class X Science covering Chemical Substances, World of Living, Natural Phenomena, Effects of Current, and Natural Resources."
        })

        # 3. Curriculum
        self.repo.upsert_curriculum({
            "curriculum_id": "CBSE-SCI-10-2026-27",
            "name": "CBSE Class X Science (086) Syllabus 2026–27",
            "session_id": "2026-27",
            "subject_id": "SCI-10",
            "class_level": 10,
            "authority": "CBSE",
            "metadata_json": {
                "theory_marks": 80,
                "internal_assessment_marks": 20,
                "grand_total_marks": 100,
                "duration_hours": 3,
                "source_authority": "Central Board of Secondary Education",
                "source_doc_id": "CBSE_SCI_10_2026_27"
            }
        })

    def _populate_units(self):
        units_data = [
            {
                "unit_id": "UNIT-01",
                "unit_number": "I",
                "name": "Chemical Substances - Nature and Behaviour",
                "theme": "Materials",
                "curriculum_id": "CBSE-SCI-10-2026-27",
                "marks": 25,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page": 4,
                "source_section": "Unit I: Chemical Substances - Nature and Behaviour"
            },
            {
                "unit_id": "UNIT-02",
                "unit_number": "II",
                "name": "World of Living",
                "theme": "The World of the Living",
                "curriculum_id": "CBSE-SCI-10-2026-27",
                "marks": 25,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page": 5,
                "source_section": "Unit II: World of Living"
            },
            {
                "unit_id": "UNIT-03",
                "unit_number": "III",
                "name": "Natural Phenomena",
                "theme": "Natural Phenomena",
                "curriculum_id": "CBSE-SCI-10-2026-27",
                "marks": 12,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page": 5,
                "source_section": "Unit III: Natural Phenomena"
            },
            {
                "unit_id": "UNIT-04",
                "unit_number": "IV",
                "name": "Effects of Current",
                "theme": "How Things Work",
                "curriculum_id": "CBSE-SCI-10-2026-27",
                "marks": 13,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page": 6,
                "source_section": "Unit IV: Effects of Current"
            },
            {
                "unit_id": "UNIT-05",
                "unit_number": "V",
                "name": "Natural Resources",
                "theme": "Natural Resources",
                "curriculum_id": "CBSE-SCI-10-2026-27",
                "marks": 5,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page": 6,
                "source_section": "Unit V: Natural Resources"
            }
        ]
        for u in units_data:
            self.repo.upsert_unit(u)

    def _populate_chapters(self):
        # 13 Official NCERT Chapters mapped to Units
        chapters_data = [
            # Unit I (Marks: 25)
            {
                "chapter_id": "CH-01",
                "chapter_number": 1,
                "name": "Chemical Reactions and Equations",
                "unit_id": "UNIT-01",
                "curriculum_id": "CBSE-SCI-10-2026-27",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "metadata_json": {
                    "source_doc_id": "CBSE_SCI_10_2026_27",
                    "syllabus_page": 4,
                    "textbook_doc_id": "NCERT_SCI_10_CH01",
                    "textbook_available": True,
                    "textbook_pages": "1-16"
                }
            },
            {
                "chapter_id": "CH-02",
                "chapter_number": 2,
                "name": "Acids, Bases and Salts",
                "unit_id": "UNIT-01",
                "curriculum_id": "CBSE-SCI-10-2026-27",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "metadata_json": {
                    "source_doc_id": "CBSE_SCI_10_2026_27",
                    "syllabus_page": 4,
                    "textbook_available": False,
                    "pending_textbook_file": "jesc102.pdf"
                }
            },
            {
                "chapter_id": "CH-03",
                "chapter_number": 3,
                "name": "Metals and Non-Metals",
                "unit_id": "UNIT-01",
                "curriculum_id": "CBSE-SCI-10-2026-27",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "metadata_json": {
                    "source_doc_id": "CBSE_SCI_10_2026_27",
                    "syllabus_page": 5,
                    "textbook_available": False,
                    "pending_textbook_file": "jesc103.pdf"
                }
            },
            {
                "chapter_id": "CH-04",
                "chapter_number": 4,
                "name": "Carbon and Its Compounds",
                "unit_id": "UNIT-01",
                "curriculum_id": "CBSE-SCI-10-2026-27",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "metadata_json": {
                    "source_doc_id": "CBSE_SCI_10_2026_27",
                    "syllabus_page": 5,
                    "textbook_available": False,
                    "pending_textbook_file": "jesc104.pdf"
                }
            },
            # Unit II (Marks: 25)
            {
                "chapter_id": "CH-05",
                "chapter_number": 5,
                "name": "Life Processes",
                "unit_id": "UNIT-02",
                "curriculum_id": "CBSE-SCI-10-2026-27",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "metadata_json": {
                    "source_doc_id": "CBSE_SCI_10_2026_27",
                    "syllabus_page": 5,
                    "textbook_available": False,
                    "pending_textbook_file": "jesc105.pdf"
                }
            },
            {
                "chapter_id": "CH-06",
                "chapter_number": 6,
                "name": "Control and Coordination",
                "unit_id": "UNIT-02",
                "curriculum_id": "CBSE-SCI-10-2026-27",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "metadata_json": {
                    "source_doc_id": "CBSE_SCI_10_2026_27",
                    "syllabus_page": 5,
                    "textbook_available": False,
                    "pending_textbook_file": "jesc106.pdf"
                }
            },
            {
                "chapter_id": "CH-07",
                "chapter_number": 7,
                "name": "How Do Organisms Reproduce?",
                "unit_id": "UNIT-02",
                "curriculum_id": "CBSE-SCI-10-2026-27",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "metadata_json": {
                    "source_doc_id": "CBSE_SCI_10_2026_27",
                    "syllabus_page": 5,
                    "textbook_available": False,
                    "pending_textbook_file": "jesc107.pdf"
                }
            },
            {
                "chapter_id": "CH-08",
                "chapter_number": 8,
                "name": "Heredity",
                "unit_id": "UNIT-02",
                "curriculum_id": "CBSE-SCI-10-2026-27",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "metadata_json": {
                    "source_doc_id": "CBSE_SCI_10_2026_27",
                    "syllabus_page": 5,
                    "formative_subtopic": "Evolution",
                    "textbook_available": False,
                    "pending_textbook_file": "jesc108.pdf"
                }
            },
            # Unit III (Marks: 12)
            {
                "chapter_id": "CH-09",
                "chapter_number": 9,
                "name": "Light – Reflection and Refraction",
                "unit_id": "UNIT-03",
                "curriculum_id": "CBSE-SCI-10-2026-27",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "metadata_json": {
                    "source_doc_id": "CBSE_SCI_10_2026_27",
                    "syllabus_page": 5,
                    "textbook_available": False,
                    "pending_textbook_file": "jesc109.pdf"
                }
            },
            {
                "chapter_id": "CH-10",
                "chapter_number": 10,
                "name": "The Human Eye and the Colourful World",
                "unit_id": "UNIT-03",
                "curriculum_id": "CBSE-SCI-10-2026-27",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "metadata_json": {
                    "source_doc_id": "CBSE_SCI_10_2026_27",
                    "syllabus_page": 6,
                    "excluded_scope": "Colour of the sun at sunrise and sunset",
                    "textbook_available": False,
                    "pending_textbook_file": "jesc110.pdf"
                }
            },
            # Unit IV (Marks: 13)
            {
                "chapter_id": "CH-11",
                "chapter_number": 11,
                "name": "Electricity",
                "unit_id": "UNIT-04",
                "curriculum_id": "CBSE-SCI-10-2026-27",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "metadata_json": {
                    "source_doc_id": "CBSE_SCI_10_2026_27",
                    "syllabus_page": 6,
                    "textbook_available": False,
                    "pending_textbook_file": "jesc111.pdf"
                }
            },
            {
                "chapter_id": "CH-12",
                "chapter_number": 12,
                "name": "Magnetic Effects of Electric Current",
                "unit_id": "UNIT-04",
                "curriculum_id": "CBSE-SCI-10-2026-27",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "metadata_json": {
                    "source_doc_id": "CBSE_SCI_10_2026_27",
                    "syllabus_page": 6,
                    "formative_subtopics": "Motor, Electromagnetic Induction, Electric Generator",
                    "textbook_available": False,
                    "pending_textbook_file": "jesc112.pdf"
                }
            },
            # Unit V (Marks: 05)
            {
                "chapter_id": "CH-13",
                "chapter_number": 13,
                "name": "Our Environment",
                "unit_id": "UNIT-05",
                "curriculum_id": "CBSE-SCI-10-2026-27",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "metadata_json": {
                    "source_doc_id": "CBSE_SCI_10_2026_27",
                    "syllabus_page": 6,
                    "textbook_available": False,
                    "pending_textbook_file": "jesc113.pdf"
                }
            }
        ]
        for ch in chapters_data:
            self.repo.upsert_chapter(ch)

    def _populate_topics_and_subtopics(self):
        topics_data = [
            # ---------------- CHAPTER 1 ----------------
            {
                "topic_id": "CH01-T01",
                "chapter_id": "CH-01",
                "name": "Chemical Equations and Balancing",
                "sequence_order": 1,
                "description": "Chemical reactions, representation by chemical equations, balanced chemical equation, law of conservation of mass, hit-and-trial balancing method.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 4,
                "source_page_end": 4,
                "source_section": "Unit I: Chemical Reactions and Equations",
                "subtopics": [
                    {"subtopic_id": "CH01-T01-S01", "name": "Chemical Reactions and Everyday Observations", "sequence_order": 1, "description": "Changes in state, colour, temperature, and evolution of gas."},
                    {"subtopic_id": "CH01-T01-S02", "name": "Writing Chemical Equations and Skeletal Equations", "sequence_order": 2, "description": "Formulas of reactants and products, symbols of physical states."},
                    {"subtopic_id": "CH01-T01-S03", "name": "Balanced Chemical Equations", "sequence_order": 3, "description": "Conservation of mass and hit-and-trial balancing."}
                ]
            },
            {
                "topic_id": "CH01-T02",
                "chapter_id": "CH-01",
                "name": "Types of Chemical Reactions",
                "sequence_order": 2,
                "description": "Combination, decomposition, displacement, double displacement, precipitation, and exothermic/endothermic reactions.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 4,
                "source_page_end": 4,
                "source_section": "Unit I: Chemical Reactions and Equations",
                "subtopics": [
                    {"subtopic_id": "CH01-T02-S01", "name": "Combination Reactions", "sequence_order": 1, "description": "Two or more reactants combine to form a single product (quicklime and water)."},
                    {"subtopic_id": "CH01-T02-S02", "name": "Decomposition Reactions", "sequence_order": 2, "description": "Thermal, electrolytic, and photolytic decomposition."},
                    {"subtopic_id": "CH01-T02-S03", "name": "Displacement Reactions", "sequence_order": 3, "description": "More reactive metal displacing less reactive metal from salt solution."},
                    {"subtopic_id": "CH01-T02-S04", "name": "Double Displacement and Precipitation Reactions", "sequence_order": 4, "description": "Exchange of ions between reactants forming insoluble precipitate."},
                    {"subtopic_id": "CH01-T02-S05", "name": "Exothermic and Endothermic Reactions", "sequence_order": 5, "description": "Heat release (respiration, decomposition of vegetable matter) versus heat absorption."}
                ]
            },
            {
                "topic_id": "CH01-T03",
                "chapter_id": "CH-01",
                "name": "Oxidation and Reduction",
                "sequence_order": 3,
                "description": "Gain or loss of oxygen and hydrogen, redox reactions, oxidizing and reducing agents.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 4,
                "source_page_end": 4,
                "source_section": "Unit I: Chemical Reactions and Equations",
                "subtopics": [
                    {"subtopic_id": "CH01-T03-S01", "name": "Redox Reactions Mechanisms", "sequence_order": 1, "description": "Simultaneous oxidation and reduction in chemical processes."},
                    {"subtopic_id": "CH01-T03-S02", "name": "Corrosion and Rancidity in Everyday Life", "sequence_order": 2, "description": "Oxidation of iron (rusting), antioxidants, and packaging of fats/oils."}
                ]
            },
            {
                "topic_id": "CH01-T04",
                "chapter_id": "CH-01",
                "name": "Periodic Classification of Elements (Formative Learning)",
                "sequence_order": 4,
                "description": "Historical development of periodic classification: Döbereiner’s Triads, Newlands’ Law of Octaves, Mendeléev’s Periodic Table, Modern Periodic Table and Metallic/Non-metallic properties.",
                "assessment_status": AssessmentClassification.FORMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 4,
                "source_page_end": 4,
                "source_section": "Unit I: Note on Formative Topics / Periodic Classification",
                "subtopics": [
                    {"subtopic_id": "CH01-T04-S01", "name": "Early Attempts at Classification", "sequence_order": 1, "description": "Döbereiner’s Triads and Newlands’ Law of Octaves."},
                    {"subtopic_id": "CH01-T04-S02", "name": "Mendeléev’s Periodic Table", "sequence_order": 2, "description": "Periodic Law, merits, anomalies, and gaps."},
                    {"subtopic_id": "CH01-T04-S03", "name": "Modern Periodic Table and Trends", "sequence_order": 3, "description": "Atomic number, valency, atomic size, metallic and non-metallic properties."}
                ]
            },

            # ---------------- CHAPTER 2 ----------------
            {
                "topic_id": "CH02-T01",
                "chapter_id": "CH-02",
                "name": "Acids and Bases - Nature and Indicators",
                "sequence_order": 1,
                "description": "Definitions in terms of furnishing of H+ and OH– ions, identification using indicators (litmus, phenolphthalein, methyl orange, universal indicator, olfactory indicators).",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 4,
                "source_page_end": 5,
                "source_section": "Unit I: Acids, Bases and Salts",
                "subtopics": [
                    {"subtopic_id": "CH02-T01-S01", "name": "Ion Furnishing Definitions (H+ and OH-)", "sequence_order": 1, "description": "Arrhenius conceptualization of acidic and basic character in aqueous solutions."},
                    {"subtopic_id": "CH02-T01-S02", "name": "Acid-Base Indicators", "sequence_order": 2, "description": "Natural, synthetic, universal, and olfactory indicators."}
                ]
            },
            {
                "topic_id": "CH02-T02",
                "chapter_id": "CH-02",
                "name": "Chemical Properties of Acids and Bases",
                "sequence_order": 2,
                "description": "Reactions with metals, metal carbonates, metal hydrogen carbonates, metallic oxides, non-metallic oxides, and neutralization.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 4,
                "source_page_end": 5,
                "source_section": "Unit I: Acids, Bases and Salts",
                "subtopics": [
                    {"subtopic_id": "CH02-T02-S01", "name": "Reaction with Metals", "sequence_order": 1, "description": "Evolution of hydrogen gas with dilute acids and amphoteric bases."},
                    {"subtopic_id": "CH02-T02-S02", "name": "Reaction with Carbonates and Hydrogencarbonates", "sequence_order": 2, "description": "Formation of salt, water, and carbon dioxide gas (lime water test)."},
                    {"subtopic_id": "CH02-T02-S03", "name": "Neutralization Reaction", "sequence_order": 3, "description": "Reaction of acid and base producing salt and water."}
                ]
            },
            {
                "topic_id": "CH02-T03",
                "chapter_id": "CH-02",
                "name": "Concept of pH Scale and Everyday Applications",
                "sequence_order": 3,
                "description": "pH scale (definition relating to logarithm not required), measurement of hydrogen ion concentration, importance of pH in everyday life.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 4,
                "source_page_end": 5,
                "source_section": "Unit I: Acids, Bases and Salts",
                "subtopics": [
                    {"subtopic_id": "CH02-T03-S01", "name": "pH Scale Definition and Interpretation", "sequence_order": 1, "description": "0 to 14 scale, neutral, acidic, and basic ranges without logarithmic formula."},
                    {"subtopic_id": "CH02-T03-S02", "name": "pH in Daily Life", "sequence_order": 2, "description": "Digestive system, tooth decay, soil testing, acid rain, animal/plant defense."}
                ]
            },
            {
                "topic_id": "CH02-T04",
                "chapter_id": "CH-02",
                "name": "Preparation, Properties and Uses of Important Salts",
                "sequence_order": 4,
                "description": "Chemical formulas, preparation, properties, and commercial/domestic uses of Sodium Hydroxide, Bleaching Powder, Baking Soda, Washing Soda, and Plaster of Paris.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 4,
                "source_page_end": 5,
                "source_section": "Unit I: Acids, Bases and Salts",
                "subtopics": [
                    {"subtopic_id": "CH02-T04-S01", "name": "Sodium Hydroxide (Chlor-Alkali Process)", "sequence_order": 1, "description": "Electrolysis of brine, production of NaOH, Cl2, and H2."},
                    {"subtopic_id": "CH02-T04-S02", "name": "Bleaching Powder (CaOCl2)", "sequence_order": 2, "description": "Action of chlorine on dry slaked lime and bleaching applications."},
                    {"subtopic_id": "CH02-T04-S03", "name": "Baking Soda (NaHCO3)", "sequence_order": 3, "description": "Solvay process, baking powder composition, antacid use."},
                    {"subtopic_id": "CH02-T04-S04", "name": "Washing Soda (Na2CO3.10H2O)", "sequence_order": 4, "description": "Recrystallization of sodium carbonate, removal of permanent hardness."},
                    {"subtopic_id": "CH02-T04-S05", "name": "Plaster of Paris (CaSO4.1/2H2O)", "sequence_order": 5, "description": "Heating gypsum, water of crystallization, medical casts and statues."}
                ]
            },

            # ---------------- CHAPTER 3 ----------------
            {
                "topic_id": "CH03-T01",
                "chapter_id": "CH-03",
                "name": "Physical and Chemical Properties of Metals and Non-Metals",
                "sequence_order": 1,
                "description": "Lustre, malleability, ductility, electrical and thermal conductivity, sonority, chemical reactions with oxygen, water, and dilute acids.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit I: Metals and Non-metals",
                "subtopics": [
                    {"subtopic_id": "CH03-T01-S01", "name": "Physical Properties and Exceptions", "sequence_order": 1, "description": "Ductility, malleability, mercury, iodine, diamond, gallium, caesium."},
                    {"subtopic_id": "CH03-T01-S02", "name": "Reactions with Oxygen, Water, and Acids", "sequence_order": 2, "description": "Basic and amphoteric oxides, evolution of hydrogen."}
                ]
            },
            {
                "topic_id": "CH03-T02",
                "chapter_id": "CH-03",
                "name": "Reactivity Series of Metals",
                "sequence_order": 2,
                "description": "Arrangement of metals in order of decreasing reactivity (K, Na, Ca, Mg, Al, Zn, Fe, Pb, H, Cu, Hg, Ag, Au).",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit I: Metals and Non-metals",
                "subtopics": [
                    {"subtopic_id": "CH03-T02-S01", "name": "Activity Series and Displacement Trends", "sequence_order": 1, "description": "Experimental verification using metal and salt solutions."}
                ]
            },
            {
                "topic_id": "CH03-T03",
                "chapter_id": "CH-03",
                "name": "Formation and Properties of Ionic Compounds",
                "sequence_order": 3,
                "description": "Transfer of electrons from metals to non-metals, electron dot structures, crystal lattice, high melting/boiling points, conductivity in solution.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit I: Metals and Non-metals",
                "subtopics": [
                    {"subtopic_id": "CH03-T03-S01", "name": "Electron Transfer and Dot Representations", "sequence_order": 1, "description": "Formation of NaCl and MgCl2."},
                    {"subtopic_id": "CH03-T03-S02", "name": "Properties of Ionic Compounds", "sequence_order": 2, "description": "Physical state, melting points, solubility, and electrical conductivity."}
                ]
            },
            {
                "topic_id": "CH03-T04",
                "chapter_id": "CH-03",
                "name": "Basic Metallurgical Processes",
                "sequence_order": 4,
                "description": "Occurrence of metals, minerals, ores, enrichment of ores, roasting, calcination, reduction to metal, and refining.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit I: Metals and Non-metals",
                "subtopics": [
                    {"subtopic_id": "CH03-T04-S01", "name": "Extraction Principles by Reactivity Category", "sequence_order": 1, "description": "Metals low, medium, and high in the reactivity series."},
                    {"subtopic_id": "CH03-T04-S02", "name": "Refining of Metals", "sequence_order": 2, "description": "Electrolytic refining of copper."}
                ]
            },
            {
                "topic_id": "CH03-T05",
                "chapter_id": "CH-03",
                "name": "Corrosion and Its Prevention",
                "sequence_order": 5,
                "description": "Conditions for corrosion, rusting of iron, tarnishing of silver, green coating on copper, prevention by painting, greasing, galvanisation, chrome plating, anodising, and alloying.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit I: Metals and Non-metals",
                "subtopics": [
                    {"subtopic_id": "CH03-T05-S01", "name": "Mechanisms and Prevention Techniques", "sequence_order": 1, "description": "Galvanisation, alloys (steel, stainless steel, brass, bronze, solder, amalgam)."}
                ]
            },

            # ---------------- CHAPTER 4 ----------------
            {
                "topic_id": "CH04-T01",
                "chapter_id": "CH-04",
                "name": "Covalent Bonding and Versatile Nature of Carbon",
                "sequence_order": 1,
                "description": "Covalent bonds, formation and properties of covalent compounds, electron dot structures of H2, O2, N2, CH4, versatile nature of carbon: catenation and tetravalency.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit I: Carbon and its Compounds",
                "subtopics": [
                    {"subtopic_id": "CH04-T01-S01", "name": "Covalent Bond Formation and Electron Dot Structures", "sequence_order": 1, "description": "Single, double, and triple covalent bonds."},
                    {"subtopic_id": "CH04-T01-S02", "name": "Catenation and Tetravalency", "sequence_order": 2, "description": "Reasons for millions of carbon compounds."}
                ]
            },
            {
                "topic_id": "CH04-T02",
                "chapter_id": "CH-04",
                "name": "Saturated and Unsaturated Hydrocarbons and Homologous Series",
                "sequence_order": 2,
                "description": "Alkanes, alkenes, alkynes, chains, branches and rings, structural isomers, characteristics of homologous series.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit I: Carbon and its Compounds",
                "subtopics": [
                    {"subtopic_id": "CH04-T02-S01", "name": "Alkanes, Alkenes, Alkynes", "sequence_order": 1, "description": "General formulas CnH2n+2, CnH2n, CnH2n-2."},
                    {"subtopic_id": "CH04-T02-S02", "name": "Homologous Series", "sequence_order": 2, "description": "CH2 gradation, gradation in physical properties."}
                ]
            },
            {
                "topic_id": "CH04-T03",
                "chapter_id": "CH-04",
                "name": "Nomenclature of Carbon Compounds Containing Functional Groups",
                "sequence_order": 3,
                "description": "Nomenclature of alkanes, alkenes, alkynes and compounds containing functional groups: halogens, alcohol, ketones, aldehydes.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit I: Carbon and its Compounds",
                "subtopics": [
                    {"subtopic_id": "CH04-T03-S01", "name": "IUPAC Naming Rules for Class 10", "sequence_order": 1, "description": "Prefixes, suffixes, functional group identification."}
                ]
            },
            {
                "topic_id": "CH04-T04",
                "chapter_id": "CH-04",
                "name": "Chemical Properties of Carbon Compounds",
                "sequence_order": 4,
                "description": "Combustion, oxidation (alkaline KMnO4 / acidified K2Cr2O7), addition reactions (hydrogenation of vegetable oils), and substitution reactions.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit I: Carbon and its Compounds",
                "subtopics": [
                    {"subtopic_id": "CH04-T04-S01", "name": "Combustion and Flame Types", "sequence_order": 1, "description": "Sooty vs clean flame."},
                    {"subtopic_id": "CH04-T04-S02", "name": "Oxidation, Addition and Substitution", "sequence_order": 2, "description": "Reactions with chlorine, oxidizing agents, and catalysts."}
                ]
            },
            {
                "topic_id": "CH04-T05",
                "chapter_id": "CH-04",
                "name": "Ethanol and Ethanoic Acid",
                "sequence_order": 5,
                "description": "Properties and uses of ethanol and ethanoic acid, esterification reaction, saponification reaction, reaction with sodium, and carbonates.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit I: Carbon and its Compounds",
                "subtopics": [
                    {"subtopic_id": "CH04-T05-S01", "name": "Ethanol Properties and Reactions", "sequence_order": 1, "description": "Combustion, sodium reaction, dehydration to ethene."},
                    {"subtopic_id": "CH04-T05-S02", "name": "Ethanoic Acid Reactions", "sequence_order": 2, "description": "Glacial acetic acid, esterification, reaction with carbonates."}
                ]
            },
            {
                "topic_id": "CH04-T06",
                "chapter_id": "CH-04",
                "name": "Soaps and Detergents",
                "sequence_order": 6,
                "description": "Structure of soap molecule, hydrophilic and hydrophobic ends, micelle formation, mechanism of cleansing action, limitation of soaps in hard water, synthetic detergents.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit I: Carbon and its Compounds",
                "subtopics": [
                    {"subtopic_id": "CH04-T06-S01", "name": "Cleansing Action and Micelles", "sequence_order": 1, "description": "Emulsification of grease and scum formation in hard water."}
                ]
            },

            # ---------------- CHAPTER 5 ----------------
            {
                "topic_id": "CH05-T01",
                "chapter_id": "CH-05",
                "name": "Concept of Living Beings and Maintenance Processes",
                "sequence_order": 1,
                "description": "Criteria for living beings, molecular movement, need for maintenance processes.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit II: Life processes",
                "subtopics": [
                    {"subtopic_id": "CH05-T01-S01", "name": "Characteristics of Life Processes", "sequence_order": 1, "description": "Molecular movements and cellular maintenance."}
                ]
            },
            {
                "topic_id": "CH05-T02",
                "chapter_id": "CH-05",
                "name": "Nutrition in Plants and Animals",
                "sequence_order": 2,
                "description": "Autotrophic nutrition, photosynthesis equation, light and dark phases, stomata opening and closing, heterotrophic nutrition (saprophytic, parasitic, holozoic), human alimentary canal and digestive enzymes.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit II: Life processes",
                "subtopics": [
                    {"subtopic_id": "CH05-T02-S01", "name": "Autotrophic Nutrition and Photosynthesis", "sequence_order": 1, "description": "Chloroplast, chlorophyll, stomatal apparatus, absorption/reduction steps."},
                    {"subtopic_id": "CH05-T02-S02", "name": "Nutrition in Amoeba and Paramecium", "sequence_order": 2, "description": "Phagocytosis and food vacuole."},
                    {"subtopic_id": "CH05-T02-S03", "name": "Human Digestive System", "sequence_order": 3, "description": "Salivary amylase, pepsin, HCl, bile, trypsin, lipase, intestinal enzymes, villi."}
                ]
            },
            {
                "topic_id": "CH05-T03",
                "chapter_id": "CH-05",
                "name": "Respiration in Plants and Animals",
                "sequence_order": 3,
                "description": "Breakdown of glucose by various pathways (glycolysis, aerobic in mitochondria, anaerobic in yeast and muscle cells), ATP as energy currency, respiratory organs in aquatic vs terrestrial animals, human respiratory system and alveolar gas exchange.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit II: Life processes",
                "subtopics": [
                    {"subtopic_id": "CH05-T03-S01", "name": "Glucose Breakdown Pathways", "sequence_order": 1, "description": "Aerobic, anaerobic (fermentation), lactic acid build-up."},
                    {"subtopic_id": "CH05-T03-S02", "name": "Human Respiratory System", "sequence_order": 2, "description": "Trachea, bronchi, alveoli, diaphragm mechanism, hemoglobin."}
                ]
            },
            {
                "topic_id": "CH05-T04",
                "chapter_id": "CH-05",
                "name": "Transportation in Plants and Animals",
                "sequence_order": 4,
                "description": "Circulatory system in humans: heart structure, double circulation, arteries, veins, capillaries, blood pressure, lymphatic system, transportation in plants: xylem (transpiration pull) and phloem (translocation).",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit II: Life processes",
                "subtopics": [
                    {"subtopic_id": "CH05-T04-S01", "name": "Human Heart and Double Circulation", "sequence_order": 1, "description": "Four chambers, systemic and pulmonary circulation, valves."},
                    {"subtopic_id": "CH05-T04-S02", "name": "Blood Vessels, Platelets and Lymph", "sequence_order": 2, "description": "Clotting, interstitial fluid, tissue drainage."},
                    {"subtopic_id": "CH05-T04-S03", "name": "Transport of Water and Solutes in Plants", "sequence_order": 3, "description": "Xylem vessels/tracheids, suction pull, phloem sieve tubes/companion cells."}
                ]
            },
            {
                "topic_id": "CH05-T05",
                "chapter_id": "CH-05",
                "name": "Excretion in Plants and Animals",
                "sequence_order": 5,
                "description": "Human excretory system, structure and functioning of nephron, urine formation (filtration, reabsorption, secretion), artificial kidney (dialysis), excretion mechanisms in plants.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit II: Life processes",
                "subtopics": [
                    {"subtopic_id": "CH05-T05-S01", "name": "Nephron and Urine Formation", "sequence_order": 1, "description": "Bowman's capsule, glomerulus, tubular reabsorption, collecting duct."},
                    {"subtopic_id": "CH05-T05-S02", "name": "Excretion in Plants", "sequence_order": 2, "description": "Gaseous waste via stomata, storage in leaves/bark, gums and resins."}
                ]
            },

            # ---------------- CHAPTER 6 ----------------
            {
                "topic_id": "CH06-T01",
                "chapter_id": "CH-06",
                "name": "Tropic Movements and Plant Hormones",
                "sequence_order": 1,
                "description": "Directional movements (phototropism, geotropism, chemotropism, hydrotropism), non-directional nastic movements (touch-me-not), plant hormones (auxins, gibberellins, cytokinins, abscisic acid).",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit II: Control and co-ordination in animals and plants",
                "subtopics": [
                    {"subtopic_id": "CH06-T01-S01", "name": "Plant Tropisms", "sequence_order": 1, "description": "Stimulus-response curvature mechanisms."},
                    {"subtopic_id": "CH06-T01-S02", "name": "Phytohormones Function", "sequence_order": 2, "description": "Growth promoters vs growth inhibitors (ABA)."}
                ]
            },
            {
                "topic_id": "CH06-T02",
                "chapter_id": "CH-06",
                "name": "Nervous System and Reflex Action in Animals",
                "sequence_order": 2,
                "description": "Structure of neuron, sensory/motor neurons, synapse, neuromuscular junction, reflex arc, reflex action.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit II: Control and co-ordination in animals and plants",
                "subtopics": [
                    {"subtopic_id": "CH06-T02-S01", "name": "Neuron Architecture and Synaptic Transmission", "sequence_order": 1, "description": "Dendrite, cyton, axon, neurotransmitters."},
                    {"subtopic_id": "CH06-T02-S02", "name": "Reflex Arc Pathway", "sequence_order": 2, "description": "Receptor, sensory nerve, spinal cord interneuron, motor nerve, effector."}
                ]
            },
            {
                "topic_id": "CH06-T03",
                "chapter_id": "CH-06",
                "name": "Human Brain and Voluntary/Involuntary Actions",
                "sequence_order": 3,
                "description": "Central Nervous System (CNS) and Peripheral Nervous System (PNS), anatomy and functions of forebrain, midbrain, and hindbrain (cerebellum, medulla, pons).",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit II: Control and co-ordination in animals and plants",
                "subtopics": [
                    {"subtopic_id": "CH06-T03-S01", "name": "Brain Compartments and Control Functions", "sequence_order": 1, "description": "Cerebrum, cerebellum, posture balance, involuntary centres."}
                ]
            },
            {
                "topic_id": "CH06-T04",
                "chapter_id": "CH-06",
                "name": "Chemical Coordination: Animal Hormones",
                "sequence_order": 4,
                "description": "Endocrine system, ductless glands, pituitary (growth hormone), thyroid (thyroxine, iodine requirement), pancreas (insulin), adrenal (adrenaline), gonads (testosterone, oestrogen), feedback mechanism.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit II: Control and co-ordination in animals and plants",
                "subtopics": [
                    {"subtopic_id": "CH06-T04-S01", "name": "Endocrine Glands and Target Organs", "sequence_order": 1, "description": "Thyroxine, insulin, adrenaline, hormone deficiency disorders (goitre, diabetes, dwarfism/gigantism)."},
                    {"subtopic_id": "CH06-T04-S02", "name": "Feedback Regulation", "sequence_order": 2, "description": "Negative feedback control of insulin release."}
                ]
            },

            # ---------------- CHAPTER 7 ----------------
            {
                "topic_id": "CH07-T01",
                "chapter_id": "CH-07",
                "name": "Asexual Reproduction in Organisms",
                "sequence_order": 1,
                "description": "Binary and multiple fission (Amoeba, Leishmania, Plasmodium), budding (yeast, Hydra), spore formation (Rhizopus), regeneration (Planaria), fragmentation (Spirogyra), vegetative propagation and tissue culture.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit II: Reproduction",
                "subtopics": [
                    {"subtopic_id": "CH07-T01-S01", "name": "Cellular and Multicellular Asexual Modes", "sequence_order": 1, "description": "Fission, budding, regeneration, fragmentation, sporulation."},
                    {"subtopic_id": "CH07-T01-S02", "name": "Vegetative Propagation", "sequence_order": 2, "description": "Natural and artificial propagation, layering, grafting, tissue culture."}
                ]
            },
            {
                "topic_id": "CH07-T02",
                "chapter_id": "CH-07",
                "name": "Sexual Reproduction in Flowering Plants",
                "sequence_order": 2,
                "description": "Anatomy of flower (calyx, corolla, androecium, gynoecium), unisexual and bisexual flowers, pollination agents, pollen tube growth, double fertilization, seed and fruit formation.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit II: Reproduction",
                "subtopics": [
                    {"subtopic_id": "CH07-T02-S01", "name": "Floral Parts and Pollination", "sequence_order": 1, "description": "Stamen, pistil, self and cross pollination."},
                    {"subtopic_id": "CH07-T02-S02", "name": "Fertilization and Dicot Seed Embryo", "sequence_order": 2, "description": "Pollen germination, zygote, cotyledons, plumule, radicle."}
                ]
            },
            {
                "topic_id": "CH07-T03",
                "chapter_id": "CH-07",
                "name": "Reproduction in Human Beings",
                "sequence_order": 3,
                "description": "Puberty and secondary sexual characteristics, male reproductive system (testes, vas deferens, prostate, seminal vesicle, urethra), female reproductive system (ovaries, fallopian tubes, uterus, cervix, vagina), menstrual cycle, fertilization, placenta.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit II: Reproduction",
                "subtopics": [
                    {"subtopic_id": "CH07-T03-S01", "name": "Male and Female Reproductive Systems", "sequence_order": 1, "description": "Gametogenesis organs and copulatory structures."},
                    {"subtopic_id": "CH07-T03-S02", "name": "Fertilization and Embryo Development", "sequence_order": 2, "description": "Zygote implantation, placenta nutrition, gestation period."}
                ]
            },
            {
                "topic_id": "CH07-T04",
                "chapter_id": "CH-07",
                "name": "Reproductive Health and Family Planning",
                "sequence_order": 4,
                "description": "Need and methods of family planning (barrier, chemical, IUD, surgical methods), prevention of STDs (bacterial: gonorrhoea, syphilis; viral: warts, HIV/AIDS), sex ratio, female foeticide, child bearing and women’s health.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit II: Reproduction",
                "subtopics": [
                    {"subtopic_id": "CH07-T04-S01", "name": "Contraceptive Methods", "sequence_order": 1, "description": "Mechanical, oral hormonal pills, copper-T, vasectomy, tubectomy."},
                    {"subtopic_id": "CH07-T04-S02", "name": "Sexually Transmitted Infections and Women's Health", "sequence_order": 2, "description": "Safe sex practices, HIV prevention, maternal nutrition and healthcare."}
                ]
            },

            # ---------------- CHAPTER 8 ----------------
            {
                "topic_id": "CH08-T01",
                "chapter_id": "CH-08",
                "name": "Heredity and Mendel's Laws of Inheritance",
                "sequence_order": 1,
                "description": "Heredity, variations, Mendel’s hybridization experiments on Pisum sativum, monohybrid cross (law of segregation), dihybrid cross (law of independent assortment), dominant and recessive traits, phenotype and genotype ratio.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit II: Heredity",
                "subtopics": [
                    {"subtopic_id": "CH08-T01-S01", "name": "Mendel’s Experiments and Traits Inheritance", "sequence_order": 1, "description": "Monohybrid 3:1 ratio and dihybrid 9:3:3:1 ratio."},
                    {"subtopic_id": "CH08-T01-S02", "name": "Expression of Traits", "sequence_order": 2, "description": "Proteins, genes, enzymes, and DNA controlling phenotypic traits."}
                ]
            },
            {
                "topic_id": "CH08-T02",
                "chapter_id": "CH-08",
                "name": "Sex Determination in Human Beings",
                "sequence_order": 2,
                "description": "Environmental vs genetic sex determination, human sex chromosomes (XX in females, XY in males), 50% probability of male or female offspring.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit II: Heredity",
                "subtopics": [
                    {"subtopic_id": "CH08-T02-S01", "name": "XX-XY Chromosomal Mechanism", "sequence_order": 1, "description": "Equal probability determination of offspring gender by male gamete."}
                ]
            },
            {
                "topic_id": "CH08-T03",
                "chapter_id": "CH-08",
                "name": "Evolution and Speciation (Formative Learning)",
                "sequence_order": 3,
                "description": "Acquired and Inherited Traits, Speciation, Evolution and Classification, Tracing Evolutionary Relationships, Fossils, Evolution by Stages, Human Evolution. (Assessed only formatively in 2026-27).",
                "assessment_status": AssessmentClassification.FORMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 6,
                "source_section": "Unit II: Note on Formative Topics / Evolution",
                "subtopics": [
                    {"subtopic_id": "CH08-T03-S01", "name": "Acquired vs Inherited Traits", "sequence_order": 1, "description": "Somatic variations vs germ cell changes."},
                    {"subtopic_id": "CH08-T03-S02", "name": "Speciation and Evolutionary Relationships", "sequence_order": 2, "description": "Genetic drift, natural selection, homologous and analogous organs, fossil evidence."},
                    {"subtopic_id": "CH08-T03-S03", "name": "Evolution by Stages and Human Evolution", "sequence_order": 3, "description": "Eye evolution, artificial selection in wild cabbage, single human species origin in Africa."}
                ]
            },

            # ---------------- CHAPTER 9 ----------------
            {
                "topic_id": "CH09-T01",
                "chapter_id": "CH-09",
                "name": "Reflection of Light by Spherical Mirrors",
                "sequence_order": 1,
                "description": "Curved surfaces, concave and convex mirrors, terms: pole, centre of curvature, principal axis, principal focus, focal length, radius of curvature (R = 2f).",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit III: Natural Phenomena",
                "subtopics": [
                    {"subtopic_id": "CH09-T01-S01", "name": "Spherical Mirror Terminology and Sign Convention", "sequence_order": 1, "description": "New Cartesian Sign Convention."},
                    {"subtopic_id": "CH09-T01-S02", "name": "Ray Diagrams for Concave and Convex Mirrors", "sequence_order": 2, "description": "Standard rays and image formation across positions."}
                ]
            },
            {
                "topic_id": "CH09-T02",
                "chapter_id": "CH-09",
                "name": "Mirror Formula and Magnification",
                "sequence_order": 2,
                "description": "Mirror formula 1/v + 1/u = 1/f (derivation not required), linear magnification m = -v/u = h'/h, applications in headlights, shaving mirrors, rear-view mirrors.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit III: Natural Phenomena",
                "subtopics": [
                    {"subtopic_id": "CH09-T02-S01", "name": "Mirror Equation Calculations", "sequence_order": 1, "description": "Numerical problem solving using sign convention."},
                    {"subtopic_id": "CH09-T02-S02", "name": "Mirror Applications in Daily Life", "sequence_order": 2, "description": "Concave mirrors (solar furnaces, dentists) and convex mirrors (traffic surveillance, vehicles)."}
                ]
            },
            {
                "topic_id": "CH09-T03",
                "chapter_id": "CH-09",
                "name": "Refraction of Light and Refractive Index",
                "sequence_order": 3,
                "description": "Refraction at plane interface, laws of refraction, Snell’s law (sin i / sin r = constant), absolute and relative refractive index, optical density.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit III: Natural Phenomena",
                "subtopics": [
                    {"subtopic_id": "CH09-T03-S01", "name": "Snell’s Law and Glass Slab Refraction", "sequence_order": 1, "description": "Lateral displacement, speed of light in media."},
                    {"subtopic_id": "CH09-T03-S02", "name": "Refractive Index Calculations", "sequence_order": 2, "description": "Ratio of velocities and media index relations."}
                ]
            },
            {
                "topic_id": "CH09-T04",
                "chapter_id": "CH-09",
                "name": "Refraction by Spherical Lenses, Lens Formula and Power",
                "sequence_order": 4,
                "description": "Convex and concave lenses, optical centre, principal focus, focal length, ray diagrams, lens formula 1/v - 1/u = 1/f (derivation not required), magnification m = v/u, power of a lens (P = 1/f in metres, Dioptre).",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 5,
                "source_page_end": 5,
                "source_section": "Unit III: Natural Phenomena",
                "subtopics": [
                    {"subtopic_id": "CH09-T04-S01", "name": "Lens Ray Diagrams", "sequence_order": 1, "description": "Image characteristics for converging and diverging lenses."},
                    {"subtopic_id": "CH09-T04-S02", "name": "Lens Formula and Power of Lens", "sequence_order": 2, "description": "Numericals on focal length, image position, and dioptre power."}
                ]
            },

            # ---------------- CHAPTER 10 ----------------
            {
                "topic_id": "CH10-T01",
                "chapter_id": "CH-10",
                "name": "Human Eye and Defects of Vision",
                "sequence_order": 1,
                "description": "Functioning of lens in human eye, power of accommodation, near point, far point, defects of vision (myopia, hypermetropia, presbyopia) and corrective lenses, applications of spherical mirrors and lenses.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 6,
                "source_page_end": 6,
                "source_section": "Unit III: Natural Phenomena",
                "subtopics": [
                    {"subtopic_id": "CH10-T01-S01", "name": "Anatomy and Accommodation of Eye", "sequence_order": 1, "description": "Cornea, iris, pupil, ciliary muscles, crystalline lens, retina."},
                    {"subtopic_id": "CH10-T01-S02", "name": "Vision Defects and Corrections", "sequence_order": 2, "description": "Ray diagrams for myopia (concave lens), hypermetropia (convex lens), and presbyopia."}
                ]
            },
            {
                "topic_id": "CH10-T02",
                "chapter_id": "CH-10",
                "name": "Prism Refraction and Dispersion of Light",
                "sequence_order": 2,
                "description": "Refraction of light through triangular glass prism, angle of deviation, dispersion of white light into spectrum (VIBGYOR), recombination of spectrum, natural rainbow formation.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 6,
                "source_page_end": 6,
                "source_section": "Unit III: Natural Phenomena",
                "subtopics": [
                    {"subtopic_id": "CH10-T02-S01", "name": "Prism Deviation and Newton's Experiment", "sequence_order": 1, "description": "Splitting and recombination of white light."},
                    {"subtopic_id": "CH10-T02-S02", "name": "Rainbow Formation", "sequence_order": 2, "description": "Refraction, dispersion, and internal reflection in raindrops."}
                ]
            },
            {
                "topic_id": "CH10-T03",
                "chapter_id": "CH-10",
                "name": "Atmospheric Refraction and Scattering of Light",
                "sequence_order": 3,
                "description": "Atmospheric refraction phenomena (twinkling of stars, advance sunrise and delayed sunset), Tyndall effect, scattering of light, blue colour of the clear sky, reddish appearance of deep space.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 6,
                "source_page_end": 6,
                "source_section": "Unit III: Natural Phenomena",
                "subtopics": [
                    {"subtopic_id": "CH10-T03-S01", "name": "Atmospheric Refraction Phenomena", "sequence_order": 1, "description": "Apparent position of stars, 2-minute time shifts at sunrise/sunset."},
                    {"subtopic_id": "CH10-T03-S02", "name": "Tyndall Effect and Sky Colour", "sequence_order": 2, "description": "Rayleigh scattering inverse fourth power law qualitative concept."}
                ]
            },
            {
                "topic_id": "CH10-T04",
                "chapter_id": "CH-10",
                "name": "Colour of the Sun at Sunrise and Sunset (Excluded Scope)",
                "sequence_order": 4,
                "description": "Phenomenon of red colour of the sun at sunrise and sunset, explicitly excluded by CBSE 2026-27 syllabus from the examination scope.",
                "assessment_status": AssessmentClassification.NOT_IN_CURRENT_SCOPE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 6,
                "source_page_end": 6,
                "source_section": "Unit III: Natural Phenomena",
                "subtopics": [
                    {"subtopic_id": "CH10-T04-S01", "name": "Excluded Sunset/Sunrise Sun Colour", "sequence_order": 1, "description": "Explicitly excluded by CBSE syllabus parenthetical remark: '(excluding colour of the sun at sunrise and sunset)'."}
                ]
            },

            # ---------------- CHAPTER 11 ----------------
            {
                "topic_id": "CH11-T01",
                "chapter_id": "CH-11",
                "name": "Electric Current, Potential Difference and Ohm's Law",
                "sequence_order": 1,
                "description": "Electric charge, current I = Q/t, ampere, electric potential and potential difference V = W/Q, volt, circuit diagrams, Ohm’s law V = IR, V-I characteristics.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 6,
                "source_page_end": 6,
                "source_section": "Unit IV: Effects of Current",
                "subtopics": [
                    {"subtopic_id": "CH11-T01-S01", "name": "Electric Current and Potential Difference", "sequence_order": 1, "description": "Flow of electrons, ammeter and voltmeter connections."},
                    {"subtopic_id": "CH11-T01-S02", "name": "Ohm’s Law and Resistance Definition", "sequence_order": 2, "description": "Linear V-I graph, slope equals resistance."}
                ]
            },
            {
                "topic_id": "CH11-T02",
                "chapter_id": "CH-11",
                "name": "Resistance and Resistivity",
                "sequence_order": 2,
                "description": "Factors on which resistance depends (length, cross-sectional area, material nature, temperature), resistivity (rho = RA/l), ohm-meter unit, conductors, alloys, and insulators.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 6,
                "source_page_end": 6,
                "source_section": "Unit IV: Effects of Current",
                "subtopics": [
                    {"subtopic_id": "CH11-T02-S01", "name": "Factors Governing Resistance and Resistivity", "sequence_order": 1, "description": "Resistivity tables and heating element alloys (nichrome)."}
                ]
            },
            {
                "topic_id": "CH11-T03",
                "chapter_id": "CH-11",
                "name": "Series and Parallel Combinations of Resistors",
                "sequence_order": 3,
                "description": "Equivalent resistance in series (Rs = R1 + R2 + ...), equivalent resistance in parallel (1/Rp = 1/R1 + 1/R2 + ...), current and voltage distributions, advantages of parallel in domestic circuits.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 6,
                "source_page_end": 6,
                "source_section": "Unit IV: Effects of Current",
                "subtopics": [
                    {"subtopic_id": "CH11-T03-S01", "name": "Series and Parallel Derivations and Numericals", "sequence_order": 1, "description": "Complex resistor network analysis."},
                    {"subtopic_id": "CH11-T03-S02", "name": "Domestic Circuit Layout Rationale", "sequence_order": 2, "description": "Independent operation and minimal resistance advantages of parallel wiring."}
                ]
            },
            {
                "topic_id": "CH11-T04",
                "chapter_id": "CH-11",
                "name": "Heating Effect of Electric Current",
                "sequence_order": 4,
                "description": "Joule’s law of heating H = I^2 R t, applications in electric toaster, iron, kettle, heater, electric bulb (tungsten filament, inert gas), electric fuse safety mechanism.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 6,
                "source_page_end": 6,
                "source_section": "Unit IV: Effects of Current",
                "subtopics": [
                    {"subtopic_id": "CH11-T04-S01", "name": "Joule's Law and Thermal Applications", "sequence_order": 1, "description": "Calculations of heat produced."},
                    {"subtopic_id": "CH11-T04-S02", "name": "Safety Fuse Operations", "sequence_order": 2, "description": "Current ratings (1A, 2A, 5A, 15A) and low melting point alloy."}
                ]
            },
            {
                "topic_id": "CH11-T05",
                "chapter_id": "CH-11",
                "name": "Electric Power and Commercial Energy",
                "sequence_order": 5,
                "description": "Definition of power P = VI = I^2 R = V^2/R, watt and kilowatt, commercial unit kilowatt-hour (1 kWh = 3.6 x 10^6 J), calculating domestic electricity bills.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 6,
                "source_page_end": 6,
                "source_section": "Unit IV: Effects of Current",
                "subtopics": [
                    {"subtopic_id": "CH11-T05-S01", "name": "Power Formulas and Interrelations", "sequence_order": 1, "description": "Numericals on power ratings across voltage changes."},
                    {"subtopic_id": "CH11-T05-S02", "name": "Commercial Electrical Energy and Costing", "sequence_order": 2, "description": "Unit conversions and domestic tariff problem sets."}
                ]
            },

            # ---------------- CHAPTER 12 ----------------
            {
                "topic_id": "CH12-T01",
                "chapter_id": "CH-12",
                "name": "Magnetic Field and Field Lines",
                "sequence_order": 1,
                "description": "Magnetic field, compass needle, bar magnet field lines, properties of magnetic field lines (closed continuous curves, tangent gives direction, no two lines intersect).",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 6,
                "source_page_end": 6,
                "source_section": "Unit IV: Magnetic effects of current",
                "subtopics": [
                    {"subtopic_id": "CH12-T01-S01", "name": "Field Line Geometry and Properties", "sequence_order": 1, "description": "Non-intersection proof and magnetic field vector."}
                ]
            },
            {
                "topic_id": "CH12-T02",
                "chapter_id": "CH-12",
                "name": "Magnetic Field Due to Current Carrying Conductors",
                "sequence_order": 2,
                "description": "Oersted experiment, field due to straight conductor, Right-Hand Thumb Rule, circular loop field pattern, solenoid magnetic field resembling bar magnet, electromagnet.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 6,
                "source_page_end": 6,
                "source_section": "Unit IV: Magnetic effects of current",
                "subtopics": [
                    {"subtopic_id": "CH12-T02-S01", "name": "Straight Conductor and Right-Hand Thumb Rule", "sequence_order": 1, "description": "Concentric magnetic field circles."},
                    {"subtopic_id": "CH12-T02-S02", "name": "Circular Loop and Solenoid", "sequence_order": 2, "description": "Uniform core field and factors strengthening electromagnet."}
                ]
            },
            {
                "topic_id": "CH12-T03",
                "chapter_id": "CH-12",
                "name": "Force on Current-Carrying Conductor in Magnetic Field",
                "sequence_order": 3,
                "description": "Displacement of conductor in magnetic field, dependence on current, field, and length, Fleming’s Left-Hand Rule.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 6,
                "source_page_end": 6,
                "source_section": "Unit IV: Magnetic effects of current",
                "subtopics": [
                    {"subtopic_id": "CH12-T03-S01", "name": "Fleming's Left-Hand Rule", "sequence_order": 1, "description": "Thumb-force, forefinger-magnetic field, middle finger-current."}
                ]
            },
            {
                "topic_id": "CH12-T04",
                "chapter_id": "CH-12",
                "name": "Direct and Alternating Current and Domestic Electric Circuits",
                "sequence_order": 4,
                "description": "Direct current (DC), Alternating current (AC), frequency of AC in India (50 Hz), advantage of AC over DC for long-distance transmission, domestic circuits: live (red/brown), neutral (black/blue), earth wire (green), grounding safety, short circuit, overloading.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 6,
                "source_page_end": 6,
                "source_section": "Unit IV: Magnetic effects of current",
                "subtopics": [
                    {"subtopic_id": "CH12-T04-S01", "name": "AC vs DC Transmission Advantages", "sequence_order": 1, "description": "Voltage step-up/step-down and minimal energy loss."},
                    {"subtopic_id": "CH12-T04-S02", "name": "Domestic Circuit Architecture and Grounding Safety", "sequence_order": 2, "description": "220V supply, three-pin plug, earth leakage protection."}
                ]
            },
            {
                "topic_id": "CH12-T05",
                "chapter_id": "CH-12",
                "name": "Electric Motor, Electromagnetic Induction and Generator (Formative Learning)",
                "sequence_order": 5,
                "description": "Electric Motor, Electromagnetic Induction, Fleming’s Right-Hand Rule, Electric Generator. (Assessed only formatively in 2026-27 to reduce academic stress).",
                "assessment_status": AssessmentClassification.FORMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 6,
                "source_page_end": 6,
                "source_section": "Unit IV: Note on Formative Topics / Motor & Generator",
                "subtopics": [
                    {"subtopic_id": "CH12-T05-S01", "name": "DC Motor Principle and Commutator Action", "sequence_order": 1, "description": "Conversion of electrical energy into mechanical torque."},
                    {"subtopic_id": "CH12-T05-S02", "name": "Electromagnetic Induction and Generator", "sequence_order": 2, "description": "Faraday’s discovery, induced EMF, AC and DC generator working."}
                ]
            },

            # ---------------- CHAPTER 13 ----------------
            {
                "topic_id": "CH13-T01",
                "chapter_id": "CH-13",
                "name": "Ecosystem and Food Chains",
                "sequence_order": 1,
                "description": "Ecosystem structure, biotic and abiotic components, producers, consumers (herbivores, carnivores, omnivores, parasites), decomposers, food chains and food webs, 10% law of energy transfer, biological magnification of pesticides.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 6,
                "source_page_end": 6,
                "source_section": "Unit V: Natural Resources",
                "subtopics": [
                    {"subtopic_id": "CH13-T01-S01", "name": "Trophic Levels and 10 Percent Law", "sequence_order": 1, "description": "Unidirectional energy flow and biomass pyramids."},
                    {"subtopic_id": "CH13-T01-S02", "name": "Biological Magnification", "sequence_order": 2, "description": "Progressive accumulation of non-biodegradable toxins across trophic tiers."}
                ]
            },
            {
                "topic_id": "CH13-T02",
                "chapter_id": "CH-13",
                "name": "Environmental Problems and Ozone Layer Depletion",
                "sequence_order": 2,
                "description": "Atmospheric ozone (O3) formation by UV action on oxygen, protective function shielding UV radiation, causes of ozone depletion (chlorofluorocarbons - CFCs), international UNEP agreement freezing CFC production.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 6,
                "source_page_end": 6,
                "source_section": "Unit V: Natural Resources",
                "subtopics": [
                    {"subtopic_id": "CH13-T02-S01", "name": "Ozone Photochemistry and Destruction", "sequence_order": 1, "description": "O2 + UV -> O + O; O + O2 -> O3, skin cancer and cataract hazards."},
                    {"subtopic_id": "CH13-T02-S02", "name": "Montreal Protocol and Global Action", "sequence_order": 2, "description": "UNEP 1987 treaty phasing out ozone depleting substances."}
                ]
            },
            {
                "topic_id": "CH13-T03",
                "chapter_id": "CH-13",
                "name": "Waste Production and Solutions",
                "sequence_order": 3,
                "description": "Biodegradable substances (broken down by biological processes) and non-biodegradable substances (persistent polymers, plastics), solid waste generation, municipal solid waste management solutions: composting, recycling, incineration, biogas, lifestyle modifications.",
                "assessment_status": AssessmentClassification.SUMMATIVE.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page_start": 6,
                "source_page_end": 6,
                "source_section": "Unit V: Natural Resources",
                "subtopics": [
                    {"subtopic_id": "CH13-T03-S01", "name": "Biodegradable vs Non-Biodegradable Waste", "sequence_order": 1, "description": "Action of saprophytes and enzymes on organic matter versus persistent plastics."},
                    {"subtopic_id": "CH13-T03-S02", "name": "Sustainable Waste Management Systems", "sequence_order": 2, "description": "Source segregation, sanitary landfills, recycling paradigms."}
                ]
            }
        ]

        for t_spec in topics_data:
            subtopics = t_spec.pop("subtopics", [])
            self.repo.upsert_topic(t_spec)
            for st in subtopics:
                st["topic_id"] = t_spec["topic_id"]
                st["assessment_status"] = t_spec["assessment_status"]
                st["verification_status"] = t_spec["verification_status"]
                st["source_doc_id"] = t_spec["source_doc_id"]
                st["source_page_start"] = t_spec["source_page_start"]
                st["source_page_end"] = t_spec["source_page_end"]
                st["source_section"] = t_spec["source_section"]
                self.repo.upsert_subtopic(st)

    def _populate_learning_outcomes(self):
        """
        Populates official Curricular Goals (CG 1 to CG 8) and Competencies (C 1.1 to C 8.2)
        from CBSE 2026-27 Syllabus pages 2-4, mapping them to Chapters and Topics.
        """
        outcomes_data = [
            # C 1.3 -> Chapter 1 (Chemical Reactions)
            {
                "outcome_id": "LO-C1.3",
                "code": "C 1.3",
                "related_chapter_id": "CH-01",
                "related_topic_id": "CH01-T01",
                "description": "Describes and represents chemical interactions and changes using symbols and chemical equations (acid and base, metal and non-metal, reversible and irreversible).",
                "curricular_goal": "CG 1 – Explores the world of matter, its interactions, and properties at the atomic level",
                "competency": "C 1.3",
                "suggestive_verbs_json": ["describe", "represent", "balance", "classify"],
                "provenance_type": ProvenanceType.OFFICIAL.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page": 2,
                "source_section": "Curricular Goals and Competencies"
            },
            # C 1.1 -> Chapter 1 / Unit I Formative (Periodic Classification)
            {
                "outcome_id": "LO-C1.1",
                "code": "C 1.1",
                "related_chapter_id": "CH-01",
                "related_topic_id": "CH01-T04",
                "description": "Describes classification of elements in the Periodic Table, and explains how compounds (including carbon compounds) are formed based on the atomic structure (Bohr’s model) and properties (valency).",
                "curricular_goal": "CG 1 – Explores the world of matter, its interactions, and properties at the atomic level",
                "competency": "C 1.1",
                "suggestive_verbs_json": ["describe", "classify", "explain"],
                "provenance_type": ProvenanceType.OFFICIAL.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page": 2,
                "source_section": "Curricular Goals and Competencies"
            },
            # C 1.2 -> Chapter 2 & 3 (Acids, Bases, Metals)
            {
                "outcome_id": "LO-C1.2",
                "code": "C 1.2",
                "related_chapter_id": "CH-02",
                "related_topic_id": "CH02-T01",
                "description": "Investigates the nature and properties of chemical substances (distillation, crystallisation, chromatography, centrifugation, types and properties of mixtures, solutions, colloids, and suspensions).",
                "curricular_goal": "CG 1 – Explores the world of matter, its interactions, and properties at the atomic level",
                "competency": "C 1.2",
                "suggestive_verbs_json": ["investigate", "distinguish", "analyze"],
                "provenance_type": ProvenanceType.OFFICIAL.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page": 2,
                "source_section": "Curricular Goals and Competencies"
            },
            # C 1.1 (part 2) -> Chapter 4 (Carbon and its Compounds)
            {
                "outcome_id": "LO-CH04-C1.1",
                "code": "C 1.1 (Carbon)",
                "related_chapter_id": "CH-04",
                "related_topic_id": "CH04-T01",
                "description": "Explains covalent bond formation, tetravalency, and catenation properties that allow carbon to form versatile saturated and unsaturated compounds and functional groups.",
                "curricular_goal": "CG 1 – Explores the world of matter, its interactions, and properties at the atomic level",
                "competency": "C 1.1",
                "suggestive_verbs_json": ["explain", "illustrate", "name"],
                "provenance_type": ProvenanceType.OFFICIAL.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page": 2,
                "source_section": "Curricular Goals and Competencies"
            },
            # C 3.2 -> Chapter 5 (Life Processes)
            {
                "outcome_id": "LO-C3.2",
                "code": "C 3.2",
                "related_chapter_id": "CH-05",
                "related_topic_id": "CH05-T02",
                "description": "Analyses similarities and differences in the life processes involved in nutrition (photosynthesis in plants; digestion in animals), transport (transport of water in plants; circulation in animals), exchange of materials (respiration and excretion), and reproduction.",
                "curricular_goal": "CG 3 – Explores the structure and function of the living world at the cellular level",
                "competency": "C 3.2",
                "suggestive_verbs_json": ["analyze", "compare", "differentiate", "diagram"],
                "provenance_type": ProvenanceType.OFFICIAL.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page": 3,
                "source_section": "Curricular Goals and Competencies"
            },
            # C 3.1 -> Chapter 6 (Control and Coordination)
            {
                "outcome_id": "LO-C3.1",
                "code": "C 3.1",
                "related_chapter_id": "CH-06",
                "related_topic_id": "CH06-T02",
                "description": "Explains cellular and tissue mechanisms in maintaining coordination, transmission of electrical and chemical impulses across neurons, and hormone-mediated physiological responses.",
                "curricular_goal": "CG 3 – Explores the structure and function of the living world at the cellular level",
                "competency": "C 3.1",
                "suggestive_verbs_json": ["explain", "trace", "identify"],
                "provenance_type": ProvenanceType.INFERRED.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page": 2,
                "source_section": "Curricular Goals and Competencies"
            },
            # C 3.2 (Reproduction) -> Chapter 7 (How Do Organisms Reproduce?)
            {
                "outcome_id": "LO-CH07-C3.2",
                "code": "C 3.2 (Reproduction)",
                "related_chapter_id": "CH-07",
                "related_topic_id": "CH07-T01",
                "description": "Compares asexual and sexual reproduction strategies in plants and animals and evaluates human reproductive health requirements.",
                "curricular_goal": "CG 3 – Explores the structure and function of the living world at the cellular level",
                "competency": "C 3.2",
                "suggestive_verbs_json": ["compare", "evaluate", "illustrate"],
                "provenance_type": ProvenanceType.OFFICIAL.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page": 3,
                "source_section": "Curricular Goals and Competencies"
            },
            # C 3.3 -> Chapter 8 (Heredity)
            {
                "outcome_id": "LO-C3.3",
                "code": "C 3.3",
                "related_chapter_id": "CH-08",
                "related_topic_id": "CH08-T01",
                "description": "Describes the mechanisms of heredity (in terms of DNA, genes, chromosomes) and variation (as changes in the sequence of DNA).",
                "curricular_goal": "CG 3 – Explores the structure and function of the living world at the cellular level",
                "competency": "C 3.3",
                "suggestive_verbs_json": ["describe", "predict", "calculate"],
                "provenance_type": ProvenanceType.OFFICIAL.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page": 3,
                "source_section": "Curricular Goals and Competencies"
            },
            # C 4.4 -> Chapter 8 (Heredity Mendel Laws)
            {
                "outcome_id": "LO-C4.4",
                "code": "C 4.4",
                "related_chapter_id": "CH-08",
                "related_topic_id": "CH08-T01",
                "description": "Analyses patterns of inheritance of traits in terms of Mendel’s laws and its consequences at a population level (using models and/or simulations).",
                "curricular_goal": "CG 4 – Explores interconnectedness between organisms and their environment",
                "competency": "C 4.4",
                "suggestive_verbs_json": ["analyze", "derive", "model"],
                "provenance_type": ProvenanceType.OFFICIAL.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page": 3,
                "source_section": "Curricular Goals and Competencies"
            },
            # C 4.5 -> Chapter 8 (Formative Evolution)
            {
                "outcome_id": "LO-C4.5",
                "code": "C 4.5",
                "related_chapter_id": "CH-08",
                "related_topic_id": "CH08-T03",
                "description": "Analyses evidences of biological evolution demonstrating the consequences of the process of natural selection in terms of changes in allele frequency in population, structure, and function of organisms.",
                "curricular_goal": "CG 4 – Explores interconnectedness between organisms and their environment",
                "competency": "C 4.5",
                "suggestive_verbs_json": ["analyze", "trace", "synthesize"],
                "provenance_type": ProvenanceType.OFFICIAL.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page": 3,
                "source_section": "Curricular Goals and Competencies"
            },
            # C 2.3 -> Chapter 9 (Light Reflection and Refraction)
            {
                "outcome_id": "LO-C2.3",
                "code": "C 2.3",
                "related_chapter_id": "CH-09",
                "related_topic_id": "CH09-T01",
                "description": "Manipulates the position of object and properties of lenses (focus, centre of curvature) to observe image characteristics and correspondence with a ray diagram, and extends this understanding to a combination of lenses (telescope, microscope).",
                "curricular_goal": "CG 2 – Explores the physical world around them, and understands scientific principles and laws based on observations and analysis",
                "competency": "C 2.3",
                "suggestive_verbs_json": ["manipulate", "construct", "calculate", "predict"],
                "provenance_type": ProvenanceType.OFFICIAL.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page": 2,
                "source_section": "Curricular Goals and Competencies"
            },
            # C 2.3 (Eye) -> Chapter 10 (The Human Eye)
            {
                "outcome_id": "LO-CH10-C2.3",
                "code": "C 2.3 (Vision)",
                "related_chapter_id": "CH-10",
                "related_topic_id": "CH10-T01",
                "description": "Applies lens principles to describe the functioning of the human crystalline lens, identifies visual defects, and calculates corrective lens powers.",
                "curricular_goal": "CG 2 – Explores the physical world around them, and understands scientific principles and laws based on observations and analysis",
                "competency": "C 2.3",
                "suggestive_verbs_json": ["apply", "diagnose", "calculate"],
                "provenance_type": ProvenanceType.INFERRED.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page": 2,
                "source_section": "Curricular Goals and Competencies"
            },
            # C 2.4 -> Chapter 11 (Electricity)
            {
                "outcome_id": "LO-C2.4",
                "code": "C 2.4",
                "related_chapter_id": "CH-11",
                "related_topic_id": "CH11-T01",
                "description": "Manipulates and analyses different characteristics of the circuit (current, voltage, resistance) and mathematises their relationship (Ohm’s law), and applies it to everyday usage (electricity bill, short circuit, safety measures).",
                "curricular_goal": "CG 2 – Explores the physical world around them, and understands scientific principles and laws based on observations and analysis",
                "competency": "C 2.4",
                "suggestive_verbs_json": ["manipulate", "analyze", "mathematise", "apply"],
                "provenance_type": ProvenanceType.OFFICIAL.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page": 2,
                "source_section": "Curricular Goals and Competencies"
            },
            # C 8.1 -> Chapter 12 (Magnetic Effects of Current)
            {
                "outcome_id": "LO-CH12-C8.1",
                "code": "C 8.1 (Electromagnetism)",
                "related_chapter_id": "CH-12",
                "related_topic_id": "CH12-T01",
                "description": "Develops accurate physical and directional vector models (Right-Hand Thumb Rule, Fleming’s Left-Hand Rule) to predict magnetic field lines and electromagnetic force directions.",
                "curricular_goal": "CG 8 – Explores the nature of Science by doing Science",
                "competency": "C 8.1",
                "suggestive_verbs_json": ["model", "predict", "demonstrate"],
                "provenance_type": ProvenanceType.OFFICIAL.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page": 3,
                "source_section": "Curricular Goals and Competencies"
            },
            # C 4.3 -> Chapter 13 (Our Environment)
            {
                "outcome_id": "LO-C4.3",
                "code": "C 4.3",
                "related_chapter_id": "CH-13",
                "related_topic_id": "CH13-T01",
                "description": "Analyses different levels of biological organisation from organisms to ecosystems and biomes along with interactions that take place at each level.",
                "curricular_goal": "CG 4 – Explores interconnectedness between organisms and their environment",
                "competency": "C 4.3",
                "suggestive_verbs_json": ["analyze", "trace", "evaluate"],
                "provenance_type": ProvenanceType.OFFICIAL.value,
                "verification_status": VerificationStatus.VERIFIED.value,
                "source_doc_id": "CBSE_SCI_10_2026_27",
                "source_page": 3,
                "source_section": "Curricular Goals and Competencies"
            }
        ]

        for lo in outcomes_data:
            self.repo.upsert_learning_outcome(lo)

    def _populate_curriculum_mappings(self):
        """Populates relational mapping bindings for hierarchy traceability."""
        mappings = [
            # Curriculum to Units
            {"mapping_id": "MAP-CURR-U01", "parent_type": "CURRICULUM", "parent_id": "CBSE-SCI-10-2026-27", "child_type": "UNIT", "child_id": "UNIT-01", "sequence_order": 1, "verification_status": "VERIFIED", "notes": "CBSE Unit I: Chemical Substances"},
            {"mapping_id": "MAP-CURR-U02", "parent_type": "CURRICULUM", "parent_id": "CBSE-SCI-10-2026-27", "child_type": "UNIT", "child_id": "UNIT-02", "sequence_order": 2, "verification_status": "VERIFIED", "notes": "CBSE Unit II: World of Living"},
            {"mapping_id": "MAP-CURR-U03", "parent_type": "CURRICULUM", "parent_id": "CBSE-SCI-10-2026-27", "child_type": "UNIT", "child_id": "UNIT-03", "sequence_order": 3, "verification_status": "VERIFIED", "notes": "CBSE Unit III: Natural Phenomena"},
            {"mapping_id": "MAP-CURR-U04", "parent_type": "CURRICULUM", "parent_id": "CBSE-SCI-10-2026-27", "child_type": "UNIT", "child_id": "UNIT-04", "sequence_order": 4, "verification_status": "VERIFIED", "notes": "CBSE Unit IV: Effects of Current"},
            {"mapping_id": "MAP-CURR-U05", "parent_type": "CURRICULUM", "parent_id": "CBSE-SCI-10-2026-27", "child_type": "UNIT", "child_id": "UNIT-05", "sequence_order": 5, "verification_status": "VERIFIED", "notes": "CBSE Unit V: Natural Resources"},

            # Units to Chapters
            {"mapping_id": "MAP-U01-CH01", "parent_type": "UNIT", "parent_id": "UNIT-01", "child_type": "CHAPTER", "child_id": "CH-01", "sequence_order": 1, "verification_status": "VERIFIED", "notes": "Chapter 1 in Unit I"},
            {"mapping_id": "MAP-U01-CH02", "parent_type": "UNIT", "parent_id": "UNIT-01", "child_type": "CHAPTER", "child_id": "CH-02", "sequence_order": 2, "verification_status": "VERIFIED", "notes": "Chapter 2 in Unit I"},
            {"mapping_id": "MAP-U01-CH03", "parent_type": "UNIT", "parent_id": "UNIT-01", "child_type": "CHAPTER", "child_id": "CH-03", "sequence_order": 3, "verification_status": "VERIFIED", "notes": "Chapter 3 in Unit I"},
            {"mapping_id": "MAP-U01-CH04", "parent_type": "UNIT", "parent_id": "UNIT-01", "child_type": "CHAPTER", "child_id": "CH-04", "sequence_order": 4, "verification_status": "VERIFIED", "notes": "Chapter 4 in Unit I"},

            {"mapping_id": "MAP-U02-CH05", "parent_type": "UNIT", "parent_id": "UNIT-02", "child_type": "CHAPTER", "child_id": "CH-05", "sequence_order": 1, "verification_status": "VERIFIED", "notes": "Chapter 5 in Unit II"},
            {"mapping_id": "MAP-U02-CH06", "parent_type": "UNIT", "parent_id": "UNIT-02", "child_type": "CHAPTER", "child_id": "CH-06", "sequence_order": 2, "verification_status": "VERIFIED", "notes": "Chapter 6 in Unit II"},
            {"mapping_id": "MAP-U02-CH07", "parent_type": "UNIT", "parent_id": "UNIT-02", "child_type": "CHAPTER", "child_id": "CH-07", "sequence_order": 3, "verification_status": "VERIFIED", "notes": "Chapter 7 in Unit II"},
            {"mapping_id": "MAP-U02-CH08", "parent_type": "UNIT", "parent_id": "UNIT-02", "child_type": "CHAPTER", "child_id": "CH-08", "sequence_order": 4, "verification_status": "VERIFIED", "notes": "Chapter 8 in Unit II"},

            {"mapping_id": "MAP-U03-CH09", "parent_type": "UNIT", "parent_id": "UNIT-03", "child_type": "CHAPTER", "child_id": "CH-09", "sequence_order": 1, "verification_status": "VERIFIED", "notes": "Chapter 9 in Unit III"},
            {"mapping_id": "MAP-U03-CH10", "parent_type": "UNIT", "parent_id": "UNIT-03", "child_type": "CHAPTER", "child_id": "CH-10", "sequence_order": 2, "verification_status": "VERIFIED", "notes": "Chapter 10 in Unit III"},

            {"mapping_id": "MAP-U04-CH11", "parent_type": "UNIT", "parent_id": "UNIT-04", "child_type": "CHAPTER", "child_id": "CH-11", "sequence_order": 1, "verification_status": "VERIFIED", "notes": "Chapter 11 in Unit IV"},
            {"mapping_id": "MAP-U04-CH12", "parent_type": "UNIT", "parent_id": "UNIT-04", "child_type": "CHAPTER", "child_id": "CH-12", "sequence_order": 2, "verification_status": "VERIFIED", "notes": "Chapter 12 in Unit IV"},

            {"mapping_id": "MAP-U05-CH13", "parent_type": "UNIT", "parent_id": "UNIT-05", "child_type": "CHAPTER", "child_id": "CH-13", "sequence_order": 1, "verification_status": "VERIFIED", "notes": "Chapter 13 in Unit V"}
        ]
        for m in mappings:
            self.repo.upsert_curriculum_mapping(m)
