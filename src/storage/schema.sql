-- P0 Curriculum Foundation Relational Database Schema
-- SQLite 3 with strict foreign key constraints and referential integrity

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS source_documents (
    document_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    document_type TEXT NOT NULL,
    academic_session TEXT NOT NULL,
    subject TEXT NOT NULL,
    subject_code TEXT,
    source_authority TEXT NOT NULL,
    file_path TEXT,
    file_size_bytes INTEGER,
    sha256_hash TEXT,
    page_count INTEGER,
    verification_status TEXT NOT NULL CHECK(verification_status IN ('VERIFIED', 'PENDING_VERIFICATION', 'UNVERIFIED')),
    metadata_json TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS academic_sessions (
    session_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    start_year INTEGER NOT NULL,
    end_year INTEGER NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1))
);

CREATE TABLE IF NOT EXISTS subjects (
    subject_id TEXT PRIMARY KEY,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    class_level INTEGER NOT NULL DEFAULT 10,
    description TEXT
);

CREATE TABLE IF NOT EXISTS curricula (
    curriculum_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    session_id TEXT NOT NULL REFERENCES academic_sessions(session_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    subject_id TEXT NOT NULL REFERENCES subjects(subject_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    class_level INTEGER NOT NULL DEFAULT 10,
    authority TEXT NOT NULL DEFAULT 'CBSE',
    metadata_json TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS units (
    unit_id TEXT PRIMARY KEY,
    unit_number TEXT NOT NULL,
    name TEXT NOT NULL,
    theme TEXT,
    curriculum_id TEXT NOT NULL REFERENCES curricula(curriculum_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    marks INTEGER,
    verification_status TEXT NOT NULL CHECK(verification_status IN ('VERIFIED', 'PENDING_VERIFICATION', 'UNVERIFIED')),
    source_doc_id TEXT REFERENCES source_documents(document_id) ON UPDATE CASCADE ON DELETE SET NULL,
    source_page INTEGER,
    source_section TEXT
);

CREATE TABLE IF NOT EXISTS chapters (
    chapter_id TEXT PRIMARY KEY,
    chapter_number INTEGER NOT NULL UNIQUE,
    name TEXT NOT NULL,
    unit_id TEXT NOT NULL REFERENCES units(unit_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    curriculum_id TEXT NOT NULL REFERENCES curricula(curriculum_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    assessment_status TEXT NOT NULL CHECK(assessment_status IN ('SUMMATIVE', 'FORMATIVE', 'NOT_IN_CURRENT_SCOPE', 'PENDING_VERIFICATION')),
    verification_status TEXT NOT NULL CHECK(verification_status IN ('VERIFIED', 'PENDING_VERIFICATION', 'UNVERIFIED')),
    metadata_json TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS topics (
    topic_id TEXT PRIMARY KEY,
    chapter_id TEXT NOT NULL REFERENCES chapters(chapter_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    name TEXT NOT NULL,
    sequence_order INTEGER NOT NULL DEFAULT 1,
    description TEXT,
    assessment_status TEXT NOT NULL CHECK(assessment_status IN ('SUMMATIVE', 'FORMATIVE', 'NOT_IN_CURRENT_SCOPE', 'PENDING_VERIFICATION')),
    verification_status TEXT NOT NULL CHECK(verification_status IN ('VERIFIED', 'PENDING_VERIFICATION', 'UNVERIFIED')),
    source_doc_id TEXT REFERENCES source_documents(document_id) ON UPDATE CASCADE ON DELETE SET NULL,
    source_page_start INTEGER,
    source_page_end INTEGER,
    source_section TEXT,
    metadata_json TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS subtopics (
    subtopic_id TEXT PRIMARY KEY,
    topic_id TEXT NOT NULL REFERENCES topics(topic_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    name TEXT NOT NULL,
    sequence_order INTEGER NOT NULL DEFAULT 1,
    description TEXT,
    assessment_status TEXT NOT NULL CHECK(assessment_status IN ('SUMMATIVE', 'FORMATIVE', 'NOT_IN_CURRENT_SCOPE', 'PENDING_VERIFICATION')),
    verification_status TEXT NOT NULL CHECK(verification_status IN ('VERIFIED', 'PENDING_VERIFICATION', 'UNVERIFIED')),
    source_doc_id TEXT REFERENCES source_documents(document_id) ON UPDATE CASCADE ON DELETE SET NULL,
    source_page_start INTEGER,
    source_page_end INTEGER,
    source_section TEXT
);

CREATE TABLE IF NOT EXISTS learning_outcomes (
    outcome_id TEXT PRIMARY KEY,
    code TEXT,
    related_chapter_id TEXT NOT NULL REFERENCES chapters(chapter_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    related_topic_id TEXT REFERENCES topics(topic_id) ON UPDATE CASCADE ON DELETE SET NULL,
    description TEXT NOT NULL,
    curricular_goal TEXT,
    competency TEXT,
    suggestive_verbs_json TEXT DEFAULT '[]',
    provenance_type TEXT NOT NULL CHECK(provenance_type IN ('OFFICIAL', 'INFERRED', 'PENDING')),
    verification_status TEXT NOT NULL CHECK(verification_status IN ('VERIFIED', 'PENDING_VERIFICATION', 'UNVERIFIED')),
    source_doc_id TEXT REFERENCES source_documents(document_id) ON UPDATE CASCADE ON DELETE SET NULL,
    source_page INTEGER,
    source_section TEXT
);

CREATE TABLE IF NOT EXISTS curriculum_mappings (
    mapping_id TEXT PRIMARY KEY,
    parent_type TEXT NOT NULL,
    parent_id TEXT NOT NULL,
    child_type TEXT NOT NULL,
    child_id TEXT NOT NULL,
    sequence_order INTEGER NOT NULL DEFAULT 1,
    verification_status TEXT NOT NULL CHECK(verification_status IN ('VERIFIED', 'PENDING_VERIFICATION', 'UNVERIFIED')),
    notes TEXT
);

CREATE TABLE IF NOT EXISTS source_citations (
    citation_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    document_id TEXT NOT NULL REFERENCES source_documents(document_id) ON UPDATE CASCADE ON DELETE CASCADE,
    page_start INTEGER,
    page_end INTEGER,
    section TEXT,
    verbatim_quote TEXT
);

-- Indexes for performance and query optimization
CREATE INDEX IF NOT EXISTS idx_chapters_unit ON chapters(unit_id);
CREATE INDEX IF NOT EXISTS idx_topics_chapter ON topics(chapter_id);
CREATE INDEX IF NOT EXISTS idx_subtopics_topic ON subtopics(topic_id);
CREATE INDEX IF NOT EXISTS idx_learning_outcomes_chapter ON learning_outcomes(related_chapter_id);
CREATE INDEX IF NOT EXISTS idx_learning_outcomes_topic ON learning_outcomes(related_topic_id);
CREATE INDEX IF NOT EXISTS idx_source_citations_entity ON source_citations(entity_type, entity_id);

-- P1 Concept Graph Engine Schema Extensions

CREATE TABLE IF NOT EXISTS concepts (
    concept_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    canonical_name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    chapter_id TEXT NOT NULL REFERENCES chapters(chapter_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    topic_id TEXT NOT NULL REFERENCES topics(topic_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    subtopic_id TEXT REFERENCES subtopics(subtopic_id) ON UPDATE CASCADE ON DELETE SET NULL,
    concept_type TEXT NOT NULL CHECK(concept_type IN ('CORE', 'FOUNDATIONAL', 'APPLIED', 'PRACTICAL', 'EXTENDED')),
    difficulty_level TEXT CHECK(difficulty_level IN ('EASY', 'MEDIUM', 'HARD', 'UNCLASSIFIED') OR difficulty_level IS NULL),
    learning_objective TEXT,
    source_status TEXT NOT NULL DEFAULT 'SOURCE_DERIVED' CHECK(source_status IN ('SOURCE_DERIVED', 'CURRICULUM_SYNTHESIZED', 'INFERRED')),
    verification_status TEXT NOT NULL CHECK(verification_status IN ('VERIFIED', 'SOURCE_VERIFIED', 'PENDING_VERIFICATION', 'HUMAN_REVIEW_REQUIRED', 'UNVERIFIED')),
    metadata_json TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS concept_relationships (
    edge_id TEXT PRIMARY KEY,
    source_concept_id TEXT NOT NULL REFERENCES concepts(concept_id) ON UPDATE CASCADE ON DELETE CASCADE,
    target_concept_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL CHECK(relationship_type IN ('PREREQUISITE_OF', 'PART_OF', 'MAPS_TO', 'SUPPORTS_LEARNING_OUTCOME', 'RELATED_TO')),
    description TEXT,
    confidence REAL CHECK(confidence >= 0.0 AND confidence <= 1.0),
    verification_status TEXT NOT NULL CHECK(verification_status IN ('VERIFIED', 'SOURCE_VERIFIED', 'PENDING_VERIFICATION', 'HUMAN_REVIEW_REQUIRED', 'UNVERIFIED')),
    source_provenance_json TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS concept_provenance (
    provenance_id TEXT PRIMARY KEY,
    concept_id TEXT NOT NULL REFERENCES concepts(concept_id) ON UPDATE CASCADE ON DELETE CASCADE,
    source_document_id TEXT NOT NULL REFERENCES source_documents(document_id) ON UPDATE CASCADE ON DELETE CASCADE,
    source_filename TEXT NOT NULL,
    page_number INTEGER,
    section_heading TEXT,
    extraction_method TEXT NOT NULL,
    confidence REAL CHECK(confidence >= 0.0 AND confidence <= 1.0),
    verification_status TEXT NOT NULL CHECK(verification_status IN ('VERIFIED', 'SOURCE_VERIFIED', 'PENDING_VERIFICATION', 'HUMAN_REVIEW_REQUIRED', 'UNVERIFIED')),
    verbatim_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_concepts_chapter ON concepts(chapter_id);
CREATE INDEX IF NOT EXISTS idx_concepts_topic ON concepts(topic_id);
CREATE INDEX IF NOT EXISTS idx_concepts_subtopic ON concepts(subtopic_id);
CREATE INDEX IF NOT EXISTS idx_concept_rel_source ON concept_relationships(source_concept_id);
CREATE INDEX IF NOT EXISTS idx_concept_rel_target ON concept_relationships(target_concept_id);
CREATE INDEX IF NOT EXISTS idx_concept_rel_type ON concept_relationships(relationship_type);
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_concept_edge ON concept_relationships(source_concept_id, target_concept_id, relationship_type);
CREATE INDEX IF NOT EXISTS idx_concept_provenance_concept ON concept_provenance(concept_id);

-- P2 Question Bank & Question Generation Engine Schema Extensions

CREATE TABLE IF NOT EXISTS questions (
    question_id TEXT PRIMARY KEY,
    question_text TEXT NOT NULL,
    question_type TEXT NOT NULL CHECK(question_type IN ('MCQ', 'SHORT_ANSWER', 'LONG_ANSWER', 'ASSERTION_REASON', 'CASE_BASED', 'NUMERICAL', 'DIAGRAM_BASED')),
    chapter_id TEXT NOT NULL REFERENCES chapters(chapter_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    topic_id TEXT NOT NULL REFERENCES topics(topic_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    difficulty TEXT NOT NULL CHECK(difficulty IN ('EASY', 'MEDIUM', 'HARD')),
    cognitive_level TEXT NOT NULL CHECK(cognitive_level IN ('KNOWLEDGE_UNDERSTANDING', 'APPLICATION', 'ANALYZE_EVALUATE_CREATE')),
    marks INTEGER NOT NULL DEFAULT 1 CHECK(marks > 0),
    expected_time_seconds INTEGER NOT NULL DEFAULT 60 CHECK(expected_time_seconds > 0),
    answer_key_json TEXT NOT NULL,
    explanation TEXT NOT NULL,
    misconception_tags_json TEXT DEFAULT '[]',
    source_status TEXT NOT NULL CHECK(source_status IN ('SOURCE_DERIVED', 'CURRICULUM_SYNTHESIZED', 'INFERRED', 'AI_GENERATED')),
    verification_status TEXT NOT NULL CHECK(verification_status IN ('VERIFIED', 'SOURCE_VERIFIED', 'PENDING_VERIFICATION', 'HUMAN_REVIEW_REQUIRED', 'UNVERIFIED')),
    question_status TEXT NOT NULL CHECK(question_status IN ('DRAFT', 'PENDING_REVIEW', 'VALIDATED', 'REJECTED')),
    provenance_json TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS question_concept_mappings (
    mapping_id TEXT PRIMARY KEY,
    question_id TEXT NOT NULL REFERENCES questions(question_id) ON UPDATE CASCADE ON DELETE CASCADE,
    concept_id TEXT NOT NULL REFERENCES concepts(concept_id) ON UPDATE CASCADE ON DELETE CASCADE,
    is_primary INTEGER NOT NULL DEFAULT 1 CHECK(is_primary IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS question_learning_outcome_mappings (
    mapping_id TEXT PRIMARY KEY,
    question_id TEXT NOT NULL REFERENCES questions(question_id) ON UPDATE CASCADE ON DELETE CASCADE,
    outcome_id TEXT NOT NULL REFERENCES learning_outcomes(outcome_id) ON UPDATE CASCADE ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_questions_chapter ON questions(chapter_id);
CREATE INDEX IF NOT EXISTS idx_questions_topic ON questions(topic_id);
CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty);
CREATE INDEX IF NOT EXISTS idx_questions_cognitive ON questions(cognitive_level);
CREATE INDEX IF NOT EXISTS idx_questions_type ON questions(question_type);
CREATE INDEX IF NOT EXISTS idx_questions_status ON questions(question_status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_qcm ON question_concept_mappings(question_id, concept_id);
CREATE INDEX IF NOT EXISTS idx_qcm_concept ON question_concept_mappings(concept_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_qlo ON question_learning_outcome_mappings(question_id, outcome_id);
CREATE INDEX IF NOT EXISTS idx_qlo_outcome ON question_learning_outcome_mappings(outcome_id);

-- P3 Diagnostic Assessment & Learner Model Schema Extensions

CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    grade INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS assessments (
    assessment_id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES students(student_id) ON UPDATE CASCADE ON DELETE CASCADE,
    assessment_type TEXT NOT NULL CHECK(assessment_type IN ('DIAGNOSTIC', 'ADAPTIVE_PRACTICE', 'REVISION')),
    chapter_id TEXT REFERENCES chapters(chapter_id),
    status TEXT NOT NULL CHECK(status IN ('IN_PROGRESS', 'SUBMITTED', 'EVALUATED')),
    total_questions INTEGER NOT NULL DEFAULT 0,
    total_marks INTEGER NOT NULL DEFAULT 0,
    score REAL DEFAULT 0.0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS assessment_questions (
    assessment_id TEXT NOT NULL REFERENCES assessments(assessment_id) ON UPDATE CASCADE ON DELETE CASCADE,
    question_id TEXT NOT NULL REFERENCES questions(question_id) ON UPDATE CASCADE ON DELETE CASCADE,
    question_order INTEGER NOT NULL,
    PRIMARY KEY (assessment_id, question_id)
);

CREATE TABLE IF NOT EXISTS student_answers (
    answer_id TEXT PRIMARY KEY,
    assessment_id TEXT NOT NULL REFERENCES assessments(assessment_id) ON UPDATE CASCADE ON DELETE CASCADE,
    student_id TEXT NOT NULL REFERENCES students(student_id) ON UPDATE CASCADE ON DELETE CASCADE,
    question_id TEXT NOT NULL REFERENCES questions(question_id) ON UPDATE CASCADE ON DELETE CASCADE,
    submitted_answer_json TEXT NOT NULL,
    is_correct INTEGER NOT NULL CHECK(is_correct IN (0, 1)),
    marks_awarded REAL NOT NULL DEFAULT 0.0,
    evaluation_feedback TEXT,
    detected_misconceptions_json TEXT DEFAULT '[]',
    time_spent_seconds INTEGER DEFAULT 0,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(assessment_id, question_id)
);

CREATE TABLE IF NOT EXISTS learner_concept_mastery (
    mastery_id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES students(student_id) ON UPDATE CASCADE ON DELETE CASCADE,
    concept_id TEXT NOT NULL REFERENCES concepts(concept_id) ON UPDATE CASCADE ON DELETE CASCADE,
    mastery_score REAL NOT NULL DEFAULT 0.0 CHECK(mastery_score >= 0.0 AND mastery_score <= 1.0),
    confidence_score REAL NOT NULL DEFAULT 0.5 CHECK(confidence_score >= 0.0 AND confidence_score <= 1.0),
    total_attempts INTEGER NOT NULL DEFAULT 0,
    correct_attempts INTEGER NOT NULL DEFAULT 0,
    incorrect_attempts INTEGER NOT NULL DEFAULT 0,
    last_attempted_at TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, concept_id)
);

CREATE TABLE IF NOT EXISTS student_misconceptions (
    misconception_record_id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES students(student_id) ON UPDATE CASCADE ON DELETE CASCADE,
    concept_id TEXT NOT NULL REFERENCES concepts(concept_id) ON UPDATE CASCADE ON DELETE CASCADE,
    misconception_tag TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('SUSPECTED', 'CONFIRMED', 'RESOLVED')),
    evidence_count INTEGER NOT NULL DEFAULT 1,
    evidence_text TEXT,
    last_observed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, concept_id, misconception_tag)
);

CREATE INDEX IF NOT EXISTS idx_assessments_student ON assessments(student_id);
CREATE INDEX IF NOT EXISTS idx_assessments_status ON assessments(status);
CREATE INDEX IF NOT EXISTS idx_answers_assessment ON student_answers(assessment_id);
CREATE INDEX IF NOT EXISTS idx_answers_student ON student_answers(student_id);
CREATE INDEX IF NOT EXISTS idx_answers_question ON student_answers(question_id);
CREATE INDEX IF NOT EXISTS idx_mastery_student ON learner_concept_mastery(student_id);
CREATE INDEX IF NOT EXISTS idx_mastery_concept ON learner_concept_mastery(concept_id);
CREATE INDEX IF NOT EXISTS idx_misconceptions_student ON student_misconceptions(student_id);

-- P4 Spaced Repetition, Targeted Remediation & Curriculum Embeddings Schema Extensions

CREATE TABLE IF NOT EXISTS spaced_repetition_schedules (
    schedule_id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES students(student_id) ON UPDATE CASCADE ON DELETE CASCADE,
    concept_id TEXT NOT NULL REFERENCES concepts(concept_id) ON UPDATE CASCADE ON DELETE CASCADE,
    last_reviewed_at TIMESTAMP,
    next_review_at TIMESTAMP NOT NULL,
    interval_days INTEGER NOT NULL DEFAULT 1,
    ease_factor REAL NOT NULL DEFAULT 2.5,
    review_count INTEGER NOT NULL DEFAULT 0,
    last_result TEXT CHECK(last_result IN ('CORRECT', 'INCORRECT', 'PARTIAL', 'NOT_REVIEWED') OR last_result IS NULL),
    current_mastery REAL DEFAULT 0.0,
    review_status TEXT NOT NULL DEFAULT 'PENDING' CHECK(review_status IN ('PENDING', 'DUE', 'COMPLETED', 'OVERDUE')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, concept_id)
);

CREATE TABLE IF NOT EXISTS remediation_records (
    remediation_id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES students(student_id) ON UPDATE CASCADE ON DELETE CASCADE,
    concept_id TEXT NOT NULL REFERENCES concepts(concept_id) ON UPDATE CASCADE ON DELETE CASCADE,
    prerequisite_concept_id TEXT REFERENCES concepts(concept_id) ON UPDATE CASCADE ON DELETE SET NULL,
    gap_summary TEXT,
    ncert_reference TEXT,
    explanation TEXT NOT NULL,
    example_activity TEXT,
    practice_question_id TEXT REFERENCES questions(question_id) ON UPDATE CASCADE ON DELETE SET NULL,
    student_answer TEXT,
    is_completed INTEGER NOT NULL DEFAULT 0 CHECK(is_completed IN (0, 1)),
    mastery_before REAL,
    mastery_after REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS curriculum_embeddings (
    chunk_id TEXT PRIMARY KEY,
    chapter_id TEXT NOT NULL REFERENCES chapters(chapter_id) ON UPDATE CASCADE ON DELETE CASCADE,
    topic_id TEXT REFERENCES topics(topic_id) ON UPDATE CASCADE ON DELETE SET NULL,
    concept_id TEXT REFERENCES concepts(concept_id) ON UPDATE CASCADE ON DELETE SET NULL,
    source_doc_id TEXT REFERENCES source_documents(document_id) ON UPDATE CASCADE ON DELETE SET NULL,
    page_number INTEGER,
    section_heading TEXT,
    chunk_text TEXT NOT NULL,
    metadata_json TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_repetition_student ON spaced_repetition_schedules(student_id);
CREATE INDEX IF NOT EXISTS idx_repetition_due ON spaced_repetition_schedules(next_review_at);
CREATE INDEX IF NOT EXISTS idx_repetition_status ON spaced_repetition_schedules(review_status);
CREATE INDEX IF NOT EXISTS idx_remediation_student ON remediation_records(student_id);
CREATE INDEX IF NOT EXISTS idx_remediation_concept ON remediation_records(concept_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_chapter ON curriculum_embeddings(chapter_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_concept ON curriculum_embeddings(concept_id);




