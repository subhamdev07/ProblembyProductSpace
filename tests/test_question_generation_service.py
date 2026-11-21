"""
Unit Tests for Question Generation Service
Tests AI-assisted question generation, hermetic mock generation,
prompt construction, and validation pipeline integration.
"""

import json
import pytest
from unittest.mock import MagicMock

from src.services.question_generation_service import (
    QuestionGenerationService,
    GeneratedQuestionCandidate,
)
from src.models.question import (
    QuestionType,
    QuestionDifficulty,
    CognitiveLevel,
    QuestionStatus,
)
from src.models.concept import ConceptVerificationStatus


def test_generation_with_mock_response(seeded_concept_repo, question_repo):
    """Test generating a question using hermetic mock JSON without hitting live LLM API."""
    service = QuestionGenerationService(
        question_repo=question_repo,
        concept_repo=seeded_concept_repo,
    )

    mock_llm_json = json.dumps({
        "question_text": "What type of chemical reaction is represented by $2H_2 + O_2 \\rightarrow 2H_2O$?",
        "question_type": "MCQ",
        "difficulty": "EASY",
        "cognitive_level": "KNOWLEDGE_UNDERSTANDING",
        "marks": 1,
        "expected_time_seconds": 45,
        "answer_key": {
            "options": {
                "A": "Combination reaction",
                "B": "Decomposition reaction",
                "C": "Displacement reaction",
                "D": "Double displacement reaction",
            },
            "correct_option": "A",
        },
        "explanation": "Two reactants combine to form a single product, which defines a combination reaction.",
        "misconception_tags": ["confusing_combination_with_decomposition"],
    })

    q = service.generate_question_for_concept(
        concept_id="CPT-CH01-001",
        question_type=QuestionType.MCQ,
        difficulty=QuestionDifficulty.EASY,
        cognitive_level=CognitiveLevel.KNOWLEDGE_UNDERSTANDING,
        mock_response=mock_llm_json,
    )

    assert q.question_id.startswith("Q-CH-01-MCQ-")
    assert q.question_type == QuestionType.MCQ
    assert q.difficulty == QuestionDifficulty.EASY
    assert q.marks == 1
    assert q.answer_key["correct_option"] == "A"
    assert q.concept_ids == ["CPT-CH01-001"]
    assert q.provenance is not None
    assert q.question_status == QuestionStatus.VALIDATED


def test_generation_with_mocked_llm_service(seeded_concept_repo, question_repo):
    """Test generation with a mocked NVIDIANemotronService object."""
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "question": {
            "question_text": "Explain why respiration is considered an exothermic reaction in human metabolism.",
            "question_type": "SHORT_ANSWER",
            "difficulty": "MEDIUM",
            "cognitive_level": "APPLICATION",
            "marks": 2,
            "expected_time_seconds": 90,
            "answer_key": {
                "key_points": [
                    "Glucose combines with oxygen in cells.",
                    "Energy is released in the form of ATP.",
                ],
            },
            "explanation": "During digestion food is broken down into glucose which combines with oxygen to release energy.",
            "misconception_tags": ["thinking_respiration_is_endothermic"],
        }
    })
    mock_llm.generate.return_value = mock_response

    service = QuestionGenerationService(
        question_repo=question_repo,
        concept_repo=seeded_concept_repo,
        llm_service=mock_llm,
    )

    q = service.generate_question_for_concept(
        concept_id="CPT-CH01-013",
        question_type=QuestionType.SHORT_ANSWER,
        difficulty=QuestionDifficulty.MEDIUM,
        cognitive_level=CognitiveLevel.APPLICATION,
    )

    assert mock_llm.generate.called
    assert q.question_type == QuestionType.SHORT_ANSWER
    assert q.difficulty == QuestionDifficulty.MEDIUM
    assert q.marks == 2
    assert "key_points" in q.answer_key


def test_generation_invalid_concept_raises_error(seeded_concept_repo, question_repo):
    """Test that requesting generation for non-existent concept raises ValueError."""
    service = QuestionGenerationService(
        question_repo=question_repo,
        concept_repo=seeded_concept_repo,
    )

    with pytest.raises(ValueError) as exc:
        service.generate_question_for_concept(
            concept_id="NON-EXISTENT-CONCEPT",
            mock_response="{}",
        )
    assert "not found in Concept Graph" in str(exc.value)


def test_generation_without_llm_service_raises_runtime_error(seeded_concept_repo, question_repo):
    """Test that attempting live generation when LLM service is None raises RuntimeError."""
    service = QuestionGenerationService(
        question_repo=question_repo,
        concept_repo=seeded_concept_repo,
        llm_service=None,
    )

    with pytest.raises(RuntimeError) as exc:
        service.generate_question_for_concept(concept_id="CPT-CH01-001")
    assert "LLM service is not configured" in str(exc.value)
