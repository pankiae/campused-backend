# exam/utils.py
from typing import Dict, List, Tuple

from client_create import client
from pydantic import BaseModel, Field


class MCQSchema(BaseModel):
    question: str
    mcq: Dict[int, str] = Field(
        ...,
        description="give four options in which one or two write. like: 1, 2, 3 and 4 for option serial number.",
    )
    correct_options: int = Field(..., description="give the correct option.")


class FlashCardSchema(BaseModel):
    question: str
    answer: str = Field(
        ...,
        description="Give the accurate and concise answer",
    )
    explanation: str = Field(
        ..., description="provide the explaination or history of the provided answer."
    )


class ExamPrepare:
    def __init__(self, n: int, language: str, difficulty: str, exam: str, subject: str):
        self.n = n
        self.language = language
        self.difficulty = difficulty
        self.exam = exam
        self.subject = subject

    def _mcq_prompt(self) -> str:
        # Placeholder MCQ generation - replace with LLM or real generator
        mcq_prompt = f"""You are helpful MCQ based Exam Preparation Assiantant. You have to prepare the number of MCQ for subject as per user request for following: {self.subject} in language: {self.language} with difficulty-level: {self.difficulty}.
        Give four options where one or two can be correct answers. Provide the option with serial numbering like: 1, 2, 3, 4. Also provide the correct Answer option.
        """

        return mcq_prompt

    def _flashcard_prompt(self) -> str:
        flashcard_prompt = f"""

            You are helpful flashcard based Exam Preparation Assiantant. You have to prepare the number of flashcard for subject as per user request for following: {self.subject} in language: {self.language} with difficulty-level: {self.difficulty}.
            Give the accurate and concise answer. Also provide the explaination or history of the provided answer.
        """
        return flashcard_prompt

    def generate_exam(
        self,
        exam: str,
        subject: str,
        difficulty: str,
        language: str,
        mode: str,
        count: int = 10,
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
        if mode == "mcq":
            system_prompt = self._mcq_prompt()
            to_generate = MCQSchema
        if mode == "flashcard":
            system_prompt = self._flashcard_prompt()
            to_generate = FlashCardSchema
        questions = []
        response = client.responses.parse(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Generate the {self.n} number of the questions",
                },
            ],
            text_format=to_generate,
        )
        questions = response.output_parsed

        # token_cost is an estimated float; compute properly if using LLMs
        token_cost_estimate = round(count * (0.2 if mode == "flashcard" else 0.5), 2)
        return questions, token_cost_estimate
