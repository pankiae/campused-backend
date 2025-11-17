import copy
import logging
import os
import uuid

from django.conf import settings
from django.http import FileResponse, Http404
from rest_framework import status
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.file_logic import file_loader, file_saver
from utils.openai_logic import (
    exam_generation,
    image_analyze,
    text_generation,
    token_calculation,
)

from .models import Channel, Exam
from .serializers import (
    ChannelListSerializer,
    ExamGetSerializer,
    ExamListSerializer,
    GenerateExamSerializer,
)

ALLOWED_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/jpeg",
    "image/png",
    "image/webp",
]

# Limit uploads to 10 MB per file by default; can be overridden in Django settings
MAX_FILE_SIZE = getattr(settings, "MAX_UPLOAD_FILE_SIZE", 20 * 1024 * 1024)

logger = logging.getLogger(__name__)

select_openai_model = settings.OPENAI_MODEL


# Create your views here.
class ChannelView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [FormParser, MultiPartParser]

    def post(self, request):
        uploaded_files = request.FILES.getlist("files")
        query = request.data.get("q")
        if not uploaded_files and not query:
            return Response(
                {"error": "No files or query provided"}, status=400
            )  # 400 Bad Request
        conversation = [
            {
                "role": "system",
                "content": "You are a Exam Preparation helpful assistant. You help students to prepare for their exams by providing them with relevant information and resources. You can also help them to create study plans and schedules. You are very friendly and always respond in a positive manner. You can provide the answer directly or MCQ questions if the user asks for it or on your own for their better clarity about the topics.",
            }
        ]

        gather_tokens = {"input": 0, "output": 0}

        logger.info("Received %d files and query: %s", len(uploaded_files), query)
        for file in uploaded_files:
            if file.content_type not in ALLOWED_TYPES:
                return Response(
                    {"error": f"File type {file.content_type} not allowed"}, status=400
                )

            ext = os.path.splitext(file.name)[1].lower().strip(".")
            logger.debug("Processing file: %s with extension: %s", file.name, ext)

            # Basic file size check
            try:
                size = getattr(file, "size", None)
                if size is not None and size > MAX_FILE_SIZE:
                    logger.warning(
                        "File %s exceeds max size (%d > %d)",
                        file.name,
                        size,
                        MAX_FILE_SIZE,
                    )
                    return Response({"error": "File too large"}, status=400)
            except Exception:
                # don't fail the whole request if size can't be determined
                logger.debug(
                    "Could not determine file size for %s", file.name, exc_info=True
                )
            if ext in ["jpg", "jpeg", "png", "webp"]:
                logger.debug("Processing image file: %s", file.name)
                try:
                    image_transcribe, image_input_tokens, image_output_tokens = (
                        image_analyze.image_analyze(file)
                    )
                    gather_tokens["input"] += image_input_tokens
                    gather_tokens["output"] += image_output_tokens
                except Exception:
                    logger.exception("Failed to analyze image: %s", file.name)
                    return Response(
                        {"error": "Failed to process image file"}, status=500
                    )
                logger.debug("Extracted text from image: %s", image_transcribe)
                conversation.append(
                    {
                        "role": "system",
                        "content": "This is the information that I have extracted from the image that user shared: \n"
                        + image_transcribe,
                    }
                )

            elif ext in ["docx", "pdf"]:
                logger.debug("Processing document file: %s", file.name)
                try:
                    docx_transcribe = file_loader.read_file(file.file)
                except Exception:
                    logger.exception("Failed to read document: %s", file.name)
                    return Response(
                        {"error": "Failed to process document file"}, status=500
                    )
                logger.debug("Extracted text from document: %s", docx_transcribe)
                conversation.append(
                    {
                        "role": "system",
                        "content": "This is the information that I have extracted from the document that user shared:\n\n"
                        + docx_transcribe,
                    }
                )

        channel_id = uuid.uuid4()
        if query:
            try:
                # sorted_conversation = remove_file_name_conversation(conversation)
                res, text_input_tokens, text_output_tokens = (
                    text_generation.text_generation(
                        conversation + [{"role": "user", "content": query}],
                        select_openai_model,
                    )
                )
                gather_tokens["input"] += text_input_tokens
                gather_tokens["output"] += text_output_tokens
            except Exception:
                logger.exception("Text generation failed for query: %s", query)
                return Response({"error": "Failed to generate text"}, status=500)

            user_query = {"role": "user", "content": query}
            if uploaded_files:
                files = file_saver.save_uploaded_files(
                    request.user.id, channel_id, uploaded_files
                )
                user_query["files"] = files
            query_res = {"role": "assistant", "content": res}
            conversation.extend([user_query, query_res])

        gather_tokens_cost_sum = token_calculation.sum_input_output_token_cost(
            select_openai_model, gather_tokens["input"], gather_tokens["output"]
        )

        try:
            title, _, _ = text_generation.title_generation(query)
            logger.info(f"Generated Title: {title}")
        except Exception as e:
            logger.warning(f"Title generation failed: {e}")
            title = "new chat"

        # that async function response going to use here. in the title section
        channnel = Channel.objects.create(
            id=channel_id,
            user=request.user,
            title=title,
            context=conversation,
            token_cost=gather_tokens_cost_sum,
        )
        logger.info(
            "Conversation saved for user %s (messages=%d)",
            request.user,
            len(conversation),
        )

        request._request.gather_tokens = gather_tokens
        request._request.gather_tokens["model"] = select_openai_model
        return Response(
            {
                "conversation": conversation,
                "title": title,
                "channel_id": channnel.id,
            },
            status=201,  # 201 Created is often used for successful POST requests
        )


class ListChannelView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChannelListSerializer

    def get_queryset(self):
        return Channel.objects.filter(user=self.request.user).order_by("-updated_at")


class PatchChannelView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, channel_id):
        conversation = Channel.objects.get(id=channel_id, user=request.user)
        return Response(
            {"conversation": conversation.context},
            status=status.HTTP_200_OK,
        )

    def post(self, request, channel_id):
        uploaded_files = request.FILES.getlist("files")
        query = request.data.get("q")
        if not uploaded_files and not query:
            return Response(
                {"error": "No files or query provided"}, status=400
            )  # 400 Bad Request
        try:
            gather_tokens = {"input": 0, "output": 0}

            channel = Channel.objects.get(id=channel_id, user=request.user)
            conversation = channel.context
            logger.info("conversation: %s", conversation)
        except Channel.DoesNotExist:
            return Response(
                {"error": "Channel not found"}, status=status.HTTP_404_NOT_FOUND
            )
        logger.info(
            "Patching channel %s: received %d files and query: %s",
            channel_id,
            len(uploaded_files),
            query,
        )

        for file in uploaded_files:
            if file.content_type not in ALLOWED_TYPES:
                return Response(
                    {"error": f"File type {file.content_type} not allowed"}, status=400
                )

            ext = os.path.splitext(file.name)[1].lower().strip(".")
            logger.debug("Processing file: %s with extension: %s", file.name, ext)

            # Basic file size check
            try:
                size = getattr(file, "size", None)
                if size is not None and size > MAX_FILE_SIZE:
                    logger.warning(
                        "File %s exceeds max size (%d > %d)",
                        file.name,
                        size,
                        MAX_FILE_SIZE,
                    )
                    return Response({"error": "File too large"}, status=400)
            except Exception:
                logger.debug(
                    "Could not determine file size for %s", file.name, exc_info=True
                )

            if ext in ["jpg", "jpeg", "png", "webp"]:
                logger.debug("Processing image file: %s", file.name)
                try:
                    image_transcribe, image_input_tokens, image_output_tokens = (
                        image_analyze.image_analyze(file)
                    )
                    gather_tokens["input"] += image_input_tokens
                    gather_tokens["output"] += image_output_tokens

                except Exception:
                    logger.exception("Failed to analyze image: %s", file.name)
                    return Response(
                        {"error": "Failed to process image file"}, status=500
                    )
                logger.debug("Extracted text from image: %s", image_transcribe)
                conversation.append(
                    {
                        "role": "system",
                        "content": "This is the information that I have extracted from the image that user shared: \n"
                        + image_transcribe,
                    }
                )

            elif ext in ["docx", "pdf"]:
                logger.debug("Processing document file: %s", file.name)
                try:
                    docx_transcribe = file_loader.read_file(file.file)
                except Exception:
                    logger.exception("Failed to read document: %s", file.name)
                    return Response(
                        {"error": "Failed to process document file"}, status=500
                    )
                logger.debug("Extracted text from document: %s", docx_transcribe)
                conversation.append(
                    {
                        "role": "system",
                        "content": "This is the information that I have extracted from the document that user shared:\n\n"
                        + docx_transcribe,
                    }
                )
        if query:
            try:
                sorted_conversation = remove_file_name_conversation(conversation)

                res, text_input_tokens, text_output_tokens = (
                    text_generation.text_generation(
                        sorted_conversation + [{"role": "user", "content": query}],
                        select_openai_model,
                    )
                )
                gather_tokens["input"] += text_input_tokens
                gather_tokens["output"] += text_output_tokens

            except Exception:
                logger.exception("Text generation failed for query: %s", query)
                return Response({"error": "Failed to generate text"}, status=500)

            user_query = {"role": "user", "content": query}

            if uploaded_files:
                files = file_saver.save_uploaded_files(
                    request.user.id, channel_id, uploaded_files
                )
                user_query["files"] = files

            query_res = {"role": "assistant", "content": res}
            conversation.extend([user_query, query_res])

        gather_tokens_cost_sum = token_calculation.sum_input_output_token_cost(
            select_openai_model, gather_tokens["input"], gather_tokens["output"]
        )

        channel.context = conversation
        print(channel.token_cost, gather_tokens_cost_sum)
        channel.token_cost = token_calculation.update_token_cost(
            channel.token_cost, gather_tokens_cost_sum
        )

        channel.save()
        logger.info(
            "Updated channel %s for user %s (messages=%d)",
            channel_id,
            request.user,
            len(conversation),
        )
        request._request.gather_tokens = gather_tokens
        request._request.gather_tokens["model"] = select_openai_model
        return Response(
            {"conversation": conversation},
            status=200,
        )


def remove_file_name_conversation(conversation):
    new_conversation = []
    for message in conversation:
        msg_copy = copy.deepcopy(message)
        msg_copy.pop("files", None)
        new_conversation.append(msg_copy)
    return new_conversation


class FileFetchView(APIView):
    """
    Securely stream a file belonging to the authenticated user,
    under media/<user_id>/<channel_id>/<file_name>.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, channel_id, file_name):
        try:
            # Verify the channel belongs to the requesting user
            channel = Channel.objects.get(id=channel_id, user=request.user)
            print(channel.id)
        except Channel.DoesNotExist:
            return Response({"error": "Channel not found or unauthorized"}, status=404)

        # Construct file path
        file_path = os.path.join(
            settings.MEDIA_ROOT, str(request.user.id), str(channel_id), file_name
        )
        print("file path: ", file_path)

        # Check if file exists
        if not os.path.exists(file_path):
            raise Http404("File not found")

        # Stream file instead of loading into memory
        try:
            response = FileResponse(open(file_path, "rb"))
            response["Content-Disposition"] = f'inline; filename="{file_name}"'
            return response
        except Exception as e:
            return Response({"error": f"Unable to read file: {str(e)}"}, status=500)


class GenerateExamAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GenerateExamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        gather_tokens = {"input": 0, "output": 0}

        try:
            # synchronous call to generate_exam
            questions_answers, text_input_token, text_output_token = (
                exam_generation.ExamPrepare(
                    exam=data["exam"],
                    subject=data["subject"],
                    difficulty=data["difficulty"],
                    language=data["language"],
                    mode=data["mode"],
                    count=data["count"],
                ).generate_exam()
            )
            print("questions_answers: \n", questions_answers)
            gather_tokens["input"] += text_input_token
            gather_tokens["output"] += text_output_token
            gather_tokens_cost_sum = token_calculation.sum_input_output_token_cost(
                select_openai_model, gather_tokens["input"], gather_tokens["output"]
            )
            exam = Exam.objects.create(
                user=request.user,
                exam=data["exam"],
                subject=data["subject"],
                difficulty=data["difficulty"],
                language=data["language"],
                mode=data["mode"],
                questions_answers=questions_answers,
                token_cost=gather_tokens_cost_sum,
            )
            logger.info(
                "Conversation saved for user %s (messages=%d)",
                request.user,
                len(questions_answers),
            )
            request._request.gather_tokens = gather_tokens
            request._request.gather_tokens["model"] = select_openai_model
            return Response(
                {
                    "status": "completed",
                    "exam": data["exam"],
                    "subject": data["subject"],
                    "difficulty": data["difficulty"],
                    "language": data["language"],
                    "mode": data["mode"],
                    "count": data["count"],
                    "questions_answers": questions_answers,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ListExamView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExamListSerializer

    def get_queryset(self):
        return Exam.objects.filter(user=self.request.user).order_by("-updated_at")


class GetExamView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExamGetSerializer

    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id, user=request.user)
        serializer = self.serializer_class(exam)
        return Response(serializer.data)
