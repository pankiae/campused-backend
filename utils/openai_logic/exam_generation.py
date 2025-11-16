# exam/utils.py
from typing import Dict, List

from pydantic import BaseModel, Field

from .client_create import client


class MCQSchema(BaseModel):
    question: str
    options: Dict[str, str]
    correct_options: int | list[int] = Field(
        ..., description="give the correct option."
    )


class MCQSchemaList(BaseModel):
    questions: List[MCQSchema]


class FlashCardSchema(BaseModel):
    question: str
    answer: str = Field(
        ...,
        description="Give the accurate and concise answer",
    )
    explanation: str = Field(
        ..., description="provide the explaination or history of the provided answer."
    )


class FlashCardList(BaseModel):
    questions: List[FlashCardSchema]


class ExamPrepare:
    def __init__(
        self,
        exam: str,
        subject: str,
        difficulty: str,
        language: str,
        mode: str,
        count: int,
    ):
        self.exam = exam
        self.subject = subject
        self.difficulty = difficulty
        self.language = language
        self.mode = mode
        self.n = count

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

    def generate_exam(self):
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
        if self.mode == "mcq":
            system_prompt = self._mcq_prompt()
            to_generate = MCQSchemaList
        if self.mode == "flashcard":
            system_prompt = self._flashcard_prompt()
            to_generate = FlashCardList
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
        print("Generate Questions:\n", questions)
        return questions
