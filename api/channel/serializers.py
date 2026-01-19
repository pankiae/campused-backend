# exam/serializers.py
from rest_framework import serializers

from .constants import (
    ALLOWED_DIFFICULTIES,
    ALLOWED_LANGUAGES,
    ALLOWED_MODES,
    EXAM_SUBJECTS,
)
from .models import Channel, Exam


class ChannelListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ["id", "title", "updated_at"]


class GenerateExamSerializer(serializers.Serializer):
    exam = serializers.CharField()
    subject = serializers.CharField()
    difficulty = serializers.ChoiceField(choices=ALLOWED_DIFFICULTIES)
    language = serializers.ChoiceField(choices=ALLOWED_LANGUAGES)
    mode = serializers.ChoiceField(choices=ALLOWED_MODES)
    count = serializers.IntegerField(min_value=1, max_value=100, default=10)

    def validate(self, data):
        exam = data.get("exam")
        subject = data.get("subject")

        # allow case-insensitive exam keys: normalize exam key
        # exact key must match EXAM_SUBJECTS keys (we'll try to match ignoring case)
        # prefer exact match first
        key_match = None
        for k in EXAM_SUBJECTS.keys():
            if k.lower() == exam.lower():
                key_match = k
                break

        if not key_match:
            raise serializers.ValidationError({"exam": "Unknown exam"})
        if subject not in EXAM_SUBJECTS[key_match]:
            raise serializers.ValidationError(
                {
                    "subject": f"'{subject}' is not a valid subject for exam '{key_match}'"
                }
            )

        # normalize exam to canonical key
        data["exam"] = key_match
        return data


class ExamListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = ["id", "exam", "difficulty", "updated_at"]


class ExamGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = [
            "exam",
            "difficulty",
            "language",
            "mode",
            "questions_answers",
            "updated_at",
        ]
