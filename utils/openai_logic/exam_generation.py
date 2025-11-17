# exam/utils.py
from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field

from .client_create import client


class Options(BaseModel):
    # Keys "1".."4" in JSON, but you access them as opt1..opt4 in Python
    model_config = ConfigDict(populate_by_name=True)

    opt1: str = Field(..., alias="1")
    opt2: str = Field(..., alias="2")
    opt3: str = Field(..., alias="3")
    opt4: str = Field(..., alias="4")


class MCQ(BaseModel):
    question: str
    options: Options
    correct_option: Literal["1", "2", "3", "4"]
    # required field, but allowed to be null (no default!)
    explanation: str | None


class MCQBatch(BaseModel):
    # A list of MCQs – you can optionally constrain count in schema
    questions_answers: List[MCQ] = Field(
        ...,
        description="A list of multiple-choice questions",
        json_schema_extra={"minItems": 1, "maxItems": 10},  # optional
    )


class FlashCardSchema(BaseModel):
    question: str
    answer: str = Field(
        ...,
        description="Give the accurate and concise answer",
    )
    explanation: str = Field(
        ..., description="provide the explaination or history of the provided answer."
    )


class FlashCardBatch(BaseModel):
    questions_answers: List[FlashCardSchema] = Field(
        ...,
        description="A list of flashcard questions",
        json_schema_extra={"minItems": 1, "maxItems": 20},  # optional
    )


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
            to_generate = MCQBatch
        if self.mode == "flashcard":
            system_prompt = self._flashcard_prompt()
            to_generate = FlashCardBatch
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
        questions_answers = response.output_parsed.model_dump()
        return (
            questions_answers.get("questions_answers"),
            response.usage.input_tokens,
            response.usage.output_tokens,
        )
