# exam/utils.py
import uuid
from typing import Dict, List, Tuple


def _make_mcq(i: int, language: str, difficulty: str, exam: str, subject: str) -> Dict:
    # Placeholder MCQ generation - replace with LLM or real generator
    options = [
        f"Option A for q{i}",
        f"Option B for q{i}",
        f"Option C for q{i}",
        f"Option D for q{i}",
    ]
    correct_index = i % len(options)
    return {
        "id": str(uuid.uuid4()),
        "question": f"[{exam} | {subject} | {difficulty} | {language}] MCQ question #{i}",
        "options": options,
        "correct_option_index": correct_index,
        "explanation": f"Short explanation for MCQ #{i}",
    }


def _make_flashcard(
    i: int, language: str, difficulty: str, exam: str, subject: str
) -> Dict:
    # Placeholder flashcard generation - replace with real content
    return {
        "id": str(uuid.uuid4()),
        "question": f"[{exam} | {subject} | {difficulty} | {language}] Flashcard Q#{i}",
        "answer": f"Answer for flashcard #{i}",
        "explanation": f"Short explanation for flashcard #{i}",
    }


def generate_exam(
    exam: str, subject: str, difficulty: str, language: str, mode: str, count: int = 10
) -> Tuple[List[Dict], float]:
    """
    Synchronous exam generator.

    Returns:
      (questions_list, token_cost_estimate)

    NOTE: This is a placeholder implementation that returns simple generated
    dummy questions. Replace the internals with your real generation logic,
    e.g., prompting an LLM, curriculum DB lookups, or templates.

    Keep the returned schema consistent with the API:
      - For MCQ: include 'options' and 'correct_option_index'
      - For Flashcard: include 'question' and 'answer'
    """
    questions = []
    for i in range(1, count + 1):
        if mode == "mcq":
            questions.append(_make_mcq(i, language, difficulty, exam, subject))
        else:
            questions.append(_make_flashcard(i, language, difficulty, exam, subject))

    # token_cost is an estimated float; compute properly if using LLMs
    token_cost_estimate = round(count * (0.2 if mode == "flashcard" else 0.5), 2)
    return questions, token_cost_estimate
