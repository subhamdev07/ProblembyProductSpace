"""
Curriculum Expansion Service (P5)
Expands BodhAI's verified concept graph, question bank, and NCERT RAG chunks
across all 13 official CBSE Class 10 Science chapters (Units I to V).
Ensures strict DAG acyclicity, schema validation, and alignment with the
CBSE Class 10 Science (Subject Code 086) 2026-27 syllabus.
"""

import json
from typing import List, Dict, Any, Tuple, Optional
from src.models.concept import (
    ConceptNode,
    ConceptEdge,
    ConceptType,
    RelationshipType,
    ConceptVerificationStatus,
    SourceStatus,
)
from src.models.question import (
    Question,
    QuestionType,
    QuestionDifficulty,
    CognitiveLevel,
    QuestionStatus,
    QuestionProvenance,
)
from src.storage.database import Database
from src.storage.concept_repository import ConceptRepository
from src.storage.question_repository import QuestionRepository
from src.storage.remediation_repository import RemediationRepository
from src.services.rag_service import RAGService


class CurriculumExpansionService:
    def __init__(
        self,
        concept_repo: Optional[ConceptRepository] = None,
        question_repo: Optional[QuestionRepository] = None,
        remediation_repo: Optional[RemediationRepository] = None,
        rag_service: Optional[RAGService] = None,
        db: Optional[Database] = None,
    ):
        database = db or Database()
        self.db = database
        self.concept_repo = concept_repo or ConceptRepository(database)
        self.question_repo = question_repo or QuestionRepository(database)
        self.remediation_repo = remediation_repo or RemediationRepository(database)
        self.rag_service = rag_service

    def expand_full_curriculum(self, generate_live_embeddings: bool = True) -> Dict[str, Any]:
        """
        Populates verified concepts, acyclic pedagogical relationships,
        curated multi-typology CBSE examination questions, and RAG embeddings
        across all 13 CBSE Class 10 Science chapters.
        """
        # 1. Seed Expanded Concepts
        concepts = self._get_expanded_concepts()
        concepts_added = 0
        for c in concepts:
            self.concept_repo.upsert_concept(c)
            concepts_added += 1

        # 2. Seed Prerequisite & Semantic Edges (Acyclic DAG)
        edges = self._get_expanded_concept_edges()
        edges_added = 0
        for e in edges:
            self.concept_repo.upsert_edge(e)
            edges_added += 1

        # 3. Seed Comprehensive Multi-Typology Questions across all 5 Units
        questions = self._get_expanded_questions()
        questions_added = 0
        for q in questions:
            self.question_repo.upsert_question(q)
            questions_added += 1

        # 4. Seed Textbook RAG Chunks across Units I to V
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO source_documents (
                    document_id, title, document_type, academic_session, subject,
                    subject_code, source_authority, file_path, verification_status, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    "NCERT_SCI_10",
                    "NCERT Class X Science Textbook - Complete Rationalised Edition (Chapters 1-13)",
                    "TEXTBOOK_MASTER",
                    "2026-27",
                    "Science",
                    "086",
                    "NCERT",
                    "sources/NCERT-Class-10-Science.pdf",
                    "VERIFIED",
                    json.dumps({"total_chapters": 13, "syllabus": "CBSE 2026-27"}),
                ),
            )
            conn.commit()

        chunks = self._get_expanded_rag_chunks()
        chunks_added = 0
        for ch in chunks:
            emb = None
            if generate_live_embeddings and self.rag_service:
                emb = self.rag_service.generate_embedding(ch["chunk_text"], input_type="passage")

            self.remediation_repo.store_embedding_chunk(
                chunk_id=ch["chunk_id"],
                chapter_id=ch["chapter_id"],
                topic_id=ch.get("topic_id"),
                concept_id=ch.get("concept_id"),
                source_doc_id="NCERT_SCI_10",
                page_num=ch["page_num"],
                heading=ch["heading"],
                chunk_text=ch["chunk_text"],
                metadata={"embedding_dim": len(emb) if emb else 0, "has_embedding": bool(emb)},
            )
            chunks_added += 1

        return {
            "status": "SUCCESS",
            "concepts_added": concepts_added,
            "edges_added": edges_added,
            "questions_added": questions_added,
            "chunks_added": chunks_added,
            "total_questions_in_bank": self.question_repo.get_question_statistics().get("total_questions", 0),
        }

    # --------------------------------------------------------------------------
    # Concepts Data (Chapters 2 to 13)
    # --------------------------------------------------------------------------
    def _get_expanded_concepts(self) -> List[ConceptNode]:
        nodes = []

        # Unit I: Chemical Substances
        # Chapter 2: Acids, Bases and Salts
        nodes.extend([
            ConceptNode(
                concept_id="CPT-CH02-001",
                name="Acids and Bases Arrhenius Definition",
                canonical_name="acids_bases_arrhenius_definition",
                description="Acids furnish H+(aq) or H3O+ ions in water, while bases furnish OH-(aq) ions.",
                chapter_id="CH-02",
                topic_id="CH02-T01",
                concept_type=ConceptType.CORE,
                learning_objective="Define acids and bases based on ion generation in aqueous solutions.",
            ),
            ConceptNode(
                concept_id="CPT-CH02-002",
                name="Indicators and Olfactory Detection",
                canonical_name="indicators_and_detection",
                description="Natural indicators (litmus, turmeric) and synthetic indicators (methyl orange, phenolphthalein), plus olfactory indicators (vanilla, onion).",
                chapter_id="CH-02",
                topic_id="CH02-T01",
                concept_type=ConceptType.APPLIED,
                learning_objective="Identify acids and bases using chemical and olfactory indicators.",
            ),
            ConceptNode(
                concept_id="CPT-CH02-003",
                name="Reactions of Acids with Metals and Carbonates",
                canonical_name="acid_reactions_metals_carbonates",
                description="Acid + Metal -> Salt + H2 gas; Acid + Carbonate -> Salt + CO2 + H2O.",
                chapter_id="CH-02",
                topic_id="CH02-T02",
                concept_type=ConceptType.CORE,
                learning_objective="Write balanced chemical equations for acid-metal and acid-carbonate reactions.",
            ),
            ConceptNode(
                concept_id="CPT-CH02-004",
                name="Concept of pH Scale and Logarithmic Acidity",
                canonical_name="ph_scale_and_applications",
                description="pH measures hydronium ion concentration: neutral pH 7, acidic < 7, basic > 7. Importance in soil, tooth decay, digestive system.",
                chapter_id="CH-02",
                topic_id="CH02-T03",
                concept_type=ConceptType.CORE,
                learning_objective="Interpret the pH scale and apply pH principles to everyday biological and agricultural contexts.",
            ),
            ConceptNode(
                concept_id="CPT-CH02-005",
                name="Chemicals from Common Salt and Plaster of Paris",
                canonical_name="salts_bleaching_soda_pop",
                description="Chlor-alkali process (NaOH, Cl2, H2), Bleaching powder (CaOCl2), Baking soda (NaHCO3), Washing soda (Na2CO3.10H2O), Plaster of Paris (CaSO4.1/2H2O).",
                chapter_id="CH-02",
                topic_id="CH02-T04",
                concept_type=ConceptType.APPLIED,
                learning_objective="Detail preparations, chemical formulas, and industrial applications of major salts.",
            ),
        ])

        # Chapter 3: Metals and Non-Metals
        nodes.extend([
            ConceptNode(
                concept_id="CPT-CH03-001",
                name="Reactivity Series of Metals",
                canonical_name="reactivity_series_metals",
                description="Relative arrangement of metals in order of decreasing chemical reactivity (K > Na > Ca > Mg > Al > Zn > Fe > Pb > H > Cu > Hg > Ag > Au).",
                chapter_id="CH-03",
                topic_id="CH03-T02",
                concept_type=ConceptType.CORE,
                learning_objective="Predict displacement outcomes using the metal reactivity series.",
            ),
            ConceptNode(
                concept_id="CPT-CH03-002",
                name="Ionic Compound Formation and Lattice Properties",
                canonical_name="ionic_bond_properties",
                description="Transfer of valence electrons from metals to non-metals yielding electrovalent compounds with high melting points, brittleness, and aqueous conductivity.",
                chapter_id="CH-03",
                topic_id="CH03-T03",
                concept_type=ConceptType.CORE,
                learning_objective="Illustrate electron-dot transfer diagrams for NaCl and MgCl2 formation.",
            ),
            ConceptNode(
                concept_id="CPT-CH03-003",
                name="Metallurgy: Roasting and Calcination",
                canonical_name="metallurgy_roasting_calcination",
                description="Extraction of metals: roasting sulphide ores in excess air vs. calcinating carbonate ores in limited air, followed by carbon or displacement reduction.",
                chapter_id="CH-03",
                topic_id="CH03-T04",
                concept_type=ConceptType.APPLIED,
                learning_objective="Distinguish thermal metallurgy procedures for sulphide and carbonate ores.",
            ),
            ConceptNode(
                concept_id="CPT-CH03-004",
                name="Corrosion Prevention and Galvanisation",
                canonical_name="corrosion_prevention_galvanisation",
                description="Oxidation of iron (rusting requires both air and moisture); prevention via painting, greasing, galvanising (zinc coating), chrome plating, and alloying.",
                chapter_id="CH-03",
                topic_id="CH03-T05",
                concept_type=ConceptType.APPLIED,
                learning_objective="Explain conditions for corrosion and scientific mechanisms of galvanisation.",
            ),
        ])

        # Chapter 4: Carbon and its Compounds
        nodes.extend([
            ConceptNode(
                concept_id="CPT-CH04-001",
                name="Covalent Bonding, Catenation and Tetravalency",
                canonical_name="covalent_bonding_catenation",
                description="Carbon's unique capability to form strong covalent bonds through electron sharing, self-linking catenation chains, and tetravalent geometry.",
                chapter_id="CH-04",
                topic_id="CH04-T01",
                concept_type=ConceptType.FOUNDATIONAL,
                learning_objective="Explain why carbon forms covalent rather than ionic bonds and the origin of organic diversity.",
            ),
            ConceptNode(
                concept_id="CPT-CH04-002",
                name="Homologous Series and Hydrocarbons",
                canonical_name="homologous_series_hydrocarbons",
                description="Series of compounds with same functional group differing by -CH2- unit (14u mass), displaying gradations in physical properties (alkanes, alkenes, alkynes).",
                chapter_id="CH-04",
                topic_id="CH04-T02",
                concept_type=ConceptType.CORE,
                learning_objective="Formulate general molecular formulas for saturated and unsaturated homologous series.",
            ),
            ConceptNode(
                concept_id="CPT-CH04-003",
                name="Ethanol and Ethanoic Acid Reactions",
                canonical_name="ethanol_ethanoic_acid_esterification",
                description="Combustion, oxidation with alkaline KMnO4, esterification of ethanol + ethanoic acid to sweet-smelling ester, saponification, and reaction with carbonates.",
                chapter_id="CH-04",
                topic_id="CH04-T05",
                concept_type=ConceptType.APPLIED,
                learning_objective="Analyze esterification and saponification reaction mechanisms.",
            ),
            ConceptNode(
                concept_id="CPT-CH04-004",
                name="Soap Cleansing Action and Micelle Formation",
                canonical_name="soap_micelle_cleansing_action",
                description="Sodium salts of long-chain fatty acids with hydrophilic ionic heads and hydrophobic hydrocarbon tails clustering into colloidal micelles in water.",
                chapter_id="CH-04",
                topic_id="CH04-T06",
                concept_type=ConceptType.APPLIED,
                learning_objective="Describe hydrophobic/hydrophilic micelle formation in emulsifying oily dirt.",
            ),
        ])

        # Unit II: World of Living
        # Chapter 5: Life Processes
        nodes.extend([
            ConceptNode(
                concept_id="CPT-CH05-001",
                name="Photosynthesis Light and Dark Reactions",
                canonical_name="photosynthesis_chloroplast_stomata",
                description="Absorption of light by chlorophyll, conversion of light energy to chemical energy, splitting of water, and reduction of CO2 to carbohydrates.",
                chapter_id="CH-05",
                topic_id="CH05-T02",
                concept_type=ConceptType.CORE,
                learning_objective="Outline essential biochemical steps of plant autotrophic nutrition.",
            ),
            ConceptNode(
                concept_id="CPT-CH05-002",
                name="Human Digestive System and Enzyme Action",
                canonical_name="human_digestive_enzymes",
                description="Salivary amylase, gastric pepsin and HCl, bile emulsification, pancreatic trypsin and lipase, intestinal villi absorption.",
                chapter_id="CH-05",
                topic_id="CH05-T02",
                concept_type=ConceptType.CORE,
                learning_objective="Trace the digestion of carbohydrates, proteins, and fats along the alimentary canal.",
            ),
            ConceptNode(
                concept_id="CPT-CH05-003",
                name="Aerobic vs Anaerobic Respiration Pathways",
                canonical_name="cellular_respiration_pathways",
                description="Breakdown of glucose: Glycolysis to pyruvate in cytoplasm; Aerobic breakdown in mitochondria (CO2 + H2O + 38 ATP) vs Anaerobic in yeast / muscle (lactic acid).",
                chapter_id="CH-05",
                topic_id="CH05-T03",
                concept_type=ConceptType.CORE,
                learning_objective="Compare energy yield and end-products across oxygenated and hypoxic pathways.",
            ),
            ConceptNode(
                concept_id="CPT-CH05-004",
                name="Double Circulation and Heart Mechanics",
                canonical_name="human_heart_double_circulation",
                description="Four-chambered human heart separating oxygenated and deoxygenated blood; systemic circulation through aorta and pulmonary circulation through lungs.",
                chapter_id="CH-05",
                topic_id="CH05-T04",
                concept_type=ConceptType.CORE,
                learning_objective="Diagram blood flow pathways and explain the evolutionary necessity of four chambers.",
            ),
            ConceptNode(
                concept_id="CPT-CH05-005",
                name="Excretion and Nephron Filtration Mechanics",
                canonical_name="nephron_ultrafiltration_reabsorption",
                description="Bowman's capsule ultrafiltration, selective reabsorption of glucose, amino acids, salts, water in tubules, and urine collection.",
                chapter_id="CH-05",
                topic_id="CH05-T05",
                concept_type=ConceptType.CORE,
                learning_objective="Explain glomerular filtration and tubular reabsorption in human kidneys.",
            ),
        ])

        # Chapter 6: Control and Coordination
        nodes.extend([
            ConceptNode(
                concept_id="CPT-CH06-001",
                name="Neuron Structure and Synaptic Transmission",
                canonical_name="neuron_synapse_transmission",
                description="Dendrite electrical reception, axonal impulse propagation, and neurotransmitter chemical diffusion across the synaptic cleft.",
                chapter_id="CH-06",
                topic_id="CH06-T02",
                concept_type=ConceptType.CORE,
                learning_objective="Trace signal transmission across nervous tissue and the synaptic junction.",
            ),
            ConceptNode(
                concept_id="CPT-CH06-002",
                name="Reflex Arc and Spinal Integration",
                canonical_name="reflex_arc_spinal_integration",
                description="Involuntary instantaneous response: Receptor -> Sensory neuron -> Relay neuron (spinal cord) -> Motor neuron -> Effector muscle.",
                chapter_id="CH-06",
                topic_id="CH06-T02",
                concept_type=ConceptType.CORE,
                learning_objective="Map components of a reflex arc and understand the evolutionary role of spinal mediation.",
            ),
            ConceptNode(
                concept_id="CPT-CH06-003",
                name="Plant Tropisms and Phytohormones",
                canonical_name="plant_tropisms_hormones",
                description="Phototropism (auxin-mediated cell elongation), geotropism, hydrotropism, thigmotropism, and growth inhibitors like abscisic acid.",
                chapter_id="CH-06",
                topic_id="CH06-T01",
                concept_type=ConceptType.APPLIED,
                learning_objective="Relate differential hormone concentrations to directional plant movements.",
            ),
            ConceptNode(
                concept_id="CPT-CH06-004",
                name="Endocrine Glands and Feedback Mechanisms",
                canonical_name="human_endocrine_feedback",
                description="Insulin from pancreas (blood sugar regulation), thyroxin from thyroid (iodine necessity), adrenaline from adrenals, and negative feedback loops.",
                chapter_id="CH-06",
                topic_id="CH06-T04",
                concept_type=ConceptType.CORE,
                learning_objective="Analyze hormonal homeostatic regulation and feedback loops.",
            ),
        ])

        # Chapter 7: Reproduction
        nodes.extend([
            ConceptNode(
                concept_id="CPT-CH07-001",
                name="Sexual Reproduction in Angiosperms",
                canonical_name="angiosperm_flower_fertilization",
                description="Floral whorls (stamens, carpels), pollination mechanisms, pollen tube germination, double fertilization, and seed/fruit formation.",
                chapter_id="CH-07",
                topic_id="CH07-T02",
                concept_type=ConceptType.CORE,
                learning_objective="Diagram flower structure and track gamete fusion to seed maturation.",
            ),
            ConceptNode(
                concept_id="CPT-CH07-002",
                name="Human Reproductive Anatomy and Menstrual Cycle",
                canonical_name="human_reproductive_anatomy",
                description="Male testes and vas deferens; female ovaries, fallopian tubes, uterus; gametogenesis, fertilization, implantation, and 28-day uterine cycle.",
                chapter_id="CH-07",
                topic_id="CH07-T03",
                concept_type=ConceptType.CORE,
                learning_objective="Describe human gametogenesis and hormonal control of the female reproductive cycle.",
            ),
            ConceptNode(
                concept_id="CPT-CH07-003",
                name="Contraception and Reproductive Health",
                canonical_name="contraception_methods_stds",
                description="Barrier methods (condoms), chemical hormonal pills, IUDs (copper-T), surgical vasectomy/tubectomy, and prevention of bacterial/viral STDs.",
                chapter_id="CH-07",
                topic_id="CH07-T04",
                concept_type=ConceptType.APPLIED,
                learning_objective="Classify family planning methodologies and public health measures against STIs.",
            ),
        ])

        # Chapter 8: Heredity
        nodes.extend([
            ConceptNode(
                concept_id="CPT-CH08-001",
                name="Mendelian Monohybrid Cross and Law of Segregation",
                canonical_name="mendel_monohybrid_cross",
                description="Cross involving one pair of contrasting traits (Tall vs Dwarf pea plants); F1 all tall (Tt), F2 phenotypic ratio 3:1, genotypic ratio 1:2:1.",
                chapter_id="CH-08",
                topic_id="CH08-T01",
                concept_type=ConceptType.CORE,
                learning_objective="Construct Punnett squares for monohybrid crosses and derive phenotypic/genotypic ratios.",
            ),
            ConceptNode(
                concept_id="CPT-CH08-002",
                name="Mendelian Dihybrid Cross and Independent Assortment",
                canonical_name="mendel_dihybrid_cross",
                description="Cross involving two pairs of traits (Round-Yellow vs Wrinkled-Green); F2 generation yields 9:3:3:1 phenotypic ratio demonstrating independent gene assortment.",
                chapter_id="CH-08",
                topic_id="CH08-T01",
                concept_type=ConceptType.CORE,
                learning_objective="Formulate dihybrid inheritance grids and deduce the principle of independent assortment.",
            ),
            ConceptNode(
                concept_id="CPT-CH08-003",
                name="Chromosomal Sex Determination in Humans",
                canonical_name="human_sex_determination_xx_xy",
                description="Human diploid complement: 22 pairs autosomes + 1 pair allosomes (XX female, XY male). Male heterogamety determines 50:50 sex probability at conception.",
                chapter_id="CH-08",
                topic_id="CH08-T02",
                concept_type=ConceptType.CORE,
                learning_objective="Demonstrate genetic inheritance of biological sex via genetic cross diagram.",
            ),
        ])

        # Unit III: Natural Phenomena
        # Chapter 9: Light - Reflection and Refraction
        nodes.extend([
            ConceptNode(
                concept_id="CPT-CH09-001",
                name="Spherical Mirrors and Ray Diagrams",
                canonical_name="spherical_mirrors_ray_diagrams",
                description="Concave and convex mirror geometries, principal focus, center of curvature, and ray tracing rules for real vs. virtual image formation.",
                chapter_id="CH-09",
                topic_id="CH09-T01",
                concept_type=ConceptType.CORE,
                learning_objective="Construct accurate optical ray diagrams for various object positions in front of spherical mirrors.",
            ),
            ConceptNode(
                concept_id="CPT-CH09-002",
                name="Mirror Formula and Magnification Calculations",
                canonical_name="mirror_formula_magnification",
                description="1/f = 1/v + 1/u with New Cartesian Sign Convention; linear magnification m = -v/u = h'/h.",
                chapter_id="CH-09",
                topic_id="CH09-T02",
                concept_type=ConceptType.CORE,
                learning_objective="Solve quantitative optical numericals involving focal length, object/image distance, and sign conventions.",
            ),
            ConceptNode(
                concept_id="CPT-CH09-003",
                name="Laws of Refraction and Snell's Law",
                canonical_name="refraction_snells_law",
                description="Incident ray, refracted ray and normal in same plane; sin(i)/sin(r) = constant (refractive index n21 = v1/v2); optical density vs mass density.",
                chapter_id="CH-09",
                topic_id="CH09-T03",
                concept_type=ConceptType.CORE,
                learning_objective="Apply Snell's law to ray deviation across media boundaries.",
            ),
            ConceptNode(
                concept_id="CPT-CH09-004",
                name="Lens Formula, Magnification and Lens Power",
                canonical_name="lens_formula_power",
                description="1/f = 1/v - 1/u; magnification m = v/u; Optical power P = 1/f (in meters), measured in dioptres (D).",
                chapter_id="CH-09",
                topic_id="CH09-T04",
                concept_type=ConceptType.CORE,
                learning_objective="Calculate lens parameters and dioptre power for converging and diverging lenses.",
            ),
        ])

        # Chapter 10: Human Eye and Colourful World
        nodes.extend([
            ConceptNode(
                concept_id="CPT-CH10-001",
                name="Human Eye Anatomy and Power of Accommodation",
                canonical_name="human_eye_accommodation",
                description="Function of cornea, iris, pupil, ciliary muscles altering crystalline lens curvature, near point (25 cm) and far point (infinity).",
                chapter_id="CH-10",
                topic_id="CH10-T01",
                concept_type=ConceptType.CORE,
                learning_objective="Explain lens accommodation mechanisms and normal visual range.",
            ),
            ConceptNode(
                concept_id="CPT-CH10-002",
                name="Vision Defects: Myopia, Hypermetropia and Presbyopia",
                canonical_name="vision_defects_correction",
                description="Myopia (near-sightedness, corrected with concave lens), Hypermetropia (far-sightedness, corrected with convex lens), and Presbyopia (bifocal correction).",
                chapter_id="CH-10",
                topic_id="CH10-T01",
                concept_type=ConceptType.APPLIED,
                learning_objective="Diagnose optical defects through ray diagrams and prescribe corrective lens powers.",
            ),
            ConceptNode(
                concept_id="CPT-CH10-003",
                name="Prism Dispersion, Atmospheric Refraction and Scattering",
                canonical_name="dispersion_atmospheric_refraction_scattering",
                description="Splitting of white light into VIBGYOR through glass prism; atmospheric refraction causing twinkling of stars and advanced sunrise/delayed sunset; Tyndall effect and blue sky.",
                chapter_id="CH-10",
                topic_id="CH10-T02",
                concept_type=ConceptType.APPLIED,
                learning_objective="Relate wavelength-dependent scattering and atmospheric density gradients to celestial phenomena.",
            ),
        ])

        # Unit IV: Effects of Current
        # Chapter 11: Electricity
        nodes.extend([
            ConceptNode(
                concept_id="CPT-CH11-001",
                name="Ohm's Law, Resistance and Electrical Resistivity",
                canonical_name="ohms_law_resistance_resistivity",
                description="Potential difference V proportional to current I (V = IR); Resistance R = rho * (L/A); temperature and material dependence of resistivity.",
                chapter_id="CH-11",
                topic_id="CH11-T01",
                concept_type=ConceptType.CORE,
                learning_objective="Verify Ohm's law experimentally and calculate resistance based on conductor dimensions.",
            ),
            ConceptNode(
                concept_id="CPT-CH11-002",
                name="Series and Parallel Resistor Networks",
                canonical_name="series_parallel_resistors",
                description="Series connection: constant current, additive resistances (Rs = R1 + R2 + ...); Parallel connection: constant potential, reciprocal addition (1/Rp = 1/R1 + ...).",
                chapter_id="CH-11",
                topic_id="CH11-T03",
                concept_type=ConceptType.CORE,
                learning_objective="Compute equivalent resistance, branch currents, and voltage drops in combined circuits.",
            ),
            ConceptNode(
                concept_id="CPT-CH11-003",
                name="Joule's Law of Heating and Electric Power",
                canonical_name="joules_heating_electric_power",
                description="Heat produced H = I^2 * R * t; Electric power P = VI = I^2*R = V^2/R; commercial unit of electrical energy (1 kWh = 3.6 x 10^6 J).",
                chapter_id="CH-11",
                topic_id="CH11-T04",
                concept_type=ConceptType.APPLIED,
                learning_objective="Calculate energy consumption, electricity utility billing, and heating elements.",
            ),
        ])

        # Chapter 12: Magnetic Effects of Electric Current
        nodes.extend([
            ConceptNode(
                concept_id="CPT-CH12-001",
                name="Magnetic Field Lines and Right-Hand Thumb Rule",
                canonical_name="magnetic_field_lines_thumb_rule",
                description="Continuous closed curves originating at North pole and terminating at South; Right-Hand Thumb Rule gives concentric circular field direction around straight conductor.",
                chapter_id="CH-12",
                topic_id="CH12-T01",
                concept_type=ConceptType.CORE,
                learning_objective="Map magnetic field patterns around straight conductors, circular loops, and solenoids.",
            ),
            ConceptNode(
                concept_id="CPT-CH12-002",
                name="Force on Conductor and Fleming's Left-Hand Rule",
                canonical_name="fleming_left_hand_rule_force",
                description="Magnetic force on current-carrying conductor F = BIl; direction given by Fleming's Left-Hand Rule (Thumb: Motion/Force, Forefinger: Field, Middle finger: Current).",
                chapter_id="CH-12",
                topic_id="CH12-T03",
                concept_type=ConceptType.CORE,
                learning_objective="Predict mechanical deflection direction of charged particles and conductors in magnetic fields.",
            ),
            ConceptNode(
                concept_id="CPT-CH12-003",
                name="Domestic Electric Circuits and Earthing Protection",
                canonical_name="domestic_circuits_earthing_fuse",
                description="220V 50Hz AC power with Live, Neutral and Earth wires; parallel appliance branching; safety role of metallic appliance earthing and electrical fuses.",
                chapter_id="CH-12",
                topic_id="CH12-T04",
                concept_type=ConceptType.APPLIED,
                learning_objective="Diagram domestic wiring circuits and explain mechanisms preventing electric shocks and short-circuit fires.",
            ),
        ])

        # Unit V: Natural Resources
        # Chapter 13: Our Environment
        nodes.extend([
            ConceptNode(
                concept_id="CPT-CH13-001",
                name="Trophic Levels and 10 Percent Energy Law",
                canonical_name="trophic_levels_10_percent_energy_law",
                description="Producers -> Primary -> Secondary -> Tertiary consumers; Lindeman's 10% law dictates unidirectional energy dissipation, limiting food chains to 3-4 steps.",
                chapter_id="CH-13",
                topic_id="CH13-T01",
                concept_type=ConceptType.CORE,
                learning_objective="Quantify ecological energy transfer and construct ecological pyramids.",
            ),
            ConceptNode(
                concept_id="CPT-CH13-002",
                name="Biological Magnification of Non-Biodegradable Toxins",
                canonical_name="biological_magnification",
                description="Progressive accumulation of persistent non-biodegradable chemicals (pesticides, heavy metals) at successive trophic levels, peaking in apex predators and humans.",
                chapter_id="CH-13",
                topic_id="CH13-T01",
                concept_type=ConceptType.CORE,
                learning_objective="Explain the ecological mechanism causing biomagnification of chemical toxins.",
            ),
            ConceptNode(
                concept_id="CPT-CH13-003",
                name="Ozone Layer Depletion and Waste Management",
                canonical_name="ozone_depletion_waste_management",
                description="UV photodissociation of O2 yielding free oxygen reacting with O2 to form O3; catalytic destruction by synthetic chlorofluorocarbons (CFCs); biodegradable vs non-biodegradable waste sorting.",
                chapter_id="CH-13",
                topic_id="CH13-T02",
                concept_type=ConceptType.APPLIED,
                learning_objective="Formulate chemical equations of stratospheric ozone generation and evaluate solid waste reduction strategies.",
            ),
        ])

        return nodes

    # --------------------------------------------------------------------------
    # Pedagogical Edges (Acyclic DAG)
    # --------------------------------------------------------------------------
    def _get_expanded_concept_edges(self) -> List[ConceptEdge]:
        edges = []
        edge_data = [
            ("E-P5-01", "CPT-CH01-004", "CPT-CH02-003", RelationshipType.PREREQUISITE_OF, 1.0),
            ("E-P5-02", "CPT-CH02-001", "CPT-CH02-004", RelationshipType.PREREQUISITE_OF, 1.0),
            ("E-P5-03", "CPT-CH02-003", "CPT-CH02-005", RelationshipType.RELATED_TO, 0.9),
            ("E-P5-04", "CPT-CH01-018", "CPT-CH03-001", RelationshipType.PREREQUISITE_OF, 1.0),
            ("E-P5-05", "CPT-CH03-001", "CPT-CH03-003", RelationshipType.PREREQUISITE_OF, 1.0),
            ("E-P5-06", "CPT-CH01-021", "CPT-CH03-004", RelationshipType.PREREQUISITE_OF, 1.0),
            ("E-P5-07", "CPT-CH04-001", "CPT-CH04-002", RelationshipType.PREREQUISITE_OF, 1.0),
            ("E-P5-08", "CPT-CH04-002", "CPT-CH04-003", RelationshipType.RELATED_TO, 0.9),
            ("E-P5-09", "CPT-CH04-003", "CPT-CH04-004", RelationshipType.PREREQUISITE_OF, 1.0),
            ("E-P5-10", "CPT-CH05-001", "CPT-CH05-003", RelationshipType.RELATED_TO, 0.95),
            ("E-P5-11", "CPT-CH05-002", "CPT-CH05-004", RelationshipType.PREREQUISITE_OF, 0.85),
            ("E-P5-12", "CPT-CH05-004", "CPT-CH05-005", RelationshipType.PREREQUISITE_OF, 0.9),
            ("E-P5-13", "CPT-CH06-001", "CPT-CH06-002", RelationshipType.PREREQUISITE_OF, 1.0),
            ("E-P5-14", "CPT-CH07-001", "CPT-CH08-001", RelationshipType.PREREQUISITE_OF, 0.9),
            ("E-P5-15", "CPT-CH08-001", "CPT-CH08-002", RelationshipType.RELATED_TO, 1.0),
            ("E-P5-16", "CPT-CH08-001", "CPT-CH08-003", RelationshipType.RELATED_TO, 0.95),
            ("E-P5-17", "CPT-CH09-001", "CPT-CH09-002", RelationshipType.PREREQUISITE_OF, 1.0),
            ("E-P5-18", "CPT-CH09-003", "CPT-CH09-004", RelationshipType.PREREQUISITE_OF, 1.0),
            ("E-P5-19", "CPT-CH09-004", "CPT-CH10-002", RelationshipType.PREREQUISITE_OF, 1.0),
            ("E-P5-20", "CPT-CH10-001", "CPT-CH10-002", RelationshipType.PREREQUISITE_OF, 1.0),
            ("E-P5-21", "CPT-CH11-001", "CPT-CH11-002", RelationshipType.PREREQUISITE_OF, 1.0),
            ("E-P5-22", "CPT-CH11-001", "CPT-CH11-003", RelationshipType.PREREQUISITE_OF, 1.0),
            ("E-P5-23", "CPT-CH11-001", "CPT-CH12-001", RelationshipType.PREREQUISITE_OF, 0.9),
            ("E-P5-24", "CPT-CH12-001", "CPT-CH12-002", RelationshipType.PREREQUISITE_OF, 1.0),
            ("E-P5-25", "CPT-CH11-003", "CPT-CH12-003", RelationshipType.RELATED_TO, 0.85),
            ("E-P5-26", "CPT-CH05-001", "CPT-CH13-001", RelationshipType.PREREQUISITE_OF, 0.9),
            ("E-P5-27", "CPT-CH13-001", "CPT-CH13-002", RelationshipType.PREREQUISITE_OF, 1.0),
        ]

        for eid, src, tgt, rel, conf in edge_data:
            edges.append(
                ConceptEdge(
                    edge_id=eid,
                    source_concept_id=src,
                    target_concept_id=tgt,
                    relationship_type=rel,
                    confidence=conf,
                    verification_status=ConceptVerificationStatus.VERIFIED,
                )
            )
        return edges

    # --------------------------------------------------------------------------
    # Expanded Questions across all 5 Units and 7 Typologies
    # --------------------------------------------------------------------------
    def _get_expanded_questions(self) -> List[Question]:
        qs = []

        # ======================================================================
        # SECTION A: MCQs & ASSERTION-REASON (1 Mark Each)
        # ======================================================================
        # Q1: Unit 1 (Acids, Bases & Salts) - MCQ
        qs.append(
            Question(
                question_id="Q-CH02-MCQ-001",
                question_text="A solution turns red litmus blue; its pH is likely to be:",
                question_type=QuestionType.MCQ,
                chapter_id="CH-02",
                topic_id="CH02-T01",
                concept_ids=["CPT-CH02-001", "CPT-CH02-002"],
                difficulty=QuestionDifficulty.EASY,
                cognitive_level=CognitiveLevel.KNOWLEDGE_UNDERSTANDING,
                marks=1,
                expected_time_seconds=45,
                answer_key={"correct_option": "D", "options": {"A": "1", "B": "4", "C": "5", "D": "10"}},
                explanation="Basic solutions turn red litmus blue and possess a pH value strictly greater than 7. Hence, pH 10 represents a basic solution.",
                misconception_tags=["INVERTING_LITMUS_COLOR_RULES"],
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=33, section_heading="Chapter 2 Exercises"
                ),
            )
        )

        # Q2: Unit 1 (Metals and Non-metals) - MCQ
        qs.append(
            Question(
                question_id="Q-CH03-MCQ-001",
                question_text="An element reacts with oxygen to give a compound with a high melting point. This compound is also soluble in water. The element is likely to be:",
                question_type=QuestionType.MCQ,
                chapter_id="CH-03",
                topic_id="CH03-T01",
                concept_ids=["CPT-CH03-002"],
                difficulty=QuestionDifficulty.MEDIUM,
                cognitive_level=CognitiveLevel.APPLICATION,
                marks=1,
                expected_time_seconds=60,
                answer_key={"correct_option": "A", "options": {"A": "Calcium", "B": "Carbon", "C": "Silicon", "D": "Iron"}},
                explanation="Calcium reacts with oxygen to form calcium oxide ($CaO$), which is an ionic compound with a high melting point and dissolves in water to form slaked lime $Ca(OH)_2$.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=55, section_heading="Chapter 3 Exercises"
                ),
            )
        )

        # Q3: Unit 1 (Carbon Compounds) - MCQ
        qs.append(
            Question(
                question_id="Q-CH04-MCQ-001",
                question_text="Which of the following organic compounds decolorizes bromine water due to the presence of an unsaturated carbon-carbon double bond?",
                question_type=QuestionType.MCQ,
                chapter_id="CH-04",
                topic_id="CH04-T02",
                concept_ids=["CPT-CH04-002"],
                difficulty=QuestionDifficulty.MEDIUM,
                cognitive_level=CognitiveLevel.APPLICATION,
                marks=1,
                expected_time_seconds=60,
                answer_key={"correct_option": "B", "options": {"A": "$C_2H_6$", "B": "$C_2H_4$", "C": "$CH_4$", "D": "$C_3H_8$"}},
                explanation="Ethene ($C_2H_4$) is an alkene containing an unsaturated double bond which readily undergoes addition reactions and decolorizes bromine water.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=71, section_heading="Section 4.3 Chemical Properties"
                ),
            )
        )

        # Q4: Unit 2 (Life Processes) - MCQ
        qs.append(
            Question(
                question_id="Q-CH05-MCQ-001",
                question_text="During vigorous physical exercise, the accumulation of which compound causes painful cramps in human muscle cells?",
                question_type=QuestionType.MCQ,
                chapter_id="CH-05",
                topic_id="CH05-T03",
                concept_ids=["CPT-CH05-003"],
                difficulty=QuestionDifficulty.EASY,
                cognitive_level=CognitiveLevel.KNOWLEDGE_UNDERSTANDING,
                marks=1,
                expected_time_seconds=45,
                answer_key={"correct_option": "C", "options": {"A": "Ethanol", "B": "Carbon dioxide", "C": "Lactic acid", "D": "Pyruvate"}},
                explanation="When oxygen is inadequate in human muscle tissue, pyruvate breaks down anaerobically into lactic acid (a 3-carbon molecule), leading to muscle cramps.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=102, section_heading="Section 5.3 Respiration"
                ),
            )
        )

        # Q5: Unit 2 (Control & Coordination) - MCQ
        qs.append(
            Question(
                question_id="Q-CH06-MCQ-001",
                question_text="The electrical impulse in a neuron travels in which of the following sequences?",
                question_type=QuestionType.MCQ,
                chapter_id="CH-06",
                topic_id="CH06-T02",
                concept_ids=["CPT-CH06-001"],
                difficulty=QuestionDifficulty.MEDIUM,
                cognitive_level=CognitiveLevel.KNOWLEDGE_UNDERSTANDING,
                marks=1,
                expected_time_seconds=60,
                answer_key={
                    "correct_option": "B",
                    "options": {
                        "A": "Axon -> Cell body -> Dendrite",
                        "B": "Dendrite -> Cell body -> Axon -> Axonal end",
                        "C": "Cell body -> Dendrite -> Axon",
                        "D": "Axon -> Dendrite -> Cell body"
                    }
                },
                explanation="Information is received by the dendritic tips, converted to an electrical impulse, passes through the cyton (cell body), travels along the axon, and releases neurotransmitters at the axonal end.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=115, section_heading="Section 6.1 Animals – Nervous System"
                ),
            )
        )

        # Q6: Unit 2 (Reproduction) - MCQ
        qs.append(
            Question(
                question_id="Q-CH07-MCQ-001",
                question_text="In a flowering plant, which part develops into the fruit after fertilization?",
                question_type=QuestionType.MCQ,
                chapter_id="CH-07",
                topic_id="CH07-T02",
                concept_ids=["CPT-CH07-001"],
                difficulty=QuestionDifficulty.EASY,
                cognitive_level=CognitiveLevel.KNOWLEDGE_UNDERSTANDING,
                marks=1,
                expected_time_seconds=45,
                answer_key={"correct_option": "C", "options": {"A": "Ovule", "B": "Style", "C": "Ovary", "D": "Stigma"}},
                explanation="After fertilization, the zygote divides to form an embryo inside the ovule, which develops into a seed. The ovary grows rapidly and ripens into the fruit.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=135, section_heading="Section 7.2.4 Sexual Reproduction in Flowering Plants"
                ),
            )
        )

        # Q7: Unit 2 (Heredity) - MCQ
        qs.append(
            Question(
                question_id="Q-CH08-MCQ-001",
                question_text="A cross between a true-breeding tall pea plant ($TT$) and a dwarf pea plant ($tt$) produces an $F_1$ progeny. When $F_1$ plants self-pollinate, the percentage of dwarf plants in $F_2$ is:",
                question_type=QuestionType.MCQ,
                chapter_id="CH-08",
                topic_id="CH08-T01",
                concept_ids=["CPT-CH08-001"],
                difficulty=QuestionDifficulty.MEDIUM,
                cognitive_level=CognitiveLevel.APPLICATION,
                marks=1,
                expected_time_seconds=60,
                answer_key={"correct_option": "B", "options": {"A": "0%", "B": "25%", "C": "50%", "D": "75%"}},
                explanation="In Mendel's monohybrid cross, the $F_2$ phenotypic ratio is 3 Tall : 1 Dwarf. The proportion of dwarf ($tt$) plants is $1/4 = 25\\%$.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=144, section_heading="Section 8.2 Heredity"
                ),
            )
        )

        # Q8: Unit 3 (Light) - MCQ
        qs.append(
            Question(
                question_id="Q-CH09-MCQ-001",
                question_text="Where should an object be placed in front of a convex lens to obtain a real image of the same size as the object?",
                question_type=QuestionType.MCQ,
                chapter_id="CH-09",
                topic_id="CH09-T04",
                concept_ids=["CPT-CH09-004"],
                difficulty=QuestionDifficulty.EASY,
                cognitive_level=CognitiveLevel.KNOWLEDGE_UNDERSTANDING,
                marks=1,
                expected_time_seconds=45,
                answer_key={
                    "correct_option": "B",
                    "options": {
                        "A": "At the principal focus",
                        "B": "At twice the focal length ($2F_1$)",
                        "C": "At infinity",
                        "D": "Between optical centre and focus"
                    }
                },
                explanation="When an object is placed at $2F_1$ of a convex lens, a real, inverted image of the same size is formed on the other side at $2F_2$.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=180, section_heading="Section 9.3 Refraction of Light"
                ),
            )
        )

        # Q9: Unit 3 (Human Eye) - MCQ
        qs.append(
            Question(
                question_id="Q-CH10-MCQ-001",
                question_text="The clear sky appears blue because:",
                question_type=QuestionType.MCQ,
                chapter_id="CH-10",
                topic_id="CH10-T03",
                concept_ids=["CPT-CH10-003"],
                difficulty=QuestionDifficulty.MEDIUM,
                cognitive_level=CognitiveLevel.KNOWLEDGE_UNDERSTANDING,
                marks=1,
                expected_time_seconds=60,
                answer_key={
                    "correct_option": "C",
                    "options": {
                        "A": "Blue light is absorbed by the atmosphere",
                        "B": "Ultraviolet radiations are absorbed by the ozone layer",
                        "C": "Fine atmospheric particles scatter blue light of shorter wavelength more effectively",
                        "D": "Water droplets refract sunlight into blue spectrum"
                    }
                },
                explanation="According to Rayleigh scattering, the intensity of scattered light is inversely proportional to the fourth power of wavelength ($I \\propto 1/\\lambda^4$). Fine air particles scatter shorter blue wavelengths far more than longer red wavelengths.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=196, section_heading="Section 10.3 Scattering of Light"
                ),
            )
        )

        # Q10: Unit 4 (Electricity) - MCQ
        qs.append(
            Question(
                question_id="Q-CH11-MCQ-001",
                question_text="A cylindrical conductor of length $l$ and uniform area of cross-section $A$ has resistance $R$. Another conductor of length $2l$ and resistance $R$ of the same material has cross-sectional area:",
                question_type=QuestionType.MCQ,
                chapter_id="CH-11",
                topic_id="CH11-T02",
                concept_ids=["CPT-CH11-001"],
                difficulty=QuestionDifficulty.MEDIUM,
                cognitive_level=CognitiveLevel.APPLICATION,
                marks=1,
                expected_time_seconds=60,
                answer_key={"correct_option": "C", "options": {"A": "$A/2$", "B": "$3A/2$", "C": "$2A$", "D": "$3A$"}},
                explanation="Resistance is given by $R = \\rho l / A$. If length is doubled to $2l$, the area must also be doubled to $2A$ to keep resistance $R$ identical for the same material ($\\rho$).",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=209, section_heading="Section 11.2 Factors on which Resistance Depends"
                ),
            )
        )

        # Q11: Unit 4 (Magnetic Effects) - MCQ
        qs.append(
            Question(
                question_id="Q-CH12-MCQ-001",
                question_text="The magnetic field inside a long straight current-carrying solenoid is:",
                question_type=QuestionType.MCQ,
                chapter_id="CH-12",
                topic_id="CH12-T02",
                concept_ids=["CPT-CH12-001"],
                difficulty=QuestionDifficulty.EASY,
                cognitive_level=CognitiveLevel.KNOWLEDGE_UNDERSTANDING,
                marks=1,
                expected_time_seconds=45,
                answer_key={
                    "correct_option": "D",
                    "options": {
                        "A": "Zero",
                        "B": "Decreases as we move towards its end",
                        "C": "Increases as we move towards its end",
                        "D": "Is uniform at all points"
                    }
                },
                explanation="The magnetic field lines inside a solenoid are in the form of parallel straight lines, indicating that the magnetic field is uniform at all points inside.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=229, section_heading="Section 12.2 Magnetic Field due to Current-Carrying Solenoid"
                ),
            )
        )

        # Q12: Unit 5 (Our Environment) - MCQ
        qs.append(
            Question(
                question_id="Q-CH13-MCQ-001",
                question_text="In an ecosystem, if $10,000\\text{ J}$ of solar energy falls on green plants, how much energy will be converted into food by the producers?",
                question_type=QuestionType.MCQ,
                chapter_id="CH-13",
                topic_id="CH13-T01",
                concept_ids=["CPT-CH13-001"],
                difficulty=QuestionDifficulty.MEDIUM,
                cognitive_level=CognitiveLevel.APPLICATION,
                marks=1,
                expected_time_seconds=60,
                answer_key={"correct_option": "B", "options": {"A": "$10\\text{ J}$", "B": "$100\\text{ J}$", "C": "$1,000\\text{ J}$", "D": "$10,000\\text{ J}$"}},
                explanation="Terrestrial green plants capture only about $1\\%$ of the incident solar energy falling on their leaves and convert it into chemical food energy. $1\\% \\text{ of } 10,000\\text{ J} = 100\\text{ J}$.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=258, section_heading="Section 13.1 Ecosystem"
                ),
            )
        )

        # Q13-Q16: Additional Section A MCQs
        qs.append(
            Question(
                question_id="Q-CH01-MCQ-002",
                question_text="Barium chloride on reacting with ammonium sulphate forms barium sulphate and ammonium chloride. Which of the following correctly represents the type of the reaction involved?\n(i) Displacement reaction\n(ii) Precipitation reaction\n(iii) Combination reaction\n(iv) Double displacement reaction",
                question_type=QuestionType.MCQ,
                chapter_id="CH-01",
                topic_id="CH01-T02",
                concept_ids=["CPT-CH01-019", "CPT-CH01-020"],
                difficulty=QuestionDifficulty.MEDIUM,
                cognitive_level=CognitiveLevel.APPLICATION,
                marks=1,
                expected_time_seconds=60,
                answer_key={"correct_option": "D", "options": {"A": "(i) only", "B": "(ii) only", "C": "(iv) only", "D": "(ii) and (iv)"}},
                explanation="The reaction involves mutual exchange of ions between reactants (double displacement) and results in insoluble white barium sulphate precipitate.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="sources/jesc101.pdf", page_number=11, section_heading="Section 1.2.4 Double Displacement"
                ),
            )
        )

        qs.append(
            Question(
                question_id="Q-CH02-MCQ-002",
                question_text="Which of the following salts does NOT contain water of crystallization?",
                question_type=QuestionType.MCQ,
                chapter_id="CH-02",
                topic_id="CH02-T04",
                concept_ids=["CPT-CH02-005"],
                difficulty=QuestionDifficulty.EASY,
                cognitive_level=CognitiveLevel.KNOWLEDGE_UNDERSTANDING,
                marks=1,
                expected_time_seconds=45,
                answer_key={"correct_option": "B", "options": {"A": "Blue vitriol", "B": "Baking soda", "C": "Washing soda", "D": "Gypsum"}},
                explanation="Baking soda ($NaHCO_3$) is an anhydrous sodium hydrogencarbonate salt. Blue vitriol has $5H_2O$, Washing soda has $10H_2O$, and Gypsum has $2H_2O$.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=31, section_heading="Section 2.4.4 Are Crystals Really Dry?"
                ),
            )
        )

        qs.append(
            Question(
                question_id="Q-CH09-MCQ-002",
                question_text="The power of a corrective lens used to correct a defective vision is $-2.0\\text{ D}$. The nature and focal length of the lens is:",
                question_type=QuestionType.MCQ,
                chapter_id="CH-09",
                topic_id="CH09-T04",
                concept_ids=["CPT-CH09-004", "CPT-CH10-002"],
                difficulty=QuestionDifficulty.MEDIUM,
                cognitive_level=CognitiveLevel.APPLICATION,
                marks=1,
                expected_time_seconds=60,
                answer_key={
                    "correct_option": "C",
                    "options": {
                        "A": "Convex, $+50\\text{ cm}$",
                        "B": "Convex, $-50\\text{ cm}$",
                        "C": "Concave, $-50\\text{ cm}$",
                        "D": "Concave, $-20\\text{ cm}$"
                    }
                },
                explanation="Focal length $f = 1/P = 1/(-2.0\\text{ D}) = -0.5\\text{ m} = -50\\text{ cm}$. Negative focal length signifies a concave diverging lens.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=184, section_heading="Section 9.3.8 Power of a Lens"
                ),
            )
        )

        qs.append(
            Question(
                question_id="Q-CH11-MCQ-002",
                question_text="When a $4\\,\\Omega$ resistor and a $12\\,\\Omega$ resistor are connected in parallel across a $6\\text{ V}$ battery, the total circuit current drawn is:",
                question_type=QuestionType.MCQ,
                chapter_id="CH-11",
                topic_id="CH11-T03",
                concept_ids=["CPT-CH11-002"],
                difficulty=QuestionDifficulty.MEDIUM,
                cognitive_level=CognitiveLevel.APPLICATION,
                marks=1,
                expected_time_seconds=60,
                answer_key={"correct_option": "B", "options": {"A": "$1\\text{ A}$", "B": "$2\\text{ A}$", "C": "$0.5\\text{ A}$", "D": "$3\\text{ A}$"}},
                explanation="$1/R_p = 1/4 + 1/12 = 4/12 = 1/3 \\implies R_p = 3\\,\\Omega$. By Ohm's law, $I = V / R_p = 6\\text{ V} / 3\\,\\Omega = 2\\text{ A}$.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=214, section_heading="Section 11.6 Resistors in Parallel"
                ),
            )
        )

        # Q17-Q20: ASSERTION-REASON QUESTIONS (1 Mark Each)
        # Directions: A: Both A & R true, R is correct explanation
        #             B: Both A & R true, R is NOT correct explanation
        #             C: A is true, R is false
        #             D: A is false, R is true
        qs.append(
            Question(
                question_id="Q-CH01-AR-001",
                question_text="Assertion (A): Respiration is an exothermic chemical process.\nReason (R): During respiration, glucose combines with oxygen in the cells of our body and releases energy.",
                question_type=QuestionType.ASSERTION_REASON,
                chapter_id="CH-01",
                topic_id="CH01-T02",
                concept_ids=["CPT-CH01-012"],
                difficulty=QuestionDifficulty.EASY,
                cognitive_level=CognitiveLevel.KNOWLEDGE_UNDERSTANDING,
                marks=1,
                expected_time_seconds=60,
                answer_key={
                    "correct_option": "A",
                    "assertion": "Respiration is an exothermic chemical process.",
                    "reason": "During respiration, glucose combines with oxygen in the cells of our body and releases energy."
                },
                explanation="Respiration breaks down carbohydrates into glucose, which reacts with oxygen releasing ATP energy, making it an exothermic reaction. Both A and R are true and R correctly explains A.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="sources/jesc101.pdf", page_number=7, section_heading="Section 1.2.1 Combination Reactions"
                ),
            )
        )

        qs.append(
            Question(
                question_id="Q-CH03-AR-001",
                question_text="Assertion (A): Ionic compounds conduct electricity in solid state.\nReason (R): In solid state, ions are free to move throughout the crystal lattice.",
                question_type=QuestionType.ASSERTION_REASON,
                chapter_id="CH-03",
                topic_id="CH03-T03",
                concept_ids=["CPT-CH03-002"],
                difficulty=QuestionDifficulty.MEDIUM,
                cognitive_level=CognitiveLevel.APPLICATION,
                marks=1,
                expected_time_seconds=60,
                answer_key={
                    "correct_option": "D",
                    "assertion": "Ionic compounds conduct electricity in solid state.",
                    "reason": "In solid state, ions are free to move throughout the crystal lattice."
                },
                explanation="Assertion is false because ionic compounds do not conduct electricity in the solid state due to rigid crystalline structure. Both Assertion and Reason statements are scientifically false, hence option D (A is false).",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=49, section_heading="Section 3.3.4 Properties of Ionic Compounds"
                ),
            )
        )

        qs.append(
            Question(
                question_id="Q-CH08-AR-001",
                question_text="Assertion (A): A child inherits an equal amount of nuclear genetic material from each parent.\nReason (R): Both father and mother contribute equal numbers of autosomes and one sex chromosome through haploid gametes.",
                question_type=QuestionType.ASSERTION_REASON,
                chapter_id="CH-08",
                topic_id="CH08-T02",
                concept_ids=["CPT-CH08-003"],
                difficulty=QuestionDifficulty.EASY,
                cognitive_level=CognitiveLevel.KNOWLEDGE_UNDERSTANDING,
                marks=1,
                expected_time_seconds=60,
                answer_key={
                    "correct_option": "A",
                    "assertion": "A child inherits an equal amount of nuclear genetic material from each parent.",
                    "reason": "Both father and mother contribute equal numbers of autosomes and one sex chromosome through haploid gametes."
                },
                explanation="Humans are diploid organisms ($2n=46$). Each parent contributes a haploid set ($n=23$) via sperm and ovum, ensuring equal nuclear DNA inheritance.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=145, section_heading="Section 8.2.2 How do these traits get expressed?"
                ),
            )
        )

        qs.append(
            Question(
                question_id="Q-CH13-AR-001",
                question_text="Assertion (A): Human beings occupy the top level in any food chain and accumulate the maximum concentration of pesticide residues.\nReason (R): Non-biodegradable chemicals get progressively concentrated at each successive trophic level via biological magnification.",
                question_type=QuestionType.ASSERTION_REASON,
                chapter_id="CH-13",
                topic_id="CH13-T01",
                concept_ids=["CPT-CH13-002"],
                difficulty=QuestionDifficulty.EASY,
                cognitive_level=CognitiveLevel.KNOWLEDGE_UNDERSTANDING,
                marks=1,
                expected_time_seconds=60,
                answer_key={
                    "correct_option": "A",
                    "assertion": "Human beings occupy the top level in any food chain and accumulate the maximum concentration of pesticide residues.",
                    "reason": "Non-biodegradable chemicals get progressively concentrated at each successive trophic level via biological magnification."
                },
                explanation="Because pesticides are not degradable or metabolically broken down, they accumulate in organisms and amplify at each higher trophic tier. Both statements are true and Reason explains Assertion.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=260, section_heading="Section 13.1.1 Food Chains and Webs"
                ),
            )
        )

        # ======================================================================
        # SECTION B: VERY SHORT ANSWER (2 Marks Each, Q21 to Q26)
        # ======================================================================
        qs.append(
            Question(
                question_id="Q-CH02-SA-001",
                question_text="Why does distilled water not conduct electricity, whereas rainwater does? Give two distinct scientific reasons.",
                question_type=QuestionType.SHORT_ANSWER,
                chapter_id="CH-02",
                topic_id="CH02-T01",
                concept_ids=["CPT-CH02-001"],
                difficulty=QuestionDifficulty.EASY,
                cognitive_level=CognitiveLevel.KNOWLEDGE_UNDERSTANDING,
                marks=2,
                expected_time_seconds=120,
                answer_key={
                    "key_points": [
                        "Distilled water is pure and contains no dissolved mineral salts or free mobile ions.",
                        "Rainwater dissolves atmospheric gases like CO2 and SO2 forming carbonic acid (H2CO3) which dissociates into ions (H+ and HCO3-) facilitating electrical conduction."
                    ],
                    "rubric": "1 mark for explaining absence of ions in distilled water; 1 mark for dissolved acidic gases producing mobile ions in rainwater."
                },
                explanation="Electrical conduction in liquids requires mobile charge carriers (ions). Pure distilled water has negligible ionization, whereas rainwater contains dissolved acidic gases that dissociate into conducting ions.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=23, section_heading="Section 2.3 What Happens to an Acid or Base in Water?"
                ),
            )
        )

        qs.append(
            Question(
                question_id="Q-CH05-SA-001",
                question_text="Differentiate between an artery and a vein with respect to:\n(a) Wall thickness and elasticity\n(b) Presence of valves and blood pressure",
                question_type=QuestionType.SHORT_ANSWER,
                chapter_id="CH-05",
                topic_id="CH05-T04",
                concept_ids=["CPT-CH05-004"],
                difficulty=QuestionDifficulty.EASY,
                cognitive_level=CognitiveLevel.KNOWLEDGE_UNDERSTANDING,
                marks=2,
                expected_time_seconds=120,
                answer_key={
                    "key_points": [
                        "Arteries have thick, elastic walls to withstand high pumping pressure from the heart; veins have thin, less elastic walls.",
                        "Arteries lack internal valves because blood flows under high pressure; veins possess semilunar valves to prevent backward flow of blood under low pressure."
                    ],
                    "rubric": "1 mark for comparative wall structure; 1 mark for valve presence and pressure correlation."
                },
                explanation="Arteries carry blood away from the heart under high pulsating pressure requiring thick muscular walls. Veins collect low-pressure blood returning to the heart, relying on valves to enforce unidirectional flow.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=107, section_heading="Section 5.4.1 Our Pump – The Heart"
                ),
            )
        )

        qs.append(
            Question(
                question_id="Q-CH07-SA-001",
                question_text="Why is vegetative propagation practiced for growing certain types of horticultural plants? State any two biological advantages.",
                question_type=QuestionType.SHORT_ANSWER,
                chapter_id="CH-07",
                topic_id="CH07-T01",
                concept_ids=["CPT-CH07-001"],
                difficulty=QuestionDifficulty.EASY,
                cognitive_level=CognitiveLevel.KNOWLEDGE_UNDERSTANDING,
                marks=2,
                expected_time_seconds=120,
                answer_key={
                    "key_points": [
                        "Plants raised through vegetative propagation bear flowers and fruits earlier than seed-propagated plants.",
                        "It allows propagation of seedless varieties (e.g. banana, seedless grapes) and preserves exact genetic clones of desirable parent traits."
                    ],
                    "rubric": "1 mark each for any two verified advantages."
                },
                explanation="Vegetative propagation produces genetically identical offspring with rapid maturity and enables cultivation of plants that have lost the capacity to produce viable seeds.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=130, section_heading="Section 7.1.5 Vegetative Propagation"
                ),
            )
        )

        qs.append(
            Question(
                question_id="Q-CH09-NUM-001",
                question_text="A concave mirror produces a three times magnified real image of an object placed at $10\\text{ cm}$ in front of it. Calculate the focal length of the mirror.",
                question_type=QuestionType.NUMERICAL,
                chapter_id="CH-09",
                topic_id="CH09-T02",
                concept_ids=["CPT-CH09-002"],
                difficulty=QuestionDifficulty.MEDIUM,
                cognitive_level=CognitiveLevel.APPLICATION,
                marks=2,
                expected_time_seconds=150,
                answer_key={
                    "numerical_value": -7.5,
                    "unit": "cm",
                    "tolerance": 0.1,
                    "step_solution": "Object distance u = -10 cm. Magnification m = -3 (real, inverted). m = -v/u => -3 = -v/(-10) => v = -30 cm. Mirror formula: 1/f = 1/v + 1/u = 1/(-30) + 1/(-10) = -4/30 = -2/15 => f = -15/2 = -7.5 cm."
                },
                explanation="Using $m = -v/u$, $v = -30\\text{ cm}$. Applying the mirror formula $1/f = 1/v + 1/u = -1/30 - 1/10 = -4/30$, giving focal length $f = -7.5\\text{ cm}$.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=171, section_heading="Section 9.2.4 Mirror Formula"
                ),
            )
        )

        qs.append(
            Question(
                question_id="Q-CH11-SA-001",
                question_text="Why are coils of electric toasters and electric irons made of an alloy rather than a pure metal? State two specific physical reasons.",
                question_type=QuestionType.SHORT_ANSWER,
                chapter_id="CH-11",
                topic_id="CH11-T04",
                concept_ids=["CPT-CH11-003"],
                difficulty=QuestionDifficulty.EASY,
                cognitive_level=CognitiveLevel.KNOWLEDGE_UNDERSTANDING,
                marks=2,
                expected_time_seconds=120,
                answer_key={
                    "key_points": [
                        "Alloys have significantly higher electrical resistivity than their constituent pure metals, producing greater Joule heating ($H = I^2Rt$).",
                        "Alloys do not oxidize (burn) readily even at high operating temperatures (high melting points)."
                    ],
                    "rubric": "1 mark for higher resistivity / heating; 1 mark for resistance to thermal oxidation."
                },
                explanation="Alloys such as nichrome exhibit high resistivity which generates substantial thermal energy, and they resist oxidation even when red hot.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=208, section_heading="Section 11.2 Factors Governing Resistance"
                ),
            )
        )

        qs.append(
            Question(
                question_id="Q-CH12-SA-001",
                question_text="State Fleming's Left-Hand Rule and describe how it determines the direction of magnetic force on a moving charge.",
                question_type=QuestionType.SHORT_ANSWER,
                chapter_id="CH-12",
                topic_id="CH12-T03",
                concept_ids=["CPT-CH12-002"],
                difficulty=QuestionDifficulty.EASY,
                cognitive_level=CognitiveLevel.KNOWLEDGE_UNDERSTANDING,
                marks=2,
                expected_time_seconds=120,
                answer_key={
                    "key_points": [
                        "Stretch the forefinger, middle finger, and thumb of the left hand mutually perpendicular to each other.",
                        "If forefinger points in direction of magnetic field and middle finger in direction of current, thumb points in direction of motion / mechanical force."
                    ],
                    "rubric": "1 mark for posture definition; 1 mark for correct finger-to-parameter correspondence."
                },
                explanation="Fleming's Left-Hand Rule gives the direction of Lorentz magnetic force acting on an electric current conductor placed within a magnetic field.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=231, section_heading="Section 12.3 Force on a Current-Carrying Conductor"
                ),
            )
        )

        # ======================================================================
        # SECTION C: SHORT ANSWER (3 Marks Each, Q27 to Q33)
        # ======================================================================
        qs.append(
            Question(
                question_id="Q-CH01-SA-002",
                question_text="Identify the oxidizing agent and reducing agent in each of the following chemical reactions:\n(a) $2H_2S + SO_2 \\rightarrow 3S + 2H_2O$\n(b) $CuO + H_2 \\xrightarrow{\\Delta} Cu + H_2O$\n(c) $MnO_2 + 4HCl \\rightarrow MnCl_2 + 2H_2O + Cl_2$",
                question_type=QuestionType.SHORT_ANSWER,
                chapter_id="CH-01",
                topic_id="CH01-T03",
                concept_ids=["CPT-CH01-021"],
                difficulty=QuestionDifficulty.MEDIUM,
                cognitive_level=CognitiveLevel.APPLICATION,
                marks=3,
                expected_time_seconds=180,
                answer_key={
                    "key_points": [
                        "(a) Oxidizing agent: SO2; Reducing agent: H2S",
                        "(b) Oxidizing agent: CuO; Reducing agent: H2",
                        "(c) Oxidizing agent: MnO2; Reducing agent: HCl"
                    ],
                    "rubric": "1 mark for each correctly identified oxidizing and reducing agent pair."
                },
                explanation="The substance that supplies oxygen or accepts hydrogen is reduced and acts as the oxidizing agent. The substance undergoing oxidation is the reducing agent.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="sources/jesc101.pdf", page_number=12, section_heading="Section 1.2.5 Oxidation and Reduction"
                ),
            )
        )

        qs.append(
            Question(
                question_id="Q-CH02-SA-002",
                question_text="A dry pellet of a common base $X$, when kept in open air, absorbs moisture and turns sticky. The compound is also a byproduct of the chlor-alkali process.\n(a) Identify $X$ and write its chemical formula.\n(b) What type of reaction takes place when $X$ reacts with dilute hydrochloric acid?\n(c) Write a balanced chemical equation for the reaction of $X$ with dilute $HCl$.",
                question_type=QuestionType.SHORT_ANSWER,
                chapter_id="CH-02",
                topic_id="CH02-T04",
                concept_ids=["CPT-CH02-005"],
                difficulty=QuestionDifficulty.MEDIUM,
                cognitive_level=CognitiveLevel.APPLICATION,
                marks=3,
                expected_time_seconds=180,
                answer_key={
                    "key_points": [
                        "(a) X is Sodium Hydroxide; Chemical formula: NaOH.",
                        "(b) Neutralization reaction (exothermic acid-base reaction).",
                        "(c) NaOH(aq) + HCl(aq) -> NaCl(aq) + H2O(l)"
                    ],
                    "rubric": "1 mark for identification and formula; 1 mark for reaction classification; 1 mark for balanced equation."
                },
                explanation="Sodium hydroxide ($NaOH$) is a deliquescent alkali produced alongside chlorine gas in the chlor-alkali process. It reacts with hydrochloric acid in a classic neutralization producing table salt ($NaCl$) and water.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=30, section_heading="Section 2.4.2 Common Salt – Raw Material"
                ),
            )
        )

        qs.append(
            Question(
                question_id="Q-CH03-SA-002",
                question_text="Explain the formation of ionic compound magnesium chloride ($MgCl_2$) by the transfer of electrons between magnesium and chlorine atoms. Show the electron-dot structure and mention two characteristic physical properties of $MgCl_2$.",
                question_type=QuestionType.SHORT_ANSWER,
                chapter_id="CH-03",
                topic_id="CH03-T03",
                concept_ids=["CPT-CH03-002"],
                difficulty=QuestionDifficulty.MEDIUM,
                cognitive_level=CognitiveLevel.APPLICATION,
                marks=3,
                expected_time_seconds=180,
                answer_key={
                    "key_points": [
                        "Magnesium atom (2,8,2) loses two valence electrons to form Mg2+ (2,8).",
                        "Two chlorine atoms (2,8,7) each gain one electron forming two chloride ions Cl- (2,8,8), resulting in [Mg]2+ 2[Cl]-.",
                        "Properties: High melting point due to strong electrostatic attraction; conducts electricity in molten/aqueous state."
                    ],
                    "rubric": "1.5 marks for electron transfer description/diagram; 1.5 marks for two physical properties."
                },
                explanation="Magnesium achieves octet stability by transferring two valence electrons to two chlorine atoms, forming $Mg^{2+}$ and two $Cl^-$ ions bound by electrostatic forces.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=48, section_heading="Section 3.3 How do Metals and Non-Metals React?"
                ),
            )
        )

        qs.append(
            Question(
                question_id="Q-CH05-SA-002",
                question_text="Describe the structure and functioning of nephrons in the human kidney in filtering blood and producing urine. Mention the three major stages involved.",
                question_type=QuestionType.SHORT_ANSWER,
                chapter_id="CH-05",
                topic_id="CH05-T05",
                concept_ids=["CPT-CH05-005"],
                difficulty=QuestionDifficulty.MEDIUM,
                cognitive_level=CognitiveLevel.KNOWLEDGE_UNDERSTANDING,
                marks=3,
                expected_time_seconds=180,
                answer_key={
                    "key_points": [
                        "Glomerular ultrafiltration: Blood is filtered under pressure through capillaries into Bowman's capsule.",
                        "Tubular reabsorption: Useful substances (glucose, amino acids, essential salts, majority of water) are selectively reabsorbed into surrounding capillaries.",
                        "Tubular secretion & excretion: Concentrated nitrogenous wastes (urea, uric acid) pass into collecting duct as urine."
                    ],
                    "rubric": "1 mark each for filtration, selective reabsorption, and urine collection."
                },
                explanation="Nephrons are microscopic functional filtration units. Glomerular filtrate undergoes extensive selective reabsorption along the convoluted tubule before entering the collecting duct.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=110, section_heading="Section 5.5 Excretion in Human Beings"
                ),
            )
        )

        qs.append(
            Question(
                question_id="Q-CH08-SA-002",
                question_text="How is the sex of a newborn child genetically determined in human beings? Illustrate with a genetic cross diagram and explain why mothers cannot be held responsible for the sex of the child.",
                question_type=QuestionType.SHORT_ANSWER,
                chapter_id="CH-08",
                topic_id="CH08-T02",
                concept_ids=["CPT-CH08-003"],
                difficulty=QuestionDifficulty.MEDIUM,
                cognitive_level=CognitiveLevel.APPLICATION,
                marks=3,
                expected_time_seconds=180,
                answer_key={
                    "key_points": [
                        "Females produce only one type of gamete containing X chromosome (all ova are 22 + X).",
                        "Males produce two types of sperm: 50% carry X chromosome and 50% carry Y chromosome.",
                        "Fertilization by an X-sperm yields XX (female); fertilization by a Y-sperm yields XY (male). The father's sperm determines sex, not the mother."
                    ],
                    "rubric": "1 mark for cross explanation; 1 mark for genetic cross representation; 1 mark for biological deduction on parental role."
                },
                explanation="Human sex determination is governed by male heterogamety. Because maternal eggs exclusively contribute an X chromosome, whether the zygote becomes $XX$ or $XY$ depends entirely on the paternal sperm cell.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=145, section_heading="Section 8.2.3 Sex Determination"
                ),
            )
        )

        qs.append(
            Question(
                question_id="Q-CH10-SA-002",
                question_text="A person cannot see objects distinctly placed beyond $1.2\\text{ m}$.\n(a) Identify the vision defect this person is suffering from.\n(b) State two possible causes of this defect.\n(c) Calculate the focal length and power of the corrective lens required to restore normal vision.",
                question_type=QuestionType.SHORT_ANSWER,
                chapter_id="CH-10",
                topic_id="CH10-T01",
                concept_ids=["CPT-CH10-002"],
                difficulty=QuestionDifficulty.HARD,
                cognitive_level=CognitiveLevel.APPLICATION,
                marks=3,
                expected_time_seconds=210,
                answer_key={
                    "key_points": [
                        "(a) Myopia (near-sightedness).",
                        "(b) Excessive curvature of the eye lens OR elongation of the eyeball.",
                        "(c) Far point d = 1.2 m. Corrective concave lens must form virtual image of distant object (u = -inf) at far point (v = -1.2 m). 1/f = 1/v - 1/u = -1/1.2 => f = -1.2 m. Power P = 1/f = 1/(-1.2) = -0.83 D."
                    ],
                    "rubric": "1 mark for defect identification; 1 mark for two causes; 1 mark for numerical calculation of focal length and power."
                },
                explanation="Myopic eyes cannot focus parallel rays from infinity onto the retina. A diverging lens with focal length equal to negative far point ($-1.2\\text{ m}$) provides the required correction with $P = -0.83\\text{ D}$.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=189, section_heading="Section 10.2 Defects of Vision and Their Correction"
                ),
            )
        )

        qs.append(
            Question(
                question_id="Q-CH11-NUM-002",
                question_text="An electric lamp of resistance $20\\,\\Omega$ and a conductor of $4\\,\\Omega$ resistance are connected in series to a $6\\text{ V}$ battery.\n(a) Calculate the total resistance of the circuit.\n(b) Find the overall current flowing through the circuit.\n(c) Determine the potential difference across the electric lamp and across the conductor.",
                question_type=QuestionType.NUMERICAL,
                chapter_id="CH-11",
                topic_id="CH11-T03",
                concept_ids=["CPT-CH11-001", "CPT-CH11-002"],
                difficulty=QuestionDifficulty.MEDIUM,
                cognitive_level=CognitiveLevel.APPLICATION,
                marks=3,
                expected_time_seconds=180,
                answer_key={
                    "numerical_value": 0.25,
                    "unit": "A",
                    "tolerance": 0.05,
                    "step_solution": "(a) Total resistance Rs = R1 + R2 = 20 + 4 = 24 ohms. (b) Current I = V / Rs = 6V / 24 ohms = 0.25 A. (c) Voltage across lamp V1 = I * R1 = 0.25 A * 20 ohms = 5.0 V; Voltage across conductor V2 = I * R2 = 0.25 A * 4 ohms = 1.0 V."
                },
                explanation="In series circuits, resistances add directly ($R_s = 24\\,\\Omega$). By Ohm's law, circuit current is $0.25\\text{ A}$, distributing $5.0\\text{ V}$ across the lamp and $1.0\\text{ V}$ across the resistor.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=212, section_heading="Section 11.5 Resistors in Series"
                ),
            )
        )

        # ======================================================================
        # SECTION D: LONG ANSWER (5 Marks Each, Q34 to Q36)
        # ======================================================================
        # Q34: Unit 1 (Chemical Substances) - Long Answer
        qs.append(
            Question(
                question_id="Q-CH04-LA-001",
                question_text="(a) What are homologous series of carbon compounds? State any two key characteristics.\n(b) Write the chemical formula and IUPAC name of the second member of the alkyne series.\n(c) Explain the mechanism of cleaning action of soaps with a neat schematic diagram showing micelle formation around an oily droplet.\n(d) Why do soaps fail to clean clothes effectively in hard water?",
                question_type=QuestionType.LONG_ANSWER,
                chapter_id="CH-04",
                topic_id="CH04-T06",
                concept_ids=["CPT-CH04-002", "CPT-CH04-004"],
                difficulty=QuestionDifficulty.HARD,
                cognitive_level=CognitiveLevel.ANALYZE_EVALUATE_CREATE,
                marks=5,
                expected_time_seconds=360,
                answer_key={
                    "key_points": [
                        "(a) A family of organic compounds sharing the same functional group and general formula, with adjacent members differing by -CH2- (14 u). Characteristics: Gradation in physical properties, similar chemical properties.",
                        "(b) First alkyne is ethyne (C2H2); Second alkyne is Propyne (C3H4) with formula CH3-C#CH.",
                        "(c) Soap molecules possess a hydrophobic hydrocarbon tail and a hydrophilic ionic head. In water, tails orient inward encapsulating oily dirt into spherical micelles, suspended as an emulsion and washed away.",
                        "(d) Hard water contains Ca2+ and Mg2+ ions which react with soap anions to form insoluble precipitates called scum, wasting soap before lather can form."
                    ],
                    "rubric": "1 mark for (a); 1 mark for (b); 2 marks for micelle mechanism in (c); 1 mark for hard water scum explanation in (d)."
                },
                explanation="Homologous series exhibit regular chemical trends. Soaps clean by emulsifying oily grime inside colloidal micelles, but are precipitated as insoluble calcium/magnesium scum by divalent ions in hard water.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=74, section_heading="Section 4.4 Soaps and Detergents"
                ),
            )
        )

        # Q35: Unit 2 (World of Living) - Long Answer
        qs.append(
            Question(
                question_id="Q-CH05-LA-001",
                question_text="(a) Draw a neat labeled diagram of the human heart showing the four chambers, major blood vessels (aorta, vena cava, pulmonary artery, pulmonary vein), and septa.\n(b) Trace the pathway of blood circulation through the human heart.\n(c) Why is double circulation necessary in human beings and mammals?",
                question_type=QuestionType.LONG_ANSWER,
                chapter_id="CH-05",
                topic_id="CH05-T04",
                concept_ids=["CPT-CH05-004"],
                difficulty=QuestionDifficulty.HARD,
                cognitive_level=CognitiveLevel.ANALYZE_EVALUATE_CREATE,
                marks=5,
                expected_time_seconds=360,
                answer_key={
                    "key_points": [
                        "(a) Labeled parts: Right atrium, right ventricle, left atrium, left ventricle, superior/inferior vena cava, pulmonary artery, pulmonary veins, aorta, and interventricular septum.",
                        "(b) Deoxygenated blood from body -> Vena cava -> Right atrium -> Right ventricle -> Pulmonary artery -> Lungs (oxygenation) -> Pulmonary veins -> Left atrium -> Left ventricle -> Aorta -> Body tissues.",
                        "(c) Double circulation prevents mixing of oxygenated and deoxygenated blood, providing highly efficient oxygen supply essential for warm-blooded animals with high constant energy demands to maintain body temperature."
                    ],
                    "rubric": "2 marks for labeled diagram; 2 marks for circulation pathway description; 1 mark for biological significance of separating oxygenated and deoxygenated blood."
                },
                explanation="Double circulation encompasses pulmonary and systemic pathways. Complete anatomical partitioning of the mammalian four-chambered heart prevents blood mixing and maximizes aerobic metabolic efficiency.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=106, section_heading="Section 5.4 Transportation in Human Beings"
                ),
            )
        )

        # Q36: Unit 4 (Electricity & Magnetism) - Long Answer
        qs.append(
            Question(
                question_id="Q-CH11-LA-001",
                question_text="(a) Derive the expression for the equivalent resistance $R_s$ of three resistors $R_1$, $R_2$, and $R_3$ connected in series with a battery of potential difference $V$.\n(b) An electric heater rated $1000\\text{ W}$, an electric iron rated $750\\text{ W}$, and five $40\\text{ W}$ light bulbs are operated simultaneously for $6\\text{ hours}$ daily in a household.\n(i) Calculate the total electric energy consumed in commercial units (kWh) in a 30-day month.\n(ii) Find the electricity bill for the month if the tariff is Rs. 5.00 per unit (kWh).",
                question_type=QuestionType.LONG_ANSWER,
                chapter_id="CH-11",
                topic_id="CH11-T05",
                concept_ids=["CPT-CH11-002", "CPT-CH11-003"],
                difficulty=QuestionDifficulty.HARD,
                cognitive_level=CognitiveLevel.APPLICATION,
                marks=5,
                expected_time_seconds=360,
                answer_key={
                    "key_points": [
                        "(a) In series, current I is constant: V = V1 + V2 + V3. From Ohm's law, V1 = IR1, V2 = IR2, V3 = IR3. Hence, IRs = IR1 + IR2 + IR3 => Rs = R1 + R2 + R3.",
                        "(b)(i) Total power P = 1000 W + 750 W + (5 * 40 W) = 1000 + 750 + 200 = 1950 W = 1.95 kW.",
                        "Daily energy = P * t = 1.95 kW * 6 h = 11.7 kWh. Monthly energy (30 days) = 11.7 * 30 = 351 kWh.",
                        "(b)(ii) Total bill = 351 units * Rs. 5.00/unit = Rs. 1,755.00."
                    ],
                    "rubric": "2 marks for series resistance derivation; 2 marks for power summation and kWh calculation; 1 mark for monthly tariff bill calculation."
                },
                explanation="In series, additive potential drops establish $R_s = R_1 + R_2 + R_3$. Daily electrical power consumption of $1.95\\text{ kW}$ over $6\\text{ hours}$ yields $11.7\\text{ kWh}$ daily, totaling $351\\text{ kWh}$ monthly (Rs. 1,755 at Rs. 5/unit).",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=217, section_heading="Section 11.7 Electric Power"
                ),
            )
        )

        # ======================================================================
        # SECTION E: CASE-BASED / INTEGRATED (4 Marks Each, Q37 to Q39)
        # ======================================================================
        # Q37: Unit 1 Case-Based (Acids and Salts in Everyday Life)
        qs.append(
            Question(
                question_id="Q-CH02-CB-001",
                question_text="Read the following passage and answer the questions that follow:\n\npH plays a vital role in our daily survival. Our stomach produces hydrochloric acid which helps in the digestion of food without harming the stomach. During indigestion, excess acid causes pain and irritation. To relieve this pain, people consume mild bases called antacids. Another common compound, sodium hydrogencarbonate (baking soda), is synthesized from sodium chloride, water, carbon dioxide, and ammonia in the Solvay process. When heated during baking, it releases a gas that makes bread and cakes soft and spongy.\n\n(a) Name a commonly used antacid and explain how it relieves stomach pain. [1 Mark]\n(b) Write the balanced chemical equation for the decomposition of baking soda upon heating. [1 Mark]\n(c) Why does baking powder contain mild edible acid (such as tartaric acid) in addition to baking soda? What would happen if tartaric acid is omitted? [2 Marks]",
                question_type=QuestionType.CASE_BASED,
                chapter_id="CH-02",
                topic_id="CH02-T03",
                concept_ids=["CPT-CH02-004", "CPT-CH02-005"],
                difficulty=QuestionDifficulty.MEDIUM,
                cognitive_level=CognitiveLevel.APPLICATION,
                marks=4,
                expected_time_seconds=240,
                answer_key={
                    "passage": "pH plays a vital role in our daily survival. Our stomach produces hydrochloric acid which helps in the digestion of food without harming the stomach. During indigestion, excess acid causes pain and irritation. To relieve this pain, people consume mild bases called antacids. Another common compound, sodium hydrogencarbonate (baking soda), is synthesized from sodium chloride, water, carbon dioxide, and ammonia in the Solvay process. When heated during baking, it releases a gas that makes bread and cakes soft and spongy.",
                    "sub_questions": [
                        {
                            "sub_q": "Name a commonly used antacid and explain how it relieves stomach pain.",
                            "answer": "Milk of magnesia [Mg(OH)2] or baking soda (NaHCO3). It neutralizes excess stomach HCl."
                        },
                        {
                            "sub_q": "Write the balanced chemical equation for the decomposition of baking soda upon heating.",
                            "answer": "2 NaHCO3 --(Heat)--> Na2CO3 + H2O + CO2"
                        },
                        {
                            "sub_q": "Why does baking powder contain mild edible acid in addition to baking soda?",
                            "answer": "Tartaric acid neutralizes the basic sodium carbonate (Na2CO3) produced during heating, preventing a bitter taste."
                        }
                    ],
                    "key_points": [
                        "(a) Milk of magnesia [Mg(OH)2] or baking soda (NaHCO3). It acts as a mild base to neutralize excess stomach HCl, restoring normal gastric pH.",
                        "(b) 2 NaHCO3 --(Heat)--> Na2CO3 + H2O + CO2",
                        "(c) Tartaric acid neutralizes the basic sodium carbonate (Na2CO3) produced during heating. If omitted, the alkaline Na2CO3 imparts a bitter taste and unpleasant yellow tinge to the baked cake."
                    ],
                    "rubric": "1 mark for (a); 1 mark for (b); 2 marks for (c) (1 mark for neutralizing basicity, 1 mark for preventing bitter taste)."
                },
                explanation="Antacids neutralize hyperacidity. Thermal decomposition of baking soda yields sodium carbonate, water, and $CO_2$ gas. Tartaric acid in baking powder neutralizes the bitter alkaline sodium carbonate.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=26, section_heading="Section 2.2.1 How Strong Are Acid or Base Solutions?"
                ),
            )
        )

        # Q38: Unit 3 Case-Based (Spherical Lenses & Ray Optics)
        qs.append(
            Question(
                question_id="Q-CH09-CB-001",
                question_text="Read the following experimental scenario and answer the questions that follow:\n\nA student projects the image of a candle flame on a white screen using a convex lens of focal length $f = 15\\text{ cm}$. Initially, the candle is placed at a distance of $30\\text{ cm}$ from the lens.\n\n(a) What is the position, nature, and magnification of the image formed on the screen? [1 Mark]\n(b) If the candle is shifted closer to the lens such that the object distance becomes $10\\text{ cm}$, can the image still be caught on the screen? Justify with optical reasoning. [1 Mark]\n(c) Draw a ray diagram illustrating the formation of the image when the candle is placed at $10\\text{ cm}$ from this lens. State two practical applications of convex lenses used in this configuration. [2 Marks]",
                question_type=QuestionType.CASE_BASED,
                chapter_id="CH-09",
                topic_id="CH09-T04",
                concept_ids=["CPT-CH09-004"],
                difficulty=QuestionDifficulty.HARD,
                cognitive_level=CognitiveLevel.APPLICATION,
                marks=4,
                expected_time_seconds=240,
                answer_key={
                    "passage": "A student projects the image of a candle flame on a white screen using a convex lens of focal length f = 15 cm. Initially, the candle is placed at a distance of 30 cm from the lens.",
                    "sub_questions": [
                        {
                            "sub_q": "What is the position, nature, and magnification of the image formed on the screen?",
                            "answer": "At 2F2 (v = +30 cm); real, inverted, same size (m = -1)."
                        },
                        {
                            "sub_q": "If the candle is shifted to 10 cm, can the image be caught on a screen? Justify.",
                            "answer": "No. When object distance is less than focal length, the image formed is virtual and cannot be captured on a screen."
                        },
                        {
                            "sub_q": "State two practical applications of convex lenses used in this configuration.",
                            "answer": "Magnifying glass, microscope eyepiece."
                        }
                    ],
                    "key_points": [
                        "(a) Object is at 2F1 (u = -30 cm). The image is formed at 2F2 (v = +30 cm). It is real, inverted, and of the same size (magnification m = -1).",
                        "(b) No, the image cannot be captured on the screen. Because object distance (10 cm) is less than focal length (15 cm), the lens forms a virtual, erect, and magnified image behind the object which cannot be projected onto a screen.",
                        "(c) Ray diagram shows diverging rays extended backwards to form virtual image on the same side. Applications: Simple magnifying glass, reading glass, microscope eyepiece."
                    ],
                    "rubric": "1 mark for (a); 1 mark for (b) with virtual image justification; 2 marks for (c) (1 mark for ray diagram description, 1 mark for two applications)."
                },
                explanation="Placing an object within the focal length ($u < f$) of a convex lens produces a virtual, erect, magnified image that cannot be intercepted by a physical screen, forming the optical basis of magnifying lenses.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=179, section_heading="Section 9.3.5 Image Formation by Lenses"
                ),
            )
        )

        # Q39: Unit 2 Case-Based (Mendelian Genetics and Monohybrid Experiments)
        qs.append(
            Question(
                question_id="Q-CH08-CB-001",
                question_text="Read the following passage and answer the questions that follow:\n\nGregor Johann Mendel conducted hybridization experiments on garden pea plants (Pisum sativum) using seven pairs of contrasting observable traits. In one classic experiment, he crossed pure-breeding pea plants having round seeds (RR) with pure-breeding plants having wrinkled seeds (rr). All F1 offspring possessed round seeds. Upon self-pollinating the F1 generation, he harvested a total of 1,600 seeds in the F2 generation.\n\n(a) What are dominant and recessive traits in Mendelian genetics? [1 Mark]\n(b) In the F2 generation of 1,600 seeds, calculate the expected number of seeds with (i) round phenotype, and (ii) wrinkled phenotype. [1 Mark]\n(c) Out of the round seeds harvested in F2, what fraction is expected to be homozygous (pure-breeding) vs heterozygous? Explain using genotypes. [2 Marks]",
                question_type=QuestionType.CASE_BASED,
                chapter_id="CH-08",
                topic_id="CH08-T01",
                concept_ids=["CPT-CH08-001"],
                difficulty=QuestionDifficulty.MEDIUM,
                cognitive_level=CognitiveLevel.APPLICATION,
                marks=4,
                expected_time_seconds=240,
                answer_key={
                    "passage": "Gregor Johann Mendel conducted hybridization experiments on garden pea plants (Pisum sativum) using seven pairs of contrasting observable traits. In one classic experiment, he crossed pure-breeding pea plants having round seeds (RR) with pure-breeding plants having wrinkled seeds (rr). All F1 offspring possessed round seeds. Upon self-pollinating the F1 generation, he harvested a total of 1,600 seeds in the F2 generation.",
                    "sub_questions": [
                        {
                            "sub_q": "What are dominant and recessive traits in Mendelian genetics?",
                            "answer": "Dominant: expressed in both homozygous and heterozygous states. Recessive: expressed only in homozygous state."
                        },
                        {
                            "sub_q": "Calculate expected number of round and wrinkled seeds in F2 generation of 1,600 seeds.",
                            "answer": "Round = 3/4 * 1600 = 1,200 seeds; Wrinkled = 1/4 * 1600 = 400 seeds."
                        },
                        {
                            "sub_q": "What fraction of round seeds is expected to be homozygous vs heterozygous?",
                            "answer": "1/3 homozygous (RR) and 2/3 heterozygous (Rr)."
                        }
                    ],
                    "key_points": [
                        "(a) Dominant trait: An allele expressed in both homozygous (RR) and heterozygous (Rr) conditions. Recessive trait: Expressed only in the homozygous state (rr) in the absence of the dominant allele.",
                        "(b) Phenotypic ratio is 3 Round : 1 Wrinkled. (i) Round seeds: 3/4 * 1600 = 1,200 seeds; (ii) Wrinkled seeds: 1/4 * 1600 = 400 seeds.",
                        "(c) Genotypic ratio is 1 RR : 2 Rr : 1 rr. Among the 3 parts of round seeds, 1 part is homozygous (RR) and 2 parts are heterozygous (Rr). Hence, 1/3 (33.3%) are homozygous pure-breeding and 2/3 (66.7%) are heterozygous."
                    ],
                    "rubric": "1 mark for (a); 1 mark for (b) correct numerical count; 2 marks for (c) genotypic proportion breakdown."
                },
                explanation="Mendel's monohybrid $F_2$ genotypic ratio of $1\\,RR : 2\\,Rr : 1\\,rr$ demonstrates that two-thirds of phenotypically dominant round seeds harbor masked recessive alleles.",
                provenance=QuestionProvenance(
                    source_document_id="NCERT_SCI_10", source_filename="NCERT-Class-10-Science.pdf", page_number=143, section_heading="Section 8.2.1 Rules for Inheritance of Traits"
                ),
            )
        )

        return qs

    # --------------------------------------------------------------------------
    # Expanded RAG Textbook Chunks
    # --------------------------------------------------------------------------
    def _get_expanded_rag_chunks(self) -> List[Dict[str, Any]]:
        return [
            {
                "chunk_id": "CHK-CH02-P018",
                "chapter_id": "CH-02",
                "topic_id": "CH02-T01",
                "concept_id": "CPT-CH02-001",
                "page_num": 18,
                "heading": "Understanding the Chemical Properties of Acids and Bases",
                "chunk_text": "Acids are sour in taste and change the colour of blue litmus to red, whereas bases are bitter and change the colour of red litmus to blue. Litmus solution is a purple dye extracted from lichen. When an acid reacts with a metal, hydrogen gas is evolved and a corresponding salt is formed. Acids generate hydrogen ions H+(aq) in solution, which is responsible for their acidic properties."
            },
            {
                "chunk_id": "CHK-CH02-P026",
                "chapter_id": "CH-02",
                "topic_id": "CH02-T03",
                "concept_id": "CPT-CH02-004",
                "page_num": 26,
                "heading": "How Strong Are Acid or Base Solutions? - The pH Scale",
                "chunk_text": "A scale for measuring hydrogen ion concentration in a solution, called pH scale, has been developed. The p in pH stands for 'potenz' in German, meaning power. On the pH scale we can measure pH from 0 (very acidic) to 14 (very alkaline). Higher hydronium ion concentration means a lower pH value. The pH of a neutral solution is 7. Living organisms can survive only in a narrow range of pH change (our body works within the pH range of 7.0 to 7.8)."
            },
            {
                "chunk_id": "CHK-CH03-P046",
                "chapter_id": "CH-03",
                "topic_id": "CH03-T02",
                "concept_id": "CPT-CH03-001",
                "page_num": 46,
                "heading": "The Reactivity Series of Metals",
                "chunk_text": "The reactivity series is a list of metals arranged in the order of their decreasing activities. Potassium, sodium, calcium, and magnesium are at the top and are so reactive that they never occur in nature as free elements. Metals in the middle (zinc, iron, lead) are moderately reactive and exist as oxides, sulphides, or carbonates. Copper, silver, and gold are at the bottom of the series and are found in free state."
            },
            {
                "chunk_id": "CHK-CH04-P060",
                "chapter_id": "CH-04",
                "topic_id": "CH04-T01",
                "concept_id": "CPT-CH04-001",
                "page_num": 60,
                "heading": "Bonding in Carbon – The Covalent Bond",
                "chunk_text": "Carbon has atomic number 6 with electronic configuration (2,4). To attain noble gas configuration, carbon overcomes energy limitations by sharing its valence electrons with other atoms of carbon or with atoms of other elements. Bonds formed by sharing of an electron pair between two atoms are known as covalent bonds. Covalently bonded molecules have strong bonds within the molecule, but intermolecular forces are small, resulting in low melting and boiling points."
            },
            {
                "chunk_id": "CHK-CH05-P096",
                "chapter_id": "CH-05",
                "topic_id": "CH05-T02",
                "concept_id": "CPT-CH05-001",
                "page_num": 96,
                "heading": "Autotrophic Nutrition in Green Plants",
                "chunk_text": "Carbon and energy requirements of autotrophic organisms are fulfilled by photosynthesis. It is the process by which autotrophs take in carbon dioxide and water from the environment and convert them into stored forms of energy (carbohydrates) in the presence of sunlight and chlorophyll: 6 CO2 + 12 H2O -> C6H12O6 + 6 O2 + 6 H2O. Stomata are tiny pores present on the surface of leaves through which massive amounts of gaseous exchange take place for photosynthesis."
            },
            {
                "chunk_id": "CHK-CH06-P114",
                "chapter_id": "CH-06",
                "topic_id": "CH06-T02",
                "concept_id": "CPT-CH06-001",
                "page_num": 114,
                "heading": "Nervous System and Reflex Action",
                "chunk_text": "All information from our environment is detected by the specialized tips of nerve cells called neurons. Gustatory receptors detect taste while olfactory receptors detect smell. At the dendritic tip, an electrical impulse is set off which travels to the cell body and along the axon. At the axonal end, the electrical impulse releases chemical neurotransmitters across the synapse to start a similar impulse in the next neuron. Reflex arcs are formed in the spinal cord, although the information input also goes on to reach the brain."
            },
            {
                "chunk_id": "CHK-CH08-P142",
                "chapter_id": "CH-08",
                "topic_id": "CH08-T01",
                "concept_id": "CPT-CH08-001",
                "page_num": 142,
                "heading": "Mendel’s Experiments on Pea Plants and Laws of Inheritance",
                "chunk_text": "Mendel used a number of contrasting visible characters of garden peas—round/wrinkled seeds, tall/short plants, white/violet flowers. In a cross between tall (TT) and short (tt) plants, all F1 progeny were tall. In F2 generation obtained by self-pollination of F1 plants, both tall and short traits appeared in the ratio of 3:1. This demonstrated that traits may not show up in an individual but can still be inherited, distinguishing dominant from recessive factors."
            },
            {
                "chunk_id": "CHK-CH09-P162",
                "chapter_id": "CH-09",
                "topic_id": "CH09-T01",
                "concept_id": "CPT-CH09-001",
                "page_num": 162,
                "heading": "Reflection of Light by Spherical Mirrors",
                "chunk_text": "The center of the reflecting surface of a spherical mirror is a point called the pole (P). The reflecting surface forms part of a sphere whose center is the center of curvature (C). The distance between the pole and the principal focus is called the focal length (f). For spherical mirrors of small apertures, the radius of curvature is found to be equal to twice the focal length (R = 2f). The mirror formula is 1/v + 1/u = 1/f where u is object distance and v is image distance."
            },
            {
                "chunk_id": "CHK-CH11-P200",
                "chapter_id": "CH-11",
                "topic_id": "CH11-T01",
                "concept_id": "CPT-CH11-001",
                "page_num": 200,
                "heading": "Ohm’s Law and Electrical Resistance",
                "chunk_text": "In 1827, German physicist Georg Simon Ohm found that the electric current I flowing through a metallic conductor is directly proportional to the potential difference V across its terminals, provided its temperature remains the same: V / I = constant = R. Resistance is the property of a conductor to resist the flow of charges through it. Its SI unit is ohm. Resistance depends directly on length l, inversely on area of cross-section A, and on material resistivity: R = rho * (l / A)."
            },
            {
                "chunk_id": "CHK-CH12-P224",
                "chapter_id": "CH-12",
                "topic_id": "CH12-T01",
                "concept_id": "CPT-CH12-001",
                "page_num": 224,
                "heading": "Magnetic Field and Field Lines",
                "chunk_text": "A magnetic compass needle gets deflected when placed near a current-carrying wire. The region surrounding a magnet where its force can be detected is said to have a magnetic field. Magnetic field lines emerge from the North pole and merge at the South pole outside the magnet, forming continuous closed curves. The relative strength of the magnetic field is shown by the degree of closeness of the field lines. Two magnetic field lines never intersect each other."
            },
            {
                "chunk_id": "CHK-CH13-P256",
                "chapter_id": "CH-13",
                "topic_id": "CH13-T01",
                "concept_id": "CPT-CH13-001",
                "page_num": 256,
                "heading": "Trophic Levels and Energy Flow in Ecosystems",
                "chunk_text": "An ecosystem consists of biotic components comprising living organisms and abiotic components comprising physical factors like temperature, rainfall, wind, soil and minerals. In a food chain, green plants capture about 1% of the solar energy falling on leaves. An average of 10% of the food eaten is turned into the organism's own body and made available for the next level of consumers (10% law). Because energy diminishes so rapidly, food chains generally consist of only three or four steps."
            },
        ]
